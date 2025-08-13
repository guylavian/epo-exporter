product_gap collector

Exports installed vs reporting endpoints per product and gap.

Metrics

- epo_product_installed_endpoints{product}
- epo_product_reporting_endpoints{product}
- epo_product_gap{product} = installed - reporting

Saved Queries required

- `EPO_Q_INSTALLED_BY_PRODUCT`: returns per-product installed endpoints (COUNT)
- `EPO_Q_REPORTING_ENDPOINTS_BY_PRODUCT`: returns per-product distinct systems reporting (COUNT or DistinctSystems)

Expected columns

- Installed: `Product` or `ProductName`, and `COUNT`
- Reporting: `AnalyzerName` or `analyzerName`, and `DistinctSystems` or `COUNT`

Cardinality notes

- Ensure product names are bounded; consider allow-listing or documenting the cardinality risk.

Example PromQL

- Gap per product: `epo_product_gap`
- Largest gaps: `topk(10, epo_product_gap)`

