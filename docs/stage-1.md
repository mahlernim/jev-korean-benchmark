# Stage 1 report

Planned 600. Successful 600. Failed 0. Pending 0.

Frozen manifest `3f1b6dafd569fb6ea382356b45148e185a98f0c62a50da3c60865224558a7d61`.

API call time 140.813 seconds. Recorded runner wall time 147.865 seconds. Attempts 600, retries 0. Input tokens 286,838, output tokens 19,500. Estimated successful-call cost $0.012047.

Per-call latency includes network and SDK decoding at concurrency one. Runner wall time also includes initialization, disk writes, retries and report generation, and excludes human gaps. The first ten development calls preceded invocation timing instrumentation, so Stage 0 wall time is incomplete. Token charges use published pricing, not an invoice.

Rounding-compatible distributions normalized for probability metrics: 0. Previously stopped local-validation records admitted by a preserved adjudication: 0. This is a disclosed analysis amendment after one five-option vector summed to 0.99 on a 0.01 grid. Original vectors and labels remain unchanged. See methodology for tolerance and sensitivity metrics.

| Task / condition | n | Accuracy (95% Wilson CI) | Brier | Log loss | Median / p95 ms | Cost USD |
|---|---:|---:|---:|---:|---:|---:|
| belebele / en_en | 100 | 97.0% (91.5%–99.0%) | 0.0286 | 0.0445 | 217 / 299 | 0.002115 |
| belebele / ko_en | 100 | 95.0% (88.8%–97.8%) | 0.0613 | 0.1176 | 221 / 279 | 0.002503 |
| belebele / ko_ko | 100 | 96.0% (90.2%–98.4%) | 0.0515 | 0.1008 | 221 / 316 | 0.002583 |
| pawsx / en_en | 100 | 80.0% (71.1%–86.7%) | 0.2710 | 0.4051 | 226 / 326 | 0.001505 |
| pawsx / ko_en | 100 | 75.0% (65.7%–82.5%) | 0.3366 | 0.4982 | 225 / 295 | 0.001643 |
| pawsx / ko_ko | 100 | 76.0% (66.8%–83.3%) | 0.3318 | 0.4936 | 224 / 293 | 0.001698 |

Conditions name content language first, instruction language second. Brier is the sum across classes (range 0–2); log loss uses natural logarithms and clips zero gold probability to 1e-15. Metrics exclude API failures, which are counted above.

## Error versus coverage

| Task / condition | 50% | 75% | 100% |
|---|---:|---:|---:|
| belebele/en_en | 0.0% (50 retained) | 0.0% (75 retained) | 3.0% (100 retained) |
| belebele/ko_en | 0.0% (50 retained) | 0.0% (75 retained) | 5.0% (100 retained) |
| belebele/ko_ko | 0.0% (50 retained) | 0.0% (75 retained) | 4.0% (100 retained) |
| pawsx/en_en | 2.0% (50 retained) | 12.0% (75 retained) | 20.0% (100 retained) |
| pawsx/ko_en | 12.0% (50 retained) | 20.0% (75 retained) | 25.0% (100 retained) |
| pawsx/ko_ko | 12.0% (50 retained) | 18.7% (75 retained) | 24.0% (100 retained) |

Coverage uses returned Choice confidence or absolute Noul distance from 0.5. Ties break by evaluation ID. These are descriptive rankings, not calibrated deployment thresholds.

## Paired differences

- belebele, ko_en minus en_en: -2.0 percentage points, paired bootstrap 95% interval [-5.0, +0.0]. en_en-only correct 2; ko_en-only correct 0.
- belebele, ko_ko minus ko_en: +1.0 percentage points, paired bootstrap 95% interval [+0.0, +3.0]. ko_en-only correct 0; ko_ko-only correct 1.
- pawsx, ko_en minus en_en: -5.0 percentage points, paired bootstrap 95% interval [-14.0, +4.0]. en_en-only correct 13; ko_en-only correct 8.
- pawsx, ko_ko minus ko_en: +1.0 percentage points, paired bootstrap 95% interval [+0.0, +3.0]. ko_en-only correct 0; ko_ko-only correct 1.

Small-sample intervals are exploratory. For authored minimal pairs, case-level bootstrap does not account for pair dependence.


## Highest-ranked errors

| Evaluation | Gold | Prediction | Ranking signal |
|---|---|---|---:|
| belebele-66c76c721a3e9d34__ko_en | 4 | 2 | 0.6400 |
| belebele-f0b7aadb4f3e56ed__ko_en | 1 | 4 | 0.5600 |
| belebele-bb42edc717241afa__en_en | 1 | 4 | 0.5600 |
| belebele-ebf426ae131cdeff__en_en | 2 | 4 | 0.4800 |
| belebele-ebf426ae131cdeff__ko_en | 2 | 4 | 0.4600 |
| pawsx-6016__ko_en | 0 | 1 | 0.4600 |
| pawsx-6016__ko_ko | 0 | 1 | 0.4600 |
| belebele-f0b7aadb4f3e56ed__ko_ko | 1 | 4 | 0.4500 |
| pawsx-4966__ko_en | 1 | 0 | 0.4400 |
| pawsx-4966__ko_ko | 1 | 0 | 0.4400 |
| pawsx-1516__en_en | 0 | 1 | 0.4300 |
| belebele-c389cd7dfb2c53d7__en_en | 1 | 2 | 0.4300 |
| belebele-bb42edc717241afa__ko_en | 1 | 2 | 0.4300 |
| pawsx-6516__en_en | 0 | 1 | 0.4200 |
| belebele-bb42edc717241afa__ko_ko | 1 | 2 | 0.4200 |
| pawsx-6016__en_en | 0 | 1 | 0.4100 |
| pawsx-3507__en_en | 0 | 1 | 0.4100 |
| pawsx-4716__en_en | 1 | 0 | 0.4000 |
| pawsx-7715__ko_ko | 1 | 0 | 0.3900 |
| pawsx-3289__ko_en | 0 | 1 | 0.3800 |

There are 25 cases with different predictions across conditions. Full error and disagreement lists are in the adjacent JSON report. Disagreement alone does not establish a translation defect.
