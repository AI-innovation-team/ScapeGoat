"""Claude-powered generator/discriminator backend for rollout."""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    import anthropic

from scapegoat.profile.render import render_profile_prompt
from scapegoat.profile.schema import FrozenProfile
from scapegoat.runtime.config import BackendConfig
from scapegoat.runtime.schema import CritiqueStep, DeliverableStep, RuntimeState, TaskSpec

DEFAULT_MODEL = "claude-opus-4-8"
DEFAULT_MAX_TOKENS = 4096


def _new_client() -> anthropic.Anthropic:
    """Construct an Anthropic client, importing the optional SDK on demand.

    `anthropic` is an optional dependency: only this backend needs it, and the
    default in-session rollout mode never gets here.
    """

    try:
        import anthropic
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on install extras
        raise ModuleNotFoundError(
            "The 'claude' rollout backend needs the anthropic SDK: install scapegoat[claude]."
        ) from exc
    return anthropic.Anthropic()


class ClaudeRoleBackend:
    """Thin synchronous Anthropic SDK wrapper for one rollout role."""

    def __init__(self, config: BackendConfig | None = None, client: anthropic.Anthropic | None = None) -> None:
        self.config = config or BackendConfig(backend="claude", model=DEFAULT_MODEL, max_tokens=DEFAULT_MAX_TOKENS)
        self.client = client or _new_client()

    def generate(
        self,
        profile: FrozenProfile,
        task: TaskSpec,
        state: RuntimeState,
        latest_feedback: str | None,
    ) -> DeliverableStep:
        """Generate one deliverable revision using Claude."""

        prompt = self._generator_prompt(profile, task, state, latest_feedback)
        text = self._run_text(prompt)
        return DeliverableStep(
            step_index=len(state.turns) + 1,
            content=text,
            rationale=f"claude:{self.config.model}",
        )

    def critique(
        self,
        profile: FrozenProfile,
        task: TaskSpec,
        state: RuntimeState,
        deliverable: DeliverableStep,
    ) -> CritiqueStep:
        """Critique one deliverable and emit structured convergence signal."""

        prompt = self._discriminator_prompt(profile, task, state, deliverable)
        payload = self._run_json(prompt)
        feedback = str(payload.get("feedback", "")).strip() or "未提供反馈。"
        dissatisfaction_score = int(payload.get("dissatisfaction_score", 5))
        dissatisfaction_score = max(1, min(10, dissatisfaction_score))
        reasons_raw = payload.get("reasons", [])
        reasons = [str(item).strip() for item in reasons_raw if str(item).strip()]
        return CritiqueStep(
            step_index=deliverable.step_index,
            feedback=feedback,
            dissatisfaction_score=dissatisfaction_score,
            reasons=reasons,
            converged=bool(payload.get("converged", False)),
        )

    def _run_text(self, prompt: str) -> str:
        response = self.client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            thinking={"type": "adaptive"},
            output_config={"effort": self.config.effort},
            system="你是一个严格遵守角色画像的交付物生成智能体。直接输出交付物正文，不要解释你的过程。",
            messages=[{"role": "user", "content": prompt}],
        )
        return _extract_text(response).strip()

    def _run_json(self, prompt: str) -> dict:
        response = self.client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            thinking={"type": "adaptive"},
            output_config={
                "effort": self.config.effort,
                "format": {
                    "type": "json_schema",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "feedback": {"type": "string"},
                            "dissatisfaction_score": {"type": "integer"},
                            "reasons": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "converged": {"type": "boolean"},
                        },
                        "required": ["feedback", "dissatisfaction_score", "reasons", "converged"],
                        "additionalProperties": False,
                    },
                },
            },
            system=(
                "你是一个严格遵守角色画像的判别器。你的职责是持续挑刺，"
                "并给出 1-10 的 dissatisfaction_score，分数越高表示越不满意。"
                "只有在成功标准被真正满足且没有新的核心异议时，才可以给出 converged=true，"
                "否则 converged 必须为 false。输出必须是 JSON。"
            ),
            messages=[{"role": "user", "content": prompt}],
        )
        text = _extract_text(response).strip()
        return json.loads(text)

    def _generator_prompt(
        self,
        profile: FrozenProfile,
        task: TaskSpec,
        state: RuntimeState,
        latest_feedback: str | None,
    ) -> str:
        success = "\n".join(f"- {item}" for item in task.success_criteria) or "- 无显式成功标准"
        constraints = "\n".join(f"- {item}" for item in task.constraints) or "- 无额外约束"
        previous = state.current_best_deliverable or "无上一版交付物。"
        feedback = latest_feedback or "无上一轮反馈。"
        initial = task.initial_material or "无初始材料。"
        return (
            f"# 冻结画像\n{render_profile_prompt(profile)}\n\n"
            f"# 任务\n任务 ID: {task.task_id}\n目标: {task.goal}\n"
            f"交付物类型: {task.deliverable_type}\n上下文: {task.context or '无'}\n"
            f"约束:\n{constraints}\n成功标准:\n{success}\n\n"
            f"# 当前状态\n初始材料:\n{initial}\n\n上一版交付物:\n{previous}\n\n上一轮反馈:\n{feedback}\n\n"
            "请严格扮演该画像对应的生成者，输出当前时间步的新交付物正文。"
            "不要输出分析、不要解释策略、不要加 JSON。"
        )

    def _discriminator_prompt(
        self,
        profile: FrozenProfile,
        task: TaskSpec,
        state: RuntimeState,
        deliverable: DeliverableStep,
    ) -> str:
        success = "\n".join(f"- {item}" for item in task.success_criteria) or "- 无显式成功标准"
        constraints = "\n".join(f"- {item}" for item in task.constraints) or "- 无额外约束"
        history = (
            "\n\n".join(
                f"第 {turn.round} 轮\n交付物: {(turn.generator_output.content if turn.generator_output else '')}\n"
                f"反馈: {(turn.discriminator_output.feedback if turn.discriminator_output else '')}"
                for turn in state.turns
            )
            or "无历史轮次。"
        )
        return (
            f"# 冻结画像\n{render_profile_prompt(profile)}\n\n"
            f"# 任务\n任务 ID: {task.task_id}\n目标: {task.goal}\n"
            f"交付物类型: {task.deliverable_type}\n上下文: {task.context or '无'}\n"
            f"约束:\n{constraints}\n成功标准:\n{success}\n\n"
            f"# 历史\n{history}\n\n"
            f"# 当前交付物\n{deliverable.content}\n\n"
            "请严格扮演该画像对应的判别者，对当前交付物做评价。"
            "你必须持续挑刺，并输出 dissatisfaction_score（1-10，越高越不满意）以及理由。"
            "只有在成功标准被真正满足且没有新的核心异议时，才可以输出 converged=true；"
            "只要还存在真实缺口或新增风险，converged 就必须是 false。"
            "只输出符合 schema 的 JSON。"
        )


_EFFORT_LEVELS: tuple[Literal["low", "medium", "high", "xhigh", "max"], ...] = (
    "low",
    "medium",
    "high",
    "xhigh",
    "max",
)


def _resolve_effort_from_env() -> Literal["low", "medium", "high", "xhigh", "max"]:
    """Read the effort level from the environment, falling back to `high`.

    Returning the matched tuple element (rather than the environment string)
    keeps the literal type without a cast, which type checkers narrow
    inconsistently across versions.
    """

    value = os.environ.get("SCAPEGOAT_CLAUDE_EFFORT", "high")
    for level in _EFFORT_LEVELS:
        if value == level:
            return level
    return "high"


def build_claude_backends_from_env(config: BackendConfig | None = None) -> tuple[ClaudeRoleBackend, ClaudeRoleBackend]:
    """Construct generator/discriminator backends from environment variables."""

    resolved = config or BackendConfig(
        backend="claude",
        model=os.environ.get("SCAPEGOAT_CLAUDE_MODEL", DEFAULT_MODEL),
        max_tokens=int(os.environ.get("SCAPEGOAT_CLAUDE_MAX_TOKENS", str(DEFAULT_MAX_TOKENS))),
        effort=_resolve_effort_from_env(),
    )
    shared_client = _new_client()
    return (
        ClaudeRoleBackend(config=resolved, client=shared_client),
        ClaudeRoleBackend(config=resolved, client=shared_client),
    )


def _extract_text(response: Any) -> str:
    texts: list[str] = []
    for block in response.content:
        if block.type == "text":
            text = getattr(block, "text", None)
            if text:
                texts.append(text)
    return "\n".join(texts)
