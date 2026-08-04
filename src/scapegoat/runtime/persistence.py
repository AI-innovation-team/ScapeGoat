"""JSON persistence helpers for runtime state and frozen profiles."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel


def save_model(model: BaseModel, path: str | Path) -> None:
    """Serialize a pydantic model to JSON on disk."""

    target = Path(path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(model.model_dump_json(indent=2), encoding="utf-8")


def load_model[ModelT: BaseModel](path: str | Path, model_type: type[ModelT]) -> ModelT:
    """Load a pydantic model from a JSON file."""

    source = Path(path).expanduser().resolve()
    return model_type.model_validate_json(source.read_text(encoding="utf-8"))
