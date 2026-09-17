# Jev Korean and medical evaluation

A small, reproducible early-access evaluation of TypeSafe Jev. English reporting with a Korean supplement. The experiment measures general Korean understanding, Korean medical examination knowledge, and exploratory interpretation of synthetic medical notes separately.

The scored public tasks use 100 Belebele questions, 100 PAWS-X pairs and 100 KorMedMCQA doctor questions. There are 36 development calls, 120 exploratory synthetic medical calls and 80 robustness calls, for 1,036 planned calls overall. These are repeated conditions on 340 scored source cases, not 1,036 independent questions.

## Read the findings

### Results at a glance

| Task | Cases | English / English | Korean / English | Korean / Korean |
|---|---:|---:|---:|---:|
| Belebele reading | 100 | 97% | 95% | 96% |
| PAWS-X equivalence | 100 | 80% | 75% | 76% |
| KorMedMCQA doctor examination | 100 | Not tested | 82% | 80% |

Conditions denote content / instruction language. No overall score is pooled. The medical examination has no matched English arm. Synthetic medical probes achieved 40/40 in each condition but remain unreviewed and are excluded from the primary medical score.

![Task-specific accuracy with 95% Wilson intervals](docs/figures/accuracy.png)

**Figure 1.** Points are observed accuracy and bars are 95% Wilson intervals, with 100 cases per point. Conditions reuse the same cases, so interval overlap is not a test of paired differences. Missing English medical results were not evaluated.

![Paired content and instruction language differences](docs/figures/paired-differences.png)

**Figure 2.** Paired differences with 95% percentile bootstrap intervals, 4,000 resamples and seed 20260917. Content effects hold English instructions fixed. Instruction effects hold Korean content fixed. Positive values favor Korean. These small-sample, unadjusted intervals are descriptive and do not establish equivalence.

![Error versus coverage and client latency distributions](docs/figures/coverage-latency.png)

**Figure 3.** Korean-instruction conditions, 100 cases per task. Left, observed error at three prespecified coverage levels, with connecting lines as visual guides. Cases are ranked by Choice confidence or Noul distance from 0.5, with ties broken by evaluation ID. Right, empirical cumulative distributions of successful-call latency on a logarithmic axis. Network and SDK decoding are included. Failed attempts and development calls are excluded from this panel.

Across the whole pilot, estimated API cost was **$0.02056**, summed API attempt duration **262 seconds**, and successful-call median / p95 latency **221 / 306 ms**. Cost is based on reported usage, not an invoice. Total runner timing omits the first ten development calls. Reversing sentence order changed 3/5 PAWS-X predictions in a small prespecified robustness subset, which does not estimate a population flip rate.

Download [vector figures and PDFs](docs/figures/). Rebuild figures without API calls using `python -m jevbench.figures`. Detailed methods, probability-normalization amendment, exclusions, metrics and individual errors are linked below.

- [Existing Jev comparisons and proposed Luna-none extension](docs/comparison-design.md)

- [Live web report](https://ahn-lab.org/jev-korean-benchmark/)
- [English report](docs/report.md)
- [Korean supplement](docs/korean-supplement.md)
- [Methodology](docs/methodology.md)
- [Recorded outputs and frozen source metadata](results/)

## Install

Tested with Python 3.14.2 on Windows. Python 3.10 or newer is required by the SDK. Offline analysis and preparation are portable. Live runs currently use a Windows advisory process lock.

```powershell
uv venv .venv
uv pip install --python .venv/Scripts/python.exe -r requirements.txt
.venv/Scripts/python.exe -X utf8 -m pytest -q
```

For live calls, put a `TYPESAFE_API_KEY` or `TYPESAFE_KEY` assignment in local `typesafe.env`. This file is ignored by Git. Never commit credentials. The live runner reads this file directly, disables SDK retries, and implements two logged retries of transient failures itself.

## Commands

```powershell
# Download pinned sources and reconstruct the exact manifest. No API calls.
.venv/Scripts/python.exe -X utf8 -m jevbench prepare

# Import the published responses and reproduce reports. No model calls.
.venv/Scripts/python.exe -X utf8 -m jevbench restore
.venv/Scripts/python.exe -X utf8 -m jevbench report

# Make a NEW experiment for new inference; never overwrite the recorded pilot.
.venv/Scripts/python.exe -X utf8 -m jevbench prepare --experiment replication-01 --model jev-1.13.0
.venv/Scripts/python.exe -X utf8 -m jevbench run --experiment replication-01 --stage 0
.venv/Scripts/python.exe -X utf8 -m jevbench run --experiment replication-01 --stage 1
```

Before Stage 2, inspect the generated `medical_input_audit.md` and record a `medical_input_review.json` alongside the manifest. It must contain the manifest's SHA-256 in `manifest_hash`, `all_selected_text_complete: true`, the reviewer, date, scope and any caveats. This is an input-completeness audit, not a clinical correctness endorsement. Do not mark it complete without checking all selected inputs.

```powershell
.venv/Scripts/python.exe -X utf8 -m jevbench run --experiment replication-01 --stage 2
.venv/Scripts/python.exe -X utf8 -m jevbench run --experiment replication-01 --stage 3
.venv/Scripts/python.exe -X utf8 -m jevbench run --experiment replication-01 --stage 4
.venv/Scripts/python.exe -X utf8 -m jevbench report --experiment replication-01
```

Successful or terminally failed evaluations are never called again by resume. An intent without a corresponding outcome is treated as uncertain and stops the runner. Fatal validation/API failures require inspection and a new experiment. The published-price budget ceiling is $0.25 per experiment and is conservative for failed calls; it is not an account-side spending limit.

The 40 authored medical cases have not been reviewed by a clinician. Their proposed labels and translations are available in the generated review packet and [source file](jevbench/synthetic.py). They must not be presented as a validated clinical benchmark. Preserve the original results when adding review or correcting cases.

## Provenance and licensing

- Belebele, Bandarkar et al., ACL 2024. [Repository](https://github.com/facebookresearch/belebele). CC BY-SA 4.0.
- PAWS-X, Yang et al., EMNLP 2019. [Repository](https://github.com/google-research-datasets/paws/tree/master/pawsx). Consult the upstream Google PAWS license.
- KorMedMCQA, Kweon et al., 2024. [Dataset](https://huggingface.co/datasets/sean0042/KorMedMCQA). CC BY-NC 2.0.

This repository distributes code, experiment metadata and model outputs. Public benchmark passage/question text is retrieved from upstream sources during preparation and is not bundled in the published results. Source dataset licenses continue to apply to downloaded inputs. Historical exam gold answers are not updated to current medical or legal guidance.

The service was accessed through an early-access account. Model version, access date and measured token charges are disclosed in the report. Public benchmark training exposure is unknown. No other model was run in this pilot, and no speed or accuracy superiority over other models is claimed.
