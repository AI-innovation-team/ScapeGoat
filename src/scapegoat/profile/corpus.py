"""Normalize corpus sources (documents / JSON conversations) for profile ingestion.

The ingestion pipeline accepts two kinds of corpus material:

* arbitrary text documents — read verbatim;
* JSON conversations — tolerant of common export shapes, rendered into a
  speaker-labelled transcript so an LLM can read them as dialogue.

This module only normalizes; the extraction/merge itself is LLM work driven by
the `scapegoat-ingest-corpus` skill.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

_SPEAKER_KEYS = ("role", "speaker", "sender", "from", "name", "author")
_TEXT_KEYS = ("content", "text", "message", "body", "value")


class ConversationTurn(BaseModel):
    """One speaker-labelled utterance from a JSON conversation."""

    speaker: str
    text: str


class CorpusSource(BaseModel):
    """One normalized corpus source ready for LLM extraction."""

    path: str
    kind: Literal["conversation", "document"]
    text: str
    turns: int = Field(default=0, ge=0)


def _first_str(item: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _as_turn_list(data: Any) -> list[Any] | None:
    """Locate the message list inside common conversation-export shapes."""

    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("messages", "conversation", "dialog", "turns", "data"):
            value = data.get(key)
            if isinstance(value, list):
                return value
    return None


def parse_conversation(data: Any) -> list[ConversationTurn]:
    """Parse a loaded JSON object into conversation turns.

    Returns an empty list when the shape does not look like a conversation,
    which callers treat as "fall back to document".
    """

    items = _as_turn_list(data)
    if not items:
        return []
    turns: list[ConversationTurn] = []
    for item in items:
        if isinstance(item, str):
            if item.strip():
                turns.append(ConversationTurn(speaker="unknown", text=item.strip()))
            continue
        if not isinstance(item, dict):
            continue
        text = _first_str(item, _TEXT_KEYS)
        if not text:
            continue
        speaker = _first_str(item, _SPEAKER_KEYS) or "unknown"
        turns.append(ConversationTurn(speaker=speaker, text=text))
    return turns


def render_transcript(turns: list[ConversationTurn]) -> str:
    """Render turns as `speaker: text` lines."""

    return "\n".join(f"{turn.speaker}: {turn.text}" for turn in turns)


def normalize_source(path: str | Path) -> CorpusSource:
    """Normalize one corpus file into a `CorpusSource`.

    `.json` files are parsed as conversations when possible; any other file
    (and unparseable JSON) is treated as a plain document.
    """

    source = Path(path).expanduser().resolve()
    raw = source.read_text(encoding="utf-8")
    if source.suffix.lower() == ".json":
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = None
        if data is not None:
            turns = parse_conversation(data)
            if turns:
                return CorpusSource(
                    path=str(source),
                    kind="conversation",
                    text=render_transcript(turns),
                    turns=len(turns),
                )
    return CorpusSource(path=str(source), kind="document", text=raw)


def normalize_sources(paths: list[str | Path]) -> list[CorpusSource]:
    """Normalize a list of corpus files, preserving order."""

    return [normalize_source(path) for path in paths]


def render_corpus_markdown(sources: list[CorpusSource]) -> str:
    """Render normalized sources as one markdown block for LLM consumption."""

    chunks: list[str] = []
    for index, source in enumerate(sources, start=1):
        header = f"## 语料 {index}: {Path(source.path).name} ({source.kind}"
        header += f", {source.turns} turns)" if source.kind == "conversation" else ")"
        chunks.append(f"{header}\n\n{source.text.strip()}")
    return "\n\n---\n\n".join(chunks)
