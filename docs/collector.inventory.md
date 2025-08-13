inventory collector

Exports inventory snapshot metrics.

Metrics

- epo_managed_systems_count
- epo_policies_count
- epo_tags_count_total

Saved Queries: none required (uses `system.find`, `policy.find`, `system.listTags`).

Expected fields

- `policy.find`: list or object with `policies`/`policyList` array.
- `system.listTags`: list or object with `tags`/`tagList` array.

Example PromQL

- Total managed systems: `epo_managed_systems_count`
- Total policies: `epo_policies_count`

