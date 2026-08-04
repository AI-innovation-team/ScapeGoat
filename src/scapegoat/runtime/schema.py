"""Schemas for adversarial rollout runtime state."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class TaskSpec(BaseModel):
    """Description of the task being iteratively refined."""

    task_id: str
    goal: str
    context: str | None = None
    deliverable_type: str = "general"
    constraints: list[str] = Field(default_factory=list)
    initial_material: str | None = None
    success_criteria: list[str] = Field(default_factory=list)
    max_steps: int = Field(default=10, ge=1, le=20)

    @field_validator("task_id", "goal")
    @classmethod
    def fields_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value.strip()


class DeliverableStep(BaseModel):
    """A single generator output in one round."""

    step_index: int = Field(ge=1)
    content: str
    rationale: str | None = None


class CritiqueStep(BaseModel):
    """A single discriminator output in one round."""

    step_index: int = Field(ge=1)
    feedback: str
    dissatisfaction_score: int = Field(ge=1, le=10)
    reasons: list[str] = Field(default_factory=list)
    converged: bool = False


class RolloutTurn(BaseModel):
    """One complete generator/discriminator turn."""

    round: int = Field(ge=1)
    generator_output: DeliverableStep | None = None
    discriminator_output: CritiqueStep | None = None


class RuntimeState(BaseModel):
    """Mutable rollout state persisted between steps."""

    task: TaskSpec
    generator_profile_version: int = Field(ge=1)
    discriminator_profile_version: int = Field(ge=1)
    current_best_deliverable: str | None = None
    turns: list[RolloutTurn] = Field(default_factory=list)
    status: Literal["running", "converged", "max_steps_reached", "stopped"] = "running"


class RolloutResult(BaseModel):
    """Terminal result of a rollout run."""

    task_id: str
    final_deliverable: str | None
    final_dissatisfaction_score: int | None = None
    total_rounds: int
    turns: list[RolloutTurn]


class RuntimeSession(BaseModel):
    """Persisted session bundle for resume support."""

    generator_profile_path: str
    discriminator_profile_path: str
    state: RuntimeState
