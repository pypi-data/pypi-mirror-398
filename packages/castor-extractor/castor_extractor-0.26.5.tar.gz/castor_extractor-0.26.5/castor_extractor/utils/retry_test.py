from http import HTTPStatus
from statistics import variance
from time import time
from unittest.mock import patch

import pytest
import requests
from pydantic.error_wrappers import ValidationError
from requests import HTTPError, Response

from .retry import MS_IN_SEC, Retry, RetryStrategy, retry_request


def test_retry_field_validations():
    valid_args = {"max_retries": 1, "base_ms": 1000, "jitter_ms": 500}
    Retry(**valid_args)  # happy path

    failing_args_list = [
        {"max_retries": 0},
        {"base_ms": -523},
        {"jitter_ms": None},
        {"strategy": None},
    ]
    for failing_args in failing_args_list:
        args = {**valid_args, **failing_args}

        with pytest.raises(ValidationError):
            Retry(**args)


def _within(value: int, min_: int, max_: int) -> bool:
    return value >= min_ and value <= max_


def test_retry_strategy__jitter():
    retry = Retry(max_retries=2, base_ms=1000, jitter_ms=500)
    jitters = [retry.jitter() for _ in range(5)]

    # boundaries
    assert all(_within(j, 250, 750) for j in jitters)
    # randomness
    assert variance(jitters) > 0


def _iterate_base(retry: Retry, count: int) -> list[int]:
    bases: list[int] = []
    for _ in range(count):
        retry._retry_attempts += 1
        bases.append(retry.base())
    return bases


def test_retry_strategy__base():
    common_args = {"max_retries": 2, "base_ms": 2000, "jitter_ms": 500}
    # default strategy is constant
    retry = Retry(**common_args)
    assert _iterate_base(retry, 3) == [2000, 2000, 2000]
    retry = Retry(**common_args, strategy=RetryStrategy.CONSTANT)
    assert _iterate_base(retry, 3) == [2000, 2000, 2000]
    # linear
    retry = Retry(**common_args, strategy=RetryStrategy.LINEAR)
    assert _iterate_base(retry, 3) == [2000, 4000, 6000]
    # exponential
    # Set base_ms = 1000 to verify correct exponential growth.
    # With this value, (base_ms / 1000) == 1, so earlier implementations
    # incorrectly produced constant delays. This test ensures the fixed logic
    # now yields 1000, 2000, 4000, 8000 as expected.
    common_args["base_ms"] = 1000
    retry = Retry(**common_args, strategy=RetryStrategy.EXPONENTIAL)
    assert _iterate_base(retry, 4) == [1000, 2000, 4000, 8000]


def test_retry_strategy__check():
    retry = Retry(max_retries=3, base_ms=100, jitter_ms=10)
    error = ValueError

    before = time()
    assert retry.check(error)
    assert retry.check(error)
    assert retry.check(error)
    after = time()

    assert retry.check(error) is False
    delta_ms = int((after - before) * MS_IN_SEC)
    assert _within(delta_ms, 315, 345)


@patch("requests.get")
def test_retry_request(mocked_get):
    def error_response():
        response = Response()
        response.status_code = HTTPStatus.UNAUTHORIZED
        return response

    mocked_get.return_value = error_response()

    @retry_request(status_codes=(HTTPStatus.UNAUTHORIZED,), max_retries=3)
    def get():
        response = requests.get("hello")
        response.raise_for_status()
        return response.json()

    with pytest.raises(HTTPError):
        get()

    assert mocked_get.call_count == 4  # 1 call + 3 retries
