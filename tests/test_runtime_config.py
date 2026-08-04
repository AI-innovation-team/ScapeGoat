"""Tests for runtime backend config."""

from pathlib import Path

from scapegoat.runtime.config import load_backend_config


def test_load_backend_config_defaults():
    config = load_backend_config(None)
    assert config.backend == "local"
    assert config.model == "claude-opus-4-8"


def test_load_backend_config_from_file(tmp_path: Path):
    path = tmp_path / "backend.json"
    path.write_text(
        '{"backend":"claude","model":"claude-opus-4-8","max_tokens":2048,"effort":"medium"}',
        encoding="utf-8",
    )
    config = load_backend_config(path)
    assert config.backend == "claude"
    assert config.max_tokens == 2048
    assert config.effort == "medium"
