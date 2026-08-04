"""Rewrite the repository URLs embedded in docs and manifests.

Several files have to name the repository literally — the plugin's `.mcp.json`
tells uv where to fetch the package from, the README tells users what to type,
`plugin.json` records the homepage. Renaming the repo, transferring it to
another owner, or flipping it public would otherwise leave those stale.

The git transport follows visibility: a private repo needs SSH (uv cannot
authenticate over HTTPS), a public one uses HTTPS so users need no SSH key.

    python scripts/sync_repo_urls.py --check    # exit 1 if anything is stale
    python scripts/sync_repo_urls.py            # rewrite in place

Both `--repo` and `--visibility` default to the GitHub Actions environment, and
fall back to `git remote` plus the `gh` CLI when run locally.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Every literal shape a repository reference takes across the tree. Each pattern
# captures nothing but the owner/repo pair it must replace, so a rename in any
# component is picked up regardless of which form the file happens to use.
_OWNER_REPO = r"[A-Za-z0-9._-]+/[A-Za-z0-9._-]+"

TARGETS = ("README.md", ".mcp.json", "skills/cli-invocation.md", ".claude-plugin/plugin.json")
DOC_TARGETS = ("docs/installation.md",)


def _run(*args: str) -> str | None:
    try:
        out = subprocess.run(args, capture_output=True, text=True, timeout=30, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def detect_repo() -> str:
    """owner/name, from the Actions env or the origin remote."""

    env = os.environ.get("GITHUB_REPOSITORY")
    if env:
        return env
    remote = _run("git", "remote", "get-url", "origin") or ""
    match = re.search(rf"github\.com[:/]({_OWNER_REPO})", remote)
    if not match:
        raise SystemExit("cannot determine the repository: set --repo or GITHUB_REPOSITORY")
    return match.group(1).removesuffix(".git")


def detect_visibility(repo: str) -> str:
    """`public` or `private`, from the Actions event payload or the gh CLI."""

    env = os.environ.get("REPO_VISIBILITY")
    if env in {"public", "private"}:
        return env
    gh = _run("gh", "repo", "view", repo, "--json", "visibility", "-q", ".visibility")
    if gh:
        return gh.lower()
    # Assume private: SSH works for both, HTTPS only for public, so this is the
    # safe direction to guess in.
    return "private"


# One pass over every reference shape. Sequential rules would clobber each
# other: rewriting a clone URL to `https://…/repo.git` makes it match the plain
# web-URL rule too, whose owner/repo class absorbs the `.git`. Ordering the
# alternation so the `.git` forms are tried first, and replacing each whole
# match once, removes that class of bug entirely.
_REFERENCE = re.compile(
    rf"git\+ssh://git@github\.com/(?P<uv_ssh>{_OWNER_REPO})"
    rf"|git\+https://github\.com/(?P<uv_https>{_OWNER_REPO})"
    rf"|git@github\.com:(?P<clone_ssh>{_OWNER_REPO})\.git"
    rf"|https://github\.com/(?P<clone_https>{_OWNER_REPO})\.git"
    rf"|https://github\.com/(?P<web>{_OWNER_REPO})"
)


def _rewrite_reference(match: re.Match[str], repo: str, visibility: str) -> str:
    """Map one matched reference onto its current form."""

    public = visibility == "public"
    if match.lastgroup in ("uv_ssh", "uv_https"):
        return f"git+https://github.com/{repo}" if public else f"git+ssh://git@github.com/{repo}"
    if match.lastgroup in ("clone_ssh", "clone_https"):
        return f"https://github.com/{repo}.git" if public else f"git@github.com:{repo}.git"
    return f"https://github.com/{repo}"  # plain web URL: always HTTPS


def _literal_rules(repo: str, visibility: str) -> list[tuple[str, str]]:
    """Replacements outside URLs: install ids, the `cd` target, one sentence."""

    name = repo.split("/", 1)[1]
    transport = (
        "仓库是公开的，所以用 HTTPS 形式，用户无需配置 SSH key。"
        if visibility == "public"
        else "仓库是私有的，所以用 SSH 形式——HTTPS 在没有凭证时会失败。"
    )
    return [
        (rf"(?<=/plugin marketplace add ){_OWNER_REPO}", repo),
        (r"(?<=/plugin install )[A-Za-z0-9._-]+@[A-Za-z0-9._-]+", f"{name}@{name}"),
        (r"(?<=&& cd )[A-Za-z0-9._-]+", name),
        (r"仓库是(?:私有|公开)的，所以用 (?:SSH|HTTPS) 形式[^\n]*。", transport),
    ]


def apply_rules(text: str, repo: str, visibility: str) -> str:
    """Bring every repository reference in one file up to date."""

    text = _REFERENCE.sub(lambda m: _rewrite_reference(m, repo, visibility), text)
    for pattern, target in _literal_rules(repo, visibility):
        text = re.sub(pattern, target, text)
    return text


def sync(repo: str, visibility: str, check: bool) -> int:
    stale: list[str] = []
    for rel in (*TARGETS, *DOC_TARGETS):
        path = ROOT / rel
        if not path.exists():
            continue
        original = path.read_text(encoding="utf-8")
        updated = apply_rules(original, repo, visibility)
        if updated != original:
            stale.append(rel)
            if not check:
                path.write_text(updated, encoding="utf-8")
    if check:
        if stale:
            print(f"stale repository URLs in: {', '.join(stale)}")
            print(f"run: python scripts/sync_repo_urls.py  (repo={repo}, visibility={visibility})")
            return 1
        print(f"repository URLs are current (repo={repo}, visibility={visibility})")
        return 0
    print(f"updated {len(stale)} file(s) for repo={repo} visibility={visibility}")
    for rel in stale:
        print(f"  {rel}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", help="owner/name (default: GITHUB_REPOSITORY or origin remote)")
    parser.add_argument("--visibility", choices=("public", "private"), help="default: detected")
    parser.add_argument("--check", action="store_true", help="report drift without writing")
    args = parser.parse_args()
    repo = args.repo or detect_repo()
    visibility = args.visibility or detect_visibility(repo)
    return sync(repo, visibility, args.check)


if __name__ == "__main__":
    sys.exit(main())
