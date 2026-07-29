from __future__ import annotations

from collections import Counter
from typing import Any

from tools._shared import domain


def audit_sources(
    items: list[dict[str, Any]] | None = None,
    min_sources: int = 2,
    min_domains: int = 2,
) -> dict[str, Any]:
    items = items or []
    domains = [domain(item.get("url", "")) for item in items]
    domains = [value for value in domains if value]
    missing_urls = [index for index, item in enumerate(items, 1) if not item.get("url")]
    source_ok = len(items) >= max(1, int(min_sources))
    diversity_ok = len(set(domains)) >= max(1, int(min_domains))
    recommendations = []
    if not source_ok:
        recommendations.append("Collect more sources.")
    if not diversity_ok:
        recommendations.append("Add sources from more independent domains.")
    if missing_urls:
        recommendations.append("Add URLs for every source.")
    return {
        "tool": "source_audit",
        "status": "sufficient" if source_ok and diversity_ok and not missing_urls else "needs_more_sources",
        "item_count": len(items),
        "unique_domain_count": len(set(domains)),
        "domains": dict(Counter(domains)),
        "missing_url_indexes": missing_urls,
        "recommendations": recommendations,
    }
