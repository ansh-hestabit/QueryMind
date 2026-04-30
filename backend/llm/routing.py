
"""
QueryMind — Model Routing: Route queries to OpenRouter or vLLM
"""
import structlog
from typing import Literal
from langchain_openai import ChatOpenAI
from backend.core.config import settings

logger = structlog.get_logger(__name__)


def _estimate_query_complexity(query: str) -> Literal["simple", "complex"]:
    """
    Heuristic to estimate query complexity for model routing.
    """
    simple_keywords = ["how many", "count", "total", "sum", "average", "avg", "show me"]
    complex_keywords = ["join", "group by", "having", "window function", "over", "partition", "rank", "cte", "with"]

    query_lower = query.lower()

    if any(keyword in query_lower for keyword in complex_keywords):
        return "complex"

    if len(query.split()) > 20:
        return "complex"

    return "simple"


def get_llm_for_query(
    query: str,
    task: Literal["sql", "intent", "insight", "dashboard"] = "sql"
) -> ChatOpenAI:
    """
    Get appropriate LLM based on query complexity and task.
    """
    complexity = _estimate_query_complexity(query)

    if complexity == "simple" and task == "sql":
        logger.info("Routing simple SQL query to vLLM", query=query[:50])
        return ChatOpenAI(
            model=settings.VLLM_MODEL,
            base_url=settings.VLLM_BASE_URL,
            api_key="dummy",  # vLLM doesn't require API key by default
            temperature=0.1,
        )

    logger.info("Routing query to OpenRouter", complexity=complexity, task=task, query=query[:50])
    return ChatOpenAI(
        model=settings.LLM_SQL_MODEL if task == "sql" else settings.LLM_FAST_MODEL,
        base_url=settings.OPENROUTER_BASE_URL,
        api_key=settings.OPENROUTER_API_KEY,
        temperature=0.1,
    )
