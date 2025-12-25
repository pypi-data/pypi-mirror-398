"""File utilities"""


def is_text_content(data: bytes, mime_type: str) -> bool:
    """Check if content is text based on mime type and content analysis."""
    # Check mime type first
    if mime_type and (
        mime_type.startswith("text/") or mime_type in ["application/json", "application/xml", "application/javascript"]
    ):
        return True

    # Try to decode as UTF-8 to check if it's text
    try:
        data.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False
