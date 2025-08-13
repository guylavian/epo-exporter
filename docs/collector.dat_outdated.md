dat_outdated collector

Exports endpoints that have outdated DAT files per product.

Metrics

- epo_dat_outdated_total{product}

Saved Query required

- `EPO_Q_DAT_OUTDATED` — Product/Threat Properties
  - Columns: `Product` (or Analyzer/Product Name), `COUNT`
  - Filter: DAT Age > X days (or DAT Version < Latest)

Example PromQL

- Top products with outdated DAT: `topk(10, epo_dat_outdated_total)`

