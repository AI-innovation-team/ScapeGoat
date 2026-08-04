"""In-session rollout: Claude Code drives the loop, no API backend required.

This module is the bridge for running a rollout *inside* a Claude Code session
instead of through the Anthropic SDK. The orchestration model is:

* the generator (e.g. zgh) is played by the main conversation;
* the discriminator (e.g. zzl) is played by a spawned Claude Code subagent;
* this module only renders prompts, advances state, and persists sessions —
  it never calls an LLM itself.

Typical flow per round, executed by the skill:
1. `start_state` (first round) or load an existing session.
2. main session writes a deliverable -> `record_generator_step`.
3. `build_discriminator_prompt` -> spawn a subagent with it.
4. subagent returns JSON -> `record_discriminator_step` (parses + appends).
5. repeat until `is_finished`, then `save_session`.
"""

from __future__ import annotations

from pathlib import Path

from scapegoat.profile.render import parse_critique_response, render_discriminator_agent_prompt
from scapegoat.profile.schema import FrozenProfile
from scapegoat.runtime.persistence import save_model
from scapegoat.runtime.rollout import build_result, build_session
from scapegoat.runtime.schema import (
    DeliverableStep,
    RolloutResult,
    RolloutTurn,
    RuntimeState,
    TaskSpec,
)


def start_state(
    generator_profile: FrozenProfile,
    discriminator_profile: FrozenProfile,
    task: TaskSpec,
) -> RuntimeState:
    """Create the initial runtime state for an in-session rollout."""

    return RuntimeState(
        task=task,
        generator_profile_version=generator_profile.version,
        discriminator_profile_version=discriminator_profile.version,
    )


def latest_feedback(state: RuntimeState) -> str | None:
    """Return the most recent discriminator feedback, if any."""

    if state.turns and state.turns[-1].discriminator_output:
        return state.turns[-1].discriminator_output.feedback
    return None


def is_finished(state: RuntimeState) -> bool:
    """Whether the rollout has converged or hit its max step budget."""

    return state.status == "converged" or len(state.turns) >= state.task.max_steps


def next_round_index(state: RuntimeState) -> int:
    """1-based index of the round to be produced next."""

    return len(state.turns) + 1


def record_generator_step(state: RuntimeState, content: str, rationale: str | None = None) -> DeliverableStep:
    """Open a new round with the generator deliverable produced by the main session.

    Appends a turn carrying only the generator output; the discriminator output
    is filled in by `record_discriminator_step`.
    """

    step_index = next_round_index(state)
    deliverable = DeliverableStep(step_index=step_index, content=content, rationale=rationale or "in-session:main")
    state.turns.append(RolloutTurn(round=step_index, generator_output=deliverable))
    state.current_best_deliverable = content
    return deliverable


def build_discriminator_prompt(
    discriminator_profile: FrozenProfile,
    state: RuntimeState,
) -> str:
    """Render the role-play prompt to hand to the zzl subagent for the open round.

    Must be called after `record_generator_step` for the current round.
    """

    if not state.turns or state.turns[-1].generator_output is None:
        raise ValueError("no open generator deliverable to critique; call record_generator_step first")
    deliverable = state.turns[-1].generator_output
    return render_discriminator_agent_prompt(discriminator_profile, state.task, deliverable, state)


def record_discriminator_step(state: RuntimeState, response: str) -> RuntimeState:
    """Parse the subagent's JSON critique and attach it to the open round.

    A critique carrying `converged=True` ends the session immediately; otherwise
    the session ends only once the max step budget is exhausted.
    """

    if not state.turns or state.turns[-1].generator_output is None:
        raise ValueError("no open round awaiting a critique")
    step_index = state.turns[-1].round
    critique = parse_critique_response(response, step_index)
    state.turns[-1].discriminator_output = critique
    if critique.converged:
        state.status = "converged"
    elif is_finished(state):
        state.status = "max_steps_reached"
    return state


def save_session(
    state: RuntimeState,
    generator_profile_path: str,
    discriminator_profile_path: str,
    session_out: str | Path,
    result_out: str | Path | None = None,
) -> RolloutResult:
    """Persist the session (and optionally the terminal result) to disk."""

    session = build_session(state, str(generator_profile_path), str(discriminator_profile_path))
    save_model(session, session_out)
    result = build_result(state)
    if result_out:
        save_model(result, result_out)
    return result
