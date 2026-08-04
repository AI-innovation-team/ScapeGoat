"""FastMCP server exposing scapegoat profile/rollout/training abilities.

This is the tool layer of the plugin: it adapts the existing pure-Python core
(`scapegoat.profile`, `scapegoat.runtime`, `scapegoat.training`) into MCP tools
that Claude Code can call with structured inputs and outputs. It intentionally
contains no business logic of its own — every tool delegates to the core modules
that the CLI (`scapegoat.cli`) also uses.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any, Literal

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from scapegoat.profile.budget import budget_report
from scapegoat.profile.corpus import normalize_sources, render_corpus_markdown
from scapegoat.profile.freezer import freeze_profile as freeze_profile_core
from scapegoat.profile.loader import inspect_profile as inspect_profile_core
from scapegoat.profile.loader import load_profile_bundle, subject_dir
from scapegoat.profile.schema import FrozenProfile
from scapegoat.runtime.config import load_backend_config
from scapegoat.runtime.persistence import load_model, save_model
from scapegoat.runtime.rollout import build_result, build_session
from scapegoat.runtime.rollout import run_rollout as run_rollout_core
from scapegoat.runtime.schema import TaskSpec
from scapegoat.training.loss import compute_loss, parse_loss_response, render_loss_prompt
from scapegoat.training.schema import TrainingHistory, TrainingRecord
from scapegoat.training.update import train_profiles as train_profiles_core

mcp = FastMCP("scapegoat")

_DEFAULT_BASE_DIR = "profiles"


def _read_text(path: str | Path) -> str:
    return Path(path).expanduser().resolve().read_text(encoding="utf-8")


@mcp.tool()
def inspect_profile(
    subject_id: Annotated[str, Field(description="Subject id whose markdown profile assets to check.")],
    base_dir: Annotated[str, Field(description="Directory holding subject profile folders.")] = _DEFAULT_BASE_DIR,
) -> dict[str, Any]:
    """Check whether a subject's markdown profile assets are complete.

    Returns the completeness status and which files are present or missing,
    so the caller can decide whether `freeze_profile` is safe to run.
    """

    inspection = inspect_profile_core(subject_id, base_dir)
    return {
        "subject_id": inspection.subject_id,
        "profile_dir": str(inspection.profile_dir),
        "is_complete": inspection.is_complete,
        "present_files": inspection.present_files,
        "missing_files": inspection.missing_files,
    }


@mcp.tool()
def normalize_corpus(
    sources: Annotated[list[str], Field(description="Corpus file paths: text documents or JSON conversations.")],
    out: Annotated[str | None, Field(description="Optional path to save the normalized markdown block.")] = None,
) -> dict[str, Any]:
    """Normalize corpus files into one speaker-labelled markdown block for extraction.

    `.json` files are parsed as conversations (tolerant of common export
    shapes); everything else is passed through as a document.
    """

    normalized = normalize_sources(list(sources))
    rendered = render_corpus_markdown(normalized)
    if out:
        target = Path(out).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered, encoding="utf-8")
    return {
        "saved_to": out,
        "sources": [{"path": item.path, "kind": item.kind, "turns": item.turns} for item in normalized],
        "markdown": None if out else rendered,
    }


@mcp.tool()
def profile_budget(
    subject_id: Annotated[str, Field(description="Subject id whose profile assets to measure.")],
    base_dir: Annotated[str, Field(description="Directory holding subject profile folders.")] = _DEFAULT_BASE_DIR,
) -> dict[str, Any]:
    """Measure profile assets against the minimal-bytes budgets.

    Returns per-file sizes vs budgets; ingestion/build flows must end within
    budget. Budgets are overridable via `budget.json` in the profile dir.
    """

    report = budget_report(subject_dir(subject_id, base_dir))
    return {
        "profile_dir": report.profile_dir,
        "within_budget": report.within,
        "total_bytes": report.total_bytes,
        "files": [
            {
                "path": item.relative_path,
                "size_bytes": item.size_bytes,
                "budget_bytes": item.budget_bytes,
                "over_bytes": item.over_bytes,
            }
            for item in report.files
        ],
    }


@mcp.tool()
def freeze_profile(
    subject_id: Annotated[str, Field(description="Subject id to compile into a frozen runtime profile.")],
    role: Annotated[Literal["generator", "discriminator"], Field(description="Runtime role for this profile.")],
    base_dir: Annotated[str, Field(description="Directory holding subject profile folders.")] = _DEFAULT_BASE_DIR,
    out: Annotated[str | None, Field(description="Optional path to also save the frozen profile JSON.")] = None,
) -> dict[str, Any]:
    """Compile a subject's markdown assets into one frozen runtime profile.

    Always returns the frozen profile as a JSON-serializable object. If `out`
    is given, the same profile is also written to disk at that path.
    """

    bundle = load_profile_bundle(subject_id, base_dir)
    frozen = freeze_profile_core(bundle, role=role)
    if out:
        save_model(frozen, out)
    return {"saved_to": out, "frozen_profile": frozen.model_dump(mode="json")}


@mcp.tool()
def freeze_profile_pair(
    generator_subject: Annotated[str, Field(description="Subject id used as the generator.")],
    discriminator_subject: Annotated[str, Field(description="Subject id used as the discriminator.")],
    out_dir: Annotated[str | None, Field(description="Optional directory to save both frozen profiles.")] = None,
    base_dir: Annotated[str, Field(description="Directory holding subject profile folders.")] = _DEFAULT_BASE_DIR,
) -> dict[str, Any]:
    """Freeze one generator/discriminator profile pair in a single call."""

    generator = freeze_profile_core(load_profile_bundle(generator_subject, base_dir), role="generator")
    discriminator = freeze_profile_core(load_profile_bundle(discriminator_subject, base_dir), role="discriminator")
    saved: dict[str, str] = {}
    if out_dir:
        target = Path(out_dir).expanduser().resolve()
        target.mkdir(parents=True, exist_ok=True)
        generator_path = target / f"{generator_subject}.generator.json"
        discriminator_path = target / f"{discriminator_subject}.discriminator.json"
        save_model(generator, generator_path)
        save_model(discriminator, discriminator_path)
        saved = {"generator": str(generator_path), "discriminator": str(discriminator_path)}
    return {
        "saved": saved,
        "generator_profile": generator.model_dump(mode="json"),
        "discriminator_profile": discriminator.model_dump(mode="json"),
    }


@mcp.tool()
def run_rollout(
    generator_profile_path: Annotated[str, Field(description="Path to a frozen generator profile JSON.")],
    discriminator_profile_path: Annotated[str, Field(description="Path to a frozen discriminator profile JSON.")],
    task_file: Annotated[str, Field(description="Path to a TaskSpec JSON file describing the task.")],
    backend: Annotated[Literal["local", "claude"], Field(description="Rollout backend to use.")] = "local",
    backend_config_file: Annotated[str | None, Field(description="Optional BackendConfig JSON path.")] = None,
    session_out: Annotated[str | None, Field(description="Optional path to save the full session JSON.")] = None,
    result_out: Annotated[str | None, Field(description="Optional path to save the result JSON.")] = None,
) -> dict[str, Any]:
    """Run an adversarial generator/discriminator rollout until convergence or max steps.

    The `local` backend is deterministic and needs no API key. The `claude`
    backend drives real Claude calls and requires Anthropic credentials in the
    environment. Returns the terminal result (final deliverable, score, rounds).
    """

    generator = load_model(generator_profile_path, FrozenProfile)
    discriminator = load_model(discriminator_profile_path, FrozenProfile)
    task = TaskSpec.model_validate_json(_read_text(task_file))
    backend_config = load_backend_config(backend_config_file)
    if backend == "claude":
        from scapegoat.runtime.claude_backend import build_claude_backends_from_env

        generator_backend, discriminator_backend = build_claude_backends_from_env(backend_config)
        state = run_rollout_core(
            generator,
            discriminator,
            task,
            generator_backend=generator_backend.generate,
            discriminator_backend=discriminator_backend.critique,
        )
    else:
        state = run_rollout_core(generator, discriminator, task)
    result = build_result(state)
    if session_out:
        save_model(build_session(state, generator_profile_path, discriminator_profile_path), session_out)
    if result_out:
        save_model(result, result_out)
    return {
        "session_saved_to": session_out,
        "result_saved_to": result_out,
        "result": result.model_dump(mode="json"),
    }


@mcp.tool()
def create_training_record(
    task_file: Annotated[str, Field(description="Path to a TaskSpec JSON file.")],
    deliverable_file: Annotated[str, Field(description="Path to the deliverable text the critic reviewed.")],
    real_feedback_file: Annotated[str, Field(description="Path to the real discriminator feedback text.")],
    out: Annotated[str, Field(description="Path to save the resulting TrainingRecord JSON.")],
    simulated_feedback_file: Annotated[
        str | None, Field(description="Optional path to simulated critic feedback for comparison.")
    ] = None,
    real_score: Annotated[int, Field(description="Real critic dissatisfaction score, 1-10.", ge=1, le=10)] = 10,
    simulated_score: Annotated[
        int | None,
        Field(
            description="Simulated critic dissatisfaction score, 1-10; only used with simulated feedback.", ge=1, le=10
        ),
    ] = None,
) -> dict[str, Any]:
    """Create one offline training record comparing real vs simulated critic output.

    The two scores drive `compute_loss`'s `dissatisfaction_gap`, so pass the
    scores actually observed instead of relying on the defaults.
    """

    task = TaskSpec.model_validate_json(_read_text(task_file))
    simulated_feedback = _read_text(simulated_feedback_file) if simulated_feedback_file else None
    resolved_simulated_score = None
    if simulated_feedback:
        resolved_simulated_score = 5 if simulated_score is None else simulated_score
    record = TrainingRecord(
        task=task,
        deliverable=_read_text(deliverable_file),
        real_discriminator_output=_read_text(real_feedback_file),
        real_dissatisfaction_score=real_score,
        simulated_discriminator_output=simulated_feedback,
        simulated_dissatisfaction_score=resolved_simulated_score,
    )
    save_model(record, out)
    return {"saved_to": out, "training_record": record.model_dump(mode="json")}


@mcp.tool()
def train_profiles(
    generator_profile_path: Annotated[str, Field(description="Path to the current frozen generator profile.")],
    discriminator_profile_path: Annotated[str, Field(description="Path to the current frozen discriminator profile.")],
    record_file: Annotated[str, Field(description="Path to a TrainingRecord JSON file.")],
    generator_out: Annotated[str, Field(description="Path to save the updated generator profile.")],
    discriminator_out: Annotated[str, Field(description="Path to save the updated discriminator profile.")],
    report_out: Annotated[str | None, Field(description="Optional path to save the training report JSON.")] = None,
    loss_response: Annotated[
        str | None,
        Field(
            description=(
                "Optional LLM reply to the prompt from `render_training_loss_prompt`. "
                "Given, the semantic loss (transferable discrimination dimensions) replaces the text-diff loss."
            )
        ),
    ] = None,
    history_file: Annotated[
        str | None,
        Field(
            description=(
                "Optional TrainingHistory JSON path enabling delayed verification: "
                "a loss larger than last round's rolls the profiles back before patching. Created if absent."
            )
        ),
    ] = None,
) -> dict[str, Any]:
    """Update frozen profiles from one training record and report version changes."""

    generator = load_model(generator_profile_path, FrozenProfile)
    discriminator = load_model(discriminator_profile_path, FrozenProfile)
    record = load_model(record_file, TrainingRecord)
    history: TrainingHistory | None = None
    if history_file:
        path = Path(history_file).expanduser()
        history = load_model(path, TrainingHistory) if path.exists() else TrainingHistory()
    loss = parse_loss_response(loss_response, record) if loss_response else compute_loss(record)
    new_generator, new_discriminator, result = train_profiles_core(generator, discriminator, record, loss, history)
    save_model(new_generator, generator_out)
    save_model(new_discriminator, discriminator_out)
    if report_out:
        save_model(result, report_out)
    if history_file and history is not None:
        save_model(history, history_file)
    return {
        "generator_saved_to": generator_out,
        "discriminator_saved_to": discriminator_out,
        "report_saved_to": report_out,
        "new_generator_version": new_generator.version,
        "new_discriminator_version": new_discriminator.version,
        "loss": loss.model_dump(mode="json"),
        "loss_magnitude": result.loss_magnitude,
        "rolled_back": result.rolled_back,
    }


@mcp.tool()
def render_training_loss_prompt(
    record_file: Annotated[str, Field(description="Path to a TrainingRecord JSON file.")],
) -> dict[str, Any]:
    """Render the prompt that induces transferable discrimination dimensions from a record.

    Run the returned prompt yourself (this server never calls a model), then pass
    the model's JSON reply back as `train_profiles`' `loss_response`. Without
    that round trip training falls back to sentence-level text diffing, which on
    two pieces of free-form prose copies the real feedback into the profile
    verbatim instead of generalizing it.
    """

    record = load_model(record_file, TrainingRecord)
    return {"prompt": render_loss_prompt(record)}


def main() -> None:
    """Console entry point: run the scapegoat MCP server over stdio."""

    mcp.run()


if __name__ == "__main__":
    main()
