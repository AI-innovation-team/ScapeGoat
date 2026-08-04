"""Render real rollout sessions as step-by-step markdown documents."""

from __future__ import annotations

from pathlib import Path

from scapegoat.profile.schema import FrozenProfile
from scapegoat.runtime.persistence import load_model
from scapegoat.runtime.schema import RuntimeSession


def _format_rule_list(title: str, rules: list[str]) -> list[str]:
    if not rules:
        return [f"### {title}", "", "- 无", ""]
    return [f"### {title}", "", *[f"- {rule}" for rule in rules], ""]


def _format_profile_section(title: str, profile: FrozenProfile) -> list[str]:
    lines = [
        f"## {title}",
        "",
        f"- `subject_id`: `{profile.subject_id}`",
        f"- `role`: `{profile.role}`",
        f"- `profile_signature`: `{profile.profile_signature}`",
        f"- `summary`: {profile.summary}",
        "",
    ]
    lines.extend(_format_rule_list("核心规则", profile.core_rules))
    lines.extend(_format_rule_list("风格规则", profile.style_rules))
    lines.extend(_format_rule_list("行为规则", profile.behavior_rules))
    lines.extend(_format_rule_list("策略规则", profile.strategy_rules))
    if profile.role == "discriminator":
        lines.extend(_format_rule_list("判别器关键维度：defenses", profile.dimension_rules.get("defenses", [])))
        lines.extend(_format_rule_list("判别器关键维度：situational", profile.dimension_rules.get("situational", [])))
        lines.extend(_format_rule_list("判别器关键维度：priorities", profile.dimension_rules.get("priorities", [])))
        lines.extend(_format_rule_list("判别器关键维度：execution", profile.dimension_rules.get("execution", [])))
    else:
        lines.extend(_format_rule_list("生成器关键维度：execution", profile.dimension_rules.get("execution", [])))
        lines.extend(_format_rule_list("生成器关键维度：priorities", profile.dimension_rules.get("priorities", [])))
        lines.extend(_format_rule_list("生成器关键维度：affect", profile.dimension_rules.get("affect", [])))
    return lines


def render_session_markdown(session: RuntimeSession) -> str:
    """Render a persisted runtime session into a docs-style markdown narrative."""

    generator = load_model(session.generator_profile_path, FrozenProfile)
    discriminator = load_model(session.discriminator_profile_path, FrozenProfile)
    task = session.state.task
    success = "\n".join(f"- {item}" for item in task.success_criteria) or "- 无显式成功标准"
    constraints = "\n".join(f"- {item}" for item in task.constraints) or "- 无额外约束"
    initial = task.initial_material or "无初始材料。"
    lines = [
        f"# {task.goal}",
        "",
        "## 场景说明",
        "",
        f"- `generator`: {generator.subject_id}",
        f"- `discriminator`: {discriminator.subject_id}",
        f"- `task_id`: `{task.task_id}`",
        f"- `deliverable_type`: `{task.deliverable_type}`",
        "",
    ]
    lines.extend(_format_profile_section("生成器画像（author）", generator))
    lines.extend(_format_profile_section("判别器画像（mentor）", discriminator))
    lines.extend(
        [
            "## 初始任务",
            "",
            f"- **goal**: {task.goal}",
            f"- **context**: {task.context or '无'}",
            "- **constraints**:",
            constraints,
            "- **success_criteria**:",
            success,
            f"- **initial_material**: {initial}",
            "",
            "---",
            "",
        ]
    )
    for turn in session.state.turns:
        converged = str(bool(turn.discriminator_output and turn.discriminator_output.converged)).lower()
        dissatisfaction = str(turn.discriminator_output.dissatisfaction_score) if turn.discriminator_output else "-"
        lines.extend(
            [
                f"# Step {turn.round}",
                "",
                "## Generator 交付物",
                "",
                (turn.generator_output.content if turn.generator_output else "无"),
                "",
                "## Discriminator 意见",
                "",
                (turn.discriminator_output.feedback if turn.discriminator_output else "无"),
                "",
                "### 本轮判别器画像触发点",
                "",
                *[f"- {rule}" for rule in discriminator.strategy_rules[:3]],
                *[f"- {rule}" for rule in discriminator.dimension_rules.get("defenses", [])[:2]],
                *[f"- {rule}" for rule in discriminator.dimension_rules.get("priorities", [])[:2]],
                "",
                f"**不满意度**：`dissatisfaction_score = {dissatisfaction}`",
                f"**结论**：`converged = {converged}`",
                "",
                "---",
                "",
            ]
        )
    final_score = (
        session.state.turns[-1].discriminator_output.dissatisfaction_score
        if session.state.turns and session.state.turns[-1].discriminator_output
        else "-"
    )
    lines.extend(
        [
            "## 最终状态",
            "",
            f"- `status`: `{session.state.status}`",
            f"- `total_rounds`: `{len(session.state.turns)}`",
            f"- `final_deliverable_present`: `{str(bool(session.state.current_best_deliverable)).lower()}`",
            f"- `final_dissatisfaction_score`: `{final_score}`",
        ]
    )
    return "\n".join(lines)


def export_session_markdown(session_file: str | Path, output_path: str | Path) -> None:
    """Load a session JSON file and export a markdown doc."""

    session = load_model(session_file, RuntimeSession)
    target = Path(output_path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_session_markdown(session), encoding="utf-8")
