from fastmcp.client import Client


async def test_list_tools(client: Client):
    tools = await client.list_tools()
    tool_names = [t.name for t in tools]
    assert "hello" in tool_names
    assert "add" in tool_names
    assert "delayed_echo" in tool_names


async def test_hello_default(client: Client):
    result = await client.call_tool("hello", {})
    assert result.data == "Hello, World!"


async def test_hello_with_name(client: Client):
    result = await client.call_tool("hello", {"name": "Alice"})
    assert result.data == "Hello, Alice!"


async def test_add(client: Client):
    result = await client.call_tool("add", {"a": 2, "b": 3})
    assert result.data == 5


async def test_add_negative(client: Client):
    result = await client.call_tool("add", {"a": -1, "b": 1})
    assert result.data == 0


async def test_delayed_echo(client: Client):
    result = await client.call_tool("delayed_echo", {"message": "test", "delay": 0})
    assert result.data == "Echo: test"
