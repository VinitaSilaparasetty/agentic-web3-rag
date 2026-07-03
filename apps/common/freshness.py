import json
import os
import tempfile
import time
import urllib.parse
from collections.abc import Iterable

REG_PATH = os.getenv("FRESHNESS_REG_PATH", "data/freshness.json")

def _now_ts() -> float:
    return time.time()

def _atomic_write(path: str, data: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=os.path.dirname(path) or ".") as tmp:
        tmp.write(data)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_path = tmp.name
    os.replace(tmp_path, path)

def load() -> dict[str, float]:
    try:
        with open(REG_PATH) as f:
            return {k: float(v) for k, v in json.load(f).items()}
    except FileNotFoundError:
        return {}
    except Exception:
        return {}

def save(reg: dict[str, float]) -> None:
    _atomic_write(REG_PATH, json.dumps(reg, ensure_ascii=False, separators=(",", ":")))

def domain_of(url_or_domain: str) -> str:
    if "://" in url_or_domain:
        return urllib.parse.urlparse(url_or_domain).netloc.lower()
    return url_or_domain.lower()

def mark_seen(url_or_domain: str, ts: float | None = None) -> None:
    d = domain_of(url_or_domain)
    reg = load()
    reg[d] = float(ts or _now_ts())
    save(reg)

def last_seen(url_or_domain: str) -> float | None:
    d = domain_of(url_or_domain)
    return load().get(d)

def rank_domains(domains: Iterable[str]) -> list[tuple[str, float | None]]:
    """
    Return domains sorted by staleness (least recently seen first).
    Domains never seen appear first (None).
    """
    reg = load()
    items: list[tuple[str, float | None]] = []
    seen = set()
    for raw in domains:
        d = domain_of(raw)
        if d in seen:
            continue
        seen.add(d)
        items.append((d, reg.get(d)))
    # None (never seen) first, then older timestamps
    items.sort(key=lambda t: (t[1] is not None, t[1] or 0.0))
    return items
