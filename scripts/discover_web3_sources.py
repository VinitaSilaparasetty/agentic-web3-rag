import os
import re
import sys
import time
import urllib.parse

import requests
from bs4 import BeautifulSoup

from apps.common.compliance import policy_for_url, robots_allowed

REQ_TIMEOUT = float(os.getenv("DISCOVER_TIMEOUT", "15"))
MAX_PER_DOMAIN = int(os.getenv("MAX_URLS_PER_DOMAIN", "80"))
DEFAULT_SEEDS = [
    "https://ethereum.org/en/developers/docs/",
    "https://geth.ethereum.org/docs/",
    "https://docs.solana.com/",
    "https://docs.polygon.technology/",
    "https://docs.optimism.io/",
    "https://book.getfoundry.sh/",
    "https://docs.walletconnect.com/",
    "https://docs.ethers.org/",
    "https://web3py.readthedocs.io/en/stable/",
    "https://docs.alchemy.com/",
    "https://docs.infura.io/",
]

SEEN = set()
PER_DOMAIN = {}
DOC_HINT = re.compile(r"/(docs?|guide|reference|api|tutorial|learn)/", re.I)


def add(url):
    u = url.split("#", 1)[0]
    u = u.rstrip("/")
    if u in SEEN:
        return False
    host = urllib.parse.urlparse(u).netloc.lower()
    if PER_DOMAIN.get(host, 0) >= MAX_PER_DOMAIN:
        return False
    SEEN.add(u)
    PER_DOMAIN[host] = PER_DOMAIN.get(host, 0) + 1
    print(u)
    return True


def absolutize(base, link):
    try:
        return urllib.parse.urljoin(base, link)
    except Exception:
        return None


def fetch(url):
    try:
        r = requests.get(url, timeout=REQ_TIMEOUT, headers={"User-Agent": "web3-rag-discover/1.0"})
        if r.status_code != 200:
            return None
        ct = r.headers.get("content-type", "")
        if "text/html" not in ct:
            return None
        return r.text
    except Exception:
        return None


def from_html(url, html):
    soup = BeautifulSoup(html, "html.parser")
    # prefer canonical if present
    can = soup.find("link", rel="canonical")
    if can and can.get("href"):
        add(absolutize(url, can.get("href")))
    for a in soup.find_all("a", href=True):
        h = a["href"]
        if h.startswith("mailto:") or h.startswith("javascript:"):
            continue
        full = absolutize(url, h)
        if not full:
            continue
        if not DOC_HINT.search(full):  # light heuristic for docs-like paths
            continue
        add(full)


def try_sitemap(root):
    # naive attempt: /sitemap.xml, /sitemap_index.xml
    for path in ("/sitemap.xml", "/sitemap_index.xml"):
        sm = urllib.parse.urljoin(root, path)
        try:
            r = requests.get(
                sm, timeout=REQ_TIMEOUT, headers={"User-Agent": "web3-rag-discover/1.0"}
            )
            if r.status_code != 200:
                continue
            # very light parse (we avoid external libs): just find <loc>...</loc>
            locs = re.findall(r"<loc>(.*?)</loc>", r.text, flags=re.I)
            for loc in locs:
                if DOC_HINT.search(loc):
                    add(loc.strip())
        except Exception:
            pass


def allowed_by_policy(url):
    pol = policy_for_url(url)
    if not pol.allowed:
        return False
    if not robots_allowed(url):
        return False
    return True


def seeds_from_stdin_or_default():
    data = sys.stdin.read().strip().splitlines()
    return [d.strip() for d in data if d.strip()] or DEFAULT_SEEDS


def main():
    roots = seeds_from_stdin_or_default()
    for root in roots:
        if not allowed_by_policy(root):
            continue
        add(root)
        try_sitemap(root)
        html = fetch(root)
        if html:
            from_html(root, html)
        time.sleep(0.2)  # be polite
