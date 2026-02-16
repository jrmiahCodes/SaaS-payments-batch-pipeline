"""Application settings and derived paths."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    pipeline_env: str = Field(default="LOCAL", alias="PIPELINE_ENV")
    local_data_dir: Path = Field(default=Path("./data"), alias="LOCAL_DATA_DIR")
    s3_bucket: str | None = Field(default=None, alias="S3_BUCKET")
    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")
    mock_api_base_url: str = Field(default="http://127.0.0.1:8001", alias="MOCK_API_BASE_URL")

    safety_window_seconds: int = Field(default=300, alias="SAFETY_WINDOW_SECONDS", ge=0)
    default_days: int = Field(default=1, alias="DEFAULT_DAYS", ge=1)
    max_page_size: int = Field(default=100, alias="MAX_PAGE_SIZE", ge=1, le=500)

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    webhook_secret: str | None = Field(default=None, alias="WEBHOOK_SECRET")
    verify_webhook_signatures: bool = Field(default=False, alias="VERIFY_WEBHOOK_SIGNATURES")

    @field_validator("pipeline_env")
    @classmethod
    def validate_pipeline_env(cls, value: str) -> str:
        normalized = value.upper()
        if normalized not in {"LOCAL", "AWS"}:
            raise ValueError("PIPELINE_ENV must be LOCAL or AWS")
        return normalized

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        normalized = value.upper()
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if normalized not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {sorted(allowed)}")
        return normalized

    @property
    def bronze_root(self) -> Path:
        return self.local_data_dir / "bronze"

    @property
    def silver_root(self) -> Path:
        return self.local_data_dir / "silver"

    @property
    def gold_root(self) -> Path:
        return self.local_data_dir / "gold"

    @property
    def state_root(self) -> Path:
        return self.local_data_dir / "_state"

    @property
    def watermarks_root(self) -> Path:
        return self.state_root / "watermarks"

    @property
    def manifests_root(self) -> Path:
        return self.state_root / "manifests"

    def validate_runtime(self) -> None:
        if self.pipeline_env == "AWS" and not self.s3_bucket:
            raise ValueError("S3_BUCKET is required when PIPELINE_ENV=AWS")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_runtime()
    return settings
