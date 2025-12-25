import asyncio

from django.conf import settings
from django.contrib.postgres.search import SearchQuery
from django.db import transaction
from django.db.models import F, Q, Window
from django.db.models.functions import DenseRank
from django.dispatch import receiver
import orjson
from pgvector.django import CosineDistance

from torque import models as torque_models
from torque.signals import search_filter, search_index_rebuilt, update_cache_document

from semantic_search.llm import llm
from semantic_search.models import SemanticSearchCacheDocument
from semantic_search.utils import (
    batch_queryset,
    filter_queries,
    build_semantic_summaries,
)

from semantic_search.embedding_cache import embeddings_cache

BATCH_SIZE = 20
MAX_CONCURRENCY = 5


@receiver(update_cache_document)
def update_semantic_cache_document(sender, **kwargs):
    cache_document = kwargs["cache_document"]
    document_dict = kwargs["document_dict"]

    with transaction.atomic():
        SemanticSearchCacheDocument.objects.filter(
            search_cache_document=cache_document
        ).delete()

        semantic_summaries = build_semantic_summaries(document_dict)

        for semantic_summary in semantic_summaries:
            embeddings = embeddings_cache.get(semantic_summary)

            if not embeddings:
                embeddings = llm.get_embeddings(semantic_summary)
                embeddings_cache.add(semantic_summary, embeddings)

            semantic_search_cache_documents = [
                SemanticSearchCacheDocument(
                    search_cache_document=cache_document,
                    data=semantic_summary,
                    data_embedding=embedding,
                )
                for embedding in embeddings
            ]

        SemanticSearchCacheDocument.objects.bulk_create(semantic_search_cache_documents)


def rebuild_semantic_search_index_batch(scds, wiki_config):
    semantic_summaries_to_fetch = []
    semantic_sc_documents = []

    for scd in scds:
        cached_document_dict = torque_models.DocumentDictCache.objects.get(
            document=scd.document, wiki_config=wiki_config
        )

        document_dict = orjson.loads(cached_document_dict.dictionary)

        semantic_summaries = build_semantic_summaries(document_dict["fields"])

        for semantic_summary in semantic_summaries:
            embeddings = embeddings_cache.get(semantic_summary)

            if embeddings:
                semantic_sc_documents.append(
                    SemanticSearchCacheDocument(
                        search_cache_document=scd,
                        data_embedding=embeddings,
                        data=semantic_summary,
                    )
                )
            else:
                semantic_summaries_to_fetch.append((scd, semantic_summary))

    llm_embeddings = llm.get_embeddings(
        [summary for _scd, summary in semantic_summaries_to_fetch]
    )

    for (scd, semantic_summary), embedding in zip(
        semantic_summaries_to_fetch, llm_embeddings
    ):
        embeddings_cache.add(semantic_summary, embedding)
        semantic_sc_documents.append(
            SemanticSearchCacheDocument(
                search_cache_document=scd,
                data_embedding=embedding,
                data=semantic_summary,
            )
        )
    return semantic_sc_documents

    #SemanticSearchCacheDocument.objects.bulk_create(semantic_sc_documents)


@receiver(search_index_rebuilt)
def rebuild_semantic_search_index(sender, **kwargs):
    wiki_config = kwargs["wiki_config"]

    search_cache_documents = torque_models.SearchCacheDocument.objects.filter(
        wiki_config=wiki_config
    ).select_related("document")

    import threading

    batches = list(batch_queryset(search_cache_documents, BATCH_SIZE))
    batch_chunks = [(batches[i::MAX_CONCURRENCY], i) for i in range(MAX_CONCURRENCY)]
    results = [[]] * MAX_CONCURRENCY

    def rebuild_batch_chunk(batch_chunk_pair):
        for scds in batch_chunk_pair[0]:
            results[batch_chunk_pair[1]].append(rebuild_semantic_search_index_batch(scds, wiki_config))

    threads = [
        threading.Thread(target=rebuild_batch_chunk, args=(chunk,))
        for chunk in batch_chunks if chunk[0]  # Only create threads for non-empty chunks
    ]

    for thread in threads:
        thread.start()

    sscds_to_add = []
    for thread in threads:
        thread.join()

    for result in results:
        for sscds in result:
            # If there was an error for whatever reason, and therefore sscds didn't get set
            # just don't add it and move on
            if sscds:
                sscds_to_add.extend(sscds)

    SemanticSearchCacheDocument.objects.bulk_create(sscds_to_add, batch_size=BATCH_SIZE)

@receiver(search_filter)
def semantic_filter(sender, **kwargs):
    similarity = getattr(settings, "SEMANTIC_SEARCH_SIMILARITY", 0.7)

    cache_documents = kwargs["cache_documents"]
    qs = kwargs.get("qs")
    include_snippets = kwargs.get("include_snippets", False)
    qs_without_negations = filter_queries(qs, keep_negations=False)

    if qs_without_negations:
        embeddings = llm.get_embeddings(qs_without_negations)

        distances = {}
        semantic_qs = Q()
        for i, embedding in enumerate(embeddings):
            distance_col_name = f"distance_{i}"
            distances[distance_col_name] = CosineDistance(
                "semantic_documents__data_embedding", embedding
            )
            semantic_qs |= Q(**{f"{distance_col_name}__lte": similarity})

        # filters phrases and negations from the queries,
        # what we're calling exact or advanced search
        filter_qs = Q()
        for q in filter_queries(qs):
            if q != "":
                filter_qs &= Q(data_vector=SearchQuery(q, search_type="websearch"))

        results = (
            cache_documents.alias(**distances)
            .annotate(score=1 - F("distance_0"))
            .filter(semantic_qs)
            .filter(filter_qs)
        )

        if include_snippets:
            results = results.annotate(snippets=F("semantic_documents__data"))

        return results
