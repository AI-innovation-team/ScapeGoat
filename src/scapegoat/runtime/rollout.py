"""Adversarial rollout loop for generator/discriminator profiles."""

from __future__ import annotations

from collections.abc import Callable

from scapegoat.profile.schema import FrozenProfile
from scapegoat.runtime.schema import (
    CritiqueStep,
    DeliverableStep,
    RolloutResult,
    RolloutTurn,
    RuntimeSession,
    RuntimeState,
    TaskSpec,
)

GeneratorBackend = Callable[[FrozenProfile, TaskSpec, RuntimeState, str | None], DeliverableStep]
DiscriminatorBackend = Callable[[FrozenProfile, TaskSpec, RuntimeState, DeliverableStep], CritiqueStep]


def default_generator(
    profile: FrozenProfile,
    task: TaskSpec,
    state: RuntimeState,
    latest_feedback: str | None,
) -> DeliverableStep:
    """Produce a deterministic generator step for local MVP usage."""

    step_index = len(state.turns) + 1
    lines = [
        f"[{profile.subject_id}] 交付物第 {step_index} 版",
        f"目标: {task.goal}",
        f"画像摘要: {profile.summary}",
    ]
    if state.current_best_deliverable:
        lines.append("基于上一版继续修订。")
    if latest_feedback:
        lines.append(f"吸收反馈: {latest_feedback}")
    if task.success_criteria:
        lines.append("成功标准:")
        lines.extend(f"- {criterion}" for criterion in task.success_criteria)
    lines.append("当前版本尝试覆盖以上要求，并保持与画像一致的表达。")
    return DeliverableStep(step_index=step_index, content="\n".join(lines), rationale="default-generator")


def default_discriminator(
    profile: FrozenProfile,
    task: TaskSpec,
    state: RuntimeState,
    deliverable: DeliverableStep,
) -> CritiqueStep:
    """Produce a deterministic discriminator step for local MVP usage."""

    text = deliverable.content.casefold()
    missing = [criterion for criterion in task.success_criteria if criterion.casefold() not in text]
    dissatisfaction = max(1, min(10, len(missing) + 3))
    if missing:
        feedback = f"[{profile.subject_id}] 当前仍有明显缺口: " + "；".join(missing)
        reasons = missing
    else:
        feedback = f"[{profile.subject_id}] 即使主要标准已覆盖，仍可继续从论证密度、结构和表达上挑刺。"
        reasons = ["继续挑刺", "维持高要求", "本地 stub 不做收敛判定"]
    return CritiqueStep(
        step_index=deliverable.step_index,
        feedback=feedback,
        dissatisfaction_score=dissatisfaction,
        reasons=reasons,
    )


def run_rollout(
    generator_profile: FrozenProfile,
    discriminator_profile: FrozenProfile,
    task: TaskSpec,
    state: RuntimeState | None = None,
    *,
    generator_backend: GeneratorBackend | None = None,
    discriminator_backend: DiscriminatorBackend | None = None,
) -> RuntimeState:
    """Run a rollout until the discriminator reports convergence or the max step limit.

    The loop stops as soon as a critique carries `converged=True`, marking the
    state as `converged`; otherwise it runs out its `task.max_steps` budget and
    the state becomes `max_steps_reached`.
    """

    generator = generator_backend or default_generator
    discriminator = discriminator_backend or default_discriminator
    runtime = state or RuntimeState(
        task=task,
        generator_profile_version=generator_profile.version,
        discriminator_profile_version=discriminator_profile.version,
    )
    latest_feedback: str | None = None
    if runtime.turns and runtime.turns[-1].discriminator_output:
        latest_feedback = runtime.turns[-1].discriminator_output.feedback
    while runtime.status == "running" and len(runtime.turns) < task.max_steps:
        round_index = len(runtime.turns) + 1
        turn = RolloutTurn(round=round_index)
        generator_output = generator(generator_profile, task, runtime, latest_feedback)
        critique = discriminator(discriminator_profile, task, runtime, generator_output)
        turn.generator_output = generator_output
        turn.discriminator_output = critique
        runtime.turns.append(turn)
        runtime.current_best_deliverable = generator_output.content
        latest_feedback = critique.feedback
        if critique.converged:
            runtime.status = "converged"
            break
    if runtime.status == "running":
        runtime.status = "max_steps_reached"
    return runtime


def build_result(state: RuntimeState) -> RolloutResult:
    """Convert runtime state to a terminal result object."""

    final_score = None
    if state.turns and state.turns[-1].discriminator_output:
        final_score = state.turns[-1].discriminator_output.dissatisfaction_score
    return RolloutResult(
        task_id=state.task.task_id,
        final_deliverable=state.current_best_deliverable,
        final_dissatisfaction_score=final_score,
        total_rounds=len(state.turns),
        turns=state.turns,
    )


def build_session(
    state: RuntimeState,
    generator_profile_path: str,
    discriminator_profile_path: str,
) -> RuntimeSession:
    """Create a persisted runtime session descriptor."""

    return RuntimeSession(
        generator_profile_path=generator_profile_path,
        discriminator_profile_path=discriminator_profile_path,
        state=state,
    )
