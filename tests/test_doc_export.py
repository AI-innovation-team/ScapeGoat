"""Tests for rollout markdown export."""

from pathlib import Path
from typing import Literal

from scapegoat.profile.schema import FrozenProfile
from scapegoat.runtime.doc_export import export_session_markdown
from scapegoat.runtime.persistence import save_model
from scapegoat.runtime.rollout import build_session
from scapegoat.runtime.schema import CritiqueStep, DeliverableStep, RolloutTurn, RuntimeState, TaskSpec


def _profile(subject_id: str, role: Literal["generator", "discriminator"]) -> FrozenProfile:
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


def test_export_session_markdown(tmp_path: Path):
    generator_path = tmp_path / "generator.json"
    discriminator_path = tmp_path / "discriminator.json"
    save_model(_profile("zgh", "generator"), generator_path)
    save_model(_profile("zzl", "discriminator"), discriminator_path)
    task = TaskSpec(
        task_id="task1",
        goal="book chapter",
        deliverable_type="chapter_draft",
        constraints=["formal tone"],
        success_criteria=["clear thesis"],
    )
    state = RuntimeState(
        task=task,
        generator_profile_version=1,
        discriminator_profile_version=1,
        current_best_deliverable="draft",
        turns=[
            RolloutTurn(
                round=1,
                generator_output=DeliverableStep(step_index=1, content="draft v1"),
                discriminator_output=CritiqueStep(
                    step_index=1,
                    feedback="revise thesis",
                    dissatisfaction_score=8,
                ),
            )
        ],
        status="stopped",
    )
    session_path = tmp_path / "session.json"
    doc_path = tmp_path / "cycle.md"
    save_model(build_session(state, str(generator_path), str(discriminator_path)), session_path)
    export_session_markdown(session_path, doc_path)
    text = doc_path.read_text(encoding="utf-8")
    assert "revise thesis" in text
    assert "dissatisfaction_score = 8" in text
