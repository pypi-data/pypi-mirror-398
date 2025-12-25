from django.conf import settings
import hashlib
import datetime

class EmbeddingsCache:
    """Simple LRU Cache for embeddings calls to either the local or remote LLM.

    Just in memory, so that re-runs of rebuilding the search caches are much snappier.
    For the most part, when rebuilding search caches, the document according to the
    embeddings are equivalent, and so there's no need to ask the LLM to regenerate them.

    CACHE_SIZE is in number of items, not memory.
    """

    def __init__(self, cache_size):
        self.cache = {}
        self.cache_size = cache_size

    def hash_summary(self, summary):
        return hashlib.sha256(summary.encode()).hexdigest()

    def add(self, summary, embedding):
        self.cache[self.hash_summary(summary)] = {
            "embedding": embedding,
            "used": datetime.datetime.now()
        }

        if len(self.cache) > self.cache_size:
            # Let's just lop off a quarter of it, arbitrarily
            for key in [ k for (k,v) in sorted(self.cache.items(), key=lambda item: item[1]["used"])][0:int(self.cache_size / 4)]:
                del self.cache[key]

    def get(self, summary):
        sha = self.hash_summary(summary)
        if sha in self.cache:
            resp = self.cache[sha]
            resp["used"] = datetime.datetime.now()
            return resp["embedding"]


embeddings_cache = EmbeddingsCache(getattr(settings, "SEMANTIC_SEARCH_EMBEDDINGS_CACHE_SIZE", 200))
