from urllib.parse import urlsplit, urlunsplit


def url_from(
    scheme: str = "",
    netloc: str = "",
    path: str = "",
    query: str = "",
    fragment: str = "",
) -> str:
    """Constructs an url from part"""
    return urlunsplit((scheme, netloc, path, query, fragment))


def add_path(base_url: str, *paths: str) -> str:
    """Adds a path from a base_url."""

    if not is_valid(base_url):
        raise ValueError(f"Invalid base_url: {base_url}")
    base_url = _format_base_url(base_url)
    split = urlsplit(base_url)

    return url_from(
        split.scheme,
        split.netloc,
        "/".join([split.path] + [p.strip("/") for p in paths]),
        split.query,
        split.fragment,
    )


def _format_base_url(url: str) -> str:
    """Remove trailing slash in base url, if applicable."""
    if url.endswith("/"):
        return url[:-1]
    return url


def is_valid(
    url: str,
    valid_schemes: tuple[str, ...] = ("http", "https"),
) -> bool:
    """
    Simple url validation that ensures the scheme and that there is an hostname.
    Malformatted url can pass this check such as http://http://toto.com
    """
    split = urlsplit(url)
    return split.scheme in valid_schemes and bool(split.netloc)
