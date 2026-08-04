"""Byte-budget report tests."""

import json
from pathlib import Path

from scapegoat.profile.budget import (
    DEFAULT_ANALYSE_BUDGET,
    DEFAULT_PROFILE_BUDGET,
    budget_report,
    load_budgets,
    render_report,
)
from scapegoat.profile.constants import ANALYSE_FILENAMES


def make_profile_dir(tmp_path: Path, analyse_bytes: int = 100) -> Path:
    profile_dir = tmp_path / "subj"
    (profile_dir / "analyse").mkdir(parents=True)
    (profile_dir / "profile.md").write_text("x" * 200, encoding="utf-8")
    for name in ANALYSE_FILENAMES:
        (profile_dir / "analyse" / name).write_text("y" * analyse_bytes, encoding="utf-8")
    return profile_dir


def test_report_within_budget(tmp_path: Path):
    report = budget_report(make_profile_dir(tmp_path))
    assert report.within
    assert len(report.files) == 1 + len(ANALYSE_FILENAMES)
    assert report.total_bytes == 200 + 100 * len(ANALYSE_FILENAMES)


def test_report_flags_over_budget_file(tmp_path: Path):
    profile_dir = make_profile_dir(tmp_path)
    (profile_dir / "analyse" / "execution.md").write_text("z" * (DEFAULT_ANALYSE_BUDGET + 1), encoding="utf-8")
    report = budget_report(profile_dir)
    assert not report.within
    assert [f.relative_path for f in report.over_files] == ["analyse/execution.md"]
    assert report.over_files[0].over_bytes == 1


def test_missing_files_reported_as_zero(tmp_path: Path):
    profile_dir = tmp_path / "empty"
    profile_dir.mkdir()
    report = budget_report(profile_dir)
    assert report.within
    assert all(f.size_bytes == 0 for f in report.files)


def test_budget_json_override(tmp_path: Path):
    profile_dir = make_profile_dir(tmp_path)
    (profile_dir / "budget.json").write_text(json.dumps({"profile.md": 50, "analyse": 60}), encoding="utf-8")
    assert load_budgets(profile_dir) == (50, 60)
    report = budget_report(profile_dir)
    assert not report.within
    over = {f.relative_path for f in report.over_files}
    assert "profile.md" in over  # 200B > 50B
    assert len(over) == 1 + len(ANALYSE_FILENAMES)  # every analyse file (100B) > 60B


def test_default_budgets_when_no_override(tmp_path: Path):
    profile_dir = make_profile_dir(tmp_path)
    assert load_budgets(profile_dir) == (DEFAULT_PROFILE_BUDGET, DEFAULT_ANALYSE_BUDGET)


def test_render_report_mentions_verdict(tmp_path: Path):
    report = budget_report(make_profile_dir(tmp_path))
    text = render_report(report)
    assert "verdict=within budget" in text
    assert "profile.md" in text
