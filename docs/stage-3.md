# Stage 3 report

Planned 120. Successful 120. Failed 0. Pending 0.

Frozen manifest `3f1b6dafd569fb6ea382356b45148e185a98f0c62a50da3c60865224558a7d61`.

API call time 27.545 seconds. Recorded runner wall time 29.741 seconds. Attempts 120, retries 0. Input tokens 45,015, output tokens 4,812. Estimated successful-call cost $0.001891.

Per-call latency includes network and SDK decoding at concurrency one. Runner wall time also includes initialization, disk writes, retries and report generation, and excludes human gaps. The first ten development calls preceded invocation timing instrumentation, so Stage 0 wall time is incomplete. Token charges use published pricing, not an invoice.

Rounding-compatible distributions normalized for probability metrics: 0. Previously stopped local-validation records admitted by a preserved adjudication: 0. This is a disclosed analysis amendment after one five-option vector summed to 0.99 on a 0.01 grid. Original vectors and labels remain unchanged. See methodology for tolerance and sensitivity metrics.

**Exploratory only. All 40 authored medical cases and translations await clinician review. Primary medical text score is unavailable.**

Intervals below treat items as independent and may be too narrow because minimal pairs are related. Category results have only eight cases.

| Task / condition | n | Accuracy (95% Wilson CI) | Brier | Log loss | Median / p95 ms | Cost USD |
|---|---:|---:|---:|---:|---:|---:|
| medical_text / en_en | 40 | 100.0% (91.2%–100.0%) | 0.0073 | 0.0201 | 211 / 272 | 0.000615 |
| medical_text / ko_en | 40 | 100.0% (91.2%–100.0%) | 0.0120 | 0.0266 | 221 / 271 | 0.000625 |
| medical_text / ko_ko | 40 | 100.0% (91.2%–100.0%) | 0.0004 | 0.0069 | 221 / 269 | 0.000651 |

Conditions name content language first, instruction language second. Brier is the sum across classes (range 0–2); log loss uses natural logarithms and clips zero gold probability to 1e-15. Metrics exclude API failures, which are counted above.

## Error versus coverage

| Task / condition | 50% | 75% | 100% |
|---|---:|---:|---:|
| medical_text/en_en | 0.0% (20 retained) | 0.0% (30 retained) | 0.0% (40 retained) |
| medical_text/ko_en | 0.0% (20 retained) | 0.0% (30 retained) | 0.0% (40 retained) |
| medical_text/ko_ko | 0.0% (20 retained) | 0.0% (30 retained) | 0.0% (40 retained) |

Coverage uses returned Choice confidence or absolute Noul distance from 0.5. Ties break by evaluation ID. These are descriptive rankings, not calibrated deployment thresholds.

## Paired differences

- medical_text, ko_en minus en_en: +0.0 percentage points, paired bootstrap 95% interval [+0.0, +0.0]. en_en-only correct 0; ko_en-only correct 0.
- medical_text, ko_ko minus ko_en: +0.0 percentage points, paired bootstrap 95% interval [+0.0, +0.0]. ko_en-only correct 0; ko_ko-only correct 0.

Small-sample intervals are exploratory. For authored minimal pairs, case-level bootstrap does not account for pair dependence.

## Exploratory categories

| Category / condition | Correct / n |
|---|---:|
| evidence/en_en | 8 / 8 |
| evidence/ko_en | 8 / 8 |
| evidence/ko_ko | 8 / 8 |
| experiencer/en_en | 8 / 8 |
| experiencer/ko_en | 8 / 8 |
| experiencer/ko_ko | 8 / 8 |
| medication/en_en | 8 / 8 |
| medication/ko_en | 8 / 8 |
| medication/ko_ko | 8 / 8 |
| negation/en_en | 8 / 8 |
| negation/ko_en | 8 / 8 |
| negation/ko_ko | 8 / 8 |
| temporality/en_en | 8 / 8 |
| temporality/ko_en | 8 / 8 |
| temporality/ko_ko | 8 / 8 |

## Highest-ranked errors

| Evaluation | Gold | Prediction | Ranking signal |
|---|---|---|---:|

There are 0 cases with different predictions across conditions. Full error and disagreement lists are in the adjacent JSON report. Disagreement alone does not establish a translation defect.
