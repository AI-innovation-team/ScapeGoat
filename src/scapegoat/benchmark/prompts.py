"""Prompt renderers and response parsers for benchmark runs.

The runner is in-session: Claude Code plays both the answering persona and the
judge (as separate subagents so the judge never sees the generation context).
This module renders those prompts and parses/scores the structured replies —
it never calls an LLM itself.
"""

from __future__ import annotations

import random

from scapegoat.benchmark.schema import BenchmarkCase, BenchmarkSet, CaseRun, Condition
from scapegoat.benchmark.style import style_similarity
from scapegoat.profile.render import _extract_json_object

_OPTION_LABELS = "ABCDEFGH"


def render_condition_context(bench: BenchmarkSet, condition: Condition, profile_prompt: str | None = None) -> str:
    """Render the identity context for one answering condition.

    ``bare``/``tags`` deliberately give the model nothing beyond name/labels —
    they measure the prior the profile must beat.
    """

    if condition == "bare":
        return f"你要扮演的人物：{bench.subject_name}。除了名字，不提供任何其他资料；按你对此人的了解作答。"
    if condition == "tags":
        tags = "、".join(bench.demographic_tags) or "无"
        return f"你要扮演的人物：{bench.subject_name}。已知标签：{tags}。除此之外不提供任何资料。"
    if not profile_prompt:
        raise ValueError("profile condition requires profile_prompt")
    return (
        f"你要扮演的人物：{bench.subject_name}。"
        f"以下是他的心理画像，作答必须以画像为准，而不是你的先验印象：\n\n{profile_prompt}"
    )


def render_case_prompt(case: BenchmarkCase) -> str:
    """Render the answering prompt for one case (condition context is prepended by the runner)."""

    if case.task == "choice":
        options = "\n".join(f"{_OPTION_LABELS[i]}. {text}" for i, text in enumerate(case.options))
        return (
            f"{case.situation}\n\n{options}\n\n"
            "以此人的身份判断他实际会怎么做。只输出一个 JSON："
            '{"choice": "<选项字母>", "reason": "<一句话理由>"}'
        )
    if case.task == "statement":
        return (
            f"{case.situation}\n\n"
            "以此人的身份给出他会作出的回应。只输出一个 JSON："
            '{"stance": "<他的立场，一句话>", "response": "<他的回应正文，100-300字>"}'
        )
    if case.task == "style":
        # A persona asked to "produce a piece of writing" defaults to organized
        # prose — headings, enumerations, a closing line. Real impromptu posts
        # have none of that, so the framing must suppress the deliverable
        # instinct or the task measures composure, not voice.
        return (
            f"{case.situation}\n\n"
            "这是随手发出去的，不是交付物：想到什么写什么，写完就发。\n"
            "不要编号分条、不要总分结构、不要金句收尾、不要为了完整而补充说明；"
            "话说完就停，哪怕看起来不完整。\n"
            "长度以说完为准（可短至一两句）。直接输出正文，不要任何解释或 JSON。"
        )
    return (
        f"# 待评价对象\n{case.situation}\n\n"
        "以此人的身份对上述工作提出批评。只输出一个 JSON："
        '{"feedback": "<完整批评意见>", "reasons": ["<关键问题1>", "<关键问题2>"]}'
    )


def score_choice(case: BenchmarkCase, response: str) -> CaseRun:
    """Score a choice answer by exact option-letter match."""

    payload = _extract_json_object(response)
    choice = str(payload.get("choice", "")).strip().upper()[:1]
    correct = _OPTION_LABELS[case.answer_index or 0]
    return CaseRun(
        case_id=case.case_id,
        task=case.task,
        condition="bare",  # runner overwrites
        response=response,
        score=1.0 if choice == correct else 0.0,
        detail={"chosen": choice, "correct": correct, "reason": str(payload.get("reason", ""))},
    )


def render_statement_judge_prompt(case: BenchmarkCase, response: str) -> str:
    """Judge prompt for T2: compare generated response with the real one."""

    return (
        "你是评审。对比一个人物模拟系统的预测回应与该人物的真实回应，独立打两个分（1-5 整数）：\n"
        "- stance_match：立场/结论是否一致（5=完全一致，1=相反）\n"
        "- argument_match：论证方式与理由是否一致（5=同一套理由，1=完全不同的理由）\n"
        "只看内容一致性，不评价文笔。只输出 JSON："
        '{"stance_match": <1-5>, "argument_match": <1-5>, "note": "<一句话>"}\n\n'
        f"# 情境\n{case.situation}\n\n# 真实回应\n{case.answer}\n\n# 预测回应\n{response}"
    )


def score_statement(case: BenchmarkCase, response: str, judge_response: str) -> CaseRun:
    payload = _extract_json_object(judge_response)
    stance = max(1, min(5, int(payload.get("stance_match", 1))))
    argument = max(1, min(5, int(payload.get("argument_match", 1))))
    return CaseRun(
        case_id=case.case_id,
        task=case.task,
        condition="bare",
        response=response,
        score=round((stance + argument - 2) / 8, 4),  # map 2..10 -> 0..1
        detail={"stance_match": stance, "argument_match": argument, "note": str(payload.get("note", ""))},
    )


def render_style_judge_prompt(case: BenchmarkCase, generated: str, seed: int = 0) -> tuple[str, str]:
    """Judge prompt for T3: blind A/B — which text is the real one?

    Returns (prompt, real_label). The judge is fooled when it picks the
    generated text; a fooled judge scores 1.0 for the generator.
    """

    real_first = random.Random(f"{case.case_id}:{seed}").random() < 0.5
    a, b = (case.answer, generated) if real_first else (generated, case.answer)
    real_label = "A" if real_first else "B"
    prompt = (
        "下面两段文字同题：一段是某公众人物的真实原文，另一段是模仿生成的。\n"
        "判断哪一段是真实原文。判断依据必须是**语言风格**（句式、节奏、用词习惯、语气、结构癖好），"
        "不得依据私人事实细节的有无——真实原文天然含有模仿者无从知晓的私人信息，"
        "以此判断等于没有测试风格。只输出 JSON："
        '{"real": "A" 或 "B", "confidence": <1-5>, "cue": "<你依据的线索，一句话>"}\n\n'
        f"# 文本 A\n{a}\n\n# 文本 B\n{b}"
    )
    return prompt, real_label


def score_style(case: BenchmarkCase, generated: str, judge_response: str, real_label: str) -> CaseRun:
    """Score T3 on judge deception, carrying the judge-free fingerprint alongside.

    `score` stays the A/B outcome so the metric means what it always meant;
    `detail["style_similarity"]` is the continuous companion that still moves
    when the judge wins every round.
    """

    payload = _extract_json_object(judge_response)
    picked = str(payload.get("real", "")).strip().upper()[:1]
    fooled = picked != real_label
    return CaseRun(
        case_id=case.case_id,
        task=case.task,
        condition="bare",
        response=generated,
        score=1.0 if fooled else 0.0,
        detail={
            "picked": picked,
            "real_label": real_label,
            "confidence": int(payload.get("confidence", 0) or 0),
            "cue": str(payload.get("cue", "")),
            "style_similarity": style_similarity(generated, case.answer),
        },
    )


def render_critique_judge_prompt(case: BenchmarkCase, response: str) -> str:
    """Judge prompt for T4: overlap between simulated and real critique."""

    return (
        "你是评审。对比模拟批评与真实批评，评估模拟是否抓住了真实批评的关注点。\n"
        "先列出真实批评的核心关注点（3-6条），再逐条判断模拟批评是否覆盖。只输出 JSON："
        '{"real_points": ["..."], "covered": [true, false, ...], '
        '"extra_focus": ["模拟批评关注但真实批评没提的方向"], "note": "<一句话>"}\n'
        "covered 数组与 real_points 一一对应。\n\n"
        f"# 被批评的工作\n{case.situation}\n\n# 真实批评\n{case.answer}\n\n# 模拟批评\n{response}"
    )


def score_critique(case: BenchmarkCase, response: str, judge_response: str) -> CaseRun:
    payload = _extract_json_object(judge_response)
    real_points = [str(p) for p in payload.get("real_points", [])]
    covered = [bool(c) for c in payload.get("covered", [])][: len(real_points)]
    coverage = (sum(covered) / len(real_points)) if real_points else 0.0
    return CaseRun(
        case_id=case.case_id,
        task=case.task,
        condition="bare",
        response=response,
        score=round(coverage, 4),
        detail={
            "real_points": real_points,
            "covered": covered,
            "extra_focus": [str(x) for x in payload.get("extra_focus", [])],
            "note": str(payload.get("note", "")),
        },
    )
