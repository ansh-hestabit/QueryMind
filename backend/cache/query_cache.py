
"""
QueryMind — Semantic Query Cache & SQL Generation Cache
"""
import json
import structlog
from typing import Any, Dict, Optional
from datetime import timedelta
from backend.core.config import settings
from backend.core.redis_client import get_redis
from backend.core.qdrant_client import get_qdrant
from langchain_openai import OpenAIEmbeddings
from qdrant_client.models import Filter, FieldCondition, MatchValue

logger = structlog.get_logger(__name__)

# Initialize embeddings lazily to avoid import-time issues
_embeddings = None

def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = OpenAIEmbeddings(
            model=settings.LLM_EMBEDDING_MODEL,
            base_url=settings.OPENROUTER_BASE_URL,
            api_key=settings.OPENROUTER_API_KEY,
        )
    return _embeddings


class QueryCache:
    def __init__(self):
        self.redis_ttl = timedelta(hours=24)
        self.similarity_threshold = settings.VLLM_EMBEDDING_SIMILARITY_THRESHOLD

    async def get_cached_result(
        self, query: str, source_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Check cache for semantically similar query on same source.
        Returns None if not found or expired.
        """
        try:
            qdrant = get_qdrant()
            embeddings = get_embeddings()
            query_embedding = await embeddings.aembed_query(query)

            search_result = await qdrant.search(
                collection_name=settings.QDRANT_COLLECTION_QUERY_CACHE,
                query_vector=query_embedding,
                query_filter=Filter(
                    must=[FieldCondition(key="source_id", match=MatchValue(value=source_id))]
                ),
                limit=1,
                score_threshold=self.similarity_threshold,
            )

            if search_result:
                point = search_result[0]
                cache_key = f"query_result:{point.id}"
                redis = await get_redis()
                cached_data = await redis.get(cache_key)
                if cached_data:
                    from backend.observability.prometheus import cache_hits
                    cache_hits.inc()
                    logger.info("Cache hit", source_id=source_id)
                    return json.loads(cached_data)

        except Exception as e:
            logger.warning("Cache lookup failed", error=str(e))

        from backend.observability.prometheus import cache_misses
        cache_misses.inc()
        return None

    async def cache_result(
        self,
        query: str,
        source_id: str,
        sql: str,
        result: Dict[str, Any],
    ) -> None:
        """Cache a query result and SQL for future reuse."""
        try:
            from python_ulid import ULID
            cache_id = str(ULID())

            embeddings = get_embeddings()
            query_embedding = await embeddings.aembed_query(query)

            qdrant = get_qdrant()
            await qdrant.upsert(
                collection_name=settings.QDRANT_COLLECTION_QUERY_CACHE,
                points=[
                    {
                        "id": cache_id,
                        "vector": query_embedding,
                        "payload": {
                            "query": query,
                            "source_id": source_id,
                            "sql": sql,
                        },
                    }
                ],
            )

            redis_key = f"query_result:{cache_id}"
            redis = await get_redis()
            await redis.setex(
                redis_key, json.dumps(result), ex=self.redis_ttl
            )

            logger.info("Cached query result", cache_id=cache_id, source_id=source_id)

        except Exception as e:
            logger.warning("Cache write failed", error=str(e))


query_cache = QueryCache()
