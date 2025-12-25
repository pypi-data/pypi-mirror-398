from _typeshed import Incomplete
from gllm_inference.schema.enums import ActivityType as ActivityType, WebSearchKey as WebSearchKey
from pydantic import BaseModel
from typing import Literal

WEB_SEARCH_VISIBLE_FIELDS: Incomplete
WebSearchActivityTypes: Incomplete

class Activity(BaseModel):
    """Base schema for any activity.

    Attributes:
        type (str): The type of activity being performed. Defaults to an empty string.
    """
    type: str

class MCPListToolsActivity(Activity):
    """Schema for listing tools in MCP.

    Attributes:
        type (Literal[ActivityType.MCP_LIST_TOOLS]): The type of activity being performed.
            Defaults to ActivityType.MCP_LIST_TOOLS.
        server_name (str): The name of the MCP server. Defaults to an empty string.
        tools (list[dict[str, str]] | None): The tools in the MCP server. Defaults to None.
    """
    type: Literal[ActivityType.MCP_LIST_TOOLS]
    server_name: str
    tools: list[dict[str, str]] | None

class MCPCallActivity(Activity):
    """Schema for MCP tool call.

    Attributes:
        type (Literal[ActivityType.MCP_CALL]): The type of activity being performed. Defaults to ActivityType.MCP_CALL.
        server_name (str): The name of the MCP server.
        tool_name (str): The name of the tool.
        args (dict[str, str]): The arguments of the tool.
    """
    type: Literal[ActivityType.MCP_CALL]
    server_name: str
    tool_name: str
    args: dict[str, str]

class WebSearchActivity(Activity):
    """Schema for web search tool call.

    Attributes:
        type (WebSearchActivityTypes): The type of activity being performed. Defaults to ActivityType.SEARCH.
        query (str | None): The query of the web search. Defaults to None.
        url (str | None): The URL of the page. Defaults to None.
        pattern (str | None): The pattern of the web search. Defaults to None.
        sources (list[dict[str, str]] | None): The sources of the web search.
    """
    type: WebSearchActivityTypes
    query: str | None
    url: str | None
    pattern: str | None
    sources: list[dict[str, str]] | None
    def model_dump(self, *args, **kwargs) -> dict[str, str]:
        """Serialize the activity for display.

        Returns:
            dict[str, str]: The serialized activity.
        """
