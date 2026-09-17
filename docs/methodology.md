# Methodology and reproducibility

## Status and research questions

This is an exploratory early-access pilot of TypeSafe Jev conducted on September 17, 2026. It asks whether Korean and English inputs lead to different decisions on paired public tasks, how Jev performs on selected Korean medical examination questions, and whether it can interpret explicit facts in short synthetic medical notes.

The unit of sampling is a source question or sentence pair. Language conditions and robustness calls reuse those units. Do not treat every API call as an independent sample. The synthetic set has related minimal pairs.

The protocol was agreed before testing in a local task. It was not registered with an external preregistration service. The frozen manifest contains its creation time, exact request payloads, gold labels and seed. All primary prompts and test inputs were frozen before the first development call. Report formatting and analysis code were developed during the run.

## Data and sampling

The random seed is `20260917`. Sampling uses Python's `random.Random` with deterministic source ordering. The pilot was prepared with Python 3.14.2. Released source revisions and SHA-256 hashes are in `results/source-lock.json`; selected IDs and request hashes are in `results/evaluation-index.json`.

### Belebele

The pinned English and Korean exports each contain 900 questions. These files do not contain the `split` field described in some documentation. Their `ds` fields are different language-specific export dates and must not be used to join languages. We verified that `(link, question_number)` is unique in each export and joined on those fields. All 900 pairs agree on the gold label.

The joined data cover 488 passage links. We sample 100 distinct links and choose one associated question per link. Every question has four options. No development prompts were tuned on these questions.

### PAWS-X

The pinned exports each contain 2,000 rows. We join by the original `id`, exclude 11 cross-language gold-label disagreements, and then exclude 17 matched pairs containing missing/NS text, leaving 1,972 eligible pairs. We select 50 positive and 50 negative pairs without replacement.

Exclusions are fixed before inference. The label disagreements are not independently relabeled. This balanced subset is not a random sample of all natural paraphrase requests.

### KorMedMCQA

Use the doctor test split only, with 435 questions from 2022–2024. We require nonempty question text, all five options, and a gold label from 1 to 5. A conservative Korean keyword screen excludes references potentially requiring missing figures, images, graphs, tables or results. The exact regular expression is in the preparation code, and every excluded ID and reason is recorded.

The screen retains 259 candidates and excludes 176. It deliberately over-excludes, including some items with sufficient textual representations of results. This reduces ambiguity but changes the evaluated population. We allocate 100 selections proportionally by eligible examination year using the largest-remainder method, giving 35 from 2022, 33 from 2023 and 32 from 2024. Every selected question was inspected for text completeness before Stage 2. This was an AI-assisted input audit, not a clinician validation of the gold answers.

The dataset includes clinical medicine, health law, ethics and public health. Images are not evaluated. Historical official gold answers and source spelling are retained without correction. Reported accuracy is therefore for this screened subset, not the full licensing exam or current clinical practice.

### Synthetic medical text

Forty cases were authored before inference, eight in each category of negation/uncertainty, temporality, experiencer, medication status and evidence support. Each has Korean text, an English equivalent, a proposed gold label and three task-specific options, including an unknown/insufficient-evidence outcome. Related examples form 20 designated minimal pairs.

Both labels and translations were AI-authored and remain unreviewed by a clinician. All synthetic scores are exploratory and excluded from primary medical scoring. The review packet is public so a clinician can propose corrections. Corrections must create a new experiment, preserving this version.

## Conditions and request structure

- EN/EN uses English content and instructions.
- KO/EN uses Korean content and English instructions.
- KO/KO uses Korean content and instructions.

General tasks and synthetic notes use all three conditions. KorMedMCQA uses the two Korean-content conditions only. In the public tasks, answer-option text follows content language. In the synthetic and development Choice tasks, category descriptions follow instruction language. JSON field names and category IDs remain stable.

Each request has one shared state and exactly one question named `answer`. Choice receives the finite options. PAWS-X uses Noul to ask whether the sentences have equivalent meanings, with a fixed yes threshold of 0.5, including ties. Labels and reference explanations never enter the request. There are no tools, retrieval, demonstrations, generated explanations or chain-of-thought requests.

Cases are executed in frozen order, with conditions EN/EN, KO/EN and KO/KO where applicable. This interleaves conditions within each case but does not randomize order. Each language condition receives a separate request.

The manifest hashes logical request payloads, including option order. They are not hashes of the HTTP transport bytes or headers. A mocked SDK transport test confirms option insertion order is preserved by the installed SDK.

## Probability validation amendment

The initial validator required probabilities to sum to one within 0.0001. On medical Stage 2 call 38, one five-option response summed to 0.99. Its values were 0.12, 0.05, 0, 0.01 and 0.81. All 356 Choice responses observed at that point were on a 0.01 grid, and 355 summed to one.

Execution stopped. We preserved the response and failed local-validation record and added a separate timestamped adjudication. No question, label, prediction or raw probability was changed, and this request was not called again.

The amended validator permits a nonunit sum only when all values lie on a 0.01 grid and the discrepancy is no more than `0.005 × number_of_options`, the maximum aggregate error under nearest-hundredth rounding. Other vectors retain the 0.0001 tolerance. Values must remain finite and in [0, 1], the option keys must match, and the selected answer must agree with a maximal probability. Larger discrepancies still stop execution.

Rounding is an inference from observed precision, not a verified description of the server. For proper probability scores and total-variation comparisons, accepted nonunit vectors are divided by their sum. Raw response probabilities remain available. JSON group summaries report both normalized Brier/log loss and raw-vector Brier/raw-gold log loss for sensitivity analysis. Accuracy and the returned confidence ranking are unaffected.

This amendment was made after observing the exceptional response, so it is a disclosed deviation from the original validation rule. `original-attempts.jsonl` preserves the event, `adjudications.json` explains it, and `responses.jsonl` contains the effective analysis records.

## Metrics

Accuracy is correct predictions divided by successful responses within each task and condition. Failed and pending calls are reported separately. There is no cross-task pooled accuracy.

Accuracy intervals use the Wilson formula with z = 1.959963984540054. Paired differences use 4,000 seeded bootstrap resamples of matched source IDs. Sparse discordant pairs can produce boundary intervals; these intervals are descriptive. Synthetic minimal-pair dependence is not accounted for in these item-level intervals, which are not used for clinical claims. No hypothesis-test or multiplicity-adjusted conclusion is made.

Multiclass Brier score is the sum of squared differences between the returned probability vector and the one-hot gold label, averaged over cases. Its range is 0–2. The Noul score uses the two-class vector `[1-p, p]`, so it is twice the single-probability binary Brier convention. Log loss uses the natural logarithm, clipping a zero gold probability to 1e-15.

Error-versus-coverage sorts Choice by returned confidence and Noul by `abs(p - 0.5)`. Ties break by evaluation ID. At coverage f, retain `ceil(n × f)` items and report their error fraction. Coverage is descriptive and does not establish a usable deployment threshold. Confidence is not treated as the probability of correctness.

## Robustness

Before inference, use seed `20260921` to select five Korean-instruction evaluations per scored task, 20 total. For each, make two identical repeat calls and two meaning-preserving variants. Choice variants rotate option insertion order by one and two positions while keeping category IDs, texts and gold mapping together. Noul variants both reverse sentence order, providing two calls of the reversed condition.

Compare each additional call with its original response. Report prediction flips and total variation, one half the L1 distance between probability vectors. These observations are not independent new test questions.

## Timing, cost and operations

All calls use the synchronous TypeSafe Python SDK 0.6.0 at concurrency one. The requested alias is `jev-latest`; every returned model name is checked against the first response. A model-version change stops execution. The timeout is 30 seconds. SDK retries are disabled; the runner records each of up to three attempts for transient connection, timeout, 408, 429 or 5xx failures.

Client latency uses a monotonic high-resolution clock around the SDK call. It includes network time and response decoding but excludes local record writes. Median and p95 use linearly interpolated sample quantiles. Runner wall time additionally includes initialization, retry sleep, persistence and report generation. Invocation wall time was added after the first ten development calls; per-call latency exists for all calls. Preparation, coding, manual inspection and human gaps are not included.

Client location was not measured. The workspace timezone is Asia/Seoul. No claim is made about server geography, pure inference latency, concurrent throughput or globally representative latency.

Estimated cost is input tokens × $0.042 / 1,000,000, the published rate checked on the run date. Output tokens are recorded even though their published price is zero. This is not an invoice and does not include minimum purchases or credit accounting. The $0.25 local budget reserves a conservative UTF-8-byte-based token estimate before each call and charges a conservative reserve if usage is unavailable after failure.

Intent records are written before requests, and outcome records are created exclusively rather than overwritten. A crash leaving an intent without an outcome stops resume to avoid an untracked duplicate call. Successful calls are never repeated by resume. Stage reports are generated before the next stage starts. Original records remain immutable; reports and web pages are derived artifacts.

## Reproduction and extensions

`python -m jevbench prepare` fetches the published source revisions and verifies checksums, reconstructing the released manifest hash. `python -m jevbench restore` imports recorded outputs without making model calls. `python -m jevbench report` recomputes stage results. See the repository README for environment setup.

For a new model run, create a new experiment ID and specify an explicit available model version. Keep the original recorded experiment untouched. If evaluating another provider, retain the same source IDs and answer options, label mapping, concurrency and latency boundaries. Record any differences in structured-output support, reasoning budgets, caching, pricing and tokenization.

## Sources

- [Belebele dataset and paper](https://github.com/facebookresearch/belebele), Bandarkar et al., ACL 2024.
- [PAWS-X dataset and paper](https://github.com/google-research-datasets/paws/tree/master/pawsx), Yang et al., EMNLP 2019.
- [KorMedMCQA](https://huggingface.co/datasets/sean0042/KorMedMCQA), Kweon et al., 2024.
- [TypeSafe primitives](https://docs.typesafe.ai/primitives) and [confidence](https://docs.typesafe.ai/confidence).
- [TypeSafe launch and pricing](https://typesafe.ai/blog/introducing-system-one-models-and-jev).

The study uses an early-access account. No claim is made that the measured version or pricing will remain available after early access.
