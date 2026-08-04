"""Benchmark schema, scoring, and aggregation tests."""

import pytest
from pydantic import ValidationError

from scapegoat.benchmark.prompts import (
    render_case_prompt,
    render_condition_context,
    render_style_judge_prompt,
    score_choice,
    score_critique,
    score_statement,
    score_style,
)
from scapegoat.benchmark.report import aggregate, render_report
from scapegoat.benchmark.schema import BenchmarkCase, BenchmarkRun, BenchmarkSet, CaseRun


def choice_case() -> BenchmarkCase:
    return BenchmarkCase(
        case_id="t1-001",
        task="choice",
        situation="发生了X，他会怎么做？",
        options=["沉默", "公开回击", "起诉", "道歉"],
        answer="公开回击",
        answer_index=1,
        answer_source="https://example.com",
    )


def make_set(cases: list[BenchmarkCase]) -> BenchmarkSet:
    return BenchmarkSet(subject_id="s", subject_name="某人", demographic_tags=["男性"], cases=cases)


def test_choice_case_requires_consistent_answer():
    with pytest.raises(ValidationError):
        BenchmarkCase(
            case_id="bad",
            task="choice",
            situation="x",
            options=["a", "b"],
            answer="c",
            answer_index=0,
            answer_source="s",
        )


def test_case_ids_must_be_unique():
    with pytest.raises(ValidationError):
        make_set([choice_case(), choice_case()])


def test_condition_contexts():
    bench = make_set([choice_case()])
    assert "除了名字" in render_condition_context(bench, "bare")
    assert "男性" in render_condition_context(bench, "tags")
    assert "画像" in render_condition_context(bench, "profile", profile_prompt="subject_id: s")
    with pytest.raises(ValueError):
        render_condition_context(bench, "profile")


def test_score_choice_letter_match():
    case = choice_case()
    right = score_choice(case, '{"choice": "B", "reason": "他一贯如此"}')
    wrong = score_choice(case, '{"choice": "A", "reason": "低调"}')
    assert right.score == 1.0
    assert wrong.score == 0.0


def test_score_statement_maps_to_unit_interval():
    case = BenchmarkCase(case_id="t2-001", task="statement", situation="被问X", answer="他说Y", answer_source="s")
    run = score_statement(case, "回应", '{"stance_match": 5, "argument_match": 5, "note": "一致"}')
    assert run.score == 1.0
    run = score_statement(case, "回应", '{"stance_match": 1, "argument_match": 1, "note": "相反"}')
    assert run.score == 0.0


def test_style_judge_shuffle_is_deterministic_and_scored():
    case = BenchmarkCase(case_id="t3-001", task="style", situation="同题写作", answer="真实原文", answer_source="s")
    prompt, real_label = render_style_judge_prompt(case, "生成文本", seed=1)
    prompt2, real_label2 = render_style_judge_prompt(case, "生成文本", seed=1)
    assert (prompt, real_label) == (prompt2, real_label2)
    assert "真实原文" in prompt
    fooled_pick = "B" if real_label == "A" else "A"
    fooled = score_style(case, "生成文本", f'{{"real": "{fooled_pick}", "confidence": 3, "cue": "语气"}}', real_label)
    caught = score_style(case, "生成文本", f'{{"real": "{real_label}", "confidence": 5, "cue": "细节"}}', real_label)
    assert fooled.score == 1.0
    assert caught.score == 0.0


def test_score_critique_coverage():
    case = BenchmarkCase(
        case_id="t4-001", task="critique", situation="学生汇报了X", answer="真实批评", answer_source="s"
    )
    run = score_critique(
        case,
        "模拟批评",
        '{"real_points": ["p1", "p2", "p3", "p4"], "covered": [true, true, false, false],'
        ' "extra_focus": ["格式"], "note": ""}',
    )
    assert run.score == 0.5
    assert run.detail["extra_focus"] == ["格式"]


def test_render_case_prompt_shapes():
    assert '"choice"' in render_case_prompt(choice_case())
    style = BenchmarkCase(case_id="t3", task="style", situation="写一段", answer="a", answer_source="s")
    assert "JSON" not in render_case_prompt(style).split("。")[-1]


def test_aggregate_profile_delta():
    runs = [
        CaseRun(case_id="1", task="choice", condition="bare", response="", score=0.25),
        CaseRun(case_id="2", task="choice", condition="bare", response="", score=0.25),
        CaseRun(case_id="1", task="choice", condition="profile", response="", score=0.75),
        CaseRun(case_id="2", task="choice", condition="profile", response="", score=1.0),
        CaseRun(case_id="3", task="critique", condition="profile", response="", score=0.6),
    ]
    report = aggregate(BenchmarkRun(subject_id="s", runs=runs))
    bare_cell = report.cell("choice", "bare")
    profile_cell = report.cell("choice", "profile")
    assert bare_cell is not None and bare_cell.mean_score == 0.25
    assert profile_cell is not None and profile_cell.mean_score == 0.875
    assert report.profile_delta == {"choice": 0.625}
    text = render_report(report)
    assert "profile_delta" in text
    assert "+0.6250" in text
