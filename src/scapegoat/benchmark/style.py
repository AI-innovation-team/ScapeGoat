"""Judge-free style fingerprint for T3.

The A/B discrimination score is binary and, against a strong judge, saturates
at 0 — which gives no gradient to optimize against. This module adds a
continuous, deterministic companion metric: measurable surface features of the
text (length, clause rhythm, punctuation habits, structural tells) compared
between the generated and the real text.

It measures *form*, not voice — a text can score well here and still read
nothing like the subject. Use it to detect the specific failure the judges kept
naming ("too long, too organized, too complete"), not as a replacement for the
A/B test.
"""

from __future__ import annotations

import math
import re

from pydantic import BaseModel, Field

# Rhythm is measured over clauses, not sentences: a one-sentence impromptu post
# still has a clause cadence, and splitting only on 。！？ would call it a
# single long sentence and miss exactly the rhythm we care about.
_CLAUSE_SPLIT = re.compile(r"[。！？!?;；，,、\n]+")

# "第一，" / "1." / "一、" / "首先" — enumeration markers in any of the forms a
# structured Chinese text actually uses.
_ENUMERATION = re.compile(
    r"(?:(?<=\n)|^)\s*(?:[0-9]+[.、)]|[一二三四五六七八九十]+[、.)])"
    r"|第[一二三四五六七八九十]+[，,、。.]"
    r"|(?:首先|其次|再次|最后|另外|总之|综上)[，,]"
)
_ELLIPSIS = re.compile(r"…|\.{3,}|。{3,}")

# Each feature is normalized by a scale that makes a "typical" difference ~1.0,
# so the L1 distance is comparable feature to feature. `log_char_count` gets a
# tighter scale on purpose: in the first full benchmark run, overall length was
# by far the strongest tell (real posts averaged 68 chars, generated ones 265).
_SCALES = {
    "log_char_count": 0.35,
    "mean_clause_len": 8.0,
    "short_clause_ratio": 0.35,
    "comma_density": 0.05,
    "ellipsis_density": 0.01,
    "question_density": 0.02,
    "exclaim_density": 0.02,
    "enumeration_density": 0.01,
    "line_density": 0.02,
}

_SHORT_CLAUSE_CHARS = 12


class StyleFingerprint(BaseModel):
    """Surface-form features of one text.

    `log_char_count` carries overall length on a log scale, so the feature
    measures a length *ratio* rather than an absolute gap.
    """

    char_count: int = Field(ge=0)
    log_char_count: float
    mean_clause_len: float
    short_clause_ratio: float
    comma_density: float
    ellipsis_density: float
    question_density: float
    exclaim_density: float
    enumeration_density: float
    line_density: float


def fingerprint(text: str) -> StyleFingerprint:
    """Extract surface-form features from one text."""

    stripped = text.strip()
    n = max(len(stripped), 1)
    clauses = [c.strip() for c in _CLAUSE_SPLIT.split(stripped) if c.strip()]
    lengths = [len(c) for c in clauses] or [0]
    short = sum(1 for length in lengths if length <= _SHORT_CLAUSE_CHARS)
    return StyleFingerprint(
        char_count=len(stripped),
        log_char_count=math.log(n),
        mean_clause_len=sum(lengths) / len(lengths),
        short_clause_ratio=short / len(lengths),
        comma_density=(stripped.count("，") + stripped.count(",")) / n,
        ellipsis_density=len(_ELLIPSIS.findall(stripped)) / n,
        question_density=(stripped.count("？") + stripped.count("?")) / n,
        exclaim_density=(stripped.count("！") + stripped.count("!")) / n,
        enumeration_density=len(_ENUMERATION.findall(stripped)) / n,
        line_density=stripped.count("\n") / n,
    )


def fingerprint_distance(generated: str, real: str) -> float:
    """Mean scaled absolute difference across features (0 = identical form)."""

    a, b = fingerprint(generated), fingerprint(real)
    total = 0.0
    for name, scale in _SCALES.items():
        total += abs(getattr(a, name) - getattr(b, name)) / scale
    return total / len(_SCALES)


def style_similarity(generated: str, real: str) -> float:
    """Map fingerprint distance to a [0, 1] similarity (1 = same surface form).

    Exponential decay keeps the metric sensitive near zero distance, where
    optimization actually happens, instead of flattening like a clipped linear
    score would.
    """

    return round(math.exp(-fingerprint_distance(generated, real)), 4)
