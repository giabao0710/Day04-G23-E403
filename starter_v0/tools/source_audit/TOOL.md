---
name: source_audit
track: team
kind: local_analysis
requires_env: []
inputs: [items, min_sources, min_domains]
outputs: [status, item_count, unique_domain_count, domains, missing_url_indexes, recommendations]
side_effect: false
---
# source_audit

Checks whether already-collected research items meet minimum source-count, URL, and domain-diversity requirements. It does not search, fetch, or judge whether a claim is true.
