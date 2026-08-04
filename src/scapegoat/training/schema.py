"""Schemas for offline training records and updates."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from scapegoat.profile.schema import FrozenProfile
from scapegoat.runtime.schema import TaskSpec


class TrainingRecord(BaseModel):
    """One alignment sample comparing simulated and real critic behavior."""

    task: TaskSpec
    deliverable: str
    real_discriminator_output: str
    real_dissatisfaction_score: int = Field(ge=1, le=10)
    simulated_discriminator_output: str | None = None
    simulated_dissatisfaction_score: int | None = Field(default=None, ge=1, le=10)
    source: Literal["manual", "session", "imported"] = "manual"
    created_at: datetime = Field(default_factory=datetime.now)

    @field_validator("deliverable", "real_discriminator_output")
    @classmethod
    def must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value.strip()


class MissingDimension(BaseModel):
    """One transferable discrimination axis the simulated critic failed to apply.

    A dimension is deliverable-agnostic on purpose: `trigger`/`focus` describe
    *when* the real critic starts caring and *what* he then goes after, never the
    wording of the case it was induced from. Sentence-level copies of the real
    feedback are what made training corrupt the profile.
    """

    dimension: str
    trigger: str
    focus: str

    @field_validator("dimension", "trigger", "focus")
    @classmethod
    def must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value.strip()


class LossReport(BaseModel):
    """Structured gap report between simulated and real discriminator output.

    Two producers fill this in: the deterministic `compute_loss` (text set diff,
    fills `missing_points`) and the LLM path `parse_loss_response` (semantic
    induction, fills `missing_dimensions`). `missing_dimensions` takes precedence
    downstream in `build_patches`.
    """

    dissatisfaction_gap: int
    missing_points: list[str] = Field(default_factory=list)
    extra_points: list[str] = Field(default_factory=list)
    style_mismatch: list[str] = Field(default_factory=list)
    summary: str
    missing_dimensions: list[MissingDimension] = Field(default_factory=list)


class ProfileUpdatePatch(BaseModel):
    """Patch instructions for evolving a frozen profile."""

    target_role: Literal["generator", "discriminator"]
    add_rules: list[str] = Field(default_factory=list)
    remove_rules: list[str] = Field(default_factory=list)
    rewrite_rules: list[str] = Field(default_factory=list)
    add_style_rules: list[str] = Field(default_factory=list)
    add_convergence_rules: list[str] = Field(default_factory=list)
    add_strategy_rules: list[str] = Field(default_factory=list)
    rationale: str


class TrainingResult(BaseModel):
    """Result bundle of one training update pass."""

    record: TrainingRecord
    loss: LossReport
    patches: list[ProfileUpdatePatch]
    new_generator_profile_version: int | None = None
    new_discriminator_profile_version: int | None = None
    loss_magnitude: float | None = None
    rolled_back: bool = False


class TrainingHistoryEntry(BaseModel):
    """One past training round, kept so the next round can verify it in hindsight.

    `version` is the profile version this round produced; the snapshots are the
    profiles as they stood *before* this round's patches, which is exactly what a
    rollback has to restore when the next round's loss turns out larger.
    """

    version: int
    loss_magnitude: float
    recorded_at: datetime = Field(default_factory=datetime.now)
    generator_snapshot: FrozenProfile | None = None
    discriminator_snapshot: FrozenProfile | None = None


class TrainingHistory(BaseModel):
    """Rolling loss history enabling the architecture's delayed verification.

    No separate validation pass exists: each round's loss is the verdict on the
    previous round's update. Persist this alongside the profiles to carry the
    comparison across training sessions.
    """

    entries: list[TrainingHistoryEntry] = Field(default_factory=list)

    @property
    def last(self) -> TrainingHistoryEntry | None:
        """The most recent round, or None on the first ever training pass."""

        return self.entries[-1] if self.entries else None
