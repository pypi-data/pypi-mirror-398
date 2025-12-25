from _typeshed import Incomplete
from gllm_inference.prompt_builder.format_strategy.format_strategy import BasePromptFormattingStrategy as BasePromptFormattingStrategy
from gllm_inference.schema import JinjaEnvType as JinjaEnvType
from jinja2.sandbox import SandboxedEnvironment
from typing import Any

JINJA_DEFAULT_BLACKLISTED_FILTERS: list[str]
JINJA_DEFAULT_SAFE_GLOBALS: dict[str, Any]
JINJA_DANGEROUS_PATTERNS: list[str]
PROMPT_BUILDER_VARIABLE_START_STRING: str
PROMPT_BUILDER_VARIABLE_END_STRING: str
ALLOWED_JINJA_BOOL_PARAMS: Incomplete
ALLOWED_JINJA_STR_PARAMS: Incomplete
ALLOWED_JINJA_ENV_PARAMS = ALLOWED_JINJA_BOOL_PARAMS | ALLOWED_JINJA_STR_PARAMS

class JinjaFormatStrategy(BasePromptFormattingStrategy):
    """Jinja2 template engine for formatting prompts.

    Attributes:
        jinja_env (SandboxedEnvironment): The Jinja environment for rendering templates.
        key_defaults (dict[str, str]): The default values for the keys.
    """
    jinja_env: Incomplete
    def __init__(self, environment: JinjaEnvType | SandboxedEnvironment | dict[str, Any] = ..., key_defaults: dict[str, str] | None = None) -> None:
        """Initialize the JinjaFormatStrategy.

        Args:
            environment (JinjaEnvType | SandboxedEnvironment, optional): The environment for Jinja rendering.
                It can be one of the following:
                1. `JinjaEnvType.RESTRICTED`: Uses a minimal, restricted Jinja environment.
                        Safest for most cases.
                2. `JinjaEnvType.JINJA_DEFAULT`: Uses the full Jinja environment. Allows more powerful templating,
                        but with fewer safety restrictions.
                3. `SandboxedEnvironment` instance: A custom Jinja `SandboxedEnvironment` object provided by the
                        user. Offers fine-grained control over template execution.
                4. `dict[str, Any]`: A custom Jinja environment configuration dictionary provided by the user.
                        Currently supported parameters include string-based and boolean-based parameters.
                        For parameter details, see: https://jinja.palletsprojects.com/en/3.1.x/api/#jinja2.Environment

                Defaults to `JinjaEnvType.RESTRICTED`
            key_defaults (dict[str, str], optional): The default values for the keys. Defaults to None, in which
                case no default values are used.
        """
    @staticmethod
    def create_custom_environment(env_params: dict[str, Any]) -> SandboxedEnvironment:
        '''Create a custom SandboxedEnvironment from dict of Jinja2 Environment constructor parameters.

        This method validates the provided parameters against allowed Jinja2 Environment
        constructor parameters and creates a SandboxedEnvironment instance.

        Examples:
            ```python
            env = JinjaFormatStrategy.create_custom_environment({
                "variable_start_string": "<<",
                "variable_end_string": ">>",
                "trim_blocks": True,
            })
            ```
        Args:
            env_params (dict[str, Any]): Dict of Jinja2 Environment constructor parameters.

        Returns:
            SandboxedEnvironment: SandboxedEnvironment configured with the provided parameters.

        Raises:
            ValueError: If invalid parameter types are provided or environment creation fails.
        '''
    @classmethod
    def create_default_environment(cls) -> SandboxedEnvironment:
        """Create default Jinja environment with default security controls.

        Returns:
            SandboxedEnvironment: The default Jinja environment.
        """
    def extract_keys(self, template: str | None) -> set[str]:
        """Extract keys from Jinja template using AST analysis.

        Args:
            template (str | None): The template to extract keys from.

        Returns:
            set[str]: The set of keys found in the template.
        """
