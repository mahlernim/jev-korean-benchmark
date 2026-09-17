# Stage 2 report

Planned 200. Successful 200. Failed 0. Pending 0.

Frozen manifest `3f1b6dafd569fb6ea382356b45148e185a98f0c62a50da3c60865224558a7d61`.

API call time 65.402 seconds. Recorded runner wall time 70.831 seconds. Attempts 201, retries 1. Input tokens 107,150, output tokens 10,400. Estimated successful-call cost $0.004500.

Per-call latency includes network and SDK decoding at concurrency one. Runner wall time also includes initialization, disk writes, retries and report generation, and excludes human gaps. The first ten development calls preceded invocation timing instrumentation, so Stage 0 wall time is incomplete. Token charges use published pricing, not an invoice.

Rounding-compatible distributions normalized for probability metrics: 3. Previously stopped local-validation records admitted by a preserved adjudication: 1. This is a disclosed analysis amendment after one five-option vector summed to 0.99 on a 0.01 grid. Original vectors and labels remain unchanged. See methodology for tolerance and sensitivity metrics.

Korean medical exam knowledge, not a paired language comparison or evidence of clinical readiness. Historical official gold answers are scored as provided. Conservative media screening changes the test population.

| Task / condition | n | Accuracy (95% Wilson CI) | Brier | Log loss | Median / p95 ms | Cost USD |
|---|---:|---:|---:|---:|---:|---:|
| kormed / ko_en | 100 | 82.0% (73.3%–88.3%) | 0.2543 | 0.4544 | 223 / 315 | 0.002221 |
| kormed / ko_ko | 100 | 80.0% (71.1%–86.7%) | 0.2553 | 0.4562 | 219 / 254 | 0.002280 |

Conditions name content language first, instruction language second. Brier is the sum across classes (range 0–2); log loss uses natural logarithms and clips zero gold probability to 1e-15. Metrics exclude API failures, which are counted above.

## Error versus coverage

| Task / condition | 50% | 75% | 100% |
|---|---:|---:|---:|
| kormed/ko_en | 2.0% (50 retained) | 6.7% (75 retained) | 18.0% (100 retained) |
| kormed/ko_ko | 2.0% (50 retained) | 6.7% (75 retained) | 20.0% (100 retained) |

Coverage uses returned Choice confidence or absolute Noul distance from 0.5. Ties break by evaluation ID. These are descriptive rankings, not calibrated deployment thresholds.

## Paired differences

- kormed, ko_ko minus ko_en: -2.0 percentage points, paired bootstrap 95% interval [-5.0, +0.0]. ko_en-only correct 2; ko_ko-only correct 0.

Small-sample intervals are exploratory. For authored minimal pairs, case-level bootstrap does not account for pair dependence.


## Highest-ranked errors

| Evaluation | Gold | Prediction | Ranking signal |
|---|---|---|---:|
| kormed-2024-1-74__ko_ko | 1 | 4 | 0.9300 |
| kormed-2024-1-74__ko_en | 1 | 4 | 0.9000 |
| kormed-2022-1-36__ko_ko | 3 | 5 | 0.8500 |
| kormed-2022-1-18__ko_en | 3 | 1 | 0.8100 |
| kormed-2022-1-18__ko_ko | 3 | 1 | 0.7700 |
| kormed-2022-1-36__ko_en | 3 | 5 | 0.7700 |
| kormed-2023-3-32__ko_ko | 5 | 4 | 0.6700 |
| kormed-2023-1-14__ko_en | 5 | 4 | 0.6500 |
| kormed-2023-1-79__ko_ko | 3 | 4 | 0.6400 |
| kormed-2023-1-79__ko_en | 3 | 4 | 0.6200 |
| kormed-2023-3-32__ko_en | 5 | 4 | 0.6200 |
| kormed-2024-1-25__ko_en | 1 | 5 | 0.6100 |
| kormed-2023-1-14__ko_ko | 5 | 4 | 0.6000 |
| kormed-2022-1-12__ko_en | 2 | 5 | 0.5700 |
| kormed-2022-1-12__ko_ko | 2 | 5 | 0.5600 |
| kormed-2024-1-32__ko_ko | 1 | 2 | 0.5500 |
| kormed-2022-3-71__ko_ko | 3 | 1 | 0.5400 |
| kormed-2024-1-32__ko_en | 1 | 2 | 0.5200 |
| kormed-2023-1-13__ko_en | 4 | 5 | 0.5100 |
| kormed-2023-1-13__ko_ko | 4 | 5 | 0.4900 |

There are 3 cases with different predictions across conditions. Full error and disagreement lists are in the adjacent JSON report. Disagreement alone does not establish a translation defect.
