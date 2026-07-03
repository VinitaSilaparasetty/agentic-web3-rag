"""Tests for pipelines/preprocess.py — chunking + front-matter parsing."""
import json

from pipelines.preprocess import _paragraph_chunks, _parse_front_matter, _stable_id, main

# ── _parse_front_matter ───────────────────────────────────────────────────────

def test_parse_front_matter_with_valid_json():
    raw = '---\n{"project": "myproject", "url": "https://example.com"}\n---\nBody text here.'
    meta, body = _parse_front_matter(raw)
    assert meta["project"] == "myproject"
    assert meta["url"] == "https://example.com"
    assert body.strip() == "Body text here."


def test_parse_front_matter_no_frontmatter():
    raw = "Just plain text with no front-matter."
    meta, body = _parse_front_matter(raw)
    assert meta == {}
    assert body == raw


def test_parse_front_matter_invalid_json_returns_empty_meta():
    raw = '---\n{this is not json}\n---\nSome body.'
    meta, body = _parse_front_matter(raw)
    assert meta == {}


def test_parse_front_matter_display_policy_passthrough():
    raw = '---\n{"project": "p", "display_policy": "fulltext"}\n---\nBody.'
    meta, _ = _parse_front_matter(raw)
    assert meta["display_policy"] == "fulltext"


# ── _paragraph_chunks ─────────────────────────────────────────────────────────

def test_paragraph_chunks_short_text_one_chunk():
    text = "Hello world.\n\nThis is a paragraph."
    chunks = list(_paragraph_chunks(text, max_len=1200))
    assert len(chunks) == 1


def test_paragraph_chunks_long_text_splits():
    para = "word " * 300  # ~1500 chars
    text = f"{para}\n\n{para}"
    chunks = list(_paragraph_chunks(text, max_len=1200))
    assert len(chunks) >= 2


def test_paragraph_chunks_empty_text():
    assert list(_paragraph_chunks("")) == []


# ── _stable_id ────────────────────────────────────────────────────────────────

def test_stable_id_is_deterministic():
    a = _stable_id("source-1", "hello world")
    b = _stable_id("source-1", "hello world")
    assert a == b


def test_stable_id_differs_by_source():
    a = _stable_id("source-1", "hello")
    b = _stable_id("source-2", "hello")
    assert a != b


def test_stable_id_differs_by_text():
    a = _stable_id("source-1", "hello")
    b = _stable_id("source-1", "world")
    assert a != b


# ── main() integration ────────────────────────────────────────────────────────

def test_main_writes_chunks_jsonl(tmp_path, monkeypatch):
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir()
    out_path = processed_dir / "chunks.jsonl"

    # Write a sample markdown file with front-matter
    md = (
        '---\n'
        '{"project": "test-proj", "source_url": "https://example.com", "display_policy": "fulltext"}\n'
        '---\n'
        'First paragraph about Ethereum.\n\n'
        'Second paragraph about Solidity.\n'
    )
    (processed_dir / "test-source.md").write_text(md)

    monkeypatch.setattr("pipelines.preprocess.PROCESSED_DIR", processed_dir)
    monkeypatch.setattr("pipelines.preprocess.OUT_PATH", out_path)

    main()

    assert out_path.exists()
    lines = [json.loads(line) for line in out_path.read_text().splitlines() if line.strip()]
    assert len(lines) >= 1
    first = lines[0]
    assert first["project"] == "test-proj"
    assert first["url"] == "https://example.com"
    assert first["display_policy"] == "fulltext"
    assert "text" in first
    assert "id" in first


def test_main_defaults_display_policy_to_link_only(tmp_path, monkeypatch):
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir()
    out_path = processed_dir / "chunks.jsonl"

    # No display_policy in front-matter
    md = '---\n{"project": "no-policy"}\n---\nSome content here.\n'
    (processed_dir / "no-policy.md").write_text(md)

    monkeypatch.setattr("pipelines.preprocess.PROCESSED_DIR", processed_dir)
    monkeypatch.setattr("pipelines.preprocess.OUT_PATH", out_path)

    main()

    lines = [json.loads(line) for line in out_path.read_text().splitlines() if line.strip()]
    assert lines[0]["display_policy"] == "link-only"


def test_main_empty_dir_writes_empty_file(tmp_path, monkeypatch):
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir()
    out_path = processed_dir / "chunks.jsonl"

    monkeypatch.setattr("pipelines.preprocess.PROCESSED_DIR", processed_dir)
    monkeypatch.setattr("pipelines.preprocess.OUT_PATH", out_path)

    main()

    assert out_path.exists()
    content = out_path.read_text().strip()
    assert content == ""
