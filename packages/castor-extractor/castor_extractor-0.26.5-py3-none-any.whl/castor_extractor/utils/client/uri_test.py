from .uri import uri_encode


def test_uri_encode():
    assert uri_encode("Yok0On0Jon4L3nn0n_") == "Yok0On0Jon4L3nn0n_"
    assert uri_encode("Yok0On0:Jon4L3nn0n#") == "Yok0On0%3AJon4L3nn0n%23"
    assert uri_encode("password@robase") == "password%40robase"
