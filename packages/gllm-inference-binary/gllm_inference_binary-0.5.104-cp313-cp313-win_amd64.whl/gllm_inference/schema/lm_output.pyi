from _typeshed import Incomplete
from gllm_core.schema import Chunk
from gllm_inference.schema.attachment import Attachment as Attachment
from gllm_inference.schema.code_exec_result import CodeExecResult as CodeExecResult
from gllm_inference.schema.enums import LMOutputType as LMOutputType
from gllm_inference.schema.mcp import MCPCall as MCPCall
from gllm_inference.schema.reasoning import Reasoning as Reasoning
from gllm_inference.schema.token_usage import TokenUsage as TokenUsage
from gllm_inference.schema.tool_call import ToolCall as ToolCall
from pydantic import BaseModel
from typing import Any

LMOutputData = str | dict[str, Any] | BaseModel | Attachment | ToolCall | Reasoning | Chunk | CodeExecResult | MCPCall
logger: Incomplete

class LMOutputItem(BaseModel):
    """Defines the output item of a language model.

    Attributes:
        type (str): The type of the output item.
        output (LMOutputData): The output data of the output item.
    """
    type: str
    output: LMOutputData

class LMOutput(BaseModel):
    """Defines the output of a language model.

    Attributes:
        outputs (list[LMOutputItem]): The outputs of the language model in sequential order. Defaults to an empty list.
        token_usage (TokenUsage | None): The token usage analytics, if requested. Defaults to None.
        duration (float | None): The duration of the invocation in seconds, if requested. Defaults to None.
        finish_details (dict[str, Any]): The details about how the generation finished, if requested.
            Defaults to an empty dictionary.

        text (str): The first text response.
        structured_output (dict[str, Any] | BaseModel | None): The first structured output.

        texts (list[str]): The texts from the outputs.
        structured_outputs (list[dict[str, Any] | BaseModel]): The structured outputs from the outputs.
        attachments (list[Attachment]): The attachments from the outputs.
        tool_calls (list[ToolCall]): The tool calls from the outputs.
        thinkings (list[Reasoning]): The thinkings from the outputs.
        citations (list[Chunk]): The citations from the outputs.
        code_exec_results (list[CodeExecResult]): The code exec results from the outputs.
        mcp_calls (list[MCPCall]): The MCP calls from the outputs.

        response (str): Deprecated. Replaced by `text`.
        reasoning (list[Reasoning]): Deprecated. Replaced by `thinkings`.
    """
    outputs: list[LMOutputItem]
    token_usage: TokenUsage | None
    duration: float | None
    finish_details: dict[str, Any]
    def __init__(self, *, outputs: list[LMOutputItem] | None = None, token_usage: TokenUsage | None = None, duration: float | None = None, finish_details: dict[str, Any] | None = None, response: str = '', structured_output: dict[str, Any] | BaseModel | None = None, tool_calls: list[ToolCall] | None = None, reasoning: list[Reasoning] | None = None, attachments: list[Attachment] | None = None, citations: list[Chunk] | None = None, code_exec_results: list[CodeExecResult] | None = None, mcp_calls: list[MCPCall] | None = None) -> None:
        """Initialize the LMOutput.

        This constructor is created for backward compatibility with the legacy method to initialize the LMOutput.
        This constructor will be removed in v0.6.

        Args:
            outputs (list[LMOutputItem] | None, optional): The output items. Defaults to an empty list.
            token_usage (TokenUsage | None, optional): The token usage analytics. Defaults to None.
            duration (float | None, optional): The duration of the invocation in seconds. Defaults to None.
            finish_details (dict[str, Any] | None, optional): The details about how the generation finished.
                Defaults to an empty dictionary.
            response (str, optional): The first text response. Defaults to an empty string.
            structured_output (dict[str, Any] | BaseModel | None, optional): The first structured output.
                Defaults to None.
            tool_calls (list[ToolCall] | None, optional): The tool calls. Defaults to None.
            reasoning (list[Reasoning] | None, optional): The thinkings. Defaults to None.
            attachments (list[Attachment] | None, optional): The attachments. Defaults to None.
            citations (list[Chunk] | None, optional): The citations. Defaults to None.
            code_exec_results (list[CodeExecResult] | None, optional): The code exec results. Defaults to None.
            mcp_calls (list[MCPCall] | None, optional): The MCP calls. Defaults to None.
        """
    @property
    def response(self) -> str:
        """Deprecated property to get the first text response from the LMOutput.

        Returns:
            str: The first text response from the LMOutput.
        """
    @response.setter
    def response(self, value: str) -> None:
        """Deprecated setter to set the first text response to the LMOutput.

        Args:
            value (str): The first text response to set.
        """
    @property
    def text(self) -> str:
        """Get the first text from the LMOutput.

        Returns:
            str: The first text from the LMOutput.
        """
    @property
    def structured_output(self) -> dict[str, Any] | BaseModel | None:
        """Deprecated property to get the first structured output from the LMOutput.

        Returns:
            dict[str, Any] | BaseModel | None: The first structured output from the LMOutput.
        """
    @structured_output.setter
    def structured_output(self, value: dict[str, Any] | BaseModel) -> None:
        """Deprecated setter to set the first structured output to the LMOutput.

        Args:
            value (dict[str, Any] | BaseModel): The first structured output to set.
        """
    @property
    def texts(self) -> list[str]:
        """Get the texts from the LMOutput.

        Returns:
            list[str]: The texts from the LMOutput.
        """
    @property
    def structured_outputs(self) -> list[dict[str, Any] | BaseModel]:
        """Get the structured outputs from the LMOutput.

        Returns:
            list[dict[str, Any] | BaseModel]: The structured outputs from the LMOutput.
        """
    @property
    def attachments(self) -> list[Attachment]:
        """Get the attachments from the LMOutput.

        Returns:
            list[Attachment]: The attachments from the LMOutput.
        """
    @attachments.setter
    def attachments(self, value: list[Attachment]) -> None:
        """Deprecated setter to set the attachments to the LMOutput.

        Args:
            value (list[Attachment]): The attachments to set.
        """
    @property
    def tool_calls(self) -> list[ToolCall]:
        """Get the tool calls from the LMOutput.

        Returns:
            list[ToolCall]: The tool calls from the LMOutput.
        """
    @tool_calls.setter
    def tool_calls(self, value: list[ToolCall]) -> None:
        """Deprecated setter to set the tool calls to the LMOutput.

        Args:
            value (list[ToolCall]): The tool calls to set.
        """
    @property
    def reasoning(self) -> list[Reasoning]:
        """Deprecated property to get the thinkings from the LMOutput.

        Returns:
            list[Reasoning]: The thinkings from the LMOutput.
        """
    @reasoning.setter
    def reasoning(self, value: list[Reasoning]) -> None:
        """Deprecated setter to set the thinkings to the LMOutput.

        Args:
            value (list[Reasoning]): The thinkings to set.
        """
    @property
    def thinkings(self) -> list[Reasoning]:
        """Get the thinkings from the LMOutput.

        Returns:
            list[Reasoning]: The thinkings from the LMOutput.
        """
    @property
    def citations(self) -> list[Chunk]:
        """Get the citations from the LMOutput.

        Returns:
            list[Chunk]: The citations from the LMOutput.
        """
    @citations.setter
    def citations(self, value: list[Chunk]) -> None:
        """Deprecated setter to set the citations to the LMOutput.

        Args:
            value (list[Chunk]): The citations to set.
        """
    @property
    def code_exec_results(self) -> list[CodeExecResult]:
        """Get the code exec results from the LMOutput.

        Returns:
            list[CodeExecResult]: The code exec results from the LMOutput.
        """
    @code_exec_results.setter
    def code_exec_results(self, value: list[CodeExecResult]) -> None:
        """Deprecated setter to set the code exec results to the LMOutput.

        Args:
            value (list[CodeExecResult]): The code exec results to set.
        """
    @property
    def mcp_calls(self) -> list[MCPCall]:
        """Get the MCP calls from the LMOutput.

        Returns:
            list[MCPCall]: The MCP calls from the LMOutput.
        """
    @mcp_calls.setter
    def mcp_calls(self, value: list[MCPCall]) -> None:
        """Deprecated setter to set the MCP calls to the LMOutput.

        Args:
            value (list[MCPCall]): The MCP calls to set.
        """
    def add_text(self, text: str | list[str]) -> None:
        """Add an output or a list of outputs to the LMOutput.

        Args:
            text (str | list[str]): The text or a list of texts to add.
        """
    def add_attachment(self, attachment: Attachment | list[Attachment]) -> None:
        """Add an attachment or a list of attachments to the LMOutput.

        Args:
            attachment (Attachment | list[Attachment]): The attachment or a list of attachments to add.
        """
    def add_tool_call(self, tool_call: ToolCall | list[ToolCall]) -> None:
        """Add a tool call or a list of tool calls to the LMOutput.

        Args:
            tool_call (ToolCall | list[ToolCall]): The tool call or a list of tool calls to add.
        """
    def add_structured(self, structured: dict[str, Any] | BaseModel | list[dict[str, Any] | BaseModel]) -> None:
        """Add a structured output or a list of structured outputs to the LMOutput.

        Args:
            structured (dict[str, Any] | BaseModel | list[dict[str, Any] | BaseModel]): The structured output
                or a list of structured outputs to add.
        """
    def add_thinking(self, thinking: Reasoning | list[Reasoning]) -> None:
        """Add a thinking or a list of thoughts to the LMOutput.

        Args:
            thinking (Reasoning | list[Reasoning]): The thinking or a list of thoughts to add.
        """
    def add_citation(self, citation: Chunk | list[Chunk]) -> None:
        """Add a citation or a list of citations to the LMOutput.

        Args:
            citation (Chunk | list[Chunk]): The citation or a list of citations to add.
        """
    def add_code_exec_result(self, code_exec_result: CodeExecResult | list[CodeExecResult]) -> None:
        """Add a code exec result or a list of code exec results to the LMOutput.

        Args:
            code_exec_result (CodeExecResult | list[CodeExecResult]): The code exec result or a list of code exec
                results to add.
        """
    def add_mcp_call(self, mcp_call: MCPCall | list[MCPCall]) -> None:
        """Add an MCP call or a list of MCP calls to the LMOutput.

        Args:
            mcp_call (MCPCall | list[MCPCall]): The MCP call or a list of MCP calls to add.
        """
