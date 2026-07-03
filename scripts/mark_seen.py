import sys

from apps.common.freshness import mark_seen

for ln in sys.stdin:
    s = ln.strip()
    if s:
        mark_seen(s)
