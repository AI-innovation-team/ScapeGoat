"""Message data models for the scapegoat system.

All raw data is unified as Message objects, which are the sole base data source.
Advisor profiles and Delta analysis are derived from these messages.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field, field_validator, model_validator

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class Role(StrEnum):
    STUDENT = "student"
    TEACHER = "teacher"


class Source(StrEnum):
    REAL = "real"
    SIMULATED = "simulated"


MIN_CONFIDENCE: float = 0.6


# ---------------------------------------------------------------------------
# Transcription layer — FunASR raw output per segment
# ---------------------------------------------------------------------------


class TranscriptionSegment(BaseModel):
    """One speaker-separated segment from FunASR output.

    Validates transcription quality before promotion to Message content.
    """

    speaker_label: str = Field(
        description="Raw speaker label from FunASR, e.g. 'spk1'",
    )
    text: str = Field(
        description="Transcribed text for this segment",
    )
    start_ms: int = Field(
        ge=0,
        description="Segment start time in milliseconds",
    )
    end_ms: int = Field(
        description="Segment end time in milliseconds",
    )
    confidence: Annotated[float, Field(ge=0.0, le=1.0)] = Field(
        description="ASR confidence score [0, 1]",
    )
    audio_source: str = Field(
        description="Originating audio file path or identifier",
    )

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Transcription segment text must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def end_after_start(self) -> TranscriptionSegment:
        if self.end_ms <= self.start_ms:
            raise ValueError(f"end_ms ({self.end_ms}) must be greater than start_ms ({self.start_ms})")
        return self

    @property
    def is_reliable(self) -> bool:
        """Return True if confidence meets the minimum threshold."""
        return self.confidence >= MIN_CONFIDENCE

    @property
    def duration_ms(self) -> int:
        return self.end_ms - self.start_ms


# ---------------------------------------------------------------------------
# Message layer — single message in the system
# ---------------------------------------------------------------------------


class Message(BaseModel):
    """Single message: the atomic unit of all system data.

    Teacher-only fields (convergence_signal, satisfaction_score) are rejected
    when role is student, enforced by model_validator.
    """

    role: Role
    content: str = Field(
        description="Message body text",
    )
    source: Source
    round: int | None = Field(
        default=None,
        ge=1,
        description="Iteration round number, 1-indexed",
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Message creation time",
    )

    # Teacher-only quality signals
    convergence_signal: bool | None = Field(
        default=None,
        description="[teacher only] Whether this message signals convergence",
    )
    satisfaction_score: Annotated[int, Field(ge=1, le=5)] | None = Field(
        default=None,
        description="[teacher only] Satisfaction score 1–5, aids convergence learning",
    )

    # Traceability back to raw audio
    transcription_segments: list[TranscriptionSegment] | None = Field(
        default=None,
        description="Source FunASR segments if this message came from audio",
    )

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Message content must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def teacher_only_fields_check(self) -> Message:
        if self.role == Role.STUDENT:
            if self.convergence_signal is not None:
                raise ValueError("convergence_signal is only valid for teacher messages")
            if self.satisfaction_score is not None:
                raise ValueError("satisfaction_score is only valid for teacher messages")
        return self

    @model_validator(mode="after")
    def simulated_cannot_have_segments(self) -> Message:
        if self.source == Source.SIMULATED and self.transcription_segments:
            raise ValueError("Simulated messages cannot have transcription_segments")
        return self

    @classmethod
    def from_segments(
        cls,
        segments: list[TranscriptionSegment],
        role: Role,
        round: int | None = None,
        min_confidence: float = MIN_CONFIDENCE,
        **kwargs,
    ) -> Message:
        """Promote a list of TranscriptionSegments into a real Message.

        Raises ValueError if any segment falls below min_confidence,
        forcing manual review before the message enters the system.
        """
        low_quality = [s for s in segments if s.confidence < min_confidence]
        if low_quality:
            details = ", ".join(f"[{s.start_ms}ms–{s.end_ms}ms conf={s.confidence:.2f}]" for s in low_quality)
            raise ValueError(
                f"Transcription quality below threshold ({min_confidence}): {details}. "
                "Manual review required before message can be created."
            )

        merged_text = " ".join(s.text for s in segments)
        return cls(
            role=role,
            content=merged_text,
            source=Source.REAL,
            round=round,
            transcription_segments=segments,
            **kwargs,
        )


# ---------------------------------------------------------------------------
# Session layer — one complete task session
# ---------------------------------------------------------------------------


class Session(BaseModel):
    """A complete session: one task_id with its ordered message list.

    Validates that round numbers are monotonically non-decreasing,
    preventing out-of-order writes that would corrupt profile learning.
    """

    task_id: str = Field(
        description="Unique task identifier, e.g. 'thesis_chapter1'",
    )
    messages: list[Message] = Field(
        default_factory=list,
        description="Ordered list of messages in this session",
    )

    @field_validator("task_id")
    @classmethod
    def task_id_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("task_id must not be blank")
        return v.strip()

    @model_validator(mode="after")
    def rounds_must_be_monotonic(self) -> Session:
        rounds = [m.round for m in self.messages if m.round is not None]
        for i in range(1, len(rounds)):
            if rounds[i] < rounds[i - 1]:
                raise ValueError(
                    f"Message rounds must be non-decreasing, but found round {rounds[i]} after round {rounds[i - 1]}"
                )
        return self

    def append(self, message: Message) -> None:
        """Append a message, enforcing monotonic round constraint."""
        if message.round is not None and self.messages:
            last_round = next(
                (m.round for m in reversed(self.messages) if m.round is not None),
                None,
            )
            if last_round is not None and message.round < last_round:
                raise ValueError(f"Cannot append message with round {message.round} after existing round {last_round}")
        self.messages.append(message)

    def by_role(self, role: Role) -> list[Message]:
        return [m for m in self.messages if m.role == role]

    def by_source(self, source: Source) -> list[Message]:
        return [m for m in self.messages if m.source == source]

    def by_round(self, round: int) -> list[Message]:
        return [m for m in self.messages if m.round == round]
