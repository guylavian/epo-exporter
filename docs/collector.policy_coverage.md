policy_coverage collector

Exports assigned endpoints per policy.

Metrics

- epo_policy_assigned_systems{product,policy}

Saved Query required

- `EPO_Q_POLICY_ASSIGNMENTS`

Expected columns

- `Product`
- `Policy` or `PolicyName`
- `COUNT`

Example PromQL

- Total endpoints per policy: `sum by (product, policy) (epo_policy_assigned_systems)`

