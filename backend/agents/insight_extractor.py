"""
QueryMind — Insight Extractor Node
"""
import json
from openai import AsyncOpenAI
from backend.agents.state import QueryMindState
from backend.core.config import settings
import structlog
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logger = structlog.get_logger(__name__)

async def insight_extractor_node(state: QueryMindState) -> QueryMindState:
    """Generate a natural language insight based on the data."""
    
    if state.get("error"):
        state["summary"] = f"I encountered an error I couldn't resolve: {state['error']}"
        state["reasoning"] = ["Insight Extractor: Skipped due to error."]
        return state
        
    if not state.get("results"):
        state["summary"] = "The query returned no results."
        state["reasoning"] = ["Insight Extractor: Skipped due to empty results."]
        return state
        
    client = AsyncOpenAI(
        api_key=settings.OPENROUTER_API_KEY,
        base_url=settings.OPENROUTER_BASE_URL,
        timeout=settings.OPENROUTER_TIMEOUT_SECONDS,
    )
    
    # Cap the data sample sent to LLM to save tokens
    sample_data = json.dumps(state["results"][:20], default=str)
    
    prompt = f"""
        Question: {state['question']}
        SQL Executed: {state['sql']}
        Data Sample (up to 20 rows):
        {sample_data}

        Provide a concise, highly analytical summary answering the user's question. 
        Point out any obvious trends, anomalies, or top performers in the data.
        DO NOT explain the SQL.
    """

    try:
        completion = await client.chat.completions.create(
            model=settings.LLM_FAST_MODEL,
            messages=[
                {
                    "role": "system", 
                    "content": "You are a senior data analyst. If you detect an anomaly, OR if the user explicitly asks to alert/send/message Slack, YOU MUST use the send_slack_notification tool."
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "send_slack_notification",
                        "description": "Send an anomaly alert or insight digest to a Slack channel.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "message": {"type": "string", "description": "The alert message to send"},
                                "channel": {"type": "string", "description": "The slack channel. Defaults to #social if not specified by user."},
                            },
                            "required": ["message"],
                        },
                    },
                }
            ],
        )
    except Exception as exc:
        state["summary"] = f"Failed to generate summary: {exc}"
        state["reasoning"] = [state["summary"]]
        return state
    
    # Check if a tool was called
    message = completion.choices[0].message
    
    # Debug log for user visibility
    logger.info("insight_extractor_llm_response", has_tool_calls=bool(message.tool_calls), tool_calls=str(message.tool_calls))
    
    state["summary"] = (message.content or "").strip()
    
    if message.tool_calls:
        for tool_call in message.tool_calls:
            if tool_call.function.name == "send_slack_notification":
                args = json.loads(tool_call.function.arguments)
                channel = args.get("channel", "#social")
                slack_msg = args.get("message", "No message provided")
                
                # If the LLM put the entire summary into the tool call and left content blank, use it
                if not state["summary"]:
                    state["summary"] = slack_msg
                
                state["reasoning"].append(f"Insight Extractor: Attempting to send Slack alert to {channel}")
                
                if settings.SLACK_BOT_TOKEN:
                    try:
                        client = WebClient(token=settings.SLACK_BOT_TOKEN)
                        client.chat_postMessage(channel=channel, text=slack_msg)
                        state["reasoning"].append("Insight Extractor: Successfully sent Slack notification natively.")
                    except SlackApiError as e:
                        logger.error("slack_api_error", error=e.response["error"])
                        state["reasoning"].append(f"Insight Extractor: Failed to send Slack alert. Error: {e.response['error']}")
                else:
                    state["reasoning"].append("Insight Extractor: Slack notification skipped. SLACK_BOT_TOKEN not configured.")
    
    if not state["summary"]:
        state["summary"] = "Data processed successfully."
        
    state["reasoning"].append("Insight Extractor: Generated data summary.")
    
    return state
