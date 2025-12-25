import asyncio
import logging
from _typeshed import Incomplete
from gllm_inference.constants import GOOGLE_SCOPES as GOOGLE_SCOPES
from gllm_inference.realtime_session.input_streamer import KeyboardInputStreamer as KeyboardInputStreamer
from gllm_inference.realtime_session.input_streamer.input_streamer import BaseInputStreamer as BaseInputStreamer
from gllm_inference.realtime_session.output_streamer import ConsoleOutputStreamer as ConsoleOutputStreamer
from gllm_inference.realtime_session.output_streamer.output_streamer import BaseOutputStreamer as BaseOutputStreamer
from gllm_inference.realtime_session.realtime_session import BaseRealtimeSession as BaseRealtimeSession
from pydantic import BaseModel
from typing import Literal

DEFAULT_POST_OUTPUT_AUDIO_DELAY: float
LIVE_CONNECT_CONFIG: Incomplete

class GoogleIOStreamerState(BaseModel):
    '''[BETA] Defines the state of the GoogleIOStreamer with thread-safe properties.

    Attributes:
        is_streaming_output (bool): Whether the output is streaming.
        console_mode (Literal["input", "user", "assistant"]): The current console mode.
        terminated (bool): Whether the conversation is terminated.
    '''
    is_streaming_output: bool
    console_mode: Literal['input', 'user', 'assistant']
    terminated: bool
    async def set_streaming_output(self, value: bool) -> None:
        """Thread-safe setter for is_streaming_output.

        Args:
            value (bool): The value to set for is_streaming_output.
        """
    async def get_streaming_output(self) -> bool:
        """Thread-safe getter for is_streaming_output.

        Returns:
            bool: The value of is_streaming_output.
        """
    async def set_console_mode(self, value: Literal['input', 'user', 'assistant']) -> None:
        '''Thread-safe setter for console_mode.

        Args:
            value (Literal["input", "user", "assistant"]): The value to set for console_mode.
        '''
    async def get_console_mode(self) -> Literal['input', 'user', 'assistant']:
        '''Thread-safe getter for console_mode.

        Returns:
            Literal["input", "user", "assistant"]: The value of console_mode.
        '''
    async def set_terminated(self, value: bool) -> None:
        """Thread-safe setter for terminated.

        Args:
            value (bool): The value to set for terminated.
        """
    async def get_terminated(self) -> bool:
        """Thread-safe getter for terminated.

        Returns:
            bool: The value of terminated.
        """

class GoogleIOStreamer:
    """[BETA] Defines the GoogleIOStreamer.

    This class manages the realtime conversation lifecycle.
    It handles the IO operations between the model and the input/output streamers.

    Attributes:
        session (AsyncSession): The session of the GoogleIOStreamer.
        task_group (asyncio.TaskGroup): The task group of the GoogleIOStreamer.
        input_queue (asyncio.Queue): The input queue of the GoogleIOStreamer.
        output_queue (asyncio.Queue): The output queue of the GoogleIOStreamer.
        input_streamers (list[BaseInputStreamer]): The input streamers of the GoogleIOStreamer.
        output_streamers (list[BaseOutputStreamer]): The output streamers of the GoogleIOStreamer.
        post_output_audio_delay (float): The delay in seconds to post the output audio.
    """
    session: AsyncSession
    task_group: Incomplete
    input_queue: Incomplete
    output_queue: Incomplete
    state: Incomplete
    input_streamers: Incomplete
    output_streamers: Incomplete
    post_output_audio_delay: Incomplete
    def __init__(self, session: AsyncSession, task_group: asyncio.TaskGroup, input_queue: asyncio.Queue, output_queue: asyncio.Queue, input_streamers: list[BaseInputStreamer], output_streamers: list[BaseOutputStreamer], post_output_audio_delay: float, logger: logging.Logger) -> None:
        """Initializes a new instance of the GoogleIOStreamer class.

        Args:
            session (AsyncSession): The session of the GoogleIOStreamer.
            task_group (asyncio.TaskGroup): The task group of the GoogleIOStreamer.
            input_queue (asyncio.Queue): The input queue of the GoogleIOStreamer.
            output_queue (asyncio.Queue): The output queue of the GoogleIOStreamer.
            input_streamers (list[BaseInputStreamer]): The input streamers of the GoogleIOStreamer.
            output_streamers (list[BaseOutputStreamer]): The output streamers of the GoogleIOStreamer.
            post_output_audio_delay (float): The delay in seconds to post the output audio.
            logger (logging.Logger): The logger of the GoogleIOStreamer.
        """
    async def start(self) -> None:
        """Processes the realtime conversation.

        This method is used to start the realtime conversation.
        It initializes the input and output streamers, creates the necessary tasks, and starts the conversation.
        When the conversation is terminated, it cleans up the input and output streamers.
        """

class GoogleRealtimeSession(BaseRealtimeSession):
    '''[BETA] A realtime session module to interact with Gemini Live models.

    Warning:
        The \'GoogleRealtimeSession\' class is currently in beta and may be subject to changes in the future.
        It is intended only for quick prototyping in local environments.
        Please avoid using it in production environments.

    Attributes:
        model_name (str): The name of the language model.
        client_params (dict[str, Any]): The Google client instance init parameters.

    Basic usage:
        The `GoogleRealtimeSession` can be used as started as follows:
        ```python
        realtime_session = GoogleRealtimeSession(model_name="gemini-live-2.5-flash-preview")
        await realtime_session.invoke()
        ```

    Custom IO streamers:
        The `GoogleRealtimeSession` can be used with custom IO streamers.
        ```python
        input_streamers = [KeyboardInputStreamer(), LinuxMicInputStreamer()]
        output_streamers = [ConsoleOutputStreamer(), LinuxSpeakerOutputStreamer()]
        realtime_session = GoogleRealtimeSession(model_name="gemini-live-2.5-flash-preview")
        await realtime_session.start(input_streamers=input_streamers, output_streamers=output_streamers)
        ```

        In the above example, we added a capability to use a Linux system microphone and speaker,
        allowing realtime audio input and output to the model.

    Authentication:
        The `GoogleRealtimeSession` can use either Google Gen AI or Google Vertex AI.

        Google Gen AI is recommended for quick prototyping and development.
        It requires a Gemini API key for authentication.

        Usage example:
        ```python
        realtime_session = GoogleRealtimeSession(
            model_name="gemini-2.5-flash-native-audio-preview-12-2025",
            api_key="your_api_key"
        )
        ```

        Google Vertex AI is recommended to build production-ready applications.
        It requires a service account JSON file for authentication.

        Usage example:
        ```python
        realtime_session = GoogleRealtimeSession(
            model_name="gemini-2.5-flash-native-audio-preview-12-2025",
            credentials_path="path/to/service_account.json"
        )
        ```

        If neither `api_key` nor `credentials_path` is provided, Google Gen AI will be used by default.
        The `GOOGLE_API_KEY` environment variable will be used for authentication.
    '''
    model_name: Incomplete
    client_params: Incomplete
    def __init__(self, model_name: str, api_key: str | None = None, credentials_path: str | None = None, project_id: str | None = None, location: str = 'us-central1') -> None:
        '''Initializes a new instance of the GoogleRealtimeChat class.

        Args:
            model_name (str): The name of the model to use.
            api_key (str | None, optional): Required for Google Gen AI authentication. Cannot be used together
                with `credentials_path`. Defaults to None.
            credentials_path (str | None, optional): Required for Google Vertex AI authentication. Path to the service
                account credentials JSON file. Cannot be used together with `api_key`. Defaults to None.
            project_id (str | None, optional): The Google Cloud project ID for Vertex AI. Only used when authenticating
                with `credentials_path`. Defaults to None, in which case it will be loaded from the credentials file.
            location (str, optional): The location of the Google Cloud project for Vertex AI. Only used when
                authenticating with `credentials_path`. Defaults to "us-central1".

        Note:
            If neither `api_key` nor `credentials_path` is provided, Google Gen AI will be used by default.
            The `GOOGLE_API_KEY` environment variable will be used for authentication.
        '''
    async def start(self, input_streamers: list[BaseInputStreamer] | None = None, output_streamers: list[BaseOutputStreamer] | None = None, post_output_audio_delay: float = ...) -> None:
        """Starts the realtime conversation using the provided input and output streamers.

        This method is used to start the realtime conversation using a `GoogleIOStreamer`.
        The streamers are responsible for handling the input and output of the conversation.

        Args:
            input_streamers (list[BaseInputStreamer] | None, optional): The input streamers to use.
                Defaults to None, in which case a `KeyboardInputStreamer` will be used.
            output_streamers (list[BaseOutputStreamer] | None, optional): The output streamers to use.
                Defaults to None, in which case a `ConsoleOutputStreamer` will be used.
            post_output_audio_delay (float, optional): The delay in seconds to post the output audio.
                Defaults to 0.5 seconds.

        Raises:
            ValueError: If the `input_streamers` or `output_streamers` is an empty list.
            ValueError: If the `post_output_audio_delay` is not greater than 0.
            Exception: If the conversation fails to process.
        """
