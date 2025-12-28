import logging

from fastmcp import FastMCP

logger = logging.getLogger(__name__)

mcp = FastMCP("Google Workspace")


@mcp.tool
def hello(name: str = "World") -> str:
    """Say hello to someone.

    Args:
        name: The name to greet

    Returns:
        A greeting message
    """
    logger.info("hello called with name=%s", name)
    return f"Hello, {name}!"


@mcp.tool
def add(a: int, b: int) -> int:
    """Add two numbers.

    Args:
        a: First number
        b: Second number

    Returns:
        Sum of a and b
    """
    logger.info("add called with a=%d, b=%d", a, b)
    return a + b


@mcp.tool
async def delayed_echo(message: str, delay: float = 0.1) -> str:
    """Echo a message after a delay (async example).

    Args:
        message: The message to echo
        delay: Delay in seconds before responding (max 5.0)

    Returns:
        The echoed message
    """
    import asyncio

    delay = max(0, min(delay, 5.0))  # Clamp to 0-5 seconds
    logger.info("delayed_echo called with message=%s, delay=%s", message, delay)
    await asyncio.sleep(delay)
    return f"Echo: {message}"


def main():
    """Entry point for the MCP server."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger.info("Starting MCP server")
    mcp.run()
