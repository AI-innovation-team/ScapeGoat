"""Byte budgets for profile assets — the minimal-bytes principle, enforced.

A profile must state everything predictive and nothing redundant. Rewriting is
LLM work; this module supplies the measurable half: per-file byte budgets and a
report that ingestion/build skills must pass before finishing a merge.

Budgets can be overridden per subject with a `budget.json` in the profile dir:

    {"profile.md": 6144, "analyse": 10240}
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

from scapegoat.profile.constants import ANALYSE_FILENAMES

DEFAULT_PROFILE_BUDGET = 6 * 1024
DEFAULT_ANALYSE_BUDGET = 10 * 1024


class FileBudget(BaseModel):
    """Budget status for one profile asset."""

    relative_path: str
    size_bytes: int = Field(ge=0)
    budget_bytes: int = Field(gt=0)

    @property
    def over_bytes(self) -> int:
        return max(0, self.size_bytes - self.budget_bytes)

    @property
    def within(self) -> bool:
        return self.size_bytes <= self.budget_bytes


class BudgetReport(BaseModel):
    """Budget status for a whole profile directory."""

    profile_dir: str
    files: list[FileBudget]

    @property
    def within(self) -> bool:
        return all(item.within for item in self.files)

    @property
    def total_bytes(self) -> int:
        return sum(item.size_bytes for item in self.files)

    @property
    def over_files(self) -> list[FileBudget]:
        return [item for item in self.files if not item.within]


def load_budgets(profile_dir: str | Path) -> tuple[int, int]:
    """Return (profile.md budget, per-analyse budget), honoring budget.json."""

    profile_budget = DEFAULT_PROFILE_BUDGET
    analyse_budget = DEFAULT_ANALYSE_BUDGET
    override = Path(profile_dir) / "budget.json"
    if override.exists():
        data = json.loads(override.read_text(encoding="utf-8"))
        profile_budget = int(data.get("profile.md", profile_budget))
        analyse_budget = int(data.get("analyse", analyse_budget))
    return profile_budget, analyse_budget


def budget_report(profile_dir: str | Path) -> BudgetReport:
    """Measure every profile asset against its byte budget.

    Missing files are reported with size 0 so the report doubles as a
    completeness check.
    """

    directory = Path(profile_dir).expanduser().resolve()
    profile_budget, analyse_budget = load_budgets(directory)
    files: list[FileBudget] = []
    profile_path = directory / "profile.md"
    files.append(
        FileBudget(
            relative_path="profile.md",
            size_bytes=profile_path.stat().st_size if profile_path.exists() else 0,
            budget_bytes=profile_budget,
        )
    )
    for name in ANALYSE_FILENAMES:
        path = directory / "analyse" / name
        files.append(
            FileBudget(
                relative_path=f"analyse/{name}",
                size_bytes=path.stat().st_size if path.exists() else 0,
                budget_bytes=analyse_budget,
            )
        )
    return BudgetReport(profile_dir=str(directory), files=files)


def render_report(report: BudgetReport) -> str:
    """Render a budget report as aligned plain text."""

    lines = [f"profile_dir={report.profile_dir}"]
    for item in report.files:
        status = "ok" if item.within else f"OVER by {item.over_bytes}B"
        lines.append(f"{item.relative_path:<28} {item.size_bytes:>7}B / {item.budget_bytes}B  {status}")
    verdict = "within budget" if report.within else f"{len(report.over_files)} file(s) over budget"
    lines.append(f"total={report.total_bytes}B  verdict={verdict}")
    return "\n".join(lines)
