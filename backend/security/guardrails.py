
"""
QueryMind — Query Safety Guardrails
Blocks dangerous SQL statements, enforces row limits, etc.
"""
import structlog
import sqlglot
from typing import Tuple, Optional
from backend.core.config import settings

logger = structlog.get_logger(__name__)

DANGEROUS_KEYWORDS = {
    "DROP",
    "DELETE",
    "UPDATE",
    "INSERT",
    "TRUNCATE",
    "ALTER",
    "CREATE",
    "REPLACE",
    "GRANT",
    "REVOKE",
    "EXECUTE",
    "CALL",
    "COPY",
}


def validate_sql_safety(sql: str) -> Tuple[bool, Optional[str]]:
    """
    Validate SQL query for safety.
    Returns (is_safe, error_message).
    """
    try:
        sql_upper = sql.upper()

        for keyword in DANGEROUS_KEYWORDS:
            if f"{keyword} " in sql_upper or sql_upper.startswith(keyword):
                return False, f"Query contains forbidden keyword: {keyword}"

        try:
            parsed = sqlglot.parse_one(sql)
            statement_type = parsed.key
            if statement_type not in ("SELECT", "WITH"):
                return False, f"Only SELECT statements are allowed (found: {statement_type})"
        except Exception:
            logger.warning("SQL parsing failed, falling back to keyword check")

        return True, None

    except Exception as e:
        logger.error("SQL safety validation failed", error=str(e))
        return False, "Query validation failed"


def enforce_row_limit(sql: str, max_rows: Optional[int] = None) -> str:
    """
    Add or enforce a row limit on the SQL query.
    """
    if max_rows is None:
        max_rows = settings.MAX_QUERY_ROWS

    try:
        parsed = sqlglot.parse_one(sql)
        limit = parsed.find(sqlglot.exp.Limit)

        if limit:
            current_limit = int(limit.expression.this)
            if current_limit > max_rows:
                limit.set("expression", sqlglot.exp.Literal(this=str(max_rows)))
        else:
            parsed = parsed.limit(max_rows)

        return parsed.sql(dialect="postgres")

    except Exception:
        logger.warning("Could not parse SQL to add limit, appending LIMIT clause")
        if "LIMIT" not in sql.upper():
            return f"{sql.rstrip(';')} LIMIT {max_rows};"
        return sql
