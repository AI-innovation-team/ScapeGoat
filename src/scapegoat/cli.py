"""Console script for profile freezing, rollout, and training."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal

import typer
from rich.console import Console

from scapegoat.benchmark.report import aggregate
from scapegoat.benchmark.report import render_report as render_benchmark_report
from scapegoat.benchmark.schema import BenchmarkRun, BenchmarkSet
from scapegoat.profile.budget import budget_report, render_report
from scapegoat.profile.corpus import normalize_sources, render_corpus_markdown
from scapegoat.profile.freezer import freeze_profile
from scapegoat.profile.loader import inspect_profile, load_profile_bundle, subject_dir
from scapegoat.profile.schema import FrozenProfile
from scapegoat.runtime.config import load_backend_config
from scapegoat.runtime.doc_export import export_session_markdown
from scapegoat.runtime.persistence import load_model, save_model
from scapegoat.runtime.rollout import build_result, build_session, run_rollout
from scapegoat.runtime.schema import RuntimeSession, TaskSpec
from scapegoat.training.loss import compute_loss
from scapegoat.training.schema import TrainingHistory, TrainingRecord
from scapegoat.training.update import train_profiles

app = typer.Typer(help="Profile-driven generator/discriminator plugin.")
profile_app = typer.Typer(help="Inspect and freeze human-readable profiles.")
rollout_app = typer.Typer(help="Run or resume frozen-profile rollout.")
train_app = typer.Typer(help="Create training records and update frozen profiles.")
benchmark_app = typer.Typer(help="Validate and aggregate behavior-prediction benchmarks.")
app.add_typer(profile_app, name="profile")
app.add_typer(rollout_app, name="rollout")
app.add_typer(train_app, name="train")
app.add_typer(benchmark_app, name="benchmark")
console = Console()


def _read_text(path: Path) -> str:
    return path.expanduser().resolve().read_text(encoding="utf-8")


@profile_app.command("inspect")
def profile_inspect(
    subject_id: str,
    base_dir: Annotated[Path, typer.Option("--base-dir", exists=True)] = Path("profiles"),
) -> None:
    """Check whether a subject profile has all required markdown assets."""

    inspection = inspect_profile(subject_id, base_dir)
    status = "complete" if inspection.is_complete else "incomplete"
    console.print(f"subject={subject_id} status={status}")
    for missing in inspection.missing_files:
        console.print(f"missing: {missing}")


@profile_app.command("corpus")
def profile_corpus(
    sources: Annotated[list[Path], typer.Argument(exists=True)],
    out: Annotated[Path | None, typer.Option("--out")] = None,
) -> None:
    """Normalize corpus files (documents / JSON conversations) into one markdown block."""

    normalized = normalize_sources([str(path) for path in sources])
    rendered = render_corpus_markdown(normalized)
    if out:
        out = out.expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered, encoding="utf-8")
        console.print(f"corpus_out={out} sources={len(normalized)}")
    else:
        console.print(rendered)


@profile_app.command("budget")
def profile_budget(
    subject_id: str,
    base_dir: Annotated[Path, typer.Option("--base-dir", exists=True)] = Path("profiles"),
    strict: Annotated[bool, typer.Option("--strict", help="Exit non-zero when over budget.")] = False,
) -> None:
    """Report profile asset sizes against the minimal-bytes budgets."""

    report = budget_report(subject_dir(subject_id, base_dir))
    console.print(render_report(report))
    if strict and not report.within:
        raise typer.Exit(code=1)


@profile_app.command("freeze")
def profile_freeze(
    subject_id: str,
    role: Annotated[Literal["generator", "discriminator"], typer.Option("--role")],
    out: Annotated[Path, typer.Option("--out")],
    base_dir: Annotated[Path, typer.Option("--base-dir", exists=True)] = Path("profiles"),
) -> None:
    """Compile markdown assets into one frozen runtime profile JSON."""

    bundle = load_profile_bundle(subject_id, base_dir)
    frozen = freeze_profile(bundle, role=role)
    save_model(frozen, out)
    console.print(f"frozen_profile={out}")


@profile_app.command("freeze-pair")
def profile_freeze_pair(
    generator_subject: Annotated[str, typer.Option("--generator-subject")],
    discriminator_subject: Annotated[str, typer.Option("--discriminator-subject")],
    out_dir: Annotated[Path, typer.Option("--out-dir")],
    base_dir: Annotated[Path, typer.Option("--base-dir", exists=True)] = Path("profiles"),
) -> None:
    """Freeze one generator/discriminator profile pair."""

    out_dir = out_dir.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    generator = freeze_profile(load_profile_bundle(generator_subject, base_dir), role="generator")
    discriminator = freeze_profile(load_profile_bundle(discriminator_subject, base_dir), role="discriminator")
    save_model(generator, out_dir / f"{generator_subject}.generator.json")
    save_model(discriminator, out_dir / f"{discriminator_subject}.discriminator.json")
    console.print(f"pair_dir={out_dir}")


@rollout_app.command("run")
def rollout_run(
    generator_profile: Annotated[Path, typer.Option("--generator-profile", exists=True)],
    discriminator_profile: Annotated[Path, typer.Option("--discriminator-profile", exists=True)],
    task_file: Annotated[Path, typer.Option("--task-file", exists=True)],
    backend: Annotated[str, typer.Option("--backend")] = "local",
    backend_config_file: Annotated[Path | None, typer.Option("--backend-config-file")] = None,
    session_out: Annotated[Path | None, typer.Option("--session-out")] = None,
    result_out: Annotated[Path | None, typer.Option("--result-out")] = None,
) -> None:
    """Run a frozen-profile rollout until convergence or max steps."""

    generator = load_model(generator_profile, FrozenProfile)
    discriminator = load_model(discriminator_profile, FrozenProfile)
    task = TaskSpec.model_validate_json(_read_text(task_file))
    backend_config = load_backend_config(backend_config_file)
    if backend == "claude":
        from scapegoat.runtime.claude_backend import build_claude_backends_from_env

        generator_backend_obj, discriminator_backend_obj = build_claude_backends_from_env(backend_config)
        state = run_rollout(
            generator,
            discriminator,
            task,
            generator_backend=generator_backend_obj.generate,
            discriminator_backend=discriminator_backend_obj.critique,
        )
    else:
        state = run_rollout(generator, discriminator, task)
    result = build_result(state)
    if session_out:
        save_model(build_session(state, str(generator_profile), str(discriminator_profile)), session_out)
    if result_out:
        save_model(result, result_out)
    console.print(
        "task="
        f"{result.task_id} "
        "final_dissatisfaction_score="
        f"{result.final_dissatisfaction_score} "
        f"rounds={result.total_rounds}"
    )


@rollout_app.command("resume")
def rollout_resume(
    session_file: Annotated[Path, typer.Option("--session-file", exists=True)],
    backend: Annotated[str, typer.Option("--backend")] = "local",
    backend_config_file: Annotated[Path | None, typer.Option("--backend-config-file")] = None,
    result_out: Annotated[Path | None, typer.Option("--result-out")] = None,
) -> None:
    """Resume a saved rollout session."""

    session = load_model(session_file, RuntimeSession)
    backend_config = load_backend_config(backend_config_file)
    generator = load_model(session.generator_profile_path, FrozenProfile)
    discriminator = load_model(session.discriminator_profile_path, FrozenProfile)
    if backend == "claude":
        from scapegoat.runtime.claude_backend import build_claude_backends_from_env

        generator_backend_obj, discriminator_backend_obj = build_claude_backends_from_env(backend_config)
        state = run_rollout(
            generator,
            discriminator,
            session.state.task,
            session.state,
            generator_backend=generator_backend_obj.generate,
            discriminator_backend=discriminator_backend_obj.critique,
        )
    else:
        state = run_rollout(generator, discriminator, session.state.task, session.state)
    result = build_result(state)
    save_model(build_session(state, session.generator_profile_path, session.discriminator_profile_path), session_file)
    if result_out:
        save_model(result, result_out)
    console.print(
        "task="
        f"{result.task_id} "
        "final_dissatisfaction_score="
        f"{result.final_dissatisfaction_score} "
        f"rounds={result.total_rounds}"
    )


@rollout_app.command("export-doc")
def rollout_export_doc(
    session_file: Annotated[Path, typer.Option("--session-file", exists=True)],
    out: Annotated[Path, typer.Option("--out")],
) -> None:
    """Export a real rollout session as a step-by-step markdown doc."""

    export_session_markdown(session_file, out)
    console.print(f"doc_export={out}")


@train_app.command("record")
def train_record(
    task_file: Annotated[Path, typer.Option("--task-file", exists=True)],
    deliverable_file: Annotated[Path, typer.Option("--deliverable-file", exists=True)],
    real_feedback_file: Annotated[Path, typer.Option("--real-feedback-file", exists=True)],
    out: Annotated[Path, typer.Option("--out")],
    simulated_feedback_file: Annotated[Path | None, typer.Option("--simulated-feedback-file")] = None,
    real_score: Annotated[int, typer.Option("--real-score", min=1, max=10)] = 10,
    simulated_score: Annotated[int | None, typer.Option("--simulated-score", min=1, max=10)] = None,
) -> None:
    """Create one offline training record JSON.

    The two scores drive the loss `dissatisfaction_gap`, so pass the scores
    actually observed instead of relying on the defaults.
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
    console.print(f"training_record={out}")


@train_app.command("update")
def train_update(
    generator_profile: Annotated[Path, typer.Option("--generator-profile", exists=True)],
    discriminator_profile: Annotated[Path, typer.Option("--discriminator-profile", exists=True)],
    record_file: Annotated[Path, typer.Option("--record-file", exists=True)],
    generator_out: Annotated[Path, typer.Option("--generator-out")],
    discriminator_out: Annotated[Path, typer.Option("--discriminator-out")],
    report_out: Annotated[Path | None, typer.Option("--report-out")] = None,
    history_file: Annotated[Path | None, typer.Option("--history-file")] = None,
) -> None:
    """Update frozen profiles from one training record.

    With `--history-file` the run performs delayed verification: a loss larger
    than the previous round's rolls the profiles back before patching. The file
    is created on first use and rewritten afterwards.
    """

    generator = load_model(generator_profile, FrozenProfile)
    discriminator = load_model(discriminator_profile, FrozenProfile)
    record = load_model(record_file, TrainingRecord)
    history: TrainingHistory | None = None
    if history_file:
        history = load_model(history_file, TrainingHistory) if history_file.exists() else TrainingHistory()
    loss = compute_loss(record)
    new_generator, new_discriminator, result = train_profiles(generator, discriminator, record, loss, history)
    save_model(new_generator, generator_out)
    save_model(new_discriminator, discriminator_out)
    if report_out:
        save_model(result, report_out)
    if history_file and history is not None:
        save_model(history, history_file)
    console.print(
        f"generator_version={new_generator.version} discriminator_version={new_discriminator.version} "
        f"loss_magnitude={result.loss_magnitude} rolled_back={result.rolled_back}"
    )


@benchmark_app.command("validate")
def benchmark_validate(
    cases_file: Annotated[Path, typer.Argument(exists=True)],
) -> None:
    """Validate a benchmark cases.json against the schema and report composition."""

    bench = BenchmarkSet.model_validate_json(_read_text(cases_file))
    by_task: dict[str, int] = {}
    post_cutoff = 0
    for case in bench.cases:
        by_task[case.task] = by_task.get(case.task, 0) + 1
        post_cutoff += int(case.post_cutoff)
    tasks = " ".join(f"{task}={count}" for task, count in sorted(by_task.items()))
    console.print(f"subject={bench.subject_id} cases={len(bench.cases)} {tasks} post_cutoff={post_cutoff}")


@benchmark_app.command("report")
def benchmark_report(
    run_file: Annotated[Path, typer.Argument(exists=True)],
) -> None:
    """Aggregate a saved BenchmarkRun JSON into per-task/condition scores and deltas."""

    run = BenchmarkRun.model_validate_json(_read_text(run_file))
    console.print(render_benchmark_report(aggregate(run)))


@app.callback()
def main() -> None:
    """Scapegoat runtime CLI."""


if __name__ == "__main__":
    app()
