from django.db import models
from pgvector.django import HnswIndex, VectorField
from torque.models import SearchCacheDocument


from semantic_search.llm import llm


class SemanticSearchCacheDocument(models.Model):
    search_cache_document = models.ForeignKey(
        SearchCacheDocument,
        on_delete=models.CASCADE,
        related_name="semantic_documents",
    )
    data = models.TextField()
    data_embedding = VectorField(
        dimensions=llm.dimensions,
        null=True,
    )

    class Meta:
        indexes = [
            HnswIndex(
                name="data_embedding_index",
                fields=["data_embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            ),
        ]
