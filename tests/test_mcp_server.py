"""Tests for the MCP tool layer."""

from __future__ import annotations

import json
from pathlib import Path

from scapegoat.mcp.server import create_training_record, render_training_loss_prompt, train_profiles
from scapegoat.profile.schema import FrozenProfile
from scapegoat.runtime.persistence import save_model


def _write_inputs(tmp_path: Path) -> tuple[str, str, str, str]:
    task_file = tmp_path / "task.json"
    task_file.write_text(json.dumps({"task_id": "task1", "goal": "write"}, ensure_ascii=False), encoding="utf-8")
    deliverable = tmp_path / "deliverable.md"
    deliverable.write_text("草稿正文", encoding="utf-8")
    real_feedback = tmp_path / "real.md"
    real_feedback.write_text("缺少中心论题。", encoding="utf-8")
    simulated_feedback = tmp_path / "simulated.md"
    simulated_feedback.write_text("整体不错。", encoding="utf-8")
    return str(task_file), str(deliverable), str(real_feedback), str(simulated_feedback)


def _write_profile(path: Path, subject_id: str, role: str) -> str:
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
    return str(path)


def test_render_training_loss_prompt_returns_the_induction_prompt(tmp_path: Path):
    task_file, deliverable, real_feedback, simulated_feedback = _write_inputs(tmp_path)
    record_out = tmp_path / "record.json"
    create_training_record(
        task_file=task_file,
        deliverable_file=deliverable,
        real_feedback_file=real_feedback,
        out=str(record_out),
        simulated_feedback_file=simulated_feedback,
    )
    prompt = render_training_loss_prompt(record_file=str(record_out))["prompt"]
    assert "missing_dimensions" in prompt
    assert "缺少中心论题。" in prompt


def test_train_profiles_accepts_a_semantic_loss_response(tmp_path: Path):
    task_file, deliverable, real_feedback, simulated_feedback = _write_inputs(tmp_path)
    record_out = tmp_path / "record.json"
    create_training_record(
        task_file=task_file,
        deliverable_file=deliverable,
        real_feedback_file=real_feedback,
        out=str(record_out),
        simulated_feedback_file=simulated_feedback,
        real_score=9,
        simulated_score=3,
    )
    loss_response = json.dumps(
        {
            "missing_dimensions": [
                {"dimension": "时间规划冗余度", "trigger": "当交付物给出时间计划时", "focus": "追问是否留了冗余余量"}
            ],
            "over_divergent": [],
            "style_notes": [],
            "dissatisfaction_gap": 6,
        },
        ensure_ascii=False,
    )
    discriminator_out = tmp_path / "discriminator-v2.json"
    payload = train_profiles(
        generator_profile_path=_write_profile(tmp_path / "generator.json", "zgh", "generator"),
        discriminator_profile_path=_write_profile(tmp_path / "discriminator.json", "zzl", "discriminator"),
        record_file=str(record_out),
        generator_out=str(tmp_path / "generator-v2.json"),
        discriminator_out=str(discriminator_out),
        loss_response=loss_response,
        history_file=str(tmp_path / "history.json"),
    )
    assert payload["loss"]["missing_dimensions"][0]["dimension"] == "时间规划冗余度"
    assert payload["rolled_back"] is False
    rules = json.loads(discriminator_out.read_text(encoding="utf-8"))["behavior_rules"]
    assert "真实反馈关注[时间规划冗余度]: 当交付物给出时间计划时 → 追问是否留了冗余余量" in rules
    assert json.loads((tmp_path / "history.json").read_text(encoding="utf-8"))["entries"]


def test_create_training_record_uses_provided_scores(tmp_path: Path):
    task_file, deliverable, real_feedback, simulated_feedback = _write_inputs(tmp_path)
    out = tmp_path / "record.json"
    payload = create_training_record(
        task_file=task_file,
        deliverable_file=deliverable,
        real_feedback_file=real_feedback,
        out=str(out),
        simulated_feedback_file=simulated_feedback,
        real_score=8,
        simulated_score=3,
    )
    record = payload["training_record"]
    assert record["real_dissatisfaction_score"] == 8
    assert record["simulated_dissatisfaction_score"] == 3
    assert json.loads(out.read_text(encoding="utf-8"))["real_dissatisfaction_score"] == 8


def test_create_training_record_defaults_stay_backward_compatible(tmp_path: Path):
    task_file, deliverable, real_feedback, simulated_feedback = _write_inputs(tmp_path)
    out = tmp_path / "record.json"
    with_simulated = create_training_record(
        task_file=task_file,
        deliverable_file=deliverable,
        real_feedback_file=real_feedback,
        out=str(out),
        simulated_feedback_file=simulated_feedback,
    )["training_record"]
    assert with_simulated["real_dissatisfaction_score"] == 10
    assert with_simulated["simulated_dissatisfaction_score"] == 5

    without_simulated = create_training_record(
        task_file=task_file,
        deliverable_file=deliverable,
        real_feedback_file=real_feedback,
        out=str(out),
    )["training_record"]
    assert without_simulated["simulated_dissatisfaction_score"] is None
