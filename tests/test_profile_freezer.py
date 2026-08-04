"""Tests for markdown profile loading and freezing."""

from pathlib import Path

from scapegoat.profile.freezer import freeze_profile
from scapegoat.profile.loader import inspect_profile, load_profile_bundle


def test_inspect_and_freeze_real_profile():
    inspection = inspect_profile("zgh", Path("profiles"))
    assert inspection.is_complete is True
    bundle = load_profile_bundle("zgh", Path("profiles"))
    frozen = freeze_profile(bundle, role="generator")
    assert frozen.subject_id == "zgh"
    assert frozen.role == "generator"
    assert frozen.behavior_rules
