"""Corpus normalization tests."""

import json
from pathlib import Path

from scapegoat.profile.corpus import (
    normalize_source,
    normalize_sources,
    parse_conversation,
    render_corpus_markdown,
)


def test_parse_conversation_role_content():
    turns = parse_conversation([{"role": "teacher", "content": "开始吧"}, {"role": "student", "content": "好"}])
    assert [(t.speaker, t.text) for t in turns] == [("teacher", "开始吧"), ("student", "好")]


def test_parse_conversation_alternate_keys_and_wrapper():
    data = {"messages": [{"speaker": "A", "text": "hello"}, {"from": "B", "body": "hi"}]}
    turns = parse_conversation(data)
    assert [(t.speaker, t.text) for t in turns] == [("A", "hello"), ("B", "hi")]


def test_parse_conversation_skips_empty_and_unknown_items():
    turns = parse_conversation([{"role": "a", "content": "  "}, 42, {"note": "x"}, "bare line"])
    assert [(t.speaker, t.text) for t in turns] == [("unknown", "bare line")]


def test_parse_conversation_rejects_non_conversation():
    assert parse_conversation({"config": {"x": 1}}) == []


def test_normalize_source_json_conversation(tmp_path: Path):
    path = tmp_path / "chat.json"
    path.write_text(json.dumps([{"role": "t", "content": "第一句"}]), encoding="utf-8")
    source = normalize_source(path)
    assert source.kind == "conversation"
    assert source.turns == 1
    assert source.text == "t: 第一句"


def test_normalize_source_json_fallback_to_document(tmp_path: Path):
    path = tmp_path / "data.json"
    path.write_text(json.dumps({"config": True}), encoding="utf-8")
    source = normalize_source(path)
    assert source.kind == "document"


def test_normalize_source_plain_document(tmp_path: Path):
    path = tmp_path / "notes.md"
    path.write_text("他说过一句话。", encoding="utf-8")
    source = normalize_source(path)
    assert source.kind == "document"
    assert source.text == "他说过一句话。"


def test_render_corpus_markdown_headers(tmp_path: Path):
    chat = tmp_path / "chat.json"
    chat.write_text(json.dumps([{"role": "t", "content": "hi"}]), encoding="utf-8")
    doc = tmp_path / "doc.txt"
    doc.write_text("正文", encoding="utf-8")
    rendered = render_corpus_markdown(normalize_sources([chat, doc]))
    assert "## 语料 1: chat.json (conversation, 1 turns)" in rendered
    assert "## 语料 2: doc.txt (document)" in rendered
    assert "\n\n---\n\n" in rendered


def test_real_database_conversation_parses():
    path = Path("database/20240913_messages.json")
    source = normalize_source(path)
    assert source.kind == "conversation"
    assert source.turns > 100
    assert source.text.splitlines()[0].startswith(("teacher:", "student:"))
