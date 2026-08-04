"""Schemas for the behavior-prediction benchmark.

A benchmark set holds real, sourced behavior of one subject. Four task types:

* ``choice``    (T1) — real decision point as 4-option multiple choice;
* ``statement`` (T2) — real question/event, predict stance + argument;
* ``style``     (T3) — same-topic writing, judged against the real text;
* ``critique``  (T4) — real deliverable, predict the subject's critique.

Every run answers under one of three conditions, so the metric that matters is
the *profile delta* (profile vs bare prior), not the absolute score:

* ``bare``    — subject name only (model prior baseline);
* ``tags``    — name + demographic tags (stereotype baseline);
* ``profile`` — full scapegoat profile.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

TaskType = Literal["choice", "statement", "style", "critique"]
Condition = Literal["bare", "tags", "profile"]

CONDITIONS: tuple[Condition, ...] = ("bare", "tags", "profile")


class BenchmarkCase(BaseModel):
    """One evaluation case anchored to sourced real behavior."""

    case_id: str
    task: TaskType
    situation: str
    options: list[str] = Field(default_factory=list)
    answer: str
    answer_index: int | None = Field(default=None, ge=0)
    answer_source: str
    event_date: str | None = None
    post_cutoff: bool = False
    notes: str | None = None

    @field_validator("case_id", "situation", "answer", "answer_source")
    @classmethod
    def must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value.strip()

    @model_validator(mode="after")
    def choice_needs_options(self) -> BenchmarkCase:
        if self.task == "choice":
            if len(self.options) < 2:
                raise ValueError("choice case needs at least 2 options")
            if self.answer_index is None or self.answer_index >= len(self.options):
                raise ValueError("choice case needs a valid answer_index")
            if self.options[self.answer_index].strip() != self.answer:
                raise ValueError("answer must equal options[answer_index]")
        return self


class BenchmarkSet(BaseModel):
    """All cases for one subject."""

    subject_id: str
    subject_name: str
    demographic_tags: list[str] = Field(default_factory=list)
    cases: list[BenchmarkCase]

    @model_validator(mode="after")
    def case_ids_unique(self) -> BenchmarkSet:
        ids = [case.case_id for case in self.cases]
        if len(ids) != len(set(ids)):
            raise ValueError("case_id values must be unique")
        return self

    def by_task(self, task: TaskType) -> list[BenchmarkCase]:
        return [case for case in self.cases if case.task == task]


class CaseRun(BaseModel):
    """One case answered under one condition, scored to [0, 1]."""

    case_id: str
    task: TaskType
    condition: Condition
    response: str
    score: float = Field(ge=0.0, le=1.0)
    detail: dict = Field(default_factory=dict)


class BenchmarkRun(BaseModel):
    """A full evaluation pass over a benchmark set."""

    subject_id: str
    profile_dir: str | None = None
    runs: list[CaseRun] = Field(default_factory=list)
