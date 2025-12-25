from _typeshed import Incomplete

logger: Incomplete
DEFAULT_BASE64_ALLOWED_MIMETYPES: Incomplete

def base64_to_bytes(value: str, *, allowed_mimetypes: tuple[str, ...] | None = ...) -> str | bytes:
    '''Decode a base64 string to bytes based on allowed MIME type.

    The conversion steps are as follows:
        1. The function first attempts to decode the given string from base64.
        2. If decoding succeeds, it checks the MIME type of the decoded content.
        3. When the MIME type matches one of the allowed patterns (e.g., ``"image/*"``),
            the raw bytes are returned. Otherwise, the original string is returned unchanged.

    Args:
        value (str): Input data to decode.
        allowed_mimetypes (tuple[str, ...], optional): MIME type prefixes that are allowed
            to be decoded into bytes. Defaults to ("image/*", "audio/*", "video/*").

    Returns:
        str | bytes: Base64-encoded string or raw bytes if MIME type is allowed;
            otherwise returns original string.

    Raises:
        ValueError: If the input is not a string.
    '''
