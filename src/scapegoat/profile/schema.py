"""Pydantic schemas for profile assets and frozen runtime profiles."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class ProfileBundle(BaseModel):
    """Human-readable profile assets loaded from disk."""

    subject_id: str
    profile_markdown: str
    analyse: dict[str, str]
    source_dir: str
    profile_path: str

    @field_validator("subject_id", "profile_markdown", "source_dir", "profile_path")
    @classmethod
    def must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value.strip()

    @model_validator(mode="after")
    def analyse_must_not_be_empty(self) -> ProfileBundle:
        if not self.analyse:
            raise ValueError("analyse must not be empty")
        return self


class FrozenProfile(BaseModel):
    """Compact runtime representation derived from markdown profile assets."""

    subject_id: str
    role: Literal["generator", "discriminator"]
    version: int = Field(ge=1)
    frozen_at: datetime = Field(default_factory=datetime.now)
    summary: str
    core_rules: list[str]
    style_rules: list[str]
    behavior_rules: list[str]
    convergence_rules: list[str]
    dimension_rules: dict[str, list[str]] = Field(default_factory=dict)
    strategy_rules: list[str] = Field(default_factory=list)
    profile_signature: str = ""
    evidence_refs: dict[str, str]
    source_profile_path: str
    source_analyse_paths: dict[str, str]

    @field_validator("subject_id", "summary", "source_profile_path")
    @classmethod
    def fields_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value.strip()

    @model_validator(mode="after")
    def rules_must_exist(self) -> FrozenProfile:
        if not self.core_rules:
            raise ValueError("core_rules must not be empty")
        if not self.behavior_rules:
            raise ValueError("behavior_rules must not be empty")
        if not self.convergence_rules:
            raise ValueError("convergence_rules must not be empty")
        if not self.profile_signature.strip():
            raise ValueError("profile_signature must not be empty")
        return self


class FrozenProfilePair(BaseModel):
    """Pair of runtime profiles for adversarial rollout."""

    generator: FrozenProfile
    discriminator: FrozenProfile
