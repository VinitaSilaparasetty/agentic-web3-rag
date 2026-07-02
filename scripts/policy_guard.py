import sys, json
from apps.common.compliance import policy_for_url, robots_allowed, trim_snippet

def main():
    url = sys.argv[1]
    pol = policy_for_url(url)
    rob = robots_allowed(url)
    print(json.dumps({
        "url": url,
        "allowed": pol.allowed and rob,
        "cache_policy": pol.cache_policy,
        "license": pol.license,
        "snippet_chars": pol.snippet_chars,
        "robots_allowed": rob,
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python scripts/policy_guard.py <url>", file=sys.stderr)
        sys.exit(1)
    main()
