"""Tests for markdown profile loading and freezing."""

from pathlib import Path

from scapegoat.profile.freezer import freeze_profile
from scapegoat.profile.loader import inspect_profile, load_profile_bundle


def test_inspect_and_freeze_real_profile(profiles_dir: Path):
    inspection = inspect_profile("gen_subject", profiles_dir)
    assert inspection.is_complete is True
    bundle = load_profile_bundle("gen_subject", profiles_dir)
    frozen = freeze_profile(bundle, role="generator")
    assert frozen.subject_id == "gen_subject"
    assert frozen.role == "generator"
    assert frozen.behavior_rules
