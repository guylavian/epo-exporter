policy_not_applied collector

Exports endpoints where effective policy is not applied as assigned.

Metrics

- epo_policy_not_applied_total{product,policy}

Saved Query required

- `EPO_Q_POLICY_NOT_APPLIED` — Managed Systems / Policy Effectiveness
  - Columns: `Product`, `Policy` (or `PolicyName`), `COUNT`
  - Filter: Effective Policy != Assigned Policy (or Last Policy Update < Policy Last Modified)

Example PromQL

- Top policies not applied: `topk(10, sum by (product, policy) (epo_policy_not_applied_total))`

