# Methodology and reproducibility

## Status and research questions

This is an exploratory early-access sample check of TypeSafe Jev conducted on September 17, 2026. It asks whether Korean and English inputs lead to different decisions on paired public tasks, how Jev performs on selected Korean medical examination questions, whether it can interpret explicit facts in short synthetic medical notes, and how a mainstream LLM compares on the same frozen cases.

The unit of sampling is a source question or sentence pair. Language conditions and robustness calls reuse those units. Do not treat every API call as an independent sample. The synthetic set has related minimal pairs.

The protocol was agreed before testing in a local task. It was not registered with an external preregistration service. The frozen manifest contains its creation time, exact request payloads, gold labels and seed. All primary prompts and test inputs were frozen before the first development call. Report formatting and analysis code were developed during the run. The Luna comparison and the sentence-order experiment were designed after inspecting Jev results and are exploratory replications, not preregistered confirmations.

## Data and sampling

The random seed is `20260917`. Sampling uses Python's `random.Random` with deterministic source ordering. The study was prepared with Python 3.14.2. Released source revisions and SHA-256 hashes are in `results/source-lock.json`; selected IDs and request hashes are in `results/evaluation-index.json`.

### Belebele

The pinned English and Korean exports each contain 900 questions. These files do not contain the `split` field described in some documentation. Their `ds` fields are different language-specific export dates and must not be used to join languages. We verified that `(link, question_number)` is unique in each export and joined on those fields. All 900 pairs agree on the gold label.

The joined data cover 488 passage links. We sample 100 distinct links and choose one associated question per link. Every question has four options. No development prompts were tuned on these questions.

### PAWS-X

The pinned exports each contain 2,000 rows. We join by the original `id`, exclude 11 cross-language gold-label disagreements, and then exclude 17 matched pairs containing missing/NS text, leaving 1,972 eligible pairs. We select 50 positive and 50 negative pairs without replacement.

Exclusions are fixed before inference. The label disagreements are not independently relabeled. This balanced subset is not a random sample of all natural paraphrase requests.

### KorMedMCQA

Use the doctor test split only, with 435 questions from 2022–2024. We require nonempty question text, all five options, and a gold label from 1 to 5. A conservative Korean keyword screen excludes references potentially requiring missing figures, images, graphs, tables or results. The exact regular expression is in the preparation code, and every excluded ID and reason is recorded.

The screen retains 259 candidates and excludes 176. It deliberately over-excludes, including some items with sufficient textual representations of results. This reduces ambiguity but changes the evaluated population. We allocate 100 selections proportionally by eligible examination year using the largest-remainder method, giving 35 from 2022, 33 from 2023 and 32 from 2024. Every selected question was inspected for text completeness before Stage 2. This was an AI-assisted input audit, not a clinician validation of the gold answers.

The dataset includes clinical medicine, health law, ethics and public health. Images are not evaluated. Historical official gold answers and source spelling are retained without correction. Reported accuracy is therefore for this screened subset, not the full licensing exam or current clinical practice. A separate 435-question study of the full doctor split is being published independently of this page.

### MedQA

The original-English extension uses the `GBaker/MedQA-USMLE-4-options` mirror of `jind11/MedQA`, file `phrases_no_exclude_test.jsonl`, revision pinned in `results/medqa-english-v3/source-manifest-index.json`. From 1,273 test rows we select 100 with the same seed discipline. Four options per question.

This is an entirely different examination from KorMedMCQA, with a different authority, curriculum, difficulty and option count. It is **not** an English arm of the Korean medical test and cannot be subtracted from it to estimate a language effect. It exists to show how the same two models behave on a widely reported medical benchmark, not to isolate language.

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

## Comparator protocol

### Why Luna without reasoning

Published Luna reasoning levels are `none`, `low`, `medium` (default), `high`, `xhigh` and `max`. We start with explicit `none`, because a decision-only low-cost baseline directly addresses whether a cheap LLM already meets this task's needs. Whether higher reasoning is worth its cost is a separate question that requires its own frozen experiment; no higher-reasoning run was performed here, and these results must not be edited if one is later added.

The hypothesis that Jev sits between Luna-none and Luna-max is untested and need not hold task by task.

### Request parity and its limits

Luna used the Responses API, standard service tier, one isolated request per case, and a strict JSON schema returning only an answer ID or boolean. Original instructions, state and choice order were retained. State and criteria were serialised as UTF-8 JSON, which is an interface difference from Jev. No tools, retrieval, explanation, probability elicitation or conversation history was used. Output was capped at 128 tokens. All 1,036 conditions were frozen before the first Luna call.

Luna was **not** asked to produce a probability vector. Requiring one would add output work unrelated to the decision and inflate both latency and cost. The consequence is that this comparison measures the cost of obtaining a decision, not equal amounts of output information: Jev returns probabilities natively, Luna returns a decision only. Self-reported probabilities are not interchangeable with token probabilities or with Jev probabilities, so no Brier score, log loss or coverage analysis exists for Luna. Fabricating one-hot probabilities for Luna would change the question being measured.

The API returned `gpt-5.6-luna` without a dated snapshot. Reported reasoning-token counts are audited and must be zero. Sampling parameters were left at provider defaults and retained in the raw responses. Calls run sequentially through httpx 0.28.1 with a 30-second timeout and at most two transient retries.

### Comparisons that timing cannot support

The Jev and Luna runs occurred at different times through different provider transports, and conditions were not randomly interleaved across providers. Provider load and date are therefore confounders. These measurements describe the observed services on the run dates; they are not architecture-only speed, server compute, or a stable population ratio. A contemporaneous interleaved replication would be needed to strengthen any latency claim.

The English MedQA extension used four concurrent requests per provider while earlier tasks ran sequentially, so its wall time is not comparable with the sequential timings and no pooled elapsed-time speedup is reported across protocols.

## Sentence-order experiment

Paraphrase equivalence is symmetric: if A means the same as B, then B means the same as A. Reversing `sentence1` and `sentence2` therefore leaves the gold label unchanged, and any changed prediction is an inconsistency rather than a different question.

The frozen experiment `order-sensitivity-v1` runs the 100 PAWS-X source questions in both orientations, in both EN/EN and KO/KO, for both models: 800 evaluations. Both orientations are re-run inside this experiment rather than paired against the original pilot records, so the comparison is internally matched and does not depend on cross-experiment timing.

Flip rate is the fraction of source questions whose prediction differs between orientations, with Wilson intervals. Total variation is one half the L1 distance between probability vectors, available for Jev only. Flip direction is reported separately as wrong→right and right→wrong counts, because a symmetric flip rate and a directional one have different practical meanings.

### Nondeterminism control

Flip rate alone conflates order sensitivity with ordinary service variation. The frozen control `order-repeat-v1` re-sends the 200 unchanged original-orientation Jev requests a second time. It verifies the source manifest hash and every individual request hash before comparing, so it measures the same request rather than a rebuilt one.

Observed same-input flip rates were 2% (English) and 1% (Korean), against 14% and 13% under reversal, with mean total variation 0.012 against 0.101 and 0.117. The control is a floor for the reversal figure: any flip a repeated identical request produces is not attributable to sentence order.

### An earlier five-item result

The original pilot's Stage 4 selected five Korean-instruction evaluations per task and observed 3 of 5 PAWS-X flips, implying a rate near 60%. At 100 questions the Korean rate is 13%. The same five items still flip in the same way, so this was not measurement error but an unrepresentative draw: under a true rate of 13%, three or more flips in five items has probability about 0.018. The five-item figure should not be cited.

## Metrics

Accuracy is correct predictions divided by successful responses within each task and condition. Failed and pending calls are reported separately. There is no cross-task pooled accuracy.

Accuracy intervals use the Wilson formula with z = 1.959963984540054. Paired differences use 4,000 seeded bootstrap resamples of matched source IDs. Sparse discordant pairs can produce boundary intervals; these intervals are descriptive. Synthetic minimal-pair dependence is not accounted for in these item-level intervals, which are not used for clinical claims. No hypothesis-test or multiplicity-adjusted conclusion is made, and intervals are unadjusted for multiple comparisons.

Multiclass Brier score is the sum of squared differences between the returned probability vector and the one-hot gold label, averaged over cases. Its range is 0–2. The Noul score uses the two-class vector `[1-p, p]`, so it is twice the single-probability binary Brier convention. Log loss uses the natural logarithm, clipping a zero gold probability to 1e-15.

Error-versus-coverage sorts Choice by returned confidence and Noul by `abs(p - 0.5)`. Ties break by evaluation ID. At coverage f, retain `ceil(n × f)` items and report their error fraction. Coverage is descriptive and does not establish a usable deployment threshold. Confidence is not treated as the probability of correctness.

## Timing, cost and operations

All original-pilot calls use the synchronous TypeSafe Python SDK 0.6.0 at concurrency one. The requested alias is `jev-latest`; every returned model name is checked against the first response. A model-version change stops execution. The timeout is 30 seconds. SDK retries are disabled; the runner records each of up to three attempts for transient connection, timeout, 408, 429 or 5xx failures.

Client latency uses a monotonic high-resolution clock around the SDK call. It includes network time and response decoding but excludes local record writes. Median and p95 use linearly interpolated sample quantiles. Runner wall time additionally includes initialization, retry sleep, persistence and report generation. Invocation wall time was added after the first ten development calls; per-call latency exists for all calls. Preparation, coding, manual inspection and human gaps are not included.

Client location was not measured. The workspace timezone is Asia/Seoul. No claim is made about server geography, pure inference latency, concurrent throughput or globally representative latency.

Estimated Jev cost is input tokens × $0.042 / 1,000,000, the published rate checked on the run date. Output tokens are recorded even though Jev returns none. Luna cost uses $0.20 per million input, $0.02 cached input and $1.20 output. These are estimates from published prices, not invoices, and exclude minimum purchases or credit accounting. The $0.25 local budget reserves a conservative UTF-8-byte-based token estimate before each call and charges a conservative reserve if usage is unavailable after failure. It is not an account-side spending limit.

Intent records are written before requests, and outcome records are created exclusively rather than overwritten. A crash leaving an intent without an outcome stops resume to avoid an untracked duplicate call. Successful calls are never repeated by resume. Stage reports are generated before the next stage starts. Original records remain immutable; reports, summaries and web pages are derived artifacts and may be regenerated.

## Known limits on reproducibility

Re-sending byte-identical requests to the same resolved model version (`jev-1.13.0`) changed 3 of 100 English and 1 of 100 Korean PAWS-X predictions. Results in this study are therefore reproducible to roughly ±2% per item, not bit-for-bit. Any replication that differs by a few items from the published figures is consistent with this service variation and does not by itself indicate a procedural error.

## Reproduction and extensions

`python -m jevbench prepare` fetches the published source revisions and verifies checksums, reconstructing the released manifest hash. `python -m jevbench restore` imports recorded outputs without making model calls. `python -m jevbench report` recomputes stage results. Figures rebuild with `python -m jevbench.figures`, `python -m jevbench.overview_figure` and `python -m jevbench.answer_shape`. The README results tables are regenerated from the frozen summaries by `python -m jevbench.readme`. See [Running the experiments](running-experiments.html) for environment setup.

For a new model run, create a new experiment ID and specify an explicit available model version. Keep the original recorded experiment untouched. If evaluating another provider, retain the same source IDs and answer options, label mapping, concurrency and latency boundaries. Record any differences in structured-output support, reasoning budgets, caching, pricing and tokenization.

## Sources

- [Belebele dataset and paper](https://github.com/facebookresearch/belebele), Bandarkar et al., ACL 2024.
- [PAWS-X dataset and paper](https://github.com/google-research-datasets/paws/tree/master/pawsx), Yang et al., EMNLP 2019.
- [KorMedMCQA](https://huggingface.co/datasets/sean0042/KorMedMCQA), Kweon et al., 2024.
- [MedQA](https://github.com/jind11/MedQA), Jin et al., 2020.
- [TypeSafe primitives](https://docs.typesafe.ai/primitives) and [confidence](https://docs.typesafe.ai/confidence).
- [TypeSafe launch and pricing](https://typesafe.ai/blog/introducing-system-one-models-and-jev).
- [Luna model documentation](https://developers.openai.com/api/docs/models/gpt-5.6-luna).

The study uses an early-access account. No claim is made that the measured version or pricing will remain available after early access.

<!-- lang:ko -->

# 평가 방법과 재현성

## 연구의 성격과 질문

2026년 9월 17일에 수행한 TypeSafe Jev의 탐색적 얼리 액세스 표본 점검입니다. 대응되는 공개 과제에서 한국어와 영어 입력이 서로 다른 결정을 이끄는지, 선별된 한국 의사 국가시험 문항에서 Jev의 성능이 어떤지, 짧은 합성 의무기록의 명시적 사실을 해석할 수 있는지, 그리고 동일한 고정 사례에서 주요 LLM과 어떻게 비교되는지를 묻습니다.

표집 단위는 원본 문항 또는 문장 쌍입니다. 언어 조건과 강건성 호출은 같은 단위를 재사용합니다. 모든 API 호출을 독립 표본으로 간주해서는 안 됩니다. 합성 세트에는 서로 연관된 최소 대립쌍이 있습니다.

프로토콜은 테스트 이전에 로컬 작업으로 합의했으며 외부 사전등록 서비스에는 등록하지 않았습니다. 고정된 매니페스트에는 생성 시각, 정확한 요청 페이로드, 정답 레이블, 시드가 들어 있습니다. 모든 주요 프롬프트와 테스트 입력은 첫 개발 호출 이전에 고정되었습니다. 보고서 형식과 분석 코드는 실행 중에 개발되었습니다. Luna 비교와 문장 순서 실험은 Jev 결과를 확인한 뒤에 설계한 탐색적 반복이며 사전등록된 확증 연구가 아닙니다.

## 데이터와 표집

난수 시드는 `20260917`입니다. 표집에는 Python의 `random.Random`과 결정적 원본 정렬을 사용합니다. 준비는 Python 3.14.2로 했습니다. 공개된 원본 리비전과 SHA-256 해시는 `results/source-lock.json`에, 선택된 ID와 요청 해시는 `results/evaluation-index.json`에 있습니다.

### Belebele

고정된 영어·한국어 내보내기 파일에는 각각 900문항이 있습니다. 이 파일에는 일부 문서에서 언급하는 `split` 필드가 없습니다. `ds` 필드는 언어별로 다른 내보내기 날짜이므로 언어 결합에 사용해서는 안 됩니다. 각 파일에서 `(link, question_number)`가 고유함을 확인하고 이 필드로 결합했습니다. 900쌍 모두 정답 레이블이 일치합니다.

결합된 데이터는 488개 지문 링크를 포함합니다. 100개의 서로 다른 링크를 표집하고 링크마다 문항 하나를 선택합니다. 모든 문항은 선택지가 4개입니다. 이 문항들로 개발 프롬프트를 조정하지 않았습니다.

### PAWS-X

고정된 내보내기 파일에는 각각 2,000행이 있습니다. 원본 `id`로 결합하고, 언어 간 정답 불일치 11건을 제외한 뒤, 결측 또는 NS 텍스트를 포함한 대응쌍 17건을 추가로 제외하여 1,972쌍이 남습니다. 여기에서 긍정 50쌍과 부정 50쌍을 비복원 추출합니다.

제외 기준은 추론 이전에 고정했습니다. 레이블 불일치는 독립적으로 재라벨링하지 않았습니다. 이 균형 잡힌 부분집합은 자연스러운 의미 동등성 요청 전체의 무작위 표본이 아닙니다.

### KorMedMCQA

의사 시험 test 분할만 사용하며 2022~2024년의 435문항입니다. 비어 있지 않은 문항 텍스트, 다섯 개의 선택지, 1에서 5 사이의 정답 레이블을 요구합니다. 보수적인 한국어 키워드 선별로 그림, 사진, 그래프, 표, 검사 결과가 없어 답할 수 없을 가능성이 있는 문항을 제외합니다. 정확한 정규식은 준비 코드에 있으며 제외된 모든 ID와 사유를 기록합니다.

선별 결과 259문항이 남고 176문항이 제외되었습니다. 결과가 텍스트로 충분히 제시된 일부 문항까지 제외하는 과잉 제외를 의도했습니다. 모호성은 줄지만 평가 대상 모집단이 달라집니다. 적격 시험 연도별로 최대잔여법을 써서 100문항을 비례 배분했으며 2022년 35문항, 2023년 33문항, 2024년 32문항입니다. 선택된 모든 문항은 Stage 2 이전에 텍스트 완전성을 점검했습니다. 이는 AI 보조 입력 감사이며 정답에 대한 임상적 검증이 아닙니다.

데이터셋에는 임상의학, 보건의료법규, 윤리, 공중보건이 포함됩니다. 이미지는 평가하지 않습니다. 과거 공식 정답과 원문 표기는 수정 없이 유지합니다. 따라서 보고된 정확도는 선별된 부분집합에 대한 것이며 전체 국가시험이나 현재의 임상 진료에 대한 것이 아닙니다. 전체 의사 시험 분할에 대한 435문항 연구는 이 페이지와 별도로 발표됩니다.

### MedQA

영어 원문 확장은 `jind11/MedQA`의 미러인 `GBaker/MedQA-USMLE-4-options`, 파일 `phrases_no_exclude_test.jsonl`을 사용하며 리비전은 `results/medqa-english-v3/source-manifest-index.json`에 고정되어 있습니다. 1,273개 test 행에서 동일한 시드 원칙으로 100문항을 선택했습니다. 문항당 선택지는 4개입니다.

이것은 KorMedMCQA와 완전히 다른 시험이며 출제 기관, 교육과정, 난이도, 선택지 수가 모두 다릅니다. 한국어 의학 시험의 영어판이 **아니며**, 두 점수를 빼서 언어 효과를 추정할 수 없습니다. 이 항목은 널리 보고되는 의학 벤치마크에서 동일한 두 모델이 어떻게 동작하는지를 보여 주기 위한 것이지 언어를 분리하기 위한 것이 아닙니다.

### 합성 의학 텍스트

추론 이전에 40개 사례를 작성했으며 부정/불확실성, 시제, 경험자, 투약 상태, 근거 충분성의 다섯 범주에 각각 8개씩 배정했습니다. 각 사례에는 한국어 텍스트, 영어 대응문, 제안된 정답 레이블, 그리고 불명확/근거 부족 결과를 포함한 세 개의 과제별 선택지가 있습니다. 연관된 예시들이 20개의 지정된 최소 대립쌍을 이룹니다.

레이블과 번역 모두 AI가 작성했으며 임상의의 검토를 받지 않았습니다. 모든 합성 점수는 탐색적이며 주요 의학 점수에서 제외됩니다. 임상의가 수정을 제안할 수 있도록 검토 패킷을 공개합니다. 수정은 이 버전을 보존한 채 새로운 실험을 만들어야 합니다.

## 조건과 요청 구조

- EN/EN은 영어 내용과 영어 지시문입니다.
- KO/EN은 한국어 내용과 영어 지시문입니다.
- KO/KO는 한국어 내용과 한국어 지시문입니다.

일반 과제와 합성 의무기록은 세 조건을 모두 사용합니다. KorMedMCQA는 한국어 내용의 두 조건만 사용합니다. 공개 과제에서 선택지 텍스트는 내용 언어를 따릅니다. 합성 및 개발 Choice 과제에서 범주 설명은 지시문 언어를 따릅니다. JSON 필드 이름과 범주 ID는 그대로 유지됩니다.

각 요청은 하나의 공유 state와 `answer`라는 이름의 질문 하나만 갖습니다. Choice는 유한한 선택지를 받습니다. PAWS-X는 Noul을 사용해 두 문장의 의미가 동등한지를 묻고, 동점을 포함하여 0.5를 고정 임계값으로 사용합니다. 레이블과 참조 설명은 요청에 절대 포함되지 않습니다. 도구, 검색, 예시, 생성된 설명, 사고 연쇄 요청은 사용하지 않습니다.

사례는 고정된 순서로 실행하며 해당되는 경우 EN/EN, KO/EN, KO/KO 조건을 적용합니다. 이는 사례 내에서 조건을 교차 배치하지만 순서를 무작위화하지는 않습니다. 각 언어 조건은 별도의 요청을 받습니다.

매니페스트는 선택지 순서를 포함한 논리적 요청 페이로드를 해싱합니다. HTTP 전송 바이트나 헤더의 해시가 아닙니다. 모의 SDK 전송 테스트로 설치된 SDK가 선택지 삽입 순서를 보존함을 확인했습니다.

## 확률 검증 수정 사항

최초 검증기는 확률의 합이 0.0001 이내로 1이 될 것을 요구했습니다. 의학 Stage 2의 38번째 호출에서 다섯 선택지 응답 하나의 합이 0.99였습니다. 값은 0.12, 0.05, 0, 0.01, 0.81이었습니다. 그 시점까지 관측된 356개 Choice 응답은 모두 0.01 격자 위에 있었고 355개는 합이 1이었습니다.

실행을 중단했습니다. 해당 응답과 로컬 검증 실패 기록을 보존하고 별도의 타임스탬프가 찍힌 판정을 추가했습니다. 문항, 레이블, 예측, 원시 확률은 어느 것도 변경하지 않았으며 이 요청은 다시 호출하지 않았습니다.

수정된 검증기는 모든 값이 0.01 격자 위에 있고 오차가 `0.005 × 선택지 수` 이하일 때에만, 즉 100분의 1 반올림에서 가능한 최대 누적 오차 범위에서만 합이 1이 아닌 것을 허용합니다. 그 밖의 벡터는 0.0001 허용 오차를 유지합니다. 값은 유한하고 [0, 1] 범위여야 하며, 선택지 키가 일치하고, 선택된 답이 최대 확률과 일치해야 합니다. 더 큰 불일치는 여전히 실행을 중단시킵니다.

반올림은 관측된 정밀도로부터의 추론이며 서버 동작에 대한 검증된 설명이 아닙니다. 적절한 확률 점수와 총변동 비교를 위해, 합이 1이 아닌 채로 수용된 벡터는 합으로 나눕니다. 원시 응답 확률은 그대로 남아 있습니다. JSON 그룹 요약은 민감도 분석을 위해 정규화된 Brier/로그 손실과 원시 벡터 Brier/원시 정답 로그 손실을 모두 보고합니다. 정확도와 반환된 확신도 순위는 영향을 받지 않습니다.

이 수정은 예외적인 응답을 관측한 뒤에 이루어졌으므로 원래 검증 규칙으로부터의 공개된 이탈입니다. `original-attempts.jsonl`이 사건을 보존하고, `adjudications.json`이 이를 설명하며, `responses.jsonl`이 분석에 실제로 사용된 기록을 담고 있습니다.

## 비교 모델 프로토콜

### 왜 추론 없는 Luna인가

공개된 Luna 추론 수준은 `none`, `low`, `medium`(기본값), `high`, `xhigh`, `max`입니다. 저희는 명시적 `none`에서 시작합니다. 결정만 반환하는 저비용 기준선이 "값싼 LLM이 이미 이 과제에 충분한가"라는 질문에 직접 답하기 때문입니다. 더 높은 추론이 비용만큼의 가치가 있는지는 별도의 고정된 실험을 필요로 하는 다른 질문입니다. 여기에서는 higher-reasoning 실행을 하지 않았으며, 나중에 추가하더라도 이 결과를 수정해서는 안 됩니다.

Jev가 Luna-none과 Luna-max 사이에 위치한다는 가설은 검증되지 않았으며 과제마다 성립할 필요도 없습니다.

### 요청 동등성과 그 한계

Luna는 Responses API, 표준 서비스 계층, 사례당 하나의 독립 요청, 그리고 답 ID 또는 불리언만 반환하는 엄격한 JSON 스키마를 사용했습니다. 원래의 지시문, state, 선택지 순서를 유지했습니다. state와 criteria는 UTF-8 JSON으로 직렬화했으며 이는 Jev와의 인터페이스 차이입니다. 도구, 검색, 설명, 확률 유도, 대화 이력은 사용하지 않았습니다. 출력은 128토큰으로 제한했습니다. 1,036개 조건 모두 첫 Luna 호출 이전에 고정되었습니다.

Luna에게 확률 벡터를 요구하지 **않았습니다**. 요구했다면 결정과 무관한 출력 작업이 추가되어 지연 시간과 비용이 모두 부풀려집니다. 그 결과 이 비교는 동일한 양의 출력 정보가 아니라 결정 하나를 얻는 비용을 측정합니다. Jev는 확률을 기본으로 반환하고 Luna는 결정만 반환합니다. 모델이 스스로 보고한 확률은 토큰 확률이나 Jev의 확률과 호환되지 않으므로, Luna에 대해서는 Brier 점수, 로그 손실, 커버리지 분석이 존재하지 않습니다. Luna에 원-핫 확률을 임의로 만들어 넣는 것은 측정 대상 자체를 바꾸는 일입니다.

API는 날짜가 붙은 스냅숏 없이 `gpt-5.6-luna`를 반환했습니다. 보고된 추론 토큰 수를 감사하며 0이어야 합니다. 샘플링 파라미터는 공급자 기본값으로 두고 원시 응답에 보존했습니다. 호출은 httpx 0.28.1을 통해 30초 타임아웃, 최대 두 번의 일시적 재시도로 순차 실행됩니다.

### 타이밍이 뒷받침할 수 없는 비교

Jev와 Luna 실행은 서로 다른 시점에 서로 다른 공급자 전송 경로로 이루어졌고, 조건을 공급자 간에 무작위로 교차 배치하지 않았습니다. 따라서 공급자 부하와 날짜가 교란 요인입니다. 이 측정값은 실행일의 관측된 서비스를 기술할 뿐이며 아키텍처만의 속도, 서버 연산량, 안정적인 모집단 비율이 아닙니다. 지연 시간 주장을 강화하려면 동시기에 교차 배치한 반복 실험이 필요합니다.

영어 MedQA 확장은 공급자당 4개의 동시 요청을 사용한 반면 이전 과제들은 순차 실행되었으므로, 그 실행 시간은 순차 측정값과 비교할 수 없고 프로토콜 간 통합 속도 향상은 보고하지 않습니다.

## 문장 순서 실험

의미 동등성은 대칭입니다. A가 B와 같은 뜻이면 B도 A와 같은 뜻입니다. 따라서 `sentence1`과 `sentence2`를 뒤바꾸어도 정답 레이블은 변하지 않으며, 예측이 바뀌면 그것은 다른 문항이 아니라 비일관성입니다.

고정 실험 `order-sensitivity-v1`은 PAWS-X 원본 100문항을 두 가지 순서로, EN/EN과 KO/KO 두 조건에서, 두 모델에 대해 실행합니다. 총 800개 평가입니다. 두 순서 모두 원래 파일럿 기록과 대응시키는 대신 이 실험 안에서 다시 실행하므로, 비교가 내부적으로 대응되며 실험 간 시점 차이에 의존하지 않습니다.

플립률은 두 순서 사이에 예측이 달라진 원본 문항의 비율이며 Wilson 구간을 함께 제시합니다. 총변동은 확률 벡터 간 L1 거리의 절반이며 Jev에 대해서만 산출됩니다. 플립 방향은 오답→정답과 정답→오답 건수로 따로 보고합니다. 대칭적인 플립률과 방향성 있는 플립률은 실무적 의미가 다르기 때문입니다.

### 비결정성 대조

플립률만으로는 순서 민감도와 일반적인 서비스 변동이 뒤섞입니다. 고정 대조 실험 `order-repeat-v1`은 변경하지 않은 원래 순서의 Jev 요청 200개를 한 번 더 보냅니다. 비교 이전에 원본 매니페스트 해시와 개별 요청 해시를 모두 검증하므로, 재구성된 요청이 아니라 동일한 요청을 측정합니다.

관측된 동일 입력 플립률은 영어 2%, 한국어 1%로, 순서를 뒤집었을 때의 14%와 13%에 대비됩니다. 평균 총변동은 0.012 대 0.101 및 0.117입니다. 이 대조값은 순서 실험 수치의 하한입니다. 동일한 요청을 반복했을 때 발생하는 플립은 문장 순서 때문이라고 할 수 없습니다.

### 이전의 5문항 결과

원래 파일럿의 Stage 4는 과제별로 한국어 지시문 평가 5건을 선택했고 PAWS-X에서 5건 중 3건의 플립을 관측하여 약 60%의 비율을 시사했습니다. 100문항에서 한국어 비율은 13%입니다. 같은 5문항은 지금도 동일하게 동작하므로 측정 오류가 아니라 대표성이 없는 표본이었습니다. 실제 비율이 13%일 때 5문항 중 3건 이상이 플립할 확률은 약 0.018입니다. 이 5문항 수치는 인용해서는 안 됩니다.

## 지표

정확도는 각 과제와 조건에서 성공한 응답 대비 정답 예측의 비율입니다. 실패와 대기 중인 호출은 별도로 보고합니다. 과제 간 통합 정확도는 없습니다.

정확도 구간은 z = 1.959963984540054를 사용한 Wilson 공식을 씁니다. 대응 차이는 대응된 원본 ID에 대한 4,000회의 시드 부트스트랩 재표본을 사용합니다. 불일치 쌍이 희소하면 경계 구간이 나올 수 있으며 이 구간들은 기술적입니다. 합성 최소 대립쌍의 종속성은 이 문항 수준 구간에 반영되지 않으며, 이 구간들은 임상적 주장에 사용하지 않습니다. 가설검정이나 다중성 보정을 거친 결론은 제시하지 않으며, 구간은 다중 비교에 대해 보정되지 않았습니다.

다범주 Brier 점수는 반환된 확률 벡터와 원-핫 정답 레이블 간 제곱차의 합을 사례에 대해 평균한 값입니다. 범위는 0~2입니다. Noul 점수는 두 범주 벡터 `[1-p, p]`를 사용하므로 단일 확률 이진 Brier 관례의 두 배입니다. 로그 손실은 자연로그를 사용하며 정답 확률이 0이면 1e-15로 절단합니다.

오류 대 커버리지는 Choice를 반환된 확신도로, Noul을 `abs(p - 0.5)`로 정렬합니다. 동점은 평가 ID로 처리합니다. 커버리지 f에서 `ceil(n × f)`개 항목을 남기고 그 오류 비율을 보고합니다. 커버리지는 기술적이며 실제 배포 임계값을 제시하지 않습니다. 확신도를 정답일 확률로 취급하지 않습니다.

## 시간, 비용, 운영

원래 파일럿의 모든 호출은 동기식 TypeSafe Python SDK 0.6.0을 동시성 1로 사용합니다. 요청 별칭은 `jev-latest`이며 반환된 모델 이름을 첫 응답과 대조합니다. 모델 버전이 바뀌면 실행이 중단됩니다. 타임아웃은 30초입니다. SDK 재시도는 비활성화했으며, 러너가 일시적 연결·타임아웃·408·429·5xx 실패에 대해 최대 세 번의 시도를 각각 기록합니다.

클라이언트 지연 시간은 SDK 호출을 감싸는 단조 고해상도 시계로 측정합니다. 네트워크 시간과 응답 디코딩을 포함하고 로컬 기록 쓰기는 제외합니다. 중앙값과 p95는 선형 보간된 표본 분위수를 사용합니다. 러너 실행 시간에는 초기화, 재시도 대기, 저장, 보고서 생성이 추가로 포함됩니다. 호출 실행 시간 계측은 처음 열 번의 개발 호출 이후에 추가되었으며, 호출별 지연 시간은 모든 호출에 대해 존재합니다. 준비, 코딩, 수동 점검, 사람의 공백 시간은 포함되지 않습니다.

클라이언트 위치는 측정하지 않았습니다. 작업 환경 시간대는 Asia/Seoul입니다. 서버 지리적 위치, 순수 추론 지연, 동시 처리량, 전 세계적으로 대표적인 지연 시간에 대해서는 어떤 주장도 하지 않습니다.

Jev의 추정 비용은 입력 토큰 × $0.042 / 1,000,000이며 실행일에 확인한 공개 요율입니다. Jev는 출력 토큰이 없지만 출력 토큰 수도 기록합니다. Luna 비용은 100만 입력 토큰당 $0.20, 캐시된 입력 $0.02, 출력 $1.20을 사용합니다. 이는 공개 가격에 기반한 추정치이며 청구서가 아니고, 최소 구매액이나 크레딧 회계를 포함하지 않습니다. $0.25의 로컬 예산은 각 호출 전에 UTF-8 바이트 기반의 보수적 토큰 추정치를 예약하고, 실패 후 사용량을 알 수 없으면 보수적 예약분을 차감합니다. 계정 차원의 지출 한도가 아닙니다.

의도 기록은 요청 전에 기록되며, 결과 기록은 덮어쓰지 않고 배타적으로 생성됩니다. 결과 없이 의도만 남은 채 중단되면 추적되지 않는 중복 호출을 피하기 위해 재개가 중단됩니다. 성공한 호출은 재개 시 절대 반복되지 않습니다. 단계 보고서는 다음 단계 시작 전에 생성됩니다. 원본 기록은 변경되지 않으며, 보고서·요약·웹 페이지는 파생 산출물로서 다시 생성할 수 있습니다.

## 재현성의 알려진 한계

동일한 모델 버전(`jev-1.13.0`)에 바이트 단위로 같은 요청을 다시 보냈을 때 PAWS-X 영어 100문항 중 3건, 한국어 100문항 중 1건의 예측이 달라졌습니다. 따라서 이 연구의 결과는 비트 단위가 아니라 문항당 약 ±2% 수준에서 재현됩니다. 공개된 수치와 몇 문항 차이가 나는 반복 실험은 이 서비스 변동과 부합하며, 그 자체로 절차상 오류를 뜻하지 않습니다.

## 재현과 확장

`python -m jevbench prepare`는 공개된 원본 리비전을 가져오고 체크섬을 검증하여 공개된 매니페스트 해시를 재구성합니다. `python -m jevbench restore`는 모델 호출 없이 기록된 출력을 가져옵니다. `python -m jevbench report`는 단계별 결과를 다시 계산합니다. 그림은 `python -m jevbench.figures`, `python -m jevbench.overview_figure`, `python -m jevbench.answer_shape`로 다시 만듭니다. README의 결과 표는 `python -m jevbench.readme`가 고정된 요약본으로부터 재생성합니다. 환경 설정은 [실험 실행하기](running-experiments.html)를 참고하세요.

새 모델을 실행하려면 새 실험 ID를 만들고 사용 가능한 모델 버전을 명시하십시오. 원래 기록된 실험은 그대로 두십시오. 다른 공급자를 평가한다면 동일한 원본 ID와 선택지, 레이블 매핑, 동시성, 지연 시간 측정 경계를 유지하십시오. 구조화 출력 지원, 추론 예산, 캐싱, 가격, 토큰화의 차이를 기록하십시오.

## 출처

- [Belebele 데이터셋과 논문](https://github.com/facebookresearch/belebele), Bandarkar et al., ACL 2024.
- [PAWS-X 데이터셋과 논문](https://github.com/google-research-datasets/paws/tree/master/pawsx), Yang et al., EMNLP 2019.
- [KorMedMCQA](https://huggingface.co/datasets/sean0042/KorMedMCQA), Kweon et al., 2024.
- [MedQA](https://github.com/jind11/MedQA), Jin et al., 2020.
- [TypeSafe 기본 요소](https://docs.typesafe.ai/primitives)와 [확신도](https://docs.typesafe.ai/confidence).
- [TypeSafe 출시 및 가격 안내](https://typesafe.ai/blog/introducing-system-one-models-and-jev).
- [Luna 모델 문서](https://developers.openai.com/api/docs/models/gpt-5.6-luna).

이 연구는 얼리 액세스 계정을 사용합니다. 측정된 버전이나 가격이 얼리 액세스 이후에도 유지된다고 주장하지 않습니다.
