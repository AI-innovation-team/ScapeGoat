"""Tests for message data models — quality gate validation."""

import pytest
from pydantic import ValidationError

from scapegoat.data.message import Message, Role, Session, Source, TranscriptionSegment

# ---------------------------------------------------------------------------
# TranscriptionSegment
# ---------------------------------------------------------------------------


def make_segment(**overrides) -> TranscriptionSegment:
    defaults = dict(
        speaker_label="spk1",
        text="你这里逻辑有问题",
        start_ms=0,
        end_ms=3000,
        confidence=0.92,
        audio_source="meeting.wav",
    )
    return TranscriptionSegment(**(defaults | overrides))


def test_segment_valid():
    s = make_segment()
    assert s.is_reliable is True
    assert s.duration_ms == 3000


def test_segment_blank_text_rejected():
    with pytest.raises(ValidationError, match="must not be blank"):
        make_segment(text="   ")


def test_segment_end_before_start_rejected():
    with pytest.raises(ValidationError, match="end_ms.*must be greater than start_ms"):
        make_segment(start_ms=5000, end_ms=2000)


def test_segment_low_confidence_is_unreliable():
    s = make_segment(confidence=0.4)
    assert s.is_reliable is False


def test_segment_confidence_out_of_range():
    with pytest.raises(ValidationError):
        make_segment(confidence=1.5)


# ---------------------------------------------------------------------------
# Message — construction
# ---------------------------------------------------------------------------


def make_teacher_msg(**overrides) -> Message:
    defaults = dict(role=Role.TEACHER, content="你这里理论理解太浅", source=Source.REAL, round=1)
    return Message(**(defaults | overrides))


def make_student_msg(**overrides) -> Message:
    defaults = dict(role=Role.STUDENT, content="第一章草稿...", source=Source.REAL, round=1)
    return Message(**(defaults | overrides))


def test_message_valid_teacher():
    m = make_teacher_msg(convergence_signal=False, satisfaction_score=3)
    assert m.role == Role.TEACHER
    assert m.source == Source.REAL


def test_message_valid_student():
    m = make_student_msg()
    assert m.role == Role.STUDENT


def test_message_blank_content_rejected():
    with pytest.raises(ValidationError, match="must not be blank"):
        make_teacher_msg(content="  ")


def test_student_convergence_signal_rejected():
    with pytest.raises(ValidationError, match="convergence_signal is only valid for teacher"):
        make_student_msg(convergence_signal=True)


def test_student_satisfaction_score_rejected():
    with pytest.raises(ValidationError, match="satisfaction_score is only valid for teacher"):
        make_student_msg(satisfaction_score=4)


def test_simulated_message_no_segments():
    seg = make_segment()
    with pytest.raises(ValidationError, match="Simulated messages cannot have transcription_segments"):
        Message(
            role=Role.TEACHER,
            content="模拟意见",
            source=Source.SIMULATED,
            transcription_segments=[seg],
        )


# ---------------------------------------------------------------------------
# Message.from_segments — transcription quality gate
# ---------------------------------------------------------------------------


def test_from_segments_high_confidence():
    segs = [make_segment(text="你这里逻辑有问题", start_ms=0, end_ms=2000, confidence=0.91)]
    m = Message.from_segments(segs, role=Role.TEACHER, round=1)
    assert m.source == Source.REAL
    assert "你这里逻辑有问题" in m.content
    assert len(m.transcription_segments) == 1


def test_from_segments_merges_text():
    segs = [
        make_segment(text="你这里", start_ms=0, end_ms=1000, confidence=0.90),
        make_segment(text="逻辑有问题", start_ms=1000, end_ms=2500, confidence=0.88),
    ]
    m = Message.from_segments(segs, role=Role.TEACHER)
    assert m.content == "你这里 逻辑有问题"


def test_from_segments_low_confidence_blocked():
    segs = [make_segment(text="模糊片段", confidence=0.45)]
    with pytest.raises(ValueError, match="Transcription quality below threshold"):
        Message.from_segments(segs, role=Role.TEACHER)


def test_from_segments_partial_low_confidence_blocked():
    segs = [
        make_segment(text="清晰片段", start_ms=0, end_ms=1500, confidence=0.95),
        make_segment(text="模糊片段", start_ms=1500, end_ms=3000, confidence=0.30),
    ]
    with pytest.raises(ValueError, match="Manual review required"):
        Message.from_segments(segs, role=Role.TEACHER)


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------


def test_session_valid():
    s = Session(
        task_id="thesis_chapter1",
        messages=[
            make_student_msg(round=1),
            make_teacher_msg(round=1),
            make_student_msg(round=2),
        ],
    )
    assert len(s.messages) == 3


def test_session_blank_task_id_rejected():
    with pytest.raises(ValidationError, match="must not be blank"):
        Session(task_id="  ")


def test_session_non_monotonic_rounds_rejected():
    with pytest.raises(ValidationError, match="non-decreasing"):
        Session(
            task_id="task1",
            messages=[
                make_teacher_msg(round=3),
                make_student_msg(round=1),
            ],
        )


def test_session_append_enforces_monotonic():
    s = Session(task_id="task1")
    s.append(make_teacher_msg(round=2))
    with pytest.raises(ValueError, match="Cannot append"):
        s.append(make_student_msg(round=1))


def test_session_by_role():
    s = Session(
        task_id="task1",
        messages=[make_student_msg(round=1), make_teacher_msg(round=1)],
    )
    assert len(s.by_role(Role.TEACHER)) == 1
    assert len(s.by_role(Role.STUDENT)) == 1


def test_session_by_source():
    s = Session(
        task_id="task1",
        messages=[
            make_teacher_msg(round=1, source=Source.REAL),
            Message(role=Role.TEACHER, content="模拟意见", source=Source.SIMULATED, round=2),
        ],
    )
    assert len(s.by_source(Source.SIMULATED)) == 1


def test_session_by_round():
    s = Session(
        task_id="task1",
        messages=[
            make_student_msg(round=1),
            make_teacher_msg(round=1),
            make_student_msg(round=2),
        ],
    )
    assert len(s.by_round(1)) == 2
    assert len(s.by_round(2)) == 1
