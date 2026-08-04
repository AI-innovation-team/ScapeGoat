"""Tests for Claude backend prompt assembly and parsing."""

from types import SimpleNamespace

from scapegoat.profile.schema import FrozenProfile
from scapegoat.runtime.claude_backend import ClaudeRoleBackend
from scapegoat.runtime.config import BackendConfig
from scapegoat.runtime.schema import RuntimeState, TaskSpec


class FakeClient:
    def __init__(self, text: str) -> None:
        self.text = text
        self.messages = self

    def create(self, **kwargs):
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=self.text)])


def make_profile(subject_id: str, role: str) -> FrozenProfile:
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


def test_claude_backend_generate_and_critique_parse():
    task = TaskSpec(
        task_id="task1",
        goal="write",
        deliverable_type="draft",
        constraints=["be concise"],
        success_criteria=["criterion"],
    )
    state = RuntimeState(task=task, generator_profile_version=1, discriminator_profile_version=1)
    generator_backend = ClaudeRoleBackend(BackendConfig(backend="claude"), client=FakeClient("draft text"))
    deliverable = generator_backend.generate(make_profile("zgh", "generator"), task, state, None)
    assert deliverable.content == "draft text"

    discriminator_backend = ClaudeRoleBackend(
        BackendConfig(backend="claude"),
        client=FakeClient('{"feedback": "ok", "dissatisfaction_score": 4, "reasons": ["done"]}'),
    )
    critique = discriminator_backend.critique(make_profile("zzl", "discriminator"), task, state, deliverable)
    assert critique.dissatisfaction_score == 4
    assert critique.feedback == "ok"
    assert critique.reasons == ["done"]
    assert critique.converged is False


def test_claude_backend_critique_reads_converged_flag():
    task = TaskSpec(task_id="task1", goal="write", success_criteria=["criterion"])
    state = RuntimeState(task=task, generator_profile_version=1, discriminator_profile_version=1)
    backend = ClaudeRoleBackend(
        BackendConfig(backend="claude"),
        client=FakeClient('{"feedback": "ok", "dissatisfaction_score": 2, "reasons": [], "converged": true}'),
    )
    deliverable = ClaudeRoleBackend(BackendConfig(backend="claude"), client=FakeClient("draft text")).generate(
        make_profile("zgh", "generator"), task, state, None
    )
    critique = backend.critique(make_profile("zzl", "discriminator"), task, state, deliverable)
    assert critique.converged is True
