import sys, json, requests, bs4
from apps.common.compliance import policy_for_url, robots_allowed, trim_snippet
from apps.common.freshness import mark_seen

def fetch_title_and_text(url):
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    soup = bs4.BeautifulSoup(r.text, "html.parser")
    title = (soup.title.string if soup.title else url).strip()
    main = soup.get_text("\n")
    return title, main

def main():
    for line in sys.stdin:
        url = line.strip()
        if not url:
            continue
        pol = policy_for_url(url)
        if not pol.allowed or not robots_allowed(url):
            print(json.dumps({"url": url, "policy": pol.cache_policy, "note": "blocked by policy/robots"}, ensure_ascii=False))
            continue

        rec = {"url": url, "policy": pol.cache_policy, "license": pol.license}
        if pol.cache_policy == "link-only":
            try:
                title, _ = fetch_title_and_text(url)
            except Exception:
                title = url
            rec.update({"title": title, "snippet": None, "text": None})
        elif pol.cache_policy == "snippet":
            title, text = fetch_title_and_text(url)
            mark_seen(url)
            rec.update({"title": title, "snippet": trim_snippet(text, pol.snippet_chars), "text": None})
        else:  # fulltext
            title, text = fetch_title_and_text(url)
            rec.update({"title": title, "snippet": trim_snippet(text, pol.snippet_chars), "text": text})

        print(json.dumps(rec, ensure_ascii=False))
if __name__ == "__main__":
    main()
