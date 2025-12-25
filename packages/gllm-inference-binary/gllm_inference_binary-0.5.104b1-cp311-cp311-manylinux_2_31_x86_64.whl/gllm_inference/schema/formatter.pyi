from gllm_inference.schema.enums import MessageRole as MessageRole
from gllm_inference.schema.message import Message as Message
from gllm_inference.schema.type_alias import MessageContent as MessageContent
from pydantic import BaseModel

class HistoryFormatter(BaseModel):
    """Configuration for history formatting.

    Attributes:
        prefix_user_message (str): Prefix for user messages.
        suffix_user_message (str): Suffix for user messages.
        prefix_assistant_message (str): Prefix for assistant messages.
        suffix_assistant_message (str): Suffix for assistant messages.
    """
    prefix_user_message: str
    suffix_user_message: str
    prefix_assistant_message: str
    suffix_assistant_message: str
    def format_history(self, history: list[Message]) -> list[Message]:
        """Formats a list of messages based on their roles.

        This method formats each message in the history list by applying the appropriate
        formatting based on the message role (user or assistant). Other message types
        are added to the result without modification.

        Args:
            history (list[Message]): The list of messages to format.

        Returns:
            list[Message]: A new list containing the formatted messages.
        """
