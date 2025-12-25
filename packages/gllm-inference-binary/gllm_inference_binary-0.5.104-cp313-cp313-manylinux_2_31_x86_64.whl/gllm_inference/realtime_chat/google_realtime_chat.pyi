from gllm_inference.realtime_chat.realtime_chat import DEPRECATION_MESSAGE as DEPRECATION_MESSAGE
from gllm_inference.realtime_session.google_realtime_session import GoogleRealtimeSession as GoogleRealtimeSession

class GoogleRealtimeChat(GoogleRealtimeSession):
    """[BETA] A realtime chat module to interact with Gemini Live models.

    Attributes:
        model_name (str): The name of the language model.
        client_params (dict[str, Any]): The Google client instance init parameters.
    """
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
