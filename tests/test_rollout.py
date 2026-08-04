"""Tests for rollout state machine."""

from typing import Literal

from scapegoat.profile.schema import FrozenProfile
from scapegoat.runtime.rollout import build_result, run_rollout
from scapegoat.runtime.schema import CritiqueStep, DeliverableStep, TaskSpec


def make_profile(subject_id: str, role: Literal["generator", "discriminator"]) -> FrozenProfile:
    return FrozenProfile(
        subject_id=subject_id,
        role=role,
        version=1,
        summary="summary",
        core_rules=["rule"],
        style_rules=["style"],
        behavior_rules=["behavior"],
        convergence_rules=["converge"],
        dimension_rules={"execution": ["behavior"]},
        strategy_rules=["strategy"],
        profile_signature=f"{subject_id}: summary | dimensions=execution",
        evidence_refs={"execution": "# exec"},
        source_profile_path="/tmp/profile.md",
        source_analyse_paths={"execution": "/tmp/execution.md"},
    )


def test_rollout_generator_runs_to_max_steps_with_stub():
    task = TaskSpec(task_id="task1", goal="write", success_criteria=["criterion"], max_steps=3)

    def generator(profile, task, state, feedback):
        return DeliverableStep(step_index=len(state.turns) + 1, content="criterion reached")

    def discriminator(profile, task, state, deliverable):
        return CritiqueStep(step_index=deliverable.step_index, feedback="ok", dissatisfaction_score=2)

    state = run_rollout(
        make_profile("author", "generator"),
        make_profile("mentor", "discriminator"),
        task,
        generator_backend=generator,
        discriminator_backend=discriminator,
    )
    result = build_result(state)
    assert result.final_dissatisfaction_score == 2
    assert result.total_rounds == 3
    assert state.status == "max_steps_reached"
    assert state.turns[0].generator_output is not None


def test_rollout_stops_early_when_discriminator_converges():
    task = TaskSpec(task_id="task1", goal="write", success_criteria=["criterion"], max_steps=5)

    def generator(profile, task, state, feedback):
        return DeliverableStep(step_index=len(state.turns) + 1, content="criterion reached")

    def discriminator(profile, task, state, deliverable):
        return CritiqueStep(
            step_index=deliverable.step_index,
            feedback="标准已满足",
            dissatisfaction_score=2,
            converged=deliverable.step_index == 2,
        )

    state = run_rollout(
        make_profile("author", "generator"),
        make_profile("mentor", "discriminator"),
        task,
        generator_backend=generator,
        discriminator_backend=discriminator,
    )
    assert state.status == "converged"
    assert build_result(state).total_rounds == 2


def test_critique_step_defaults_to_not_converged():
    critique = CritiqueStep(step_index=1, feedback="仍有缺口", dissatisfaction_score=7)
    assert critique.converged is False
