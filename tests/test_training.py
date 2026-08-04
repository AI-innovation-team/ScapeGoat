"""Tests for offline training updates."""

import json
from typing import Literal

import pytest

from scapegoat.profile.schema import FrozenProfile
from scapegoat.runtime.schema import TaskSpec
from scapegoat.training.loss import compute_loss, loss_magnitude, parse_loss_response, render_loss_prompt
from scapegoat.training.schema import (
    LossReport,
    MissingDimension,
    ProfileUpdatePatch,
    TrainingHistory,
    TrainingRecord,
)
from scapegoat.training.update import MAX_BEHAVIOR_RULES, apply_patch, build_patches, train_profiles


def make_profile(subject_id: str, role: Literal["generator", "discriminator"]) -> FrozenProfile:
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


def test_training_updates_versions():
    record = TrainingRecord(
        task=TaskSpec(task_id="task1", goal="write", success_criteria=["criterion"]),
        deliverable="draft",
        real_discriminator_output="缺少 criterion。",
        real_dissatisfaction_score=9,
        simulated_discriminator_output="一切都好。",
        simulated_dissatisfaction_score=3,
    )
    loss = compute_loss(record)
    new_generator, new_discriminator, result = train_profiles(
        make_profile("author", "generator"),
        make_profile("mentor", "discriminator"),
        record,
        loss,
    )
    assert new_generator.version == 2
    assert new_discriminator.version == 2
    assert result.loss.dissatisfaction_gap == 6


def test_build_patches_keeps_removal_points_raw():
    loss = LossReport(
        dissatisfaction_gap=4,
        missing_points=["缺少中心论题"],
        extra_points=["过度展开背景介绍"],
        style_mismatch=[],
        summary="summary",
    )
    discriminator_patch = build_patches(loss)[0]
    assert discriminator_patch.remove_rules == ["过度展开背景介绍"]


def test_apply_patch_removes_matching_rules_by_substring():
    profile = make_profile("mentor", "discriminator").model_copy(
        update={
            "behavior_rules": ["真实反馈关注: 过度展开背景介绍", "保留这条规则"],
            "dimension_rules": {"execution": ["过度展开背景介绍的旧习惯", "保留这条规则"]},
            "core_rules": ["过度展开背景介绍"],
        }
    )
    patch = ProfileUpdatePatch(
        target_role="discriminator",
        remove_rules=["过度展开背景介绍"],
        rationale="drop over-divergent points",
    )
    updated = apply_patch(profile, patch)
    assert updated.behavior_rules == ["保留这条规则"]
    assert updated.dimension_rules["execution"] == ["保留这条规则"]
    assert updated.core_rules == ["过度展开背景介绍"]


def test_train_profiles_drops_over_divergent_rule_end_to_end():
    over_divergent = "反复追问排版细节"
    discriminator = make_profile("mentor", "discriminator").model_copy(
        update={
            "behavior_rules": ["真实反馈关注: 反复追问排版细节", "保留这条规则"],
            "dimension_rules": {"execution": ["反复追问排版细节", "保留这条规则"]},
        }
    )
    record = TrainingRecord(
        task=TaskSpec(task_id="task1", goal="write", success_criteria=["criterion"]),
        deliverable="draft",
        real_discriminator_output="缺少中心论题。",
        real_dissatisfaction_score=9,
        simulated_discriminator_output=f"{over_divergent}。",
        simulated_dissatisfaction_score=3,
    )
    loss = compute_loss(record)
    assert over_divergent in loss.extra_points
    _, new_discriminator, _ = train_profiles(make_profile("author", "generator"), discriminator, record, loss)
    assert not any(over_divergent in rule for rule in new_discriminator.behavior_rules)
    assert not any(over_divergent in rule for rule in new_discriminator.dimension_rules["execution"])
    assert "保留这条规则" in new_discriminator.behavior_rules


def test_apply_patch_removal_ignores_blank_points():
    profile = make_profile("mentor", "discriminator")
    patch = ProfileUpdatePatch(
        target_role="discriminator",
        remove_rules=["", "   "],
        rationale="no-op removal",
    )
    updated = apply_patch(profile, patch)
    assert updated.behavior_rules == profile.behavior_rules


def make_record(simulated_score: int | None = 3) -> TrainingRecord:
    return TrainingRecord(
        task=TaskSpec(task_id="task1", goal="写一本书", success_criteria=["有中心论题"]),
        deliverable="草稿正文",
        real_discriminator_output="你这个时间表根本没留余量。",
        real_dissatisfaction_score=9,
        simulated_discriminator_output="整体结构还可以，建议补充案例。",
        simulated_dissatisfaction_score=simulated_score,
    )


def make_loss_response() -> str:
    return json.dumps(
        {
            "missing_dimensions": [
                {
                    "dimension": "时间规划冗余度",
                    "trigger": "当交付物给出时间计划时",
                    "focus": "追问是否留了冗余余量",
                },
                {
                    "dimension": "归因落点",
                    "trigger": "当对方解释失败原因时",
                    "focus": "追问责任是否落回自己身上",
                },
            ],
            "over_divergent": ["反复追问排版细节"],
            "style_notes": ["真实更偏短促追问"],
            "dissatisfaction_gap": 99,
        },
        ensure_ascii=False,
    )


def test_render_loss_prompt_states_the_transferability_contract():
    prompt = render_loss_prompt(make_record())
    assert "missing_dimensions" in prompt
    assert "over_divergent" in prompt
    assert "可迁移" in prompt
    # The whole point of the rewrite: case-specific wording must be banned.
    assert "严禁" in prompt
    assert "你这个时间表根本没留余量。" in prompt


def test_render_loss_prompt_handles_missing_simulation():
    record = make_record().model_copy(
        update={"simulated_discriminator_output": None, "simulated_dissatisfaction_score": None}
    )
    prompt = render_loss_prompt(record)
    assert "模拟完全缺席" in prompt
    assert "模拟不满意度：未给出" in prompt


def test_parse_loss_response_yields_dimensions_not_sentences():
    loss = parse_loss_response(make_loss_response(), make_record())
    assert [item.dimension for item in loss.missing_dimensions] == ["时间规划冗余度", "归因落点"]
    assert loss.missing_points == []
    assert loss.extra_points == ["反复追问排版细节"]
    assert loss.style_mismatch == ["真实更偏短促追问"]


def test_parse_loss_response_prefers_record_scores_over_model_arithmetic():
    loss = parse_loss_response(make_loss_response(), make_record(simulated_score=3))
    assert loss.dissatisfaction_gap == 6


def test_parse_loss_response_falls_back_to_model_gap_without_simulated_score():
    record = make_record().model_copy(
        update={"simulated_discriminator_output": None, "simulated_dissatisfaction_score": None}
    )
    response = json.dumps({"missing_dimensions": [], "dissatisfaction_gap": 4}, ensure_ascii=False)
    assert parse_loss_response(response, record).dissatisfaction_gap == 4


def test_parse_loss_response_skips_incomplete_dimensions():
    response = json.dumps(
        {
            "missing_dimensions": [
                {"dimension": "时间规划冗余度", "trigger": "当给出时间计划时", "focus": "追问余量"},
                {"dimension": "缺字段", "trigger": ""},
                "不是对象",
            ],
            "over_divergent": ["", "  ", "排版细节"],
        },
        ensure_ascii=False,
    )
    loss = parse_loss_response(response, make_record())
    assert len(loss.missing_dimensions) == 1
    assert loss.extra_points == ["排版细节"]


def test_parse_loss_response_tolerates_surrounding_prose():
    response = f"这是我的分析：\n```json\n{make_loss_response()}\n```\n以上。"
    assert len(parse_loss_response(response, make_record()).missing_dimensions) == 2


def test_build_patches_writes_situation_arrow_focus_rules():
    loss = parse_loss_response(make_loss_response(), make_record())
    discriminator_patch, generator_patch = build_patches(loss)
    assert discriminator_patch.add_rules == [
        "真实反馈关注[时间规划冗余度]: 当交付物给出时间计划时 → 追问是否留了冗余余量",
        "真实反馈关注[归因落点]: 当对方解释失败原因时 → 追问责任是否落回自己身上",
    ]
    assert all(" → " in rule for rule in discriminator_patch.add_rules)
    # No sentence from the real feedback may be carried over verbatim.
    assert not any("你这个时间表根本没留余量" in rule for rule in discriminator_patch.add_rules)
    assert all(" → " in rule for rule in generator_patch.add_rules)


def test_build_patches_keeps_legacy_sentence_path_without_dimensions():
    loss = LossReport(
        dissatisfaction_gap=4,
        missing_points=["缺少中心论题"],
        extra_points=[],
        style_mismatch=[],
        summary="summary",
    )
    discriminator_patch = build_patches(loss)[0]
    assert discriminator_patch.add_rules == ["真实反馈关注: 缺少中心论题"]


def test_apply_patch_caps_behavior_rules_and_evicts_oldest_training_rules():
    trained = [f"真实反馈关注[维度{i}]: 当情境{i}时 → 关注点{i}" for i in range(MAX_BEHAVIOR_RULES)]
    profile = make_profile("mentor", "discriminator").model_copy(
        update={"behavior_rules": ["原始规则", *trained], "dimension_rules": {"execution": ["原始规则", *trained]}}
    )
    patch = ProfileUpdatePatch(
        target_role="discriminator",
        add_rules=["真实反馈关注[新维度]: 当新情境时 → 新关注点"],
        rationale="add one more",
    )
    updated = apply_patch(profile, patch)
    assert len(updated.behavior_rules) == MAX_BEHAVIOR_RULES
    assert len(updated.dimension_rules["execution"]) == MAX_BEHAVIOR_RULES
    assert "原始规则" in updated.behavior_rules
    assert updated.behavior_rules[-1] == "真实反馈关注[新维度]: 当新情境时 → 新关注点"
    # 1 frozen rule + 24 old training rules + 1 new one is 2 over the cap, so the
    # two oldest training rules go and everything newer stays.
    assert trained[0] not in updated.behavior_rules
    assert trained[1] not in updated.behavior_rules
    assert trained[2] in updated.behavior_rules


def test_apply_patch_never_evicts_frozen_profile_rules():
    original = [f"原始规则{i}" for i in range(MAX_BEHAVIOR_RULES + 5)]
    profile = make_profile("mentor", "discriminator").model_copy(update={"behavior_rules": list(original)})
    patch = ProfileUpdatePatch(
        target_role="discriminator",
        add_rules=["真实反馈关注[新维度]: 当新情境时 → 新关注点"],
        rationale="add over the cap",
    )
    updated = apply_patch(profile, patch)
    assert all(rule in updated.behavior_rules for rule in original)
    assert "真实反馈关注[新维度]: 当新情境时 → 新关注点" not in updated.behavior_rules


def test_repeated_training_stops_inflating_behavior_rules():
    generator = make_profile("author", "generator")
    discriminator = make_profile("mentor", "discriminator")
    for round_index in range(20):
        loss = LossReport(
            dissatisfaction_gap=3,
            summary="summary",
            missing_dimensions=[
                MissingDimension(
                    dimension=f"维度{round_index}",
                    trigger=f"当情境{round_index}时",
                    focus=f"关注点{round_index}",
                )
            ],
        )
        generator, discriminator, _ = train_profiles(generator, discriminator, make_record(), loss)
    assert len(discriminator.behavior_rules) <= MAX_BEHAVIOR_RULES
    assert len(generator.behavior_rules) <= MAX_BEHAVIOR_RULES


def test_loss_magnitude_combines_gap_and_counts():
    loss = LossReport(
        dissatisfaction_gap=-3,
        missing_points=["a", "b"],
        extra_points=["c", "d"],
        summary="summary",
    )
    assert loss_magnitude(loss) == pytest.approx(3 + 2 * 1.0 + 2 * 0.5)


def test_loss_magnitude_counts_structured_dimensions_when_present():
    loss = LossReport(
        dissatisfaction_gap=1,
        missing_points=["ignored", "ignored2", "ignored3"],
        summary="summary",
        missing_dimensions=[MissingDimension(dimension="d", trigger="当X时", focus="Y")],
    )
    assert loss_magnitude(loss) == pytest.approx(2.0)


def small_loss() -> LossReport:
    return LossReport(
        dissatisfaction_gap=1,
        summary="small",
        missing_dimensions=[MissingDimension(dimension="小维度", trigger="当情境A时", focus="关注A")],
    )


def large_loss() -> LossReport:
    return LossReport(
        dissatisfaction_gap=8,
        summary="large",
        missing_dimensions=[
            MissingDimension(dimension="大维度", trigger="当情境B时", focus="关注B"),
            MissingDimension(dimension="大维度2", trigger="当情境C时", focus="关注C"),
        ],
    )


def test_train_profiles_records_history_without_rolling_back_on_first_pass():
    history = TrainingHistory()
    generator, discriminator, result = train_profiles(
        make_profile("author", "generator"),
        make_profile("mentor", "discriminator"),
        make_record(),
        small_loss(),
        history,
    )
    assert result.rolled_back is False
    assert len(history.entries) == 1
    assert history.entries[0].version == discriminator.version
    assert history.entries[0].discriminator_snapshot is not None
    assert generator.version == 2


def test_train_profiles_rolls_back_when_loss_grows():
    history = TrainingHistory()
    generator, discriminator, _ = train_profiles(
        make_profile("author", "generator"),
        make_profile("mentor", "discriminator"),
        make_record(),
        small_loss(),
        history,
    )
    harmful_rule = "真实反馈关注[小维度]: 当情境A时 → 关注A"
    assert harmful_rule in discriminator.behavior_rules

    generator, discriminator, result = train_profiles(generator, discriminator, make_record(), large_loss(), history)
    assert result.rolled_back is True
    # The previous round's update was harmful, so its rules are gone...
    assert harmful_rule not in discriminator.behavior_rules
    # ...while this round's patches land and the version keeps moving forward.
    assert "真实反馈关注[大维度]: 当情境B时 → 关注B" in discriminator.behavior_rules
    assert discriminator.version == 3
    assert len(history.entries) == 2


def test_train_profiles_keeps_previous_update_when_loss_shrinks():
    history = TrainingHistory()
    generator, discriminator, _ = train_profiles(
        make_profile("author", "generator"),
        make_profile("mentor", "discriminator"),
        make_record(),
        large_loss(),
        history,
    )
    kept_rule = "真实反馈关注[大维度]: 当情境B时 → 关注B"
    generator, discriminator, result = train_profiles(generator, discriminator, make_record(), small_loss(), history)
    assert result.rolled_back is False
    assert kept_rule in discriminator.behavior_rules
    assert discriminator.version == 3


def test_train_profiles_without_history_never_rolls_back():
    generator, discriminator, result = train_profiles(
        make_profile("author", "generator"),
        make_profile("mentor", "discriminator"),
        make_record(),
        large_loss(),
    )
    assert result.rolled_back is False
    assert result.loss_magnitude == pytest.approx(10.0)
    assert discriminator.version == 2
