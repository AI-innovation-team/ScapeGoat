"""Validate the book-writing example assets."""

from pathlib import Path

from scapegoat.runtime.config import load_backend_config
from scapegoat.runtime.schema import TaskSpec
from scapegoat.training.schema import TrainingRecord

EXAMPLE_DIR = Path("examples/book_writing_ai_cognitive_neuroscience")


def test_book_writing_example_assets_parse():
    task = TaskSpec.model_validate_json((EXAMPLE_DIR / "task.json").read_text(encoding="utf-8"))
    local_backend = load_backend_config(EXAMPLE_DIR / "backend_config.local.json")
    claude_backend = load_backend_config(EXAMPLE_DIR / "backend_config.claude.json")
    record = TrainingRecord.model_validate_json(
        (EXAMPLE_DIR / "training_record_v1.json").read_text(encoding="utf-8")
    )

    assert task.deliverable_type == "chapter_draft"
    assert task.constraints
    assert local_backend.backend == "local"
    assert claude_backend.backend == "claude"
    assert record.task.task_id == task.task_id
    assert "中心论题" in record.real_discriminator_output
