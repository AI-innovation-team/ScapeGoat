"""Shared fixtures.

Real profiles and recordings are personal data and stay out of version control,
so tests build a synthetic profile directory instead. This keeps the pipeline
under test in CI rather than skipping it wherever the private data is absent.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scapegoat.profile.constants import ANALYSE_FILENAMES

_PROFILE_MD = """# 测试对象总览

### 规则一：交付物没有明确出口时，先追问最终形态。
### 规则二：时间计划不留余量的，一律视为没有计划。

他把"说清楚"排在"说得好听"前面，冲突时优先保进度。
"""

_ANALYSE_TEMPLATE = """# {name}

## 核心命题

在 {name} 这一层，他的稳定模式是先看代价再看收益。

## 预测规则

### 规则一：当对方只给结论不给依据时，他会要求补出推理链。
### 规则二：当资源紧张时，他会砍范围而不是砍质量。

## 稳定性分析

这一层由早期经历固化，短期内不会改变。
"""


def write_profile(base_dir: Path, subject_id: str) -> Path:
    """Create a complete synthetic profile directory and return its path."""

    profile_dir = base_dir / subject_id
    (profile_dir / "analyse").mkdir(parents=True, exist_ok=True)
    (profile_dir / "profile.md").write_text(_PROFILE_MD, encoding="utf-8")
    for name in ANALYSE_FILENAMES:
        (profile_dir / "analyse" / name).write_text(_ANALYSE_TEMPLATE.format(name=name[:-3]), encoding="utf-8")
    return profile_dir


@pytest.fixture
def profiles_dir(tmp_path: Path) -> Path:
    """A base dir holding two complete synthetic profiles."""

    base = tmp_path / "profiles"
    write_profile(base, "gen_subject")
    write_profile(base, "disc_subject")
    return base
