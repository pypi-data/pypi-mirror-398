"""Configuration scaffolding for Carbon Ops Guardrails."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import BaseSettings, Field


class CarbonOpsSettings(BaseSettings):
    """Runtime configuration for the carbon accounting pipeline.

    The defaults are placeholders and should be updated with project-specific values.
    Environment variables follow the prefix ``CARBON_OPS_``.
    """

    environment: str = Field(default="development", description="Runtime environment name")
    project_id: str = Field(default="dcl-ops", description="GCP project ID")
    ledger_bucket: str = Field(default="carbon-ops-ledger", description="GCS bucket for ledger exports")
    telemetry_topic: str = Field(default="carbon-ops-telemetry", description="Pub/Sub topic for ingestion")
    watt_time_api_key: Optional[str] = Field(default=None, description="WattTime API key for grid intensity")
    secret_manager_prefix: str = Field(default="projects/123/secrets", description="Secret Manager path prefix")

    class Config:
        env_prefix = "CARBON_OPS_"
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache(maxsize=1)
def settings() -> CarbonOpsSettings:
    """Return a cached settings instance for use across the package."""

    return CarbonOpsSettings()


def project_root() -> Path:
    """Resolve the repository root."""

    return Path(__file__).resolve().parent.parent
