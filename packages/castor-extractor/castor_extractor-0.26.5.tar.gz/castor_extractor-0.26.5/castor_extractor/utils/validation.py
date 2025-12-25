from urllib.parse import urlsplit, urlunsplit

BASE_URL_SCHEME = "https"


class InvalidBaseUrl(ValueError): ...


def _preprocess_url(base_url: str) -> str:
    if "://" not in base_url:
        return f"{BASE_URL_SCHEME}://{base_url}"

    return base_url.strip()


def clean_path(path: str) -> str:
    return path.rstrip("/")


def _get_hostname_port(netloc: str) -> tuple[str, str]:
    hostname, *rest = netloc.split(":")
    port = ":".join(rest)
    return hostname, port


def _urlsplit(base_url: str) -> tuple[str, str, str, str, str, str]:
    """
    Returns URL split parts

    Parameters:
            base_url (str): The URL used for the splitting.

    Returns:
            scheme (str)
            hostname (str)
            path (str)
            port (str)
            query (str)
            fragment (str)
    """

    base_url = _preprocess_url(base_url)
    url = urlsplit(base_url)

    hostname, port = _get_hostname_port(url.netloc)
    path = clean_path(url.path)

    return url.scheme, hostname, path, port, url.query, url.fragment


def _expect(
    attr: str,
    expected: list[str] | None,
    actual: str | None,
) -> None:
    if not expected and not actual:
        return
    if expected and actual in expected:
        return
    raise InvalidBaseUrl(
        f"Invalid base url {attr} | expected: {expected}, got: {actual}",
    )


def validate_baseurl(base_url: str) -> str:
    scheme, hostname, path, port, query, fragment = _urlsplit(base_url)
    hostname_with_port = f"{hostname}:{port}" if port else hostname

    if not hostname:
        raise InvalidBaseUrl(f"Invalid base url hostname: {hostname}")

    _expect("scheme", ["https", "http"], scheme)
    _expect("query", None, query)
    _expect("fragment", None, fragment)
    result = urlunsplit((scheme, hostname_with_port, path, "", ""))

    return result
