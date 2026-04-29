"""
QueryMind — Dashboard Agent Node
"""
from backend.dashboard_engine.spec import build_dashboard_spec
from backend.agents.state import QueryMindState

async def dashboard_agent_node(state: QueryMindState) -> QueryMindState:
    """Generate a UI Chart Spec based on the data if the intent was 'dashboard'."""
    if state.get("error") or not state.get("results"):
        return state
        
    # Only run if intent is explicitly dashboard
    if state.get("intent") != "dashboard":
        return state

    try:
        state["dashboard_spec"] = build_dashboard_spec(
            question=state["question"],
            results=state["results"],
        )
        state["reasoning"] = ["Dashboard Agent: Generated chart specification via schema-based selector."]
    except Exception as e:
        state["reasoning"] = [f"Dashboard Agent: Failed to generate chart spec: {e}"]
        
    return state
