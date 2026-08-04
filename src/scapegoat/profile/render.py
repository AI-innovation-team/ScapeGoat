"""Render runtime prompt blocks from frozen profiles."""

from __future__ import annotations

import json

from scapegoat.profile.schema import FrozenProfile
from scapegoat.runtime.schema import CritiqueStep, DeliverableStep, RuntimeState, TaskSpec

# Dimensions that most define each role's critique/generation voice; these get
# surfaced explicitly in the prompt so the runtime behavior tracks the profile.
_ROLE_KEY_DIMENSIONS = {
    "discriminator": ("defenses", "situational", "priorities", "drives_fears"),
    "generator": ("execution", "priorities", "affect"),
}


def render_profile_prompt(profile: FrozenProfile) -> str:
    """Render a frozen profile into a concise runtime prompt block."""

    sections = [
        f"subject_id: {profile.subject_id}",
        f"role: {profile.role}",
        f"summary: {profile.summary}",
        "core_rules:",
        *[f"- {rule}" for rule in profile.core_rules],
        "behavior_rules:",
        *[f"- {rule}" for rule in profile.behavior_rules],
        "convergence_rules:",
        *[f"- {rule}" for rule in profile.convergence_rules],
    ]
    if profile.style_rules:
        sections.extend(["style_rules:", *[f"- {rule}" for rule in profile.style_rules]])
    if profile.strategy_rules:
        sections.extend(["strategy_rules:", *[f"- {rule}" for rule in profile.strategy_rules]])
    key_rules: list[str] = []
    for dimension in _ROLE_KEY_DIMENSIONS.get(profile.role, ()):
        for rule in profile.dimension_rules.get(dimension, []):
            key_rules.append(f"- [{dimension}] {rule}")
    if key_rules:
        sections.extend(["key_dimension_rules:", *key_rules])
    return "\n".join(sections)


def _format_task_block(task: TaskSpec) -> str:
    success = "\n".join(f"- {item}" for item in task.success_criteria) or "- 无显式成功标准"
    constraints = "\n".join(f"- {item}" for item in task.constraints) or "- 无额外约束"
    return (
        f"任务 ID: {task.task_id}\n"
        f"目标: {task.goal}\n"
        f"交付物类型: {task.deliverable_type}\n"
        f"上下文: {task.context or '无'}\n"
        f"约束:\n{constraints}\n"
        f"成功标准:\n{success}"
    )


def _format_history_block(state: RuntimeState) -> str:
    if not state.turns:
        return "无历史轮次。"
    chunks: list[str] = []
    for turn in state.turns:
        deliverable = turn.generator_output.content if turn.generator_output else ""
        feedback = turn.discriminator_output.feedback if turn.discriminator_output else ""
        chunks.append(f"第 {turn.round} 轮\n交付物:\n{deliverable}\n你的上一轮反馈:\n{feedback}")
    return "\n\n".join(chunks)


def render_discriminator_agent_prompt(
    profile: FrozenProfile,
    task: TaskSpec,
    deliverable: DeliverableStep,
    state: RuntimeState,
) -> str:
    """Render a full role-play prompt for a Claude Code subagent to BE the discriminator.

    The subagent receives the frozen profile as its persona, the task, the full
    history, and the current deliverable. It must return only the JSON critique
    described at the end, which `parse_critique_response` then validates.
    """

    return (
        "你现在要严格扮演下面这个冻结画像所描述的判别者，对一份交付物做评价。\n"
        "你不是助手，不是中立评审；你就是这个画像本人，用他的认知方式、优先级和防御逻辑去挑刺。\n\n"
        f"# 你的冻结画像\n{render_profile_prompt(profile)}\n\n"
        f"# 当前任务\n{_format_task_block(task)}\n\n"
        f"# 历史\n{_format_history_block(state)}\n\n"
        f"# 待评价的当前交付物\n{deliverable.content}\n\n"
        "# 你的判别要求\n"
        "- 严格按画像的判别风格输出：先给总体定位，再点出最关键的几个问题，每个问题落到具体内容而不是泛泛而谈。\n"
        "- 你的默认职责是持续找到真实缺口与新增风险，不要为了结束对抗而放水。\n"
        "- 给出 1-10 的 dissatisfaction_score，分数越高越不满意。\n"
        "- 只在成功标准被真正满足且没有新的核心异议时，才可以给较低分并输出 converged=true；\n"
        "  只要还存在真实缺口或新增风险，converged 就必须是 false。\n\n"
        "# 输出格式（只输出一个 JSON 对象，不要任何额外文字）\n"
        '{"feedback": "<完整的判别意见正文>", '
        '"dissatisfaction_score": <1-10 整数>, '
        '"reasons": ["<关键问题1>", "<关键问题2>", "..."], '
        '"converged": <true 或 false>}'
    )


def parse_critique_response(response: str, step_index: int) -> CritiqueStep:
    """Parse a subagent's JSON critique response into a validated CritiqueStep.

    Tolerates surrounding prose or ```json fences by extracting the first JSON
    object found; clamps the score to the valid 1-10 range and treats a missing
    convergence signal as "not converged".
    """

    payload = _extract_json_object(response)
    feedback = str(payload.get("feedback", "")).strip() or "未提供反馈。"
    score = int(payload.get("dissatisfaction_score", 5))
    score = max(1, min(10, score))
    reasons = [str(item).strip() for item in payload.get("reasons", []) if str(item).strip()]
    return CritiqueStep(
        step_index=step_index,
        feedback=feedback,
        dissatisfaction_score=score,
        reasons=reasons,
        converged=bool(payload.get("converged", False)),
    )


def _extract_json_object(text: str) -> dict:
    stripped = text.strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("no JSON object found in discriminator response")
    return json.loads(stripped[start : end + 1])
