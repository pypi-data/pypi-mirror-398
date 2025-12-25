from _typeshed import Incomplete
from gllm_inference.prompt_builder.format_strategy.format_strategy import BasePromptFormattingStrategy as BasePromptFormattingStrategy

KEY_EXTRACTOR_REGEX: Incomplete

class StringFormatStrategy(BasePromptFormattingStrategy):
    """String format strategy using str.format() method.

    Attributes:
        key_defaults (dict[str, str]): The default values for the keys.
    """
    def extract_keys(self, template: str | None) -> set[str]:
        """Extract keys from a template.

        Args:
            template (str | None): The template to extract keys from.

        Returns:
            set[str]: The set of keys found in the template.
        """
