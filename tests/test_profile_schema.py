"""Tests for frozen profile schema."""

from scapegoat.profile.schema import FrozenProfile


def test_frozen_profile_valid():
    profile = FrozenProfile(
        subject_id="author",
        role="generator",
        version=1,
        summary="summary",
        core_rules=["rule"],
        style_rules=["style"],
        behavior_rules=["behavior"],
        convergence_rules=["converge"],
        dimension_rules={"execution": ["behavior"]},
        strategy_rules=["strategy"],
        profile_signature="author: summary | dimensions=execution",
        evidence_refs={"execution": "# exec"},
        source_profile_path="/tmp/profile.md",
        source_analyse_paths={"execution": "/tmp/execution.md"},
    )
    assert profile.version == 1
