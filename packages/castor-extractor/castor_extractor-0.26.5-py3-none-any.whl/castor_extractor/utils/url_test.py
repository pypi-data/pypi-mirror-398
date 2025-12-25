from pytest import raises

from ..utils.url import (
    add_path,
    is_valid,
    url_from,
)


def test_add_path():
    base = "https://test.com"

    # simple
    assert add_path(base, "toto") == f"{base}/toto"

    # multiple parts
    assert add_path(base, "to", "ta") == f"{base}/to/ta"

    # multiple parts with slash
    assert add_path(base, "a/b", "/c/d") == f"{base}/a/b/c/d"

    # base with path
    assert add_path(f"{base}/my/path", "/1/2/", "3") == f"{base}/my/path/1/2/3"

    # base with query string and fragment
    assert add_path(f"{base}?q=2#frag", "1/2") == f"{base}/1/2?q=2#frag"

    # bad base url
    with raises(ValueError):
        add_path("toto", "toto")

    # trailing slash
    base = "https://test.com/"

    # multiple parts with slash
    assert add_path(base, "a/b", "/c/d") == "https://test.com/a/b/c/d"


def test_url_is_valid():
    # valid
    assert is_valid("https://google.com")
    assert is_valid("http://user:pass@test.com:444/my/path?my=query#fragment")
    assert is_valid("ftp://hello.com", valid_schemes=("ftp",))

    # invalid
    assert not is_valid("hello.com")
    assert not is_valid("ftp://hello.com")
    assert not is_valid("http://")


def test_url_from():
    assert url_from() == ""
    assert url_from("http") == "http://"
    assert url_from("https", "google.com") == "https://google.com"
    assert url_from(netloc="te.st", query="q=3") == "//te.st?q=3"
