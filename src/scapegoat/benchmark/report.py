"""Aggregate benchmark runs into per-task, per-condition scores and deltas."""

from __future__ import annotations

from pydantic import BaseModel, Field

from scapegoat.benchmark.schema import CONDITIONS, BenchmarkRun, Condition, TaskType

TASKS: tuple[TaskType, ...] = ("choice", "statement", "style", "critique")


class CellScore(BaseModel):
    """Mean score for one (task, condition) cell."""

    task: TaskType
    condition: Condition
    n: int = Field(ge=0)
    mean_score: float | None = None


class BenchmarkReport(BaseModel):
    """Aggregated result of one benchmark run."""

    subject_id: str
    cells: list[CellScore]
    profile_delta: dict[str, float] = Field(default_factory=dict)

    def cell(self, task: TaskType, condition: Condition) -> CellScore | None:
        for item in self.cells:
            if item.task == task and item.condition == condition:
                return item
        return None


def aggregate(run: BenchmarkRun) -> BenchmarkReport:
    """Compute per-cell means and the profile-vs-bare delta per task.

    ``profile_delta`` is the headline metric: how much the profile improves
    prediction over the model's bare prior. For every task including ``style``,
    higher is better (style score is judge-fooled rate).
    """

    cells: list[CellScore] = []
    means: dict[tuple[str, str], float] = {}
    for task in TASKS:
        for condition in CONDITIONS:
            scores = [r.score for r in run.runs if r.task == task and r.condition == condition]
            mean = round(sum(scores) / len(scores), 4) if scores else None
            cells.append(CellScore(task=task, condition=condition, n=len(scores), mean_score=mean))
            if mean is not None:
                means[(task, condition)] = mean
    delta: dict[str, float] = {}
    for task in TASKS:
        profile = means.get((task, "profile"))
        bare = means.get((task, "bare"))
        if profile is not None and bare is not None:
            delta[task] = round(profile - bare, 4)
    return BenchmarkReport(subject_id=run.subject_id, cells=cells, profile_delta=delta)


def render_report(report: BenchmarkReport) -> str:
    """Render the aggregate as an aligned text table."""

    lines = [f"subject={report.subject_id}", f"{'task':<10} {'condition':<8} {'n':>3}  mean"]
    for cell in report.cells:
        if cell.n == 0:
            continue
        mean = f"{cell.mean_score:.4f}" if cell.mean_score is not None else "-"
        lines.append(f"{cell.task:<10} {cell.condition:<8} {cell.n:>3}  {mean}")
    if report.profile_delta:
        lines.append("profile_delta (profile - bare):")
        for task, value in report.profile_delta.items():
            lines.append(f"  {task}: {value:+.4f}")
    return "\n".join(lines)
