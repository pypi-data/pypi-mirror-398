from gllm_inference.builder.build_lm_invoker import build_lm_invoker as build_lm_invoker
from gllm_inference.lm_invoker.lm_invoker import BaseLMInvoker as BaseLMInvoker
from gllm_inference.output_parser.output_parser import BaseOutputParser as BaseOutputParser
from gllm_inference.prompt_builder.prompt_builder import PromptBuilder as PromptBuilder
from gllm_inference.request_processor.lm_request_processor import LMRequestProcessor as LMRequestProcessor
from gllm_inference.schema import LMOutput as LMOutput
from pydantic import BaseModel as BaseModel
from typing import Any

class UsesLM:
    '''A mixin to be extended by components that use LMRequestProcessor.

    This mixin should be extended by components that use LMRequestProcessor. Components that extend this mixin
    must have a constructor that accepts the LMRequestProcessor instance as its first argument.

    LM based components can be categorized into two types:
    1. Components that do not utilize structured output.
    2. Components that utilize structured output.

    Building a component without structured output:
        As defined above, the component must accepts an LMRequestProcessor instance as its first argument, e.g.:
        ```python
        class LMBasedComponent(Component, UsesLM):
            def __init__(self, lm_request_processor: LMRequestProcessor, custom_kwarg: str):
                self.lm_request_processor = lm_request_processor
                self.custom_kwarg = custom_kwarg
        ```

        Using the `from_lm_components` method provided by this mixin, the component can be instantiated as follows:
        ```python
        component = LMBasedComponent.from_lm_components(
            prompt_builder,
            lm_invoker,
            output_parser,
            custom_kwarg="custom_value",
        )
        ```

    Building a component with structured output:
        When the component utilizes structured output, the `_parse_structured_output` method can be used
        to simplify the process of extracting the structured output in the component\'s runtime methods, e.g.:
        ```python
        class LMBasedComponent(Component, UsesLM):
            def __init__(self, lm_request_processor: LMRequestProcessor, custom_kwarg: str):
                self.lm_request_processor = lm_request_processor
                self.custom_kwarg = custom_kwarg

            def runtime_method(self, param1: str, param2: str) -> str:
                lm_output = self.lm_request_processor.process(param1=param1, param2=param2)
                return self._parse_structured_output(lm_output, "target_key", "fallback_output")
        ```

        Notice that in the above example, the LMRequestProcessor is configured to take `param1` and `param2`
        as keyword arguments and output a structured output that contains the `target_key` key. Hence,
        these conditions must be fulfilled when instantiating the component.

        This mixin also provides the `with_structured_output` method to simplify the process of instantiating
        the component with structured output. Let\'s take a look at an example that meets the above conditions:
        ```python
        class Schema(BaseModel):
            target_key: str

        component = LMBasedComponent.with_structured_output(
            model_id="openai/gpt-4.1-mini",
            response_schema=Schema,
            system_template="system_template {param1}",
            user_template="user_template {param2}",
            custom_kwarg="custom_value",
        )
        ```

    Building a structured output preset:
        If desired, the component can also define a quick preset. This can be done by providing default prompts
        as response schema. Here\'s an example:
        ```python
        class Schema(BaseModel):
            target_key: str

        @classmethod
        def from_preset(cls, model_id: str, custom_kwarg: str) -> "LMBasedComponent":
            return cls.with_structured_output(
                model_id=model_id,
                response_schema=Schema,
                system_template=PRESET_SYSTEM_TEMPLATE,
                user_template=PRESET_USER_TEMPLATE,
                custom_kwarg=custom_kwarg,
            )
        )
        ```

        Then, the preset can be instantiated as follows:
        ```python
        component = LMBasedComponent.from_preset(
            model_id="openai/gpt-4.1-mini",
            custom_kwarg="custom_value",
        )
        ```
    '''
    @classmethod
    def from_lm_components(cls, prompt_builder: PromptBuilder, lm_invoker: BaseLMInvoker, output_parser: BaseOutputParser | None = None, **kwargs: Any) -> UsesLM:
        """Creates an instance from LMRequestProcessor components directly.

        This method is a shortcut to initialize the class by providing the LMRequestProcessor components directly.

        Args:
            prompt_builder (PromptBuilder): The prompt builder used to format the prompt.
            lm_invoker (BaseLMInvoker): The language model invoker that handles the model inference.
            output_parser (BaseOutputParser, optional): An optional parser to process the model's output.
                Defaults to None.
            **kwargs (Any): Additional keyword arguments to be passed to the class constructor.

        Returns:
            UsesLM: An instance of the class that mixes in this mixin.
        """
    @classmethod
    def with_structured_output(cls, model_id: str, response_schema: type[BaseModel], system_template: str = '', user_template: str = '', **kwargs: Any) -> UsesLM:
        """Creates an instance with structured output configuration.

        This method is a shortcut to initialize the class with structured output configuration.

        Args:
            model_id (str): The model ID of the language model.
            response_schema (type[BaseModel]): The response schema of the language model.
            system_template (str, optional): The system template of the language model. Defaults to an empty string.
            user_template (str, optional): The user template of the language model. Defaults to an empty string.
            **kwargs (Any): Additional keyword arguments to be passed to the class constructor.

        Returns:
            UsesLM: An instance of the class that mixes in this mixin with structured output configuration.
        """
