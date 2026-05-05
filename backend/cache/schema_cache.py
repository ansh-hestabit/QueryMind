"""
QueryMind — Redis Schema Cache
"""
import json
import structlog
from dataclasses import asdict
from typing import Optional

from backend.core.redis_client import get_redis
from backend.connectors.base import SchemaInfo, TableMeta, ColumnMeta, SourceType

logger = structlog.get_logger(__name__)

CACHE_TTL_SECONDS = 86400  # 24 hours

def _dict_to_schema_info(data: dict) -> SchemaInfo:
    """Convert JSON dict back into SchemaInfo dataclass hierarchy."""
    tables = []
    for t in data.get("tables", []):
        columns = [ColumnMeta(**c) for c in t.get("columns", [])]
        table = TableMeta(
            name=t["name"],
            schema=t.get("schema", "public"),
            columns=columns,
            row_count=t.get("row_count", 0),
            description=t.get("description", "")
        )
        tables.append(table)
        
    return SchemaInfo(
        source_id=data["source_id"],
        source_type=SourceType(data["source_type"]),
        database=data["database"],
        tables=tables
    )

async def get_cached_schema(source_id: str) -> Optional[SchemaInfo]:
    """Retrieve schema from Redis if it exists."""
    try:
        redis = await get_redis()
        cached = await redis.get(f"schema:{source_id}")
        if cached:
            data = json.loads(cached)
            return _dict_to_schema_info(data)
    except Exception as exc:
        logger.warning("schema_cache_read_error", error=str(exc))
    return None

async def set_cached_schema(source_id: str, schema: SchemaInfo) -> None:
    """Store schema in Redis with TTL."""
    try:
        redis = await get_redis()
        data = asdict(schema)
        # Convert Enum to value
        data["source_type"] = data["source_type"].value
        await redis.setex(
            f"schema:{source_id}", 
            CACHE_TTL_SECONDS, 
            json.dumps(data)
        )
        logger.info("schema_cached_in_redis", source_id=source_id)
    except Exception as exc:
        logger.warning("schema_cache_write_error", error=str(exc))

async def invalidate_cached_schema(source_id: str) -> None:
    """Delete schema cache when it is manually crawled."""
    try:
        redis = await get_redis()
        await redis.delete(f"schema:{source_id}")
        logger.info("schema_cache_invalidated", source_id=source_id)
    except Exception as exc:
        logger.warning("schema_cache_invalidate_error", error=str(exc))
