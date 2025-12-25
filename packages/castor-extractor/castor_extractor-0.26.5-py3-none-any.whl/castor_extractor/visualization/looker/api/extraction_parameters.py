from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from ....utils import OUTPUT_DIR
from ..constants import (
    DEFAULT_LOOKER_PAGE_SIZE,
    DEFAULT_LOOKER_THREAD_POOL_SIZE,
    LOOKER_ENV_PREFIX,
    MAX_THREAD_POOL_SIZE,
    MIN_THREAD_POOL_SIZE,
)


class ExtractionParameters(BaseSettings):
    """
    Class holding all the parameters needed for the extraction of
    Looker metadata
    """

    model_config = SettingsConfigDict(
        env_prefix=LOOKER_ENV_PREFIX,
        extra="ignore",
        populate_by_name=True,
    )

    is_safe_mode: bool = False
    log_to_stdout: bool
    output: str = Field(validation_alias=OUTPUT_DIR)
    search_per_folder: bool
    page_size: int = Field(default=DEFAULT_LOOKER_PAGE_SIZE)
    thread_pool_size: int = Field(default=DEFAULT_LOOKER_THREAD_POOL_SIZE)

    @field_validator("thread_pool_size", mode="before")
    @classmethod
    def _check_thread_pool_size(cls, thread_pool_size: int) -> int:
        thread_pool_size = thread_pool_size or DEFAULT_LOOKER_THREAD_POOL_SIZE
        if MIN_THREAD_POOL_SIZE <= thread_pool_size <= MAX_THREAD_POOL_SIZE:
            return thread_pool_size
        raise ValueError("Thread pool size must be between 1 and 200 inclusive")
