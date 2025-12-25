import logging
from collections.abc import Callable

logger = logging.getLogger(__name__)


class SafeMode:
    """
    SafeMode class to parameterize safe_mode decorator

    Attributes:
        self.exceptions: tuple of exception that will be caught
        self.max_errors: nb of errors to catch
        self.errors_caught : list of errors caught
    """

    def __init__(
        self,
        exceptions: tuple[type[BaseException], ...],
        max_errors: int | float,
    ):
        self.exceptions = exceptions
        self.max_errors = max_errors
        self.errors_caught: list[type[BaseException]] = []

    @property
    def should_raise(self) -> bool:
        return len(self.errors_caught) >= self.max_errors


def safe_mode(
    safe_mode_params: SafeMode | None = None,
    default: Callable | None = None,
):
    """
    safe_mode decorator

    Args : safe_mode_params: param exception and number of exceptions to
    catch default: Optional - default function to execute if decorated
    function raises exception

    Note: KeyboardInterrupt is excluded from being excepted by design.
    """

    def decorator(function):
        def wrapper(*args, **kwargs):
            if safe_mode_params is None:
                return function(*args, **kwargs)

            try:
                result = function(*args, **kwargs)
            except KeyboardInterrupt:
                raise
            except safe_mode_params.exceptions as e:
                if safe_mode_params.should_raise:
                    raise e
                logger.error(
                    f"Safe mode : skip error {e} in function {function.__name__} with args {args} kwargs {kwargs}",
                )
                logger.debug(e, exc_info=True)
                safe_mode_params.errors_caught.append(e)
                return default() if default else None
            return result

        return wrapper

    return decorator
