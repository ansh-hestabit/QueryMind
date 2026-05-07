import os
import structlog
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from mcp.server.fastmcp import FastMCP

logger = structlog.get_logger(__name__)

mcp = FastMCP("Slack Server")

@mcp.tool()
def send_slack_notification(message: str, channel: str = "#social") -> str:
    """Send a Slack notification with the summary or alert to a specific channel.
    
    Args:
        message: The actual summary or alert text to send.
        channel: The slack channel to send to, defaults to #social.
    """
    token = os.getenv("SLACK_BOT_TOKEN")
    if not token:
        logger.error("SLACK_BOT_TOKEN not found in environment.")
        return "Failed: SLACK_BOT_TOKEN not configured on MCP Server."
        
    client = WebClient(token=token)
    try:
        response = client.chat_postMessage(
            channel=channel,
            text=message
        )
        logger.info("Successfully sent Slack message", channel=channel, ts=response["ts"])
        return f"Successfully sent message to {channel}."
    except SlackApiError as e:
        logger.error("Slack API error", error=e.response["error"])
        return f"Failed to send Slack message: {e.response['error']}"

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Slack MCP Server over SSE on port 8001")
    uvicorn.run(mcp.sse_app, host="0.0.0.0", port=8001)
