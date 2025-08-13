policy_mismatch collector

Exports counts for stale/uneffective policies and overdue agents.

Metrics

- epo_policy_mismatch_total{product,policy}
- epo_agents_overdue_total

Saved Query required

- `EPO_Q_MANAGED_SYSTEMS_COMM` — returns per-endpoint product/policy, last communication, last policy update.

Expected columns

- `Product`
- `Policy` or `PolicyName`
- `LastCommunication` (epoch or ISO)
- `LastPolicyUpdate` (epoch or ISO)

Logic

- Overdue if now − LastCommunication > ASCI_MINUTES × 60 × ASCI_OVERDUE_MULTIPLIER
- Mismatch if LastPolicyUpdate < LastCommunication − 1

Example PromQL

- Top mismatches: `topk(10, sum by (product, policy) (epo_policy_mismatch_total))`
- Overdue trend: `rate(epo_agents_overdue_total[5m])`

