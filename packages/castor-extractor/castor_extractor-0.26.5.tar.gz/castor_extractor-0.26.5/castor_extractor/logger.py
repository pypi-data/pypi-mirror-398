import logging
import os
import sys

from .utils import current_timestamp

MAIN_LOGGER_NAME = "castor_extractor"
CASTOR_LOG_FILENAME = "castor.log"
LOG_FORMAT = "%(levelname)s - %(message)s"


logger = logging.getLogger(MAIN_LOGGER_NAME)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(LOG_FORMAT)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.INFO)
logger.addHandler(stream_handler)


def add_logging_file_handler(output_directory: str) -> None:
    """
    Add a filehandler to the main logger.
    """
    filename = f"{current_timestamp()}-{CASTOR_LOG_FILENAME}"
    file_path = os.path.join(output_directory, filename)

    fmt = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
    file_handler = logging.FileHandler(file_path)
    file_handler.setFormatter(fmt)

    logger.addHandler(file_handler)


def set_stream_handler_to_stdout():
    """Change the StreamHandler's output destination from stderr to stdout"""
    logger_ = logging.getLogger(MAIN_LOGGER_NAME)
    for handler in logger_.handlers:
        if isinstance(handler, logging.StreamHandler):
            handler.setStream(sys.stdout)
