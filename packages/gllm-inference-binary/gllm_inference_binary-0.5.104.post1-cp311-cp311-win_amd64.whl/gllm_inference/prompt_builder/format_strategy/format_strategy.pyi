from _typeshed import Incomplete
from abc import ABC, abstractmethod
from gllm_inference.schema.message import MessageContent as MessageContent

class BasePromptFormattingStrategy(ABC):
    """Base class for prompt formatting strategies.

    This class defines the interface for different prompt templating engines. Subclasses
    implement specific formatting strategies to render templates with variable
    substitution.

    The strategy pattern allows the PromptBuilder to work with different templating engines
    without changing its core logic.

    Attributes:
        key_defaults (dict[str, str]): The default values for the keys.
    """
    key_defaults: Incomplete
    def __init__(self, key_defaults: dict[str, str] | None = None) -> None:
        """Initialize the BasePromptFormattingStrategy.

        Args:
            key_defaults (dict[str, str] | None, optional): The default values for the keys. Defaults to None,
                in which case no default values are used.
        """
    def format(self, template: str, variables_map: dict[str, str] | None = None, extra_contents: list[MessageContent] | None = None) -> list[str]:
        """Format template with variables using the template method pattern.

        This is a template method that defines the algorithm for formatting:
        1. Merge key_defaults and variables_map
        2. Render the template (delegated to subclass via _render_template)
        3. Append extra_contents to the result

        Args:
            template (str): Template string to format.
            variables_map (dict[str, str] | None, optional): Variables for substitution. Defaults to None.
            extra_contents (list[MessageContent] | None, optional): Extra contents to format. Defaults to None.

        Returns:
            str: Formatted template string.
        """
    @abstractmethod
    def extract_keys(self, template: str | None) -> set[str]:
        """Extract variable keys from template.

        Args:
            template (str | None): Template string to extract keys from.

        Returns:
            set[str]: Set of variable keys found in template.

        Raises:
            NotImplementedError: If the method is not implemented.
        """
