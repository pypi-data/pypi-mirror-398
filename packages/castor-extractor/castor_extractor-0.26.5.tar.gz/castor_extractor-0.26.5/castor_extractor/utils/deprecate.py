import logging
import sys
import warnings


def deprecate_python(min_version_supported: tuple[int, ...]):
    """raises a warning if python version < min_version_supported"""

    python_version = (
        sys.version_info.major,
        sys.version_info.minor,
        sys.version_info.micro,
    )

    python_version_str = ".".join(map(str, python_version))
    min_supported_str = ".".join(map(str, min_version_supported))

    message = f"You are using python version {python_version_str}, please upgrade to version {min_supported_str} or higher."
    " Your version will be soon deprecated"

    if python_version < min_version_supported:
        warnings.warn(message, DeprecationWarning)

        # Since warnings are disabled by default, let's add a log as well
        logging.warning(message)
