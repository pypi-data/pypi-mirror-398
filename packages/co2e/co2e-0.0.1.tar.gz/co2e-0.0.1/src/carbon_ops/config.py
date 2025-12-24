"""Configuration scaffolding for Carbon Ops Guardrails."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from os import getenv
from pathlib import Path
from typing import Optional

_ENV_PREFIX = "CARBON_OPS_"


@dataclass(frozen=True)
class CarbonOpsSettings:
    """Runtime configuration resolved from environment variables.

    This lightweight implementation intentionally avoids third-party dependencies so
    the placeholder release can ship with a minimal footprint. Defaults mirror the
    original design notes and can be overridden via environment variables prefixed
    with ``CARBON_OPS_`` (for example ``CARBON_OPS_PROJECT_ID``).
    """

    environment: str = "development"
    project_id: str = "dcl-ops"
    ledger_bucket: str = "carbon-ops-ledger"
    telemetry_topic: str = "carbon-ops-telemetry"
    watt_time_api_key: Optional[str] = None
    secret_manager_prefix: str = "projects/123/secrets"

    @classmethod
    def from_env(cls) -> "CarbonOpsSettings":
        """Build settings from environment variables."""

        return cls(
            environment=getenv(f"{_ENV_PREFIX}ENVIRONMENT", cls.environment),
            project_id=getenv(f"{_ENV_PREFIX}PROJECT_ID", cls.project_id),
            ledger_bucket=getenv(f"{_ENV_PREFIX}LEDGER_BUCKET", cls.ledger_bucket),
            telemetry_topic=getenv(f"{_ENV_PREFIX}TELEMETRY_TOPIC", cls.telemetry_topic),
            watt_time_api_key=getenv(f"{_ENV_PREFIX}WATT_TIME_API_KEY", cls.watt_time_api_key),
            secret_manager_prefix=getenv(f"{_ENV_PREFIX}SECRET_MANAGER_PREFIX", cls.secret_manager_prefix),
        )


@lru_cache(maxsize=1)
def settings() -> CarbonOpsSettings:
    """Return a cached settings instance for use across the package."""

    return CarbonOpsSettings.from_env()


def project_root() -> Path:
    """Resolve the repository root."""

    return Path(__file__).resolve().parent.parent
