from pydantic import BaseModel
from typing import Any

class MCPServer(BaseModel):
    """Defines an MCP server.

    Attributes:
        url (str): The URL of the MCP server.
        name (str): The name of the MCP server.
        allowed_tools (list[str] | None): The allowed tools of the MCP server.
            Defaults to None, in which case all tools are allowed.
    """
    url: str
    name: str
    allowed_tools: list[str] | None

class MCPCall(BaseModel):
    """Defines an MCP call.

    Attributes:
        id (str): The ID of the MCP call. Defaults to an empty string.
        server_name (str): The name of the MCP server. Defaults to an empty string.
        tool_name (str): The name of the tool. Defaults to an empty string.
        args (dict[str, Any]): The arguments of the tool. Defaults to an empty dictionary.
        output (str | None): The output of the tool. Defaults to None.
    """
    id: str
    server_name: str
    tool_name: str
    args: dict[str, Any]
    output: str | None
