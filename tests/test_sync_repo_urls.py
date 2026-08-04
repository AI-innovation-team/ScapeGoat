"""Repository-URL sync tests."""

import importlib.util
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "sync_repo_urls", Path(__file__).resolve().parent.parent / "scripts" / "sync_repo_urls.py"
)
assert _SPEC and _SPEC.loader
sync_repo_urls = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(sync_repo_urls)

apply_rules = sync_repo_urls.apply_rules

SAMPLE = """\
/plugin marketplace add old/name
/plugin install name@name
git clone git@github.com:old/name.git && cd name
`uvx --from git+ssh://git@github.com/old/name scapegoat ...`
"repository": "https://github.com/old/name",
[tarball](https://github.com/old/name/tarball/main)
仓库是私有的，所以用 SSH 形式——HTTPS 在没有凭证时会失败。
"""


def test_public_switches_transport_to_https():
    out = apply_rules(SAMPLE, "old/name", "public", previous="old/name")
    assert "git+https://github.com/old/name" in out
    assert "git+ssh://" not in out
    assert "仓库是公开的" in out


def test_private_keeps_ssh():
    out = apply_rules(SAMPLE, "old/name", "private", previous="old/name")
    assert "git+ssh://git@github.com/old/name" in out
    assert "git clone git@github.com:old/name.git" in out


def test_clone_url_keeps_the_git_suffix():
    """The owner/repo class contains dots, so `.git` is easy to swallow."""

    out = apply_rules(SAMPLE, "old/name", "public", previous="old/name")
    assert "git clone https://github.com/old/name.git" in out


def test_web_urls_keep_their_path():
    out = apply_rules(SAMPLE, "old/name", "public", previous="old/name")
    assert "https://github.com/old/name/tarball/main" in out


def test_rename_updates_every_shape():
    out = apply_rules(SAMPLE, "newowner/newrepo", "public", previous="old/name")
    assert "old/name" not in out
    assert "/plugin marketplace add newowner/newrepo" in out
    assert "/plugin install newrepo@newrepo" in out
    assert "&& cd newrepo" in out
    assert '"https://github.com/newowner/newrepo"' in out


def test_round_trip_is_reversible():
    once = apply_rules(SAMPLE, "old/name", "public", previous="old/name")
    back = apply_rules(once, "old/name", "private", previous="old/name")
    assert back == SAMPLE


def test_applying_twice_changes_nothing():
    once = apply_rules(SAMPLE, "new/repo", "public", previous="old/name")
    assert apply_rules(once, "new/repo", "public", previous="new/repo") == once


def test_repo_tree_is_in_sync():
    """The committed tree must already match its own remote."""

    assert sync_repo_urls.sync("colehank/scapegoat", "private", check=True) == 0


FOREIGN = """\
装 uv: https://github.com/astral-sh/uv
本仓库: https://github.com/old/name
克隆别人的: git clone git@github.com:someone/other.git
/plugin marketplace add old/name
"""


def test_other_repositories_are_left_alone():
    """The owner/repo pattern matches anything, so this needs an explicit guard."""

    out = apply_rules(FOREIGN, "new/repo", "public", previous="old/name")
    assert "https://github.com/astral-sh/uv" in out
    assert "git@github.com:someone/other.git" in out
    assert "https://github.com/new/repo" in out
    assert "/plugin marketplace add new/repo" in out


def test_transfer_and_rename_together():
    out = apply_rules(SAMPLE, "neworg/newname", "public", previous="old/name")
    assert "old/name" not in out
    assert "git+https://github.com/neworg/newname" in out
    assert "git clone https://github.com/neworg/newname.git && cd newname" in out


def test_previous_defaults_to_the_recorded_manifest():
    assert sync_repo_urls.recorded_repo() == "colehank/scapegoat"
