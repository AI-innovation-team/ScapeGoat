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
    out = apply_rules(SAMPLE, "old/name", "public")
    assert "git+https://github.com/old/name" in out
    assert "git+ssh://" not in out
    assert "仓库是公开的" in out


def test_private_keeps_ssh():
    out = apply_rules(SAMPLE, "old/name", "private")
    assert "git+ssh://git@github.com/old/name" in out
    assert "git clone git@github.com:old/name.git" in out


def test_clone_url_keeps_the_git_suffix():
    """The owner/repo class contains dots, so `.git` is easy to swallow."""

    out = apply_rules(SAMPLE, "old/name", "public")
    assert "git clone https://github.com/old/name.git" in out


def test_web_urls_keep_their_path():
    out = apply_rules(SAMPLE, "old/name", "public")
    assert "https://github.com/old/name/tarball/main" in out


def test_rename_updates_every_shape():
    out = apply_rules(SAMPLE, "newowner/newrepo", "public")
    assert "old/name" not in out
    assert "/plugin marketplace add newowner/newrepo" in out
    assert "/plugin install newrepo@newrepo" in out
    assert "&& cd newrepo" in out
    assert '"https://github.com/newowner/newrepo"' in out


def test_round_trip_is_reversible():
    once = apply_rules(SAMPLE, "old/name", "public")
    back = apply_rules(once, "old/name", "private")
    assert back == SAMPLE


def test_applying_twice_changes_nothing():
    once = apply_rules(SAMPLE, "new/repo", "public")
    assert apply_rules(once, "new/repo", "public") == once


def test_repo_tree_is_in_sync():
    """The committed tree must already match its own remote."""

    assert sync_repo_urls.sync("colehank/scapegoat", "private", check=True) == 0
