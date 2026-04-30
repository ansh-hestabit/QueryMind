"""
QueryMind — Query Validator Node
"""
import re
from backend.agents.state import QueryMindState
from backend.core.config import settings


def _normalize_leading_dot_table_refs(sql: str) -> tuple[str, bool]:
    """
    Fix invalid table refs like `FROM .titanic` or `JOIN .orders`.
    This commonly appears when historical schema context had empty schema + dot.
    """
    pattern = re.compile(r"\b(FROM|JOIN)\s+\.\s*([A-Za-z_][A-Za-z0-9_]*)", flags=re.IGNORECASE)
    fixed = pattern.sub(r"\1 \2", sql)
    return fixed, fixed != sql

import sqlglot
from sqlglot import exp

def _is_safe_read_only(sql: str) -> tuple[bool, str]:
    """Check if SQL is purely read-only using AST parsing."""
    try:
        expressions = sqlglot.parse(sql, read="duckdb")
        for expression in expressions:
            if not expression:
                continue
            
            # Look for any forbidden node types in the AST
            forbidden_types = [
                (exp.Drop, "DROP"), (exp.Delete, "DELETE"), (exp.Insert, "INSERT"),
                (exp.Update, "UPDATE"), (exp.Alter, "ALTER"), (exp.Truncate, "TRUNCATE"),
                (exp.Command, "COMMAND"), (exp.Grant, "GRANT"), (exp.Revoke, "REVOKE"),
                (exp.Create, "CREATE")
            ]
            
            for node_type, name in forbidden_types:
                if expression.find(node_type):
                    return False, f"AST Security Violation: '{name}' operation is forbidden."
        
        return True, ""
    except Exception as e:
        # Fallback to strict string matching if parsing fails
        forbidden = ["INSERT ", "UPDATE ", "DELETE ", "DROP ", "ALTER ", "TRUNCATE ", "GRANT ", "REVOKE "]
        sql_upper = sql.upper()
        for word in forbidden:
            if word in sql_upper:
                return False, f"Security Violation: Unparseable SQL contains forbidden keyword '{word.strip()}'."
        return True, ""


async def query_validator_node(state: QueryMindState) -> QueryMindState:
    """Validate the SQL for safety (Read-Only) using sqlglot before execution."""
    normalized_sql, changed = _normalize_leading_dot_table_refs(state["sql"])
    if changed:
        state["sql"] = normalized_sql
        state["reasoning"] = ["Query Validator: Normalized invalid leading-dot table reference."]
    else:
        state["reasoning"] = []

    is_safe, error_msg = _is_safe_read_only(state["sql"])
    
    if not is_safe:
        state["error"] = error_msg
        state["reasoning"].append(error_msg)
        return state
            
    state["reasoning"].append("Query Validator: SQL passed sqlglot AST security check.")
    return state

