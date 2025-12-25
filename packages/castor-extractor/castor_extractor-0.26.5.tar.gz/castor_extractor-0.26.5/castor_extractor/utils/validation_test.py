import pytest

from .validation import validate_baseurl


def test_validate_baseurl():
    assert (
        validate_baseurl("www.payfit.looker.eu")
        == "https://www.payfit.looker.eu"
    )

    assert (
        validate_baseurl("https://swile.looker.eu:443")
        == "https://swile.looker.eu:443"
    )

    assert (
        validate_baseurl("productboard.looker.eu:19999")
        == "https://productboard.looker.eu:19999"
    )

    assert (
        validate_baseurl("www.payfit.looker.eu/")
        == "https://www.payfit.looker.eu"
    )

    assert (
        validate_baseurl("productboard.looker.eu:19999/")
        == "https://productboard.looker.eu:19999"
    )

    # Idempotence
    url = "https://swile.looker.eu:443"
    assert validate_baseurl(url) == validate_baseurl(validate_baseurl(url))

    with pytest.raises(ValueError):
        validate_baseurl("")

    with pytest.raises(ValueError):
        validate_baseurl("ftp://timber.looker.eu")

    with pytest.raises(ValueError):
        validate_baseurl("https://timber.looker.eu:19999?query=params")

    with pytest.raises(ValueError):
        validate_baseurl("https://timber.looker.eu:19999#fragment")
