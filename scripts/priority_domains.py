import sys

from apps.common.freshness import rank_domains

domains = [ln.strip() for ln in sys.stdin if ln.strip()]
for d, ts in rank_domains(domains):
    print(d)
