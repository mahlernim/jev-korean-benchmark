# Stage 0 report

Planned 36. Successful 36. Failed 0. Pending 0.

Frozen manifest `3f1b6dafd569fb6ea382356b45148e185a98f0c62a50da3c60865224558a7d61`.

API call time 10.427 seconds. Recorded runner wall time 7.897 seconds. Attempts 36, retries 0. Input tokens 12,586, output tokens 1,044. Estimated successful-call cost $0.000529.

Per-call latency includes network and SDK decoding at concurrency one. Runner wall time also includes initialization, disk writes, retries and report generation, and excludes human gaps. The first ten development calls preceded invocation timing instrumentation, so Stage 0 wall time is incomplete. Token charges use published pricing, not an invoice.

Rounding-compatible distributions normalized for probability metrics: 0. Previously stopped local-validation records admitted by a preserved adjudication: 0. This is a disclosed analysis amendment after one five-option vector summed to 0.99 on a 0.01 grid. Original vectors and labels remain unchanged. See methodology for tolerance and sensitivity metrics.

Development checks only. These scores are not benchmark results.

| Task / condition | n | Accuracy (95% Wilson CI) | Brier | Log loss | Median / p95 ms | Cost USD |
|---|---:|---:|---:|---:|---:|---:|
| development_choice / en_en | 6 | 100.0% (61.0%–100.0%) | 0.0000 | 0.0000 | 247 / 674 | 0.000093 |
| development_choice / ko_en | 6 | 100.0% (61.0%–100.0%) | 0.0000 | 0.0000 | 237 / 577 | 0.000094 |
| development_choice / ko_ko | 6 | 100.0% (61.0%–100.0%) | 0.0000 | 0.0000 | 219 / 318 | 0.000100 |
| development_noul / en_en | 6 | 100.0% (61.0%–100.0%) | 0.0168 | 0.0698 | 226 / 352 | 0.000079 |
| development_noul / ko_en | 6 | 100.0% (61.0%–100.0%) | 0.0080 | 0.0505 | 281 / 506 | 0.000080 |
| development_noul / ko_ko | 6 | 100.0% (61.0%–100.0%) | 0.0147 | 0.0708 | 245 / 281 | 0.000083 |

Conditions name content language first, instruction language second. Brier is the sum across classes (range 0–2); log loss uses natural logarithms and clips zero gold probability to 1e-15. Metrics exclude API failures, which are counted above.

## Error versus coverage

| Task / condition | 50% | 75% | 100% |
|---|---:|---:|---:|
| development_choice/en_en | 0.0% (3 retained) | 0.0% (5 retained) | 0.0% (6 retained) |
| development_choice/ko_en | 0.0% (3 retained) | 0.0% (5 retained) | 0.0% (6 retained) |
| development_choice/ko_ko | 0.0% (3 retained) | 0.0% (5 retained) | 0.0% (6 retained) |
| development_noul/en_en | 0.0% (3 retained) | 0.0% (5 retained) | 0.0% (6 retained) |
| development_noul/ko_en | 0.0% (3 retained) | 0.0% (5 retained) | 0.0% (6 retained) |
| development_noul/ko_ko | 0.0% (3 retained) | 0.0% (5 retained) | 0.0% (6 retained) |

Coverage uses returned Choice confidence or absolute Noul distance from 0.5. Ties break by evaluation ID. These are descriptive rankings, not calibrated deployment thresholds.

## Paired differences

- development_choice, ko_en minus en_en: +0.0 percentage points, paired bootstrap 95% interval [+0.0, +0.0]. en_en-only correct 0; ko_en-only correct 0.
- development_choice, ko_ko minus ko_en: +0.0 percentage points, paired bootstrap 95% interval [+0.0, +0.0]. ko_en-only correct 0; ko_ko-only correct 0.
- development_noul, ko_en minus en_en: +0.0 percentage points, paired bootstrap 95% interval [+0.0, +0.0]. en_en-only correct 0; ko_en-only correct 0.
- development_noul, ko_ko minus ko_en: +0.0 percentage points, paired bootstrap 95% interval [+0.0, +0.0]. ko_en-only correct 0; ko_ko-only correct 0.

Small-sample intervals are exploratory. For authored minimal pairs, case-level bootstrap does not account for pair dependence.


## Highest-ranked errors

| Evaluation | Gold | Prediction | Ranking signal |
|---|---|---|---:|

There are 0 cases with different predictions across conditions. Full error and disagreement lists are in the adjacent JSON report. Disagreement alone does not establish a translation defect.
