from _typeshed import Incomplete
from gllm_inference.prompt_builder.format_strategy import JinjaFormatStrategy as JinjaFormatStrategy, StringFormatStrategy as StringFormatStrategy
from gllm_inference.schema import HistoryFormatter as HistoryFormatter, JinjaEnvType as JinjaEnvType, Message as Message, MessageContent as MessageContent, MessageRole as MessageRole
from jinja2.sandbox import SandboxedEnvironment
from typing import Any

class PromptBuilder:
    """A prompt builder class used in Gen AI applications.

    Attributes:
        system_template (str): The system prompt template. May contain placeholders enclosed in curly braces `{}`.
        user_template (str): The user prompt template. May contain placeholders enclosed in curly braces `{}`.
        prompt_key_set (set[str]): A set of expected keys that must be present in the prompt templates.
        key_defaults (dict[str, str]): Default values for the keys in the prompt templates.
        strategy (BasePromptFormattingStrategy): The format strategy to be used for formatting the prompt.
        history_formatter (HistoryFormatter): The history formatter to be used for formatting the history.
    """
    key_defaults: Incomplete
    system_template: Incomplete
    user_template: Incomplete
    history_formatter: Incomplete
    strategy: Incomplete
    prompt_key_set: Incomplete
    def __init__(self, system_template: str = '', user_template: str = '', key_defaults: dict[str, str] | None = None, ignore_extra_keys: bool | None = None, history_formatter: HistoryFormatter | None = None, use_jinja: bool | None = False, jinja_env: JinjaEnvType | SandboxedEnvironment | dict[str, Any] = ...) -> None:
        """Initializes a new instance of the PromptBuilder class.

        Args:
            system_template (str, optional): The system prompt template. May contain placeholders enclosed in curly
                braces `{}`. Defaults to an empty string.
            user_template (str, optional): The user prompt template. May contain placeholders enclosed in curly
                braces `{}`. Defaults to an empty string.
            key_defaults (dict[str, str] | None, optional): Default values for the keys in the prompt templates.
                Applied when the corresponding keys are not provided in the runtime input.
                Defaults to None, in which case no default values will be assigned to the keys.
            ignore_extra_keys (bool | None, optional): Deprecated parameter. Will be removed in v0.6. Extra keys
                will always raise a warning only instead of raising an error.
            history_formatter (HistoryFormatter | None, optional): The history formatter to be used for formatting
                the history. Defaults to None, in which case the history will be used as is.
            use_jinja (bool, optional): Whether to use Jinja for rendering the prompt templates.
                Defaults to False.
            jinja_env (JinjaEnvType | SandboxedEnvironment | dict[str, Any], optional): The environment
                for Jinja rendering. It can be one of the following:
                1. `JinjaEnvType.RESTRICTED`: Uses a minimal, restricted Jinja environment.
                        Safest for most cases.
                2. `JinjaEnvType.JINJA_DEFAULT`: Uses the full Jinja environment. Allows more powerful templating,
                        but with fewer safety restrictions.
                3. `SandboxedEnvironment` instance: A custom Jinja `SandboxedEnvironment` object provided by the
                        user. Offers fine-grained control over template execution.
                4. `dict[str, Any]`: A custom Jinja environment configuration dictionary.
                Defaults to `JinjaEnvType.RESTRICTED`

        Raises:
            ValueError: If both `system_template` and `user_template` are empty.
        """
    def format(self, history: list[Message] | None = None, extra_contents: list[MessageContent] | None = None, **kwargs: Any) -> list[Message]:
        """Formats the prompt templates into a list of messages.

        This method processes each prompt template, replacing the placeholders in the template content with the
        corresponding values from `kwargs`. If any required key is missing from `kwargs`, it raises a `ValueError`.
        It also handles the provided history and extra contents. It formats the prompt as a list of messages.

        Args:
            history (list[Message] | None, optional): The history to be included in the prompt. Defaults to None.
            extra_contents (list[MessageContent] | None, optional): The extra contents to be included in the user
                message. Defaults to None.
            **kwargs (Any): A dictionary of placeholder values to be injected into the prompt templates.
                Values must be either a string or an object that can be serialized to a string.

        Returns:
            list[Message]: A list of formatted messages.

        Raises:
            ValueError: If a required key for the prompt template is missing from `kwargs`.
        """
