"""Tests for the in-session rollout driver and discriminator prompt rendering."""

from __future__ import annotations

import json
from pathlib import Path

from scapegoat.profile.freezer import freeze_profile
from scapegoat.profile.loader import load_profile_bundle
from scapegoat.profile.render import parse_critique_response
from scapegoat.runtime import in_session
from scapegoat.runtime.persistence import load_model
from scapegoat.runtime.schema import RuntimeSession, TaskSpec


def _task() -> TaskSpec:
    return TaskSpec(
        task_id="t1",
        goal="写第一章草稿",
        success_criteria=["有清晰中心论题", "至少三个小节"],
        max_steps=2,
    )


def _profiles(profiles_dir: Path):
    generator = freeze_profile(load_profile_bundle("gen_subject", profiles_dir), role="generator")
    discriminator = freeze_profile(load_profile_bundle("disc_subject", profiles_dir), role="discriminator")
    return generator, discriminator


def test_discriminator_prompt_includes_persona_and_deliverable(profiles_dir: Path):
    generator, discriminator = _profiles(profiles_dir)
    task = _task()
    state = in_session.start_state(generator, discriminator, task)
    in_session.record_generator_step(state, "第一版草稿正文")
    prompt = in_session.build_discriminator_prompt(discriminator, state)
    assert "你的冻结画像" in prompt
    assert discriminator.summary[:10] in prompt
    assert "第一版草稿正文" in prompt
    assert "dissatisfaction_score" in prompt


def test_parse_critique_tolerates_fenced_json():
    response = '```json\n{"feedback": "论题不够尖锐", "dissatisfaction_score": 8, "reasons": ["论题平庸"]}\n```'
    critique = parse_critique_response(response, step_index=1)
    assert critique.dissatisfaction_score == 8
    assert critique.feedback == "论题不够尖锐"
    assert critique.reasons == ["论题平庸"]


def test_parse_critique_clamps_score():
    critique = parse_critique_response(json.dumps({"feedback": "x", "dissatisfaction_score": 99, "reasons": []}), 1)
    assert critique.dissatisfaction_score == 10


def test_parse_critique_reads_converged_flag_and_defaults_false():
    converged = parse_critique_response(
        json.dumps({"feedback": "标准已满足", "dissatisfaction_score": 2, "reasons": [], "converged": True}), 1
    )
    assert converged.converged is True
    missing = parse_critique_response(json.dumps({"feedback": "x", "dissatisfaction_score": 7, "reasons": []}), 1)
    assert missing.converged is False


def test_discriminator_prompt_documents_converged_field(profiles_dir: Path):
    generator, discriminator = _profiles(profiles_dir)
    state = in_session.start_state(generator, discriminator, _task())
    in_session.record_generator_step(state, "第一版草稿正文")
    prompt = in_session.build_discriminator_prompt(discriminator, state)
    assert "converged" in prompt
    assert "你永远不会主动宣布完成或收敛" not in prompt


def test_in_session_converged_critique_ends_session_early(profiles_dir: Path):
    generator, discriminator = _profiles(profiles_dir)
    state = in_session.start_state(generator, discriminator, _task())
    in_session.record_generator_step(state, "第 1 版草稿")
    in_session.record_discriminator_step(
        state,
        json.dumps({"feedback": "标准已满足", "dissatisfaction_score": 2, "reasons": [], "converged": True}),
    )
    assert state.status == "converged"
    assert in_session.is_finished(state) is True
    assert len(state.turns) == 1


def test_full_in_session_cycle_and_persistence(profiles_dir: Path, tmp_path):
    generator, discriminator = _profiles(profiles_dir)
    task = _task()
    gen_path = tmp_path / "author.json"
    disc_path = tmp_path / "mentor.json"
    from scapegoat.runtime.persistence import save_model

    save_model(generator, gen_path)
    save_model(discriminator, disc_path)

    state = in_session.start_state(generator, discriminator, task)
    round_no = 0
    while not in_session.is_finished(state):
        round_no += 1
        in_session.record_generator_step(state, f"第 {round_no} 版草稿")
        prompt = in_session.build_discriminator_prompt(discriminator, state)
        assert f"第 {round_no} 版草稿" in prompt
        # Simulate the subagent returning a JSON critique.
        response = json.dumps({"feedback": f"第 {round_no} 轮意见", "dissatisfaction_score": 6, "reasons": ["缺口"]})
        in_session.record_discriminator_step(state, response)

    assert state.status == "max_steps_reached"
    session_out = tmp_path / "session.json"
    result = in_session.save_session(state, str(gen_path), str(disc_path), session_out)
    assert result.total_rounds == 2
    assert session_out.exists()
    reloaded = load_model(session_out, RuntimeSession)
    assert len(reloaded.state.turns) == 2
    assert reloaded.state.turns[-1].discriminator_output is not None
