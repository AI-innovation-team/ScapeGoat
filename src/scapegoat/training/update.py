"""Apply offline training signals to frozen profiles."""

from __future__ import annotations

from scapegoat.profile.schema import FrozenProfile
from scapegoat.training.loss import loss_magnitude
from scapegoat.training.schema import (
    LossReport,
    MissingDimension,
    ProfileUpdatePatch,
    TrainingHistory,
    TrainingHistoryEntry,
    TrainingRecord,
    TrainingResult,
)

# Frozen profiles are prompt context, so an unbounded rule list is the same leak
# the minimal-bytes contract closes for markdown assets: training used to append
# a rule per training round forever, and the noise drowned out the profile's own
# discrimination tendencies.
MAX_BEHAVIOR_RULES = 24

# Prefixes stamped on every rule training writes. Anything without one of these
# came from the freeze and is never evicted. The list must stay append-only:
# profiles trained by older versions carry the earlier prefixes on disk.
_TRAINING_RULE_MARKERS = (
    "真实反馈关注",
    "后续修订需覆盖",
    "避免触发额外发散",
)


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _drop_matching(rules: list[str], removals: list[str]) -> list[str]:
    """Drop every rule containing one of the removal points as a substring.

    Removal points are raw feedback fragments, while stored rules may carry
    prefixes such as "真实反馈关注: ", so matching cannot be exact equality.
    """

    points = [point.strip() for point in removals if point.strip()]
    if not points:
        return rules
    return [rule for rule in rules if not any(point in rule for point in points)]


def _is_training_rule(rule: str) -> bool:
    return rule.startswith(_TRAINING_RULE_MARKERS)


def _cap_rules(rules: list[str], limit: int = MAX_BEHAVIOR_RULES) -> list[str]:
    """Trim a rule list to `limit`, evicting the oldest training-added rules first.

    Rules that predate training (no training marker) are never dropped, so the
    cap degrades gracefully into a no-op rather than eating the frozen profile if
    the original list is already at or over the limit.
    """

    if len(rules) <= limit:
        return rules
    trained = [rule for rule in rules if _is_training_rule(rule)]
    original_count = len(rules) - len(trained)
    budget = max(0, limit - original_count)
    keep = set(trained[len(trained) - budget :]) if budget else set()
    return [rule for rule in rules if not _is_training_rule(rule) or rule in keep]


def _dimension_rules(dimensions: list[MissingDimension]) -> list[str]:
    """Render induced dimensions as transferable `情境 → 关注点` rules."""

    return [f"真实反馈关注[{item.dimension}]: {item.trigger} → {item.focus}" for item in dimensions]


def build_patches(loss: LossReport) -> list[ProfileUpdatePatch]:
    """Translate a loss report into structured profile patch instructions.

    With `missing_dimensions` present (the LLM loss path) the discriminator gains
    `情境 → 关注点` rules that transfer to unseen deliverables; without them the
    legacy sentence-level `missing_points` path is used unchanged.

    `remove_rules` carries the raw over-divergent points; `apply_patch` matches
    them against existing rules by substring rather than by exact equality.
    """

    if loss.missing_dimensions:
        discriminator_adds = _dimension_rules(loss.missing_dimensions)
        generator_adds = [
            f"后续修订需覆盖[{item.dimension}]: {item.trigger} → {item.focus}" for item in loss.missing_dimensions
        ]
        has_signal = True
    else:
        discriminator_adds = [f"真实反馈关注: {point}" for point in loss.missing_points]
        generator_adds = [f"后续修订需覆盖: {point}" for point in loss.missing_points]
        has_signal = bool(loss.missing_points)

    discriminator_patch = ProfileUpdatePatch(
        target_role="discriminator",
        add_rules=discriminator_adds,
        remove_rules=list(loss.extra_points),
        rewrite_rules=[],
        add_style_rules=[f"判别语气校准: {note}" for note in loss.style_mismatch],
        add_convergence_rules=[],
        add_strategy_rules=[
            f"将不满意度向真实反馈靠拢，当前差值: {loss.dissatisfaction_gap}",
            "优先模仿真实反馈的关注维度，而不是平均展开所有问题。",
            "只有在成功标准被真正满足且没有新的核心异议时才给出 converged=true，否则持续寻找新的不满点。",
        ],
        rationale=loss.summary,
    )
    patches = [discriminator_patch]
    if has_signal or loss.extra_points or loss.style_mismatch:
        patches.append(
            ProfileUpdatePatch(
                target_role="generator",
                add_rules=generator_adds,
                remove_rules=[],
                rewrite_rules=[f"避免触发额外发散: {point}" for point in loss.extra_points],
                add_style_rules=[f"表达方式调整: {note}" for note in loss.style_mismatch],
                add_convergence_rules=[],
                add_strategy_rules=[
                    "根据真实判别反馈优先修正漏项，再处理表达细节。",
                ],
                rationale="根据真实判别反馈更新修订策略。",
            )
        )
    return patches


def apply_patch(profile: FrozenProfile, patch: ProfileUpdatePatch) -> FrozenProfile:
    """Create a new frozen profile version with patch instructions applied.

    Removals run before additions and only touch `behavior_rules` and the
    `execution` dimension; `core_rules` are never rewritten by training. Both
    lists are capped at `MAX_BEHAVIOR_RULES` afterwards so repeated training
    cannot inflate the profile without bound.
    """

    behavior_rules = _drop_matching(list(profile.behavior_rules), patch.remove_rules)
    for rule in patch.add_rules:
        if rule not in behavior_rules:
            behavior_rules.append(rule)
    for rule in patch.rewrite_rules:
        if rule not in behavior_rules:
            behavior_rules.append(rule)

    style_rules = _dedupe(list(profile.style_rules) + patch.add_style_rules)
    convergence_rules = _dedupe(list(profile.convergence_rules) + patch.add_convergence_rules)
    strategy_rules = _dedupe(list(profile.strategy_rules) + patch.add_strategy_rules)
    dimension_rules = dict(profile.dimension_rules)
    execution_rules = _drop_matching(list(dimension_rules.get("execution", [])), patch.remove_rules)
    execution_rules.extend(patch.add_rules)
    execution_rules.extend(patch.rewrite_rules)
    dimension_rules["execution"] = _cap_rules(_dedupe(execution_rules))

    return profile.model_copy(
        update={
            "version": profile.version + 1,
            "behavior_rules": _cap_rules(_dedupe(behavior_rules)),
            "style_rules": style_rules,
            "convergence_rules": convergence_rules,
            "strategy_rules": strategy_rules,
            "dimension_rules": dimension_rules,
        }
    )


def _rollback_base(current: FrozenProfile, snapshot: FrozenProfile | None) -> FrozenProfile:
    """Restore a snapshot's rules while keeping the version counter monotonic."""

    if snapshot is None:
        return current
    return snapshot.model_copy(update={"version": current.version})


def train_profiles(
    generator_profile: FrozenProfile,
    discriminator_profile: FrozenProfile,
    record: TrainingRecord,
    loss: LossReport,
    history: TrainingHistory | None = None,
) -> tuple[FrozenProfile, FrozenProfile, TrainingResult]:
    """Apply a single training record to frozen generator/discriminator profiles.

    Passing `history` enables the architecture's delayed verification: this
    round's loss magnitude is the verdict on the previous round's update. If the
    loss grew, the previous update was harmful, so its pre-update snapshots are
    restored before this round's patches land. `history` is appended to in place;
    without it the behavior is exactly the pre-history one.
    """

    magnitude = loss_magnitude(loss)
    previous = history.last if history is not None else None
    regressed = previous is not None and magnitude > previous.loss_magnitude
    has_snapshot = previous is not None and (
        previous.generator_snapshot is not None or previous.discriminator_snapshot is not None
    )
    rolled_back = bool(regressed and has_snapshot)

    base_generator = generator_profile
    base_discriminator = discriminator_profile
    if rolled_back and previous is not None:
        base_generator = _rollback_base(generator_profile, previous.generator_snapshot)
        base_discriminator = _rollback_base(discriminator_profile, previous.discriminator_snapshot)

    patches = build_patches(loss)
    new_generator = base_generator
    new_discriminator = base_discriminator
    for patch in patches:
        if patch.target_role == "generator":
            new_generator = apply_patch(new_generator, patch)
        else:
            new_discriminator = apply_patch(new_discriminator, patch)
    result = TrainingResult(
        record=record,
        loss=loss,
        patches=patches,
        new_generator_profile_version=new_generator.version,
        new_discriminator_profile_version=new_discriminator.version,
        loss_magnitude=magnitude,
        rolled_back=rolled_back,
    )
    if history is not None:
        history.entries.append(
            TrainingHistoryEntry(
                version=new_discriminator.version,
                loss_magnitude=magnitude,
                generator_snapshot=base_generator,
                discriminator_snapshot=base_discriminator,
            )
        )
    return new_generator, new_discriminator, result
