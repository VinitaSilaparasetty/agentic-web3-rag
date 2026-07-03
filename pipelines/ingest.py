"""
File: pipelines/ingest.py

Why:
- Provide a small, deterministic Phase-1 (opt-in) ingest that exports `run_ingest(manifest)`.
- Uses requests (+ trafilatura.extract) to avoid deprecated trafilatura.fetch_url kwargs.
- Writes normalized Markdown with provenance to data/processed/*.md.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Literal

import requests
import trafilatura
from pydantic import BaseModel, Field, HttpUrl

from models.config import settings
from models.policy import license_ok, normalize

DATA_DIR = Path("data")
PROCESSED_DIR = DATA_DIR / "processed"
CONSENTS_FILE = DATA_DIR / "consents.yaml"


class SourceItem(BaseModel):
    """A single opt-in source for Phase-1 ingest."""
    kind: Literal["website"] = "website"
    id: str = Field(min_length=1)
    project: str = Field(min_length=1)
    url: HttpUrl
    consent_proof: str | None = None  # e.g., link to issue/PR/email artifact


def _load_yaml(path: Path) -> dict:
    import yaml
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _consent_check(item: SourceItem) -> tuple[bool, str]:
    """Return (allowed, display_policy) from the consent registry."""
    from urllib.parse import urlparse

    from policies.consent_registry import ConsentRegistry
    try:
        reg = ConsentRegistry(str(CONSENTS_FILE))
    except FileNotFoundError:
        return False, "link-only"
    parsed = urlparse(str(item.url))
    ok, _ = reg.is_allowed(parsed.netloc, parsed.path or "/")
    policy = reg.display_policy_for(parsed.netloc) if ok else "link-only"
    return ok, policy


def fetch_http(url: str, ua: str) -> str:
    """
    Fetch a web page and extract main content as text.

    Why:
    - Use requests to control headers and timeouts; trafilatura.extract for robust content extraction.
    """
    try:
        r = requests.get(url, headers={"User-Agent": ua}, timeout=25)
        r.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"fetch failed: {url}: {e}") from e
    text = trafilatura.extract(r.text) or ""
    if not text.strip():
        # We emit empty text rather than failing hard to keep ingestion idempotent.
        return ""
    return text


def _write_markdown(item: SourceItem, body_text: str, display_policy: str = "link-only") -> Path:
    """
    Persist normalized Markdown with front-matter metadata.
    Why:
    - Store provenance and consent proof for audit + future purges.
    - display_policy is passed through to chunks and Qdrant payload so the
      compliance layer can enforce it without a second registry lookup.
    """
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out = PROCESSED_DIR / f"{item.id}.md"
    fm = {
        "project": item.project,
        "source_url": str(item.url),
        "consent_proof": item.consent_proof or "",
        "display_policy": display_policy,
        "ingested_at": int(time.time()),
        "user_agent": settings.user_agent,
        "policy_mode": settings.policy_mode,
    }
    # Front matter + body as Markdown
    content = [
        "---",
        json.dumps(fm, ensure_ascii=False, indent=2),
        "---",
        "",
        body_text.strip(),
        "",
    ]
    out.write_text("\n".join(content), encoding="utf-8")
    return out


def _ingest_website(item: SourceItem) -> Path:
    allowed, display_policy = _consent_check(item)
    if not allowed:
        raise PermissionError(f"source not allowed by consent registry: {item.id} ({item.project})")
    text = fetch_http(str(item.url), settings.user_agent)
    return _write_markdown(item, text, display_policy=display_policy)


def run_ingest(manifest: list[dict]) -> list[Path]:
    """
    Execute Phase-1 ingest for a list of source dicts.

    Parameters
    ----------
    manifest : List[Dict]
        List of dicts matching SourceItem schema.

    Returns
    -------
    List[Path]
        Paths of written normalized Markdown files.

    Raises
    ------
    ValidationError
        If a manifest item fails schema validation.
    PermissionError
        If a source is not in the consent allowlist.
    """
    written: list[Path] = []
    for d in manifest:
        item = SourceItem(**d)
        lic = normalize(getattr(item, 'license', None))
        if lic is not None and not license_ok(lic):
            print(f"[license-skip] {item.id} license={lic!r} not allowed; skipping")
            continue
        if item.kind == "website":
            p = _ingest_website(item)
            written.append(p)
        else:
            # Why-not: keep Phase-1 scope narrow; add more kinds in later phases.
            raise ValueError(f"unsupported kind for Phase-1: {item.kind}")
    return written


def main(argv: list[str] | None = None) -> None:
    """
    Small CLI: `python -m pipelines.ingest --manifest-json <path>`

    Flags
    -----
    --manifest-json : str
        Path to a JSON file containing a list of source items.
    """
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--manifest-json", required=True, help="path to JSON manifest (list of items)")
    args = p.parse_args(argv)

    manifest_path = Path(args.manifest_json)
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest not found: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    written = run_ingest(manifest)
    print(json.dumps({"written": [str(p) for p in written]}, indent=2))


if __name__ == "__main__":
    main()
