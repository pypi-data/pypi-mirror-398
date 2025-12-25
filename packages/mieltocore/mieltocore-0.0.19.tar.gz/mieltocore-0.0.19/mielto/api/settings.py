from __future__ import annotations

from importlib import metadata

from pydantic import field_validator
from pydantic_core.core_schema import ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict

from mielto.utils.log import logger


class MieltoAPISettings(BaseSettings):
    app_name: str = "mielto"
    app_version: str = metadata.version("mielto")

    api_runtime: str = "prd"
    alpha_features: bool = False

    api_url: str = "https://os-api.mielto.com"

    model_config = SettingsConfigDict(env_prefix="MIELTO_")

    @field_validator("api_runtime", mode="before")
    def validate_runtime_env(cls, v):
        """Validate api_runtime."""

        valid_api_runtimes = ["dev", "stg", "prd"]
        if v.lower() not in valid_api_runtimes:
            raise ValueError(f"Invalid api_runtime: {v}")

        return v.lower()

    @field_validator("api_url", mode="before")
    def update_api_url(cls, v, info: ValidationInfo):
        api_runtime = info.data["api_runtime"]
        if api_runtime == "dev":
            from os import getenv

            if getenv("MIELTO_RUNTIME") == "docker":
                return "http://host.docker.internal:7070"
            return "http://localhost:7070"
        elif api_runtime == "stg":
            return "https://api-stg.mielto.com"
        else:
            return "https://os-api.mielto.com"

    def gate_alpha_feature(self):
        if not self.alpha_features:
            logger.error("This is an Alpha feature not for general use.\nPlease message the Mielto team for access.")
            exit(1)


mielto_api_settings = MieltoAPISettings()
