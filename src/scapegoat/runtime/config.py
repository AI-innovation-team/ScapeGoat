"""Backend configuration helpers for runtime rollout."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class BackendConfig(BaseModel):
    """Top-level rollout backend configuration."""

    backend: Literal["local", "claude"] = "local"
    model: str = "claude-opus-4-8"
    max_tokens: int = Field(default=4096, ge=256, le=64000)
    effort: Literal["low", "medium", "high", "xhigh", "max"] = "high"


def load_backend_config(path: str | Path | None) -> BackendConfig:
    """Load backend configuration from JSON, or return defaults."""

    if path is None:
        return BackendConfig()
    source = Path(path).expanduser().resolve()
    return BackendConfig.model_validate_json(source.read_text(encoding="utf-8"))
