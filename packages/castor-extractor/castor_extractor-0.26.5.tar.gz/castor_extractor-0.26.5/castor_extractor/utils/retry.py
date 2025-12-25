import logging
import random
import time
from collections.abc import Callable, Sequence
from enum import Enum
from typing import Any, Union

from pydantic import BaseModel, PositiveInt, PrivateAttr
from pydantic.fields import Field
from requests import HTTPError

logger = logging.getLogger(__name__)


MS_IN_SEC = 1000


class RetryStrategy(Enum):
    """retry mechanism"""

    CONSTANT = "CONSTANT"
    LINEAR = "LINEAR"
    EXPONENTIAL = "EXPONENTIAL"


DEFAULT_STRATEGY = RetryStrategy.CONSTANT


def _warning(callable: Callable, exception: BaseException) -> None:
    exception_type = type(exception)
    exception_path = f"{exception_type.__module__}.{exception_type.__name__}"
    callable_path = f"{callable.__module__}.{callable.__name__}"

    msg = f"Exception '{exception_path}' occurred within `{callable_path}`"
    logger.warning(msg)


class Retry(BaseModel):
    """
    This class checks if the retry conditions are met, and if so, how long to
    wait until the next attempt.
    """

    max_retries: PositiveInt
    base_ms: PositiveInt
    jitter_ms: PositiveInt
    strategy: RetryStrategy = Field(DEFAULT_STRATEGY, kw_only=True)
    _retry_attempts = PrivateAttr(default=0)

    def jitter(self) -> int:
        """compute random jitter in ms"""
        min_ = self.jitter_ms // 2
        max_ = int(self.jitter_ms * 1.5)
        return random.randrange(min_, max_)

    def base(self) -> int:
        """compute base wait time in ms"""
        base = self.base_ms
        if self.strategy == RetryStrategy.CONSTANT:
            return base
        if self.strategy == RetryStrategy.LINEAR:
            return base * self._retry_attempts
        # exponential
        base_sec = float(base) / MS_IN_SEC
        exponential_factor = 2 ** (self._retry_attempts - 1)
        return int(base_sec * exponential_factor * MS_IN_SEC)

    def check(self, error: BaseException, log_exc_info: bool = False) -> bool:
        """
        Check whether retry should happen or not.
        If log_exc_info is True, it will add a more extensive log (most notably
        including the traceback).
        """
        if self._retry_attempts >= self.max_retries:
            return False

        exc_info = error if log_exc_info else None
        logger.warning("Caught a retryable exception", exc_info=exc_info)

        self._retry_attempts += 1
        wait_ms = self.base() + self.jitter()
        wait_s = float(wait_ms) / MS_IN_SEC
        msg = f"Attempting a new call in {wait_s} seconds, {self._retry_attempts} attempt(s) / {self.max_retries} max retries"
        logger.warning(msg)
        time.sleep(wait_s)
        return True


WrapperReturnType = Union[tuple[BaseException, None], tuple[None, Any]]


def retry(
    exceptions: Sequence[type[BaseException]],
    max_retries: int = 1,
    base_ms: int = 0,
    jitter_ms: int = 1,
    strategy: RetryStrategy = DEFAULT_STRATEGY,
    log_exc_info: bool = False,
) -> Callable:
    """retry decorator"""

    exceptions_ = tuple(e for e in exceptions)

    def _wrapper(callable: Callable) -> Callable:
        def _try(*args, **kwargs) -> WrapperReturnType:
            try:
                return None, callable(*args, **kwargs)
            except exceptions_ as err:
                _warning(callable, err)
                return err, None

        def _func(*args, **kwargs) -> Any:
            retry = Retry(
                max_retries=max_retries,
                base_ms=base_ms,
                jitter_ms=jitter_ms,
                strategy=strategy,
            )
            while True:
                err, result = _try(*args, **kwargs)
                if err is None:
                    return result
                if retry.check(err, log_exc_info):
                    continue
                raise err

        return _func

    return _wrapper


def retry_request(
    status_codes: Sequence[int],
    max_retries: int = 1,
    base_ms: int = 10,
    jitter_ms: int = 20,
    strategy: RetryStrategy = DEFAULT_STRATEGY,
    log_exc_info: bool = False,
) -> Callable:
    """retry decorator"""

    exceptions_ = tuple(e for e in status_codes)

    def _wrapper(callable: Callable) -> Callable:
        def _try(*args, **kwargs) -> WrapperReturnType:
            try:
                return None, callable(*args, **kwargs)
            except HTTPError as err:
                status_code = err.response.status_code
                if status_code not in exceptions_:
                    raise err
                _warning(callable, err)
                return err, None

        def _func(*args, **kwargs) -> Any:
            retry = Retry(
                max_retries=max_retries,
                base_ms=base_ms,
                jitter_ms=jitter_ms,
                strategy=strategy,
            )
            while True:
                err, result = _try(*args, **kwargs)
                if err is None:
                    return result
                if retry.check(err, log_exc_info):
                    continue
                raise err

        return _func

    return _wrapper
