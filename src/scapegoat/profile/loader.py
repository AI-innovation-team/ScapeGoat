"""Load markdown profile assets from disk."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from scapegoat.profile.constants import ANALYSE_FILENAMES, DEFAULT_PROFILE_DIR
from scapegoat.profile.schema import ProfileBundle


@dataclass(slots=True)
class ProfileInspection:
    """Filesystem completeness check for a profile directory."""

    subject_id: str
    profile_dir: Path
    profile_path: Path
    present_files: list[str]
    missing_files: list[str]

    @property
    def is_complete(self) -> bool:
        return not self.missing_files


def subject_dir(subject_id: str, base_dir: str | Path = DEFAULT_PROFILE_DIR) -> Path:
    """Resolve the on-disk directory for a subject profile."""

    return Path(base_dir).expanduser().resolve() / subject_id


def inspect_profile(subject_id: str, base_dir: str | Path = DEFAULT_PROFILE_DIR) -> ProfileInspection:
    """Check whether all required markdown assets exist for a subject."""

    directory = subject_dir(subject_id, base_dir)
    profile_path = directory / "profile.md"
    required = ["profile.md", *[f"analyse/{name}" for name in ANALYSE_FILENAMES]]
    present: list[str] = []
    missing: list[str] = []
    for relative in required:
        path = directory / relative
        if path.exists():
            present.append(relative)
        else:
            missing.append(relative)
    return ProfileInspection(
        subject_id=subject_id,
        profile_dir=directory,
        profile_path=profile_path,
        present_files=present,
        missing_files=missing,
    )


def load_profile_bundle(subject_id: str, base_dir: str | Path = DEFAULT_PROFILE_DIR) -> ProfileBundle:
    """Load `profile.md` and all `analyse/*.md` files for a subject."""

    inspection = inspect_profile(subject_id, base_dir)
    if inspection.missing_files:
        missing = ", ".join(inspection.missing_files)
        raise FileNotFoundError(f"profile assets incomplete for {subject_id}: {missing}")

    analyse_dir = inspection.profile_dir / "analyse"
    analyse = {name[:-3]: (analyse_dir / name).read_text(encoding="utf-8") for name in ANALYSE_FILENAMES}
    return ProfileBundle(
        subject_id=subject_id,
        profile_markdown=inspection.profile_path.read_text(encoding="utf-8"),
        analyse=analyse,
        source_dir=str(inspection.profile_dir),
        profile_path=str(inspection.profile_path),
    )
