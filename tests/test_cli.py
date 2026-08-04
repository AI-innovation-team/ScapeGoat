"""CLI smoke tests."""

import json
from pathlib import Path

from typer.testing import CliRunner

from scapegoat.cli import app
from scapegoat.profile.schema import FrozenProfile
from scapegoat.runtime.persistence import save_model


def make_profile(path: Path, subject_id: str, role: str) -> None:
    save_model(
        FrozenProfile(
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
        ),
        path,
    )


def test_profile_inspect_command():
    runner = CliRunner()
    result = runner.invoke(app, ["profile", "inspect", "zgh", "--base-dir", "profiles"])
    assert result.exit_code == 0
    assert "status=complete" in result.stdout


def test_rollout_run_command(tmp_path: Path):
    runner = CliRunner()
    generator_profile = tmp_path / "generator.json"
    discriminator_profile = tmp_path / "discriminator.json"
    make_profile(generator_profile, "zgh", "generator")
    make_profile(discriminator_profile, "zzl", "discriminator")
    task_file = tmp_path / "task.json"
    task_file.write_text(
        json.dumps(
            {
                "task_id": "task1",
                "goal": "write",
                "deliverable_type": "draft",
                "constraints": ["be concise"],
                "success_criteria": ["目标"],
                "max_steps": 2,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    result = runner.invoke(
        app,
        [
            "rollout",
            "run",
            "--generator-profile",
            str(generator_profile),
            "--discriminator-profile",
            str(discriminator_profile),
            "--task-file",
            str(task_file),
            "--backend",
            "local",
        ],
    )
    assert result.exit_code == 0
    assert "final_dissatisfaction_score=" in result.stdout


def test_profile_corpus_command(tmp_path: Path):
    runner = CliRunner()
    chat = tmp_path / "chat.json"
    chat.write_text(json.dumps([{"role": "t", "content": "第一句"}], ensure_ascii=False), encoding="utf-8")
    out = tmp_path / "corpus.md"
    result = runner.invoke(app, ["profile", "corpus", str(chat), "--out", str(out)])
    assert result.exit_code == 0
    assert "sources=1" in result.stdout
    assert "t: 第一句" in out.read_text(encoding="utf-8")


def test_profile_budget_command():
    runner = CliRunner()
    result = runner.invoke(app, ["profile", "budget", "zgh", "--base-dir", "profiles"])
    assert result.exit_code == 0
    assert "verdict=" in result.stdout


def test_train_record_uses_provided_scores(tmp_path: Path):
    runner = CliRunner()
    task_file = tmp_path / "task.json"
    task_file.write_text(
        json.dumps({"task_id": "task1", "goal": "write"}, ensure_ascii=False),
        encoding="utf-8",
    )
    deliverable = tmp_path / "deliverable.md"
    deliverable.write_text("草稿正文", encoding="utf-8")
    real_feedback = tmp_path / "real.md"
    real_feedback.write_text("缺少中心论题。", encoding="utf-8")
    simulated_feedback = tmp_path / "simulated.md"
    simulated_feedback.write_text("整体不错。", encoding="utf-8")
    out = tmp_path / "record.json"
    result = runner.invoke(
        app,
        [
            "train",
            "record",
            "--task-file",
            str(task_file),
            "--deliverable-file",
            str(deliverable),
            "--real-feedback-file",
            str(real_feedback),
            "--simulated-feedback-file",
            str(simulated_feedback),
            "--out",
            str(out),
            "--real-score",
            "7",
            "--simulated-score",
            "4",
        ],
    )
    assert result.exit_code == 0
    record = json.loads(out.read_text(encoding="utf-8"))
    assert record["real_dissatisfaction_score"] == 7
    assert record["simulated_dissatisfaction_score"] == 4


def test_train_update_writes_and_reuses_loss_history(tmp_path: Path):
    runner = CliRunner()
    generator = tmp_path / "generator.json"
    discriminator = tmp_path / "discriminator.json"
    make_profile(generator, "zgh", "generator")
    make_profile(discriminator, "zzl", "discriminator")
    record_file = tmp_path / "record.json"
    record_file.write_text(
        json.dumps(
            {
                "task": {"task_id": "task1", "goal": "write"},
                "deliverable": "草稿正文",
                "real_discriminator_output": "缺少中心论题。",
                "real_dissatisfaction_score": 9,
                "simulated_discriminator_output": "整体不错。",
                "simulated_dissatisfaction_score": 3,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    history_file = tmp_path / "history.json"
    args = [
        "train",
        "update",
        "--generator-profile",
        str(generator),
        "--discriminator-profile",
        str(discriminator),
        "--record-file",
        str(record_file),
        "--generator-out",
        str(generator),
        "--discriminator-out",
        str(discriminator),
        "--history-file",
        str(history_file),
    ]
    first = runner.invoke(app, args)
    assert first.exit_code == 0
    assert "rolled_back=False" in first.stdout
    second = runner.invoke(app, args)
    assert second.exit_code == 0
    history = json.loads(history_file.read_text(encoding="utf-8"))
    assert len(history["entries"]) == 2


def test_train_record_defaults_stay_backward_compatible(tmp_path: Path):
    runner = CliRunner()
    task_file = tmp_path / "task.json"
    task_file.write_text(
        json.dumps({"task_id": "task1", "goal": "write"}, ensure_ascii=False),
        encoding="utf-8",
    )
    deliverable = tmp_path / "deliverable.md"
    deliverable.write_text("草稿正文", encoding="utf-8")
    real_feedback = tmp_path / "real.md"
    real_feedback.write_text("缺少中心论题。", encoding="utf-8")
    out = tmp_path / "record.json"
    result = runner.invoke(
        app,
        [
            "train",
            "record",
            "--task-file",
            str(task_file),
            "--deliverable-file",
            str(deliverable),
            "--real-feedback-file",
            str(real_feedback),
            "--out",
            str(out),
        ],
    )
    assert result.exit_code == 0
    record = json.loads(out.read_text(encoding="utf-8"))
    assert record["real_dissatisfaction_score"] == 10
    assert record["simulated_dissatisfaction_score"] is None


def test_profile_budget_strict_exits_nonzero_when_over(tmp_path: Path):
    runner = CliRunner()
    base = tmp_path / "profiles"
    profile_dir = base / "subj"
    (profile_dir / "analyse").mkdir(parents=True)
    (profile_dir / "profile.md").write_text("x" * 7000, encoding="utf-8")
    result = runner.invoke(app, ["profile", "budget", "subj", "--base-dir", str(base), "--strict"])
    assert result.exit_code == 1
