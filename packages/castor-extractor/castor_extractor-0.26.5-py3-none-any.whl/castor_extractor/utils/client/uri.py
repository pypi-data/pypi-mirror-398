from urllib.parse import quote as escape


def uri_encode(value: str) -> str:
    """encode an uri by escaping characters"""
    return escape(value)
