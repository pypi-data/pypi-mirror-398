import asyncio
import httpx
import orjson
from django.conf import settings
from tenacity import retry, stop_after_attempt, wait_random_exponential

TIMEOUT = 60.0 * 8
RETRIES = 5


class LLM:
    def __init__(self):
        self.api_base = getattr(settings, "SEMANTIC_SEARCH_EMBEDDING_API_BASE_URL")
        self.api_key = getattr(settings, "SEMANTIC_SEARCH_EMBEDDING_API_KEY")
        self.model_name = getattr(settings, "SEMANTIC_SEARCH_EMBEDDING_MODEL")
        self.dimensions = getattr(settings, "SEMANTIC_SEARCH_NUM_DIMENSIONS", 768)

    @retry(stop=stop_after_attempt(RETRIES), wait=wait_random_exponential(multiplier=1, min=4, max=60))
    async def aget_embeddings(self, texts, *, prompt_name=None) -> list[list[float]]:
        data = {"input": texts, "model": self.model_name, "dimensions": self.dimensions}
        if prompt_name:
            data["type"] = prompt_name

        async with httpx.AsyncClient(
            base_url=self.api_base,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=TIMEOUT,
        ) as client:
            response = await client.post("embeddings", content=orjson.dumps(data))
            response.raise_for_status()

        payload = orjson.loads(response.text)
        results = payload.get("data", [])
        embeddings = [result.get("embedding") for result in results]

        return embeddings

    def get_embeddings(self, texts, *, prompt_name=None) -> list[list[float]]:
        return asyncio.run((self.aget_embeddings(texts, prompt_name=prompt_name)))


llm = LLM()
