from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

STRATEGY_ENV_PREFIX = "CATALOG_STRATEGY_"


class StrategyCredentials(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix=STRATEGY_ENV_PREFIX,
        extra="ignore",
        populate_by_name=True,
    )

    base_url: str
    password: str = Field(repr=False)
    username: str

    project_ids: list[str] | None = None

    @field_validator("project_ids", mode="before")
    @classmethod
    def _check_project_ids(cls, project_ids: Any) -> list[str] | None:
        """
        The project IDs are optional and can be either a list of strings
        or single string with project IDs separated by commas.
        """
        if project_ids is None:
            return None

        if isinstance(project_ids, str):
            return [item.strip() for item in project_ids.split(",")]

        if isinstance(project_ids, list):
            return project_ids

        raise ValueError(f"Unexpected type for project_id: {type(project_ids)}")
