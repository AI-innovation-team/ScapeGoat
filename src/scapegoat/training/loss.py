"""Gap analysis between simulated and real discriminator feedback.

Two paths produce a `LossReport`:

* `compute_loss` — deterministic sentence-set diff. Offline, dependency-free,
  but it can only see literal overlap, so on two pieces of free-form prose it
  reports the whole real feedback as "missing".
* `render_loss_prompt` + `parse_loss_response` — semantic induction by an LLM,
  which reports *discrimination dimensions* instead of sentences. This module
  never calls a model; the skill/backend layer runs the prompt and hands the
  reply back to the parser.
"""

from __future__ import annotations

import re

from scapegoat.profile.render import _extract_json_object
from scapegoat.training.schema import LossReport, MissingDimension, TrainingRecord

# Weights for `loss_magnitude`. A missing dimension is the expensive failure
# (the simulation is blind to something real), an over-divergent direction is
# noise that patching can prune, so it counts for half.
_MISSING_WEIGHT = 1.0
_EXTRA_WEIGHT = 0.5


def _points(text: str) -> set[str]:
    chunks = re.split(r"[。！？\n;；]+", text)
    return {chunk.strip() for chunk in chunks if len(chunk.strip()) >= 4}


def _style(real_feedback: str, simulated_feedback: str | None) -> list[str]:
    simulated = simulated_feedback or ""
    notes: list[str] = []
    if real_feedback.count("？") > simulated.count("？"):
        notes.append("真实反馈更偏追问式。")
    if len(real_feedback) > len(simulated) + 20:
        notes.append("真实反馈信息密度更高。")
    if len(real_feedback) + 20 < len(simulated):
        notes.append("模拟反馈发散过度。")
    return notes


def compute_loss(record: TrainingRecord) -> LossReport:
    """Compute a structured diff between real and simulated critic output.

    Sentence-level and deterministic: use it when no model is available, and
    prefer the `render_loss_prompt`/`parse_loss_response` pair otherwise.
    """

    real_points = _points(record.real_discriminator_output)
    simulated_points = _points(record.simulated_discriminator_output or "")
    missing = sorted(real_points - simulated_points)
    extra = sorted(simulated_points - real_points)
    gap = record.real_dissatisfaction_score - (record.simulated_dissatisfaction_score or 0)
    summary = f"不满意度差值 {gap}；缺失 {len(missing)} 项，额外 {len(extra)} 项。"
    return LossReport(
        dissatisfaction_gap=gap,
        missing_points=missing,
        extra_points=extra,
        style_mismatch=_style(record.real_discriminator_output, record.simulated_discriminator_output),
        summary=summary,
    )


def render_loss_prompt(record: TrainingRecord) -> str:
    """Render the prompt asking an LLM to induce discrimination dimensions.

    The output contract is deliberately narrow: what comes back must survive
    being applied to a *different* deliverable, so the prompt bans case-specific
    wording (names, project titles, numbers) from every structured field.
    """

    task = record.task
    criteria = "、".join(task.success_criteria) or "未给出"
    constraints = "、".join(task.constraints) or "无"
    simulated = record.simulated_discriminator_output or "（本次没有模拟批评，视为模拟完全缺席）"
    simulated_score = record.simulated_dissatisfaction_score
    simulated_score_text = "未给出" if simulated_score is None else str(simulated_score)
    return (
        "# 任务\n"
        "对比同一份交付物下「真实批评者」与「模拟批评者」的反馈，归纳模拟画像缺失的**判别维度**。\n\n"
        "# 交付物任务背景\n"
        f"目标：{task.goal}\n"
        f"成功标准：{criteria}\n"
        f"约束：{constraints}\n\n"
        "# 交付物\n"
        f"{record.deliverable}\n\n"
        "# 真实批评（基准）\n"
        f"{record.real_discriminator_output}\n"
        f"真实不满意度：{record.real_dissatisfaction_score}/10\n\n"
        "# 模拟批评（待校准）\n"
        f"{simulated}\n"
        f"模拟不满意度：{simulated_score_text}\n\n"
        "# 归纳要求\n"
        "1. `missing_dimensions` 写**可迁移的判别维度**——换一份完全不同的交付物仍然适用的关注轴。\n"
        "   - `dimension`：维度名，名词短语，如「时间规划冗余度」「归因是否落到自己」。\n"
        "   - `trigger`：什么情境下触发这个关注，写成「当……时」的条件句。\n"
        "   - `focus`：触发后他具体追问/攻击什么。\n"
        "2. **严禁**把本案例的特定内容写进 `dimension`/`trigger`/`focus`：不得出现人名、项目名、\n"
        "   机构名、具体数字、以及真实批评里的原话。写「当交付物给出时间计划时」，\n"
        "   不写「当他说三个月写完这本书时」。\n"
        "3. 一条原话对应不了一个维度就不要写；宁可只给 2-4 条高置信度维度，也不要逐句搬运。\n"
        "4. `over_divergent` 写模拟批评过度发散的**方向**（同样是维度级，不是原句）。\n"
        "5. `style_notes` 写语气/句式偏差，如「真实更偏短促追问，模拟偏长段落说理」。\n"
        "6. `dissatisfaction_gap` 写真实分减模拟分的整数差值。\n\n"
        "# 输出\n"
        "只输出一个 JSON 对象，不要任何解释：\n"
        "{\n"
        '  "missing_dimensions": [{"dimension": "<判别维度名>", "trigger": "<当……时>", "focus": "<他关注什么>"}],\n'
        '  "over_divergent": ["<模拟过度发散的方向>"],\n'
        '  "style_notes": ["<语气/句式偏差>"],\n'
        '  "dissatisfaction_gap": <整数>\n'
        "}"
    )


def _clean_list(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    return [str(item).strip() for item in values if str(item).strip()]


def parse_loss_response(response: str, record: TrainingRecord) -> LossReport:
    """Parse an LLM loss response into a `LossReport` carrying structured dimensions.

    `missing_points` stays empty on this path: the transferable dimensions are
    the whole point, and populating both would make `build_patches` write each
    finding twice. The dissatisfaction gap is recomputed from the record whenever
    both scores are known — the record is authoritative, the model's arithmetic
    is not.
    """

    payload = _extract_json_object(response)
    dimensions: list[MissingDimension] = []
    raw_dimensions = payload.get("missing_dimensions")
    if isinstance(raw_dimensions, list):
        for item in raw_dimensions:
            if not isinstance(item, dict):
                continue
            dimension = str(item.get("dimension", "")).strip()
            trigger = str(item.get("trigger", "")).strip()
            focus = str(item.get("focus", "")).strip()
            if dimension and trigger and focus:
                dimensions.append(MissingDimension(dimension=dimension, trigger=trigger, focus=focus))

    if record.simulated_dissatisfaction_score is not None:
        gap = record.real_dissatisfaction_score - record.simulated_dissatisfaction_score
    else:
        try:
            gap = int(float(payload.get("dissatisfaction_gap", 0)))
        except (TypeError, ValueError):
            gap = 0

    extra = _clean_list(payload.get("over_divergent"))
    style = _clean_list(payload.get("style_notes"))
    summary = f"不满意度差值 {gap}；缺失判别维度 {len(dimensions)} 条，过度发散方向 {len(extra)} 条。"
    return LossReport(
        dissatisfaction_gap=gap,
        missing_points=[],
        extra_points=extra,
        style_mismatch=style,
        summary=summary,
        missing_dimensions=dimensions,
    )


def loss_magnitude(loss: LossReport) -> float:
    """Collapse a loss report into one comparable number for delayed verification.

    Defined as `|dissatisfaction_gap| + 1.0 * missing + 0.5 * extra`, where
    `missing` counts structured dimensions when present and falls back to the
    sentence-level `missing_points` otherwise — so the two loss paths stay on the
    same scale only within a path. Compare magnitudes across training rounds that
    used the same path; mixing paths makes the comparison meaningless.
    """

    missing = len(loss.missing_dimensions) or len(loss.missing_points)
    return abs(loss.dissatisfaction_gap) + _MISSING_WEIGHT * missing + _EXTRA_WEIGHT * len(loss.extra_points)
