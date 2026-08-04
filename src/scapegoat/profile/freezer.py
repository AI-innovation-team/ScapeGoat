"""Compile markdown profile assets into frozen runtime profiles."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

from scapegoat.profile.constants import ANALYSE_FILENAMES
from scapegoat.profile.schema import FrozenProfile, ProfileBundle

DIMENSION_ORDER = (
    "formation",
    "worldview",
    "personality",
    "cognition",
    "affect",
    "drives_fears",
    "defenses",
    "narratives",
    "situational",
    "execution",
    "priorities",
)


# Headings like "### 规则一：..." / "### 要求二：..." carry the sharpest, most
# behavior-predictive content in these profiles; capture the text after the colon.
_RULE_HEADING = re.compile(r"^#{2,}\s*(?:规则|要求|原则)[^:：]*[:：]\s*(.+)$")

# Meta/framing sentences explain the document structure rather than the subject;
# they read as scaffolding ("前面所有层描述的是...") and must not become rules.
_META_MARKERS = (
    "前面所有",
    "这一层",
    "这一栏",
    "这一节",
    "如果只能用",
    "对每天和他",
    "人格、世界观",
    "人的行为是被",
    "描述的是",
)


def _is_meta(line: str) -> bool:
    if line.endswith((":", "：")):  # dangling lead-in to a list, not a standalone rule
        return True
    return any(marker in line for marker in _META_MARKERS)


def _take_sentences(text: str, limit: int) -> list[str]:
    """Extract representative rule-like sentences from one markdown asset.

    Rule headings (`### 规则X：...`) take priority because they encode explicit
    predictive rules; remaining slots fall back to substantive body sentences,
    skipping structural/meta framing.
    """

    rules: list[str] = []
    body: list[str] = []
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped:
            continue
        heading = _RULE_HEADING.match(stripped)
        if heading:
            candidate = heading.group(1).strip()
            if len(candidate) >= 4 and not _is_meta(candidate):
                rules.append(candidate)
            continue
        if stripped.startswith("#"):
            continue
        stripped = re.sub(r"^[-*]\s+", "", stripped)
        stripped = re.sub(r"^\d+\.\s+", "", stripped)
        if len(stripped) < 6 or _is_meta(stripped):
            continue
        body.append(stripped)
    ordered = rules + body
    return ordered[:limit]


def _compile_dimension_rules(bundle: ProfileBundle) -> dict[str, list[str]]:
    compiled: dict[str, list[str]] = {}
    for dimension in DIMENSION_ORDER:
        compiled[dimension] = _take_sentences(bundle.analyse.get(dimension, ""), limit=3)
    return compiled


def _build_profile_signature(bundle: ProfileBundle, dimension_rules: dict[str, list[str]]) -> str:
    profile_lines = _take_sentences(bundle.profile_markdown, limit=4)
    anchor = profile_lines[0] if profile_lines else bundle.subject_id
    dimensions = [dimension for dimension, rules in dimension_rules.items() if rules]
    return f"{bundle.subject_id}: {anchor} | dimensions={','.join(dimensions)}"


def _build_strategy_rules(
    role: Literal["generator", "discriminator"],
    dimension_rules: dict[str, list[str]],
) -> list[str]:
    if role == "generator":
        return [
            *dimension_rules.get("execution", [])[:2],
            *dimension_rules.get("priorities", [])[:2],
            "优先根据反馈修订交付物，而不是解释自己。",
            "在覆盖成功标准前，不要主动宣布完成。",
        ]
    return [
        *dimension_rules.get("situational", [])[:2],
        *dimension_rules.get("defenses", [])[:2],
        "优先指出真实缺口与新增风险，而不是重复表扬。",
        "只有在成功标准被满足且没有新的核心异议时才收敛。",
    ]


def freeze_profile(
    bundle: ProfileBundle,
    role: Literal["generator", "discriminator"],
    version: int = 1,
) -> FrozenProfile:
    """Create a compact runtime profile from markdown assets."""

    dimension_rules = _compile_dimension_rules(bundle)
    profile_lines = _take_sentences(bundle.profile_markdown, limit=10)
    summary = profile_lines[0] if profile_lines else bundle.subject_id
    core_rules = (
        profile_lines[:2] + dimension_rules.get("worldview", [])[:1] + dimension_rules.get("personality", [])[:1]
    ) or [summary]
    style_rules = (dimension_rules.get("narratives", [])[:2] + dimension_rules.get("affect", [])[:2]) or [summary]
    behavior_rules = (
        dimension_rules.get("execution", [])[:3]
        + dimension_rules.get("situational", [])[:2]
        + dimension_rules.get("priorities", [])[:2]
        + dimension_rules.get("drives_fears", [])[:1]
    ) or [summary]
    convergence_rules = dimension_rules.get("defenses", [])[:2]
    if role == "generator":
        convergence_rules.append("当反馈已覆盖成功标准且没有新的关键缺口时停止修订。")
    else:
        convergence_rules.append("当交付物覆盖任务成功标准且没有新的核心批评点时给出 converged=true。")

    evidence_refs = {name: text.splitlines()[0] if text.splitlines() else name for name, text in bundle.analyse.items()}
    source_analyse_paths = {name[:-3]: str(Path(bundle.source_dir) / "analyse" / name) for name in ANALYSE_FILENAMES}

    return FrozenProfile(
        subject_id=bundle.subject_id,
        role=role,
        version=version,
        summary=summary,
        core_rules=core_rules,
        style_rules=style_rules,
        behavior_rules=behavior_rules,
        convergence_rules=convergence_rules,
        dimension_rules=dimension_rules,
        strategy_rules=_build_strategy_rules(role, dimension_rules),
        profile_signature=_build_profile_signature(bundle, dimension_rules),
        evidence_refs=evidence_refs,
        source_profile_path=bundle.profile_path,
        source_analyse_paths=source_analyse_paths,
    )
