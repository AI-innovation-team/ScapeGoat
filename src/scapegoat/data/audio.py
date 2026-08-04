"""Audio transcription pipeline: m4a → TranscriptionSegment list.

Uses FunASR (paraformer-zh + fsmn-vad + ct-punc + cam++) to produce
speaker-separated, timestamped segments ready for Message.from_segments().

Typical usage
-------------
segments = transcribe("databasea/20260515.m4a")
speaker_map = map_speakers(segments)          # interactive, one-time
messages   = segments_to_messages(segments, speaker_map, round=1)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from funasr import AutoModel as FunASRModel

from scapegoat.data.message import MIN_CONFIDENCE, Message, Role, TranscriptionSegment

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model singleton — loaded once, reused across calls
# ---------------------------------------------------------------------------

_model: FunASRModel | None = None


def _get_model() -> FunASRModel:
    global _model
    if _model is None:
        from funasr import AutoModel

        logger.info("Loading FunASR models (first call may download ~2 GB)...")
        _model = AutoModel(
            model="paraformer-zh",
            vad_model="fsmn-vad",
            punc_model="ct-punc",
            spk_model="cam++",
            log_level="ERROR",
            disable_update=True,
        )
        logger.info("FunASR models ready.")
    return _model


# ---------------------------------------------------------------------------
# Confidence proxy
#
# FunASR does not expose token-level confidence in sentence_info.
# We estimate it from token density: tokens-per-second relative to a
# normal speech rate. Sentences with very few or very many tokens per
# second (likely silence, noise, or hallucination) get penalised.
# ---------------------------------------------------------------------------

_NORMAL_TOKENS_PER_SEC = 5.0   # typical Mandarin speech rate
_DENSITY_PENALTY_FLOOR = 0.4   # minimum score from density alone


def _estimate_confidence(sentence: str, start_ms: int, end_ms: int) -> float:
    """Heuristic confidence in [0, 1] based on speech token density."""
    duration_s = (end_ms - start_ms) / 1000.0
    if duration_s <= 0:
        return 0.0
    n_tokens = len([c for c in sentence if c.strip()])
    density = n_tokens / duration_s
    # score peaks at _NORMAL_TOKENS_PER_SEC, falls off on both sides
    ratio = density / _NORMAL_TOKENS_PER_SEC
    if ratio <= 0:
        return _DENSITY_PENALTY_FLOOR
    # log-normal shaped: score = exp(-0.5 * (ln ratio)^2)
    import math
    score = math.exp(-0.5 * math.log(max(ratio, 1e-9)) ** 2)
    return max(_DENSITY_PENALTY_FLOOR, min(1.0, score))


# ---------------------------------------------------------------------------
# Core transcription
# ---------------------------------------------------------------------------


def transcribe(
    audio_path: str | Path,
    *,
    preset_spk_num: int | None = None,
) -> list[TranscriptionSegment]:
    """Transcribe an audio file and return one TranscriptionSegment per speaker turn.

    Parameters
    ----------
    audio_path:
        Path to the audio file (.m4a / .wav / .mp3).
    preset_spk_num:
        Number of speakers if known in advance. Helps cam++ cluster correctly.
        Leave None to auto-detect.

    Returns
    -------
    list[TranscriptionSegment]
        Ordered by start_ms. Segments below MIN_CONFIDENCE are included but
        flagged via is_reliable — caller decides whether to pass them to
        Message.from_segments (which enforces the threshold).
    """
    audio_path = Path(audio_path).resolve()
    if not audio_path.exists():
        raise FileNotFoundError(audio_path)

    model = _get_model()

    kwargs: dict = {"return_spk_res": True}
    if preset_spk_num is not None:
        kwargs["preset_spk_num"] = preset_spk_num

    raw = model.generate(input=str(audio_path), **kwargs)

    # raw is a list; first element holds the full result
    result = raw[0]
    sentence_info: list[dict] = result.get("sentence_info", [])

    if not sentence_info:
        logger.warning("FunASR returned no sentence_info for %s", audio_path.name)
        return []

    segments: list[TranscriptionSegment] = []
    for sent in sentence_info:
        text: str = sent.get("text", "").strip()
        start_ms: int = int(sent.get("start", 0))
        end_ms: int = int(sent.get("end", start_ms + 1))
        spk_label: str = f"spk{sent.get('spk', 0)}"

        if not text:
            logger.debug("Skipping empty segment at %dms", start_ms)
            continue

        confidence = _estimate_confidence(text, start_ms, end_ms)

        segments.append(
            TranscriptionSegment(
                speaker_label=spk_label,
                text=text,
                start_ms=start_ms,
                end_ms=end_ms,
                confidence=confidence,
                audio_source=str(audio_path),
            )
        )

    logger.info(
        "Transcribed %s: %d segments, %d reliable (conf >= %.2f)",
        audio_path.name,
        len(segments),
        sum(1 for s in segments if s.is_reliable),
        MIN_CONFIDENCE,
    )
    return segments


# ---------------------------------------------------------------------------
# Speaker mapping
# ---------------------------------------------------------------------------


def map_speakers(segments: list[TranscriptionSegment]) -> dict[str, Role]:
    """Interactively map raw speaker labels (spk0, spk1 …) to Role.

    Prints a sample utterance per speaker and prompts the user to assign
    teacher / student. Returns a mapping for use in segments_to_messages().
    """
    labels = sorted({s.speaker_label for s in segments})
    if not labels:
        return {}

    samples: dict[str, str] = {}
    for lbl in labels:
        sample = next((s.text for s in segments if s.speaker_label == lbl), "")
        samples[lbl] = sample[:80]

    print("\n=== Speaker Mapping ===")
    for lbl, sample in samples.items():
        print(f"  {lbl}: {sample!r}")

    mapping: dict[str, Role] = {}
    for lbl in labels:
        while True:
            choice = input(f"  Map {lbl!r} → [t]eacher / [s]tudent: ").strip().lower()
            if choice in ("t", "teacher"):
                mapping[lbl] = Role.TEACHER
                break
            if choice in ("s", "student"):
                mapping[lbl] = Role.STUDENT
                break
            print("  Please enter 't' or 's'.")

    print("Mapping:", {k: v.value for k, v in mapping.items()})
    return mapping


# ---------------------------------------------------------------------------
# Segment → Message conversion
# ---------------------------------------------------------------------------


def segments_to_messages(
    segments: list[TranscriptionSegment],
    speaker_map: dict[str, Role],
    *,
    round: int | None = None,
    min_confidence: float = MIN_CONFIDENCE,
    allow_low_confidence: bool = False,
) -> list[Message]:
    """Group consecutive same-speaker segments into Messages.

    Consecutive turns by the same speaker are merged into one Message.
    Low-confidence segments trigger a warning (or ValueError if
    allow_low_confidence is False).

    Parameters
    ----------
    segments:
        Output of transcribe().
    speaker_map:
        Output of map_speakers().
    round:
        Iteration round number to attach to all messages.
    min_confidence:
        Threshold passed to Message.from_segments.
    allow_low_confidence:
        If True, skip low-confidence segments instead of raising.
    """
    if not segments:
        return []

    messages: list[Message] = []

    # Group into runs of same speaker
    runs: list[tuple[Role, list[TranscriptionSegment]]] = []
    current_role: Role | None = None
    current_run: list[TranscriptionSegment] = []

    for seg in segments:
        role = speaker_map.get(seg.speaker_label)
        if role is None:
            logger.warning("Unknown speaker label %r, skipping segment.", seg.speaker_label)
            continue
        if role != current_role:
            if current_run and current_role is not None:
                runs.append((current_role, current_run))
            current_role = role
            current_run = [seg]
        else:
            current_run.append(seg)
    if current_run and current_role is not None:
        runs.append((current_role, current_run))

    for role, run in runs:
        low = [s for s in run if not s.is_reliable]
        if low:
            detail = ", ".join(f"{s.start_ms}ms conf={s.confidence:.2f}" for s in low)
            if allow_low_confidence:
                logger.warning("Low-confidence segments in run (skipped): %s", detail)
                run = [s for s in run if s.is_reliable]
                if not run:
                    continue
            else:
                try:
                    msg = Message.from_segments(run, role=role, round=round, min_confidence=min_confidence)
                except ValueError as exc:
                    raise ValueError(str(exc)) from exc
                messages.append(msg)
                continue

        msg = Message.from_segments(run, role=role, round=round, min_confidence=min_confidence)
        messages.append(msg)

    return messages
