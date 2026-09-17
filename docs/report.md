# An early look at Jev on Korean and medical text

## A small early-access pilot

We evaluated TypeSafe **jev-1.13.0** on September 17, 2026, using 1,036 planned evaluations and 1,037 sequential API attempts including retries. The study compares English and Korean reading comprehension and paraphrase decisions, tests Korean medical examination knowledge, and separately explores simple synthetic medical-note interpretation.

On 100 matched questions, Belebele accuracy was **97% in English and 96% in Korean with Korean instructions**. On 100 matched PAWS-X pairs, the corresponding values were **80% and 76%**. Korean medical examination accuracy was **80%** on a screened 100-question doctor subset.

The analysis contains 1,036 scored responses after the disclosed probability-rounding amendment. The total token-based cost estimate was **$0.02056 USD**, and summed client-observed API call time was **262.0 seconds**. These measurements describe this service, account, workload and run. No other model was evaluated, so this report makes no comparative speed or cost claim.

The central finding is task dependence. Good reading-comprehension performance does not establish equally strong semantic discrimination, medical competence, or dependable confidence estimates. The small sample and unknown training exposure limit generalization.

[Korean supplement](korean-supplement.html) · [Detailed methodology](methodology.html) · [Download recorded results](results.zip)

A small robustness check also found that reversing sentence order changed 3/5 paraphrase predictions. This observation is more actionable than interpreting a one-point instruction-language difference as a general advantage.

## Experiment design

The sample, labels, prompts and 20 robustness cases were frozen before inference. Jev received one question per request and no tools, retrieval or generated rationale. Choice handled multiple-choice questions; Noul returned a yes/no equivalence probability. This evaluates an observable decision task without requiring Jev to behave like a chat model.

| Component | Source cases | Conditions / calls |
|---|---:|---:|
| Development only | 12 | 3 / 36 |
| Belebele reading comprehension | 100 | 3 / 300 |
| PAWS-X paraphrase identification | 100 | 3 / 300 |
| KorMedMCQA doctor questions | 100 | 2 / 200 |
| Synthetic medical notes, unreviewed | 40 | 3 / 120 |
| Robustness | 20 reused cases | 4 extra / 80 |

There are 340 scored source cases, plus 12 development cases. The 1,036 calls are not independent questions. Synthetic medical examples include related minimal pairs.

## General language understanding

EN/EN means English content and instructions. KO/EN means Korean content with English instructions. KO/KO means Korean content and instructions. Public answer-option text follows content language.

| Task | Condition | Correct / 100 | Accuracy, 95% Wilson interval | Brier | Log loss |
|---|---|---:|---:|---:|---:|
| belebele | EN/EN | 97 | 97%, 91.5%–99.0% | 0.029 | 0.044 |
| belebele | KO/EN | 95 | 95%, 88.8%–97.8% | 0.061 | 0.118 |
| belebele | KO/KO | 96 | 96%, 90.2%–98.4% | 0.052 | 0.101 |
| pawsx | EN/EN | 80 | 80%, 71.1%–86.7% | 0.271 | 0.405 |
| pawsx | KO/EN | 75 | 75%, 65.7%–82.5% | 0.337 | 0.498 |
| pawsx | KO/KO | 76 | 76%, 66.8%–83.3% | 0.332 | 0.494 |

The English-to-Korean comparison holds the underlying item fixed, using existing translations. Switching instruction language is a separate comparison. A one-point difference here is just one answer and should not be interpreted as evidence that one prompt language is generally better.

| Paired comparison | Difference in percentage points | 95% paired bootstrap interval |
|---|---:|---:|
| belebele/ko_en-en_en | -2.0 | -5.0 to +0.0 |
| belebele/ko_ko-ko_en | +1.0 | +0.0 to +3.0 |
| pawsx/ko_en-en_en | -5.0 | -14.0 to +4.0 |
| pawsx/ko_ko-ko_en | +1.0 | +0.0 to +3.0 |

Bootstrap intervals are descriptive and can have boundary artifacts when there are very few discordant pairs. This pilot is not powered for small language differences, and no multiple-comparison-adjusted claims are made.

## Medical knowledge

The KorMedMCQA doctor sample uses original Korean examination questions and historical gold labels. It has no matched English translation, so its errors cannot be assigned specifically to Korean language understanding.

| Instructions | Correct / 100 | Accuracy, 95% Wilson interval | Brier | Log loss |
|---|---:|---:|---:|---:|
| ko_en | 82 | 82%, 73.3%–88.3% | 0.254 | 0.454 |
| ko_ko | 80 | 80%, 71.1%–86.7% | 0.255 | 0.456 |

The pinned doctor test split has 435 questions. A conservative text screen retained 259 candidates, from which 35, 33 and 32 were sampled from 2022, 2023 and 2024 respectively. The selected inputs were inspected for missing media dependencies. The screen also excludes some potentially usable text questions, so this is a selected subset rather than an official full-benchmark score.

The sample includes clinical, public-health, ethics and medical-law questions. Excluding media-dependent items can shift the subject mix away from image-heavy clinical questions. Historical answers are evaluated as provided, not reinterpreted as current clinical or legal recommendations.

## Exploratory medical-note interpretation

Forty synthetic bilingual cases cover negation, time, patient versus family history, medication status, and support for a claim. All answers are intended to follow from the supplied note. The cases and translations were AI-authored before inference and **have not received clinician review**. These results are excluded from primary medical scoring.

| Condition | Correct / 40 | Exploratory accuracy |
|---|---:|---:|
| en_en | 40 | 100.0% |
| ko_en | 40 | 100.0% |
| ko_ko | 40 | 100.0% |

These are short, deliberately simple probes, not representative clinical records. They do not test diagnosis, treatment safety, long-note processing, or real patient workflows. The [case review packet](clinician-review.html) exposes every proposed label and translation for review.

## Does uncertainty identify mistakes?

We ranked Choice answers by returned confidence and Noul answers by distance from 0.5. The table shows errors among the retained fraction, not the fraction of errors removed.

| Task, Korean instructions | 50% retained | 75% retained | All retained |
|---|---:|---:|---:|
| belebele | 0.0% | 0.0% | 4.0% |
| pawsx | 12.0% | 18.7% | 24.0% |
| kormed | 2.0% | 6.7% | 20.0% |

Returned confidence summarizes a distribution and is not itself measured correctness probability. Noul has no separate confidence field. Brier scores and log loss evaluate the actual returned probabilities against labels. No thresholds were tuned on these test results.

The initial strict sum-to-one validator stopped on one five-option vector summing to 0.99. We preserved that event and amended the analysis to allow only bounded rounding-compatible vectors, normalizing them for probability metrics. The [methodology amendment](methodology.html#probability-validation-amendment) documents the rule and timing. This is consistent with observed two-decimal precision, but server rounding has not been independently confirmed.

Three primary medical distributions and one robustness distribution needed normalization. For the medical groups, normalization changed mean Brier score by less than 0.0001 and mean log loss by less than 0.00021. Accuracy and confidence-based coverage were unchanged. Raw-vector sensitivity metrics are included in the downloadable JSON.

## Runtime and cost

The resolved model was `jev-1.13.0` throughout. The requested alias was `jev-latest`. Requests ran sequentially through Python SDK 0.6.0 on Windows, with a 30-second timeout and at most two logged retries for transient failures.

| Stage | Calls | API call seconds | Recorded runner seconds | Input tokens | Output tokens | Estimated USD |
|---|---:|---:|---:|---:|---:|---:|
| 0 | 36 | 10.427 | 7.897 | 12,586 | 1,044 | 0.000529 |
| 1 | 600 | 140.813 | 147.865 | 286,838 | 19,500 | 0.012047 |
| 2 | 201 | 65.402 | 70.831 | 107,150 | 10,400 | 0.004500 |
| 3 | 120 | 27.545 | 29.741 | 45,015 | 4,812 | 0.001891 |
| 4 | 80 | 17.842 | 19.335 | 38,000 | 3,164 | 0.001596 |

Across successful responses, median client latency was 221 ms and p95 was 306 ms. Summed API duration, including failed attempts, was 262.029 seconds. Recorded runner invocation time was 275.669 seconds, but it omits the first ten development calls because wall-time instrumentation was added afterward. Complete per-request timing exists for all attempts. Dataset preparation, coding, review and human gaps are excluded from these execution-time figures.

Transient failed attempts: 1. Retry attempts: 1. Failed attempts without reported token usage are excluded from the observed token-cost estimate; the conservative local budget ledger reserves $0.020678 including those attempts. A local validation stop was resolved without repeating its request.

Latency is measured around the synchronous SDK call and includes network travel and decoding. It is not server compute time. Client geography was not measured; the workspace timezone was Asia/Seoul. Runs were not randomized by condition order, and no concurrency sweep was performed.

Cost is calculated from reported input tokens at the September 17, 2026 published rate of $0.042 per million input tokens; output tokens were advertised as free. It is a usage estimate rather than a billing invoice, and excludes minimum purchases or account credits. [TypeSafe pricing statement](https://typesafe.ai/blog/introducing-system-one-models-and-jev).

For future model comparisons, use these same source IDs, conditions and answer choices; keep concurrency and latency boundaries identical; disclose token pricing and reasoning settings separately. Do not compare self-reported LLM confidence directly with Jev's distribution-derived confidence.

## Robustness

**Sentence-order sensitivity was visible even in this small check.** Reversing the two sentences changed 3 of 5 PAWS-X predictions relative to the base condition. The same cases flipped in both reversed runs. Semantic equivalence is symmetric, so this is a useful failure mode to investigate on a larger held-out set. It is not an estimate of the population-wide flip rate.
Five cases from each scored task were selected before viewing results. Each Korean-instruction condition was repeated twice and tested with two option-order rotations. PAWS-X instead reversed sentence order twice. Option IDs remained attached to their original meanings.

| Task / variant | Calls | Answer flips from base | Mean probability total variation |
|---|---:|---:|---:|
| belebele/repeat1 | 5 | 1 | 0.0200 |
| belebele/repeat2 | 5 | 0 | 0.0040 |
| belebele/variant1 | 5 | 0 | 0.0420 |
| belebele/variant2 | 5 | 0 | 0.0376 |
| kormed/repeat1 | 5 | 0 | 0.0200 |
| kormed/repeat2 | 5 | 0 | 0.0140 |
| kormed/variant1 | 5 | 0 | 0.0600 |
| kormed/variant2 | 5 | 0 | 0.0820 |
| medical_text/repeat1 | 5 | 0 | 0.0020 |
| medical_text/repeat2 | 5 | 0 | 0.0020 |
| medical_text/variant1 | 5 | 0 | 0.0040 |
| medical_text/variant2 | 5 | 0 | 0.0040 |
| pawsx/repeat1 | 5 | 0 | 0.0220 |
| pawsx/repeat2 | 5 | 0 | 0.0220 |
| pawsx/variant1 | 5 | 3 | 0.2420 |
| pawsx/variant2 | 5 | 3 | 0.2420 |

This small check probes repeated predictions and option ordering. It does not establish general determinism or robustness to other paraphrases.

## Limitations and disclosure

- This is a convenience-scale early-access pilot, not a leaderboard or clinical validation study. The model can change after this run.
- Public benchmark training exposure is unknown. Strong scores could partly reflect familiarity with public items.
- Translated paired benchmarks can contain translation artifacts. Disagreements identify cases to inspect, not proof of mistranslation.
- Medical question screening changes the target population. Original source typographical errors and historical labels were preserved.
- Synthetic medical labels and English equivalents are unreviewed. Perfect performance, if observed, would not establish clinical reliability.
- Repeated conditions and minimal pairs are dependent. No overall accuracy is pooled across tasks.
- The run used an early-access account. No third-party model baseline was run. This is a technical pilot report, not a peer-reviewed study.
- Code and English/Korean drafts were prepared with AI assistance. Benchmark answers were scored deterministically against frozen labels.

## Reproducibility and corrections

The original manifest hash is `3f1b6dafd569fb6ea382356b45148e185a98f0c62a50da3c60865224558a7d61`. The repository includes frozen source revisions and checksums, sample IDs, prompts, request hashes, response bodies, timing and per-item scores. Public benchmark input text is fetched from its original sources rather than redistributed in the results bundle.

[Methodology](methodology.html) · [Recorded outputs](results.zip) · [Stage 0](stage-0.html) · [Stage 1](stage-1.html) · [Stage 2](stage-2.html) · [Stage 3](stage-3.html) · [Stage 4](stage-4.html)

Corrections should identify the item and preserve the original results. Reviewed synthetic cases or revised prompts belong to a separately versioned experiment.
