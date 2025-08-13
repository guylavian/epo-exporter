product_events collector

Exports event counts by product in a Saved Query time window.

Metrics

- epo_events_total{product}

Saved Query required

- `EPO_Q_EVENTS_BY_PRODUCT` (Saved Query ID)
  - Group by `AnalyzerName`
  - Aggregate `COUNT(*)`
  - Time filter (your desired window)

Expected columns

- `AnalyzerName` (or `analyzerName` or `attributes.AnalyzerName`)
- `COUNT` (or `count` or `Total`)

Example PromQL

- Top 5 products by events: `topk(5, sum by (product) (epo_events_total))`

