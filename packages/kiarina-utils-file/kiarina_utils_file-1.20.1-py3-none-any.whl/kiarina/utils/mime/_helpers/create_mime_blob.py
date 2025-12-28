from .._models.mime_blob import MIMEBlob
from .detect_mime_type import detect_mime_type


def create_mime_blob(
    raw_data: bytes, *, fallback_mime_type: str = "application/octet-stream"
) -> MIMEBlob:
    """
    Create a MIMEBlob from raw binary data.

    This function detects the MIME type of the provided raw data and creates a MIMEBlob object.

    Args:
        raw_data (bytes): Raw binary data to analyze.
        fallback_mime_type (str, optional): MIME type to use when detection fails.
            Defaults to "application/octet-stream".

    Returns:
        MIMEBlob: Created MIMEBlob object
    """
    mime_type = detect_mime_type(raw_data=raw_data, default=fallback_mime_type)
    return MIMEBlob(mime_type=mime_type, raw_data=raw_data)
