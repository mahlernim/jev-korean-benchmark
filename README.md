# Jev in Korean: a 100-question sample check

**[한국어로 읽기 ↓](#jev의-한국어-성능-100문항-표본-점검)**

Can you use TypeSafe Jev on Korean text, or should you translate everything to English first? This is a small, frozen, reproducible check that tries to answer that — 100 questions per cell, drawn from four public test sets, with every response recorded. It is a sample check, not a benchmark: 100 questions give roughly ±8 points of uncertainty, so small differences here are not findings.

## Short answer

- **Korean reading comprehension is fine.** 96 of 100 in Korean against 97 in English, on the same questions. There is no meaningful cost.
- **Fine-grained meaning judgements are shaky in both languages.** 76 in Korean, 80 in English. The Korean number is a little lower, but 80% is not good in *either* language — this is the weak spot regardless of which one you use.
- **Don't bother writing your prompts in English.** Korean content scored within a point or two whether the instructions were Korean or English. Translating your instructions buys nothing.
- **The two medical numbers cannot be compared to each other.** 89 on an English exam and 80 on a Korean one are two different tests, not evidence about language. See [About the medical numbers](#about-the-medical-numbers).
- **Reordering your input changes about 1 answer in 8**, equally in both languages. Worth knowing, but it is not a Korean-specific problem.

![The same questions in Korean and in English](docs/figures/korean-check.png)

Bar ends are the score; the connector shows the gap between English and Korean on identical questions. Medical rows sit below the line as single points because no counterpart exists for them.

## What was tested

<!-- results-table-start -->
| Task | Language | Jev | Luna | Luna − Jev (95% CI) |
|---|---|---:|---:|---:|
| Belebele reading | English | 97/100 | 98/100 | +1 (−3, +6) |
| Belebele reading | Korean | 96/100 | 95/100 | −1 (−5, +3) |
| PAWS-X paraphrase | English | 80/100 | 83/100 | +3 (−3, +10) |
| PAWS-X paraphrase | Korean | 76/100 | 72/100 | −4 (−14, +5) |
| MedQA exam | English | 89/100 | 84/100 | −5 (−11, +0) |
| KorMedMCQA exam | Korean | 80/100 | 88/100 | **+8 (+2, +15)** |
<!-- results-table-end -->

Four public test sets. **Belebele** is reading comprehension; **PAWS-X** asks whether two sentences mean the same thing; **KorMedMCQA** is the Korean medical licensing exam; **MedQA** is its American counterpart. Belebele and PAWS-X are the same questions professionally translated, so those rows really do isolate language. The two medical sets are unrelated exams.

Luna is `gpt-5.6-luna` at reasoning effort `none`, included as a familiar point of reference rather than as a fair fight — see [How it compares](#how-it-compares-with-a-mainstream-llm).

Every cell is 100 questions, so every number carries roughly ±8 points of uncertainty. Only one difference in the whole table clears zero: Luna scores 8 points higher on the Korean medical exam.

<!-- examples-start -->
## What the questions actually look like

One real item per source, chosen at random from questions this study did **not** score. Seeing the format explains a lot about what the numbers mean.

<details>
<summary><b>Belebele — reading comprehension, same item in both languages</b></summary>

**English** · Passage

> For some festivals, the vast majority of the attendants to music festivals decide to camp on site, and most attendants consider it a vital part of the experience. If you want to be close to the action you're going to have to get in early to get a camping site close to the music. Remember that even though music on the main stages may have finished, there may be sections of the festival that will keep playing music until late into the night. Some festivals have special camping areas for families with young children.

Question: What aspect of music festivals do some attendants consider to be a crucial part of the experience?

| | Options |
|---|---|
| **1** | Bringing young children |
| **2** | Camping on site ✅ |
| **3** | Music playing late into the night |
| **4** | Getting in early |

**Korean** · Passage

> 몇몇 축제들에서 음악 축제에 참석하는 많은 사람들이 그 자리에서 야영하기로 결정하고, 대부분의 참석자는 야영을 반드시 경험해봐야 하는 일이라 생각한다. 즐거움과 활기를 가까이하려면 일찍 들어가야 음악과 가까운 곳에 캠핑장을 구할 수 있다. 비록 중앙 무대에서 연주하는 곡은 끝날 수 있지만, 축제 곳곳에서는 밤늦게까지 음악을 연주할 수도 있다는 것을 잊지 마세요. 일부 축제들은 어린아이들이 있는 가족들을 위한 특별한 캠핑 공간을 가지고 있습니다.

Question: 일부 참석자들은 음악 축제의 어떤 측면을 경험의 중요한 부분으로 생각합니까?

| | Options |
|---|---|
| **1** | 어린아이 동반 |
| **2** | 야영 ✅ |
| **3** | 밤늦게까지 음악 연주 |
| **4** | 일찍 들어가기 |

<sub>Belebele, Bandarkar et al., ACL 2024, CC BY-SA 4.0</sub>
</details>

<details>
<summary><b>PAWS-X — do these two sentences mean the same thing?</b></summary>

| | English | Korean |
|---|---|---|
| **Sentence 1** | Sulz is a municipality in the district of Vorarlberg in the Austrian province of Feldkirch . | 슐츠는 오스트리아 펠트크릭에 소재한 포르알베르크 구의 지방자치단체이다. |
| **Sentence 2** | Sulz is a municipality in the district of Feldkirch in the Austrian state of Vorarlberg . | 줄츠(Sulz)는 오스트리아의 포르알베르크(Vorarlberg) 주의 펠트키르히(Feldkirch) 지구에 있는 지자체입니다. |

Gold label: **not equivalent**

<sub>PAWS-X, Yang et al., EMNLP 2019. Data source: Google LLC</sub>
</details>

<details>
<summary><b>KorMedMCQA — Korean medical licensing exam</b></summary>

> 17세 여자가 초경을 하지 않아서 병원에 왔다. 유방 발달은 태너기 Ⅳ, 음모 발달은 태너기 I이다. 골반검사에서 질은 맹관으로 막혀 있고, 골반초음파검사에서 자궁은 보이지 않는다. 검사는?

| | Options |
|---|---|
| **1** | FMR1 유전자검사 |
| **2** | 염색체 핵형검사 ✅ |
| **3** | 골밀도검사 |
| **4** | 뇌 자기공명영상 |
| **5** | 진단복강경술 |

<sub>KorMedMCQA, Kweon et al., 2024, CC BY-NC 2.0</sub>
</details>

<details>
<summary><b>MedQA — United States medical licensing exam</b></summary>

> A 29-year-old woman presents to the clinic after several months of weight loss. She noticed a 6.8 kg (15 lb) unintentional weight loss over the preceding several months. She has not changed her diet or exercise habits. She also reports feuding with her boyfriend over the temperature of their shared apartment, as she always feels warmer than he does. The vital signs include: heart rate 110/min and blood pressure 146/78 mm Hg. The physical exam is notable for warm and slightly moist skin. She also exhibits a fine tremor in her hands when her arms are outstretched. The urine pregnancy test is negative. Which of the following is the best single treatment option for this patient?

| | Options |
|---|---|
| **A** | Glucocorticoids |
| **B** | Methimazole ✅ |
| **C** | Propranolol |
| **D** | Radioiodine therapy |

<sub>MedQA, Jin et al., 2020, MIT License</sub>
</details>

Items are shown exactly as distributed upstream, including original spelling. None of these four is among the 100 scored questions for its task.
<!-- examples-end -->

## About the medical numbers

MedQA-English is 89 and KorMedMCQA-Korean is 80. **This is not evidence that Jev is worse at medicine in Korean.** They are two different examinations, written by different bodies, with different difficulty and different subject mixes. This check has no matched English medical arm, so it cannot separate "harder exam" from "harder language". Nothing here supports subtracting one from the other.

What the medical rows *do* support is a comparison between models on the same exam, and there Jev trails: **80 against Luna's 88** on the Korean exam, a gap of +8 points (95% interval +2 to +15). That is the one result in this check that survives its own uncertainty, and it does not favour Jev.

A full 435-question study of KorMedMCQA, with more comparators, is being published separately. Treat the 100-question figure here as a first look, not as that study's result.

## Does the order of your input matter?

Somewhat, and equally in both languages. Swapping the two sentences in a PAWS-X question does not change the correct answer — if A means the same as B, then B means the same as A — so any changed answer is an inconsistency.

![What happens when the two sentences are swapped](docs/figures/order-sensitivity.png)

Jev changes its answer on **13% of Korean questions** and 14% of English ones. For comparison, asking Jev the *identical* question a second time changes 1–2%, so most of that really is the reordering and not ordinary service variation.

The interesting part is what those changes do. In English they are lopsided towards the right answer — 12 wrong→right against 2 right→wrong — so one orientation is simply easier. In Korean they are a coin toss (6 versus 7), changing answers without improving them.

> An earlier version of this document reported a much more alarming figure, based on 5 questions. At 100 questions the rate is 13%, not 60%. The 5 original questions still behave the same way; they were just an unlucky draw. It is a good illustration of why nothing in this document should be read as precise.

## How Jev answers differently

Jev is not a chat model, and that explains most of what you see above.

![Two ways to return the same decision](docs/figures/answer-shape.svg)

Ask a conventional model a multiple-choice question and it writes an answer one token at a time, each token feeding back in before the next is chosen; you then parse the answer out of the finished text. Ask Jev the same question and it returns a probability for every option at once, together with the highest-scoring option. There is no reasoning text and nothing to parse.

That has three practical consequences:

- **Speed.** 221 ms median against Luna's 1110 ms.
- **Price.** Jev is billed on input only — it produces no output tokens at all, where Luna spent about 12 per answer.
- **What you can measure.** Because Jev returns probabilities, you can ask how well-calibrated it is and how accuracy improves if you only accept confident answers. A decision-only response cannot be analysed that way, which is why the confidence analysis in this repository covers Jev and not Luna.

This describes what each interface returns. It is not a claim about how either model works internally.

## How it compares with a mainstream LLM

Across the four Korean-relevant cells the two are close, and neither is consistently ahead. Two things are worth pulling out.

**Jev handles the switch to Korean better.** On the matched tasks, moving from English to Korean costs Luna 3 points on Belebele and 11 on PAWS-X (95% interval −20 to −2, which excludes zero). The same switch costs Jev 1 and 4 points, both intervals containing zero.

![Where the differences lie](docs/figures/differences.png)

**Luna is better on the Korean medical exam**, by 8 points, as described above.

So on the narrow question this document asks — does this model degrade in Korean — Jev does well. On Korean medical knowledge specifically, it does not.

## What this cannot tell you

- **Whether these numbers generalise.** 100 questions per cell, one run, one account, one day. The intervals are wide and unadjusted for multiple comparisons.
- **Whether the models had seen these questions.** All four sets are public. Training exposure is unknown for both.
- **Anything about medical language specifically.** No matched English/Korean medical pair exists here.
- **Anything about longer or generative tasks.** Every question here is a single decision with no conversation, no retrieval and no tools.
- **Exact reproducibility.** Re-running identical requests against the same model version changed about 2% of answers. Results are reproducible to roughly that tolerance, not bit-for-bit.

## Details, data and reproduction

- [Full report and methodology](docs/methodology.md) — sampling, statistics, exclusions, the probability-normalisation amendment
- [Running the experiments yourself](docs/running-experiments.md) — install, restore published results, run new experiments
- [Recorded outputs and frozen source metadata](results/)
- [Clinician review packet](docs/clinician-review.md) — the 40 authored synthetic medical cases, which remain unreviewed and are excluded from the medical score above
- [Live web version](https://ahn-lab.org/jev-korean-benchmark/)

Rebuild every figure without any API calls:

```powershell
.venv/Scripts/python.exe -X utf8 -m jevbench.overview_figure
```

## Provenance and licensing

- Belebele, Bandarkar et al., ACL 2024. [Repository](https://github.com/facebookresearch/belebele). CC BY-SA 4.0.
- PAWS-X, Yang et al., EMNLP 2019. [Repository](https://github.com/google-research-datasets/paws/tree/master/pawsx). Consult the upstream Google PAWS license.
- KorMedMCQA, Kweon et al., 2024. [Dataset](https://huggingface.co/datasets/sean0042/KorMedMCQA). CC BY-NC 2.0.
- MedQA, Jin et al., 2020. [Repository](https://github.com/jind11/MedQA). Accessed via the `GBaker/MedQA-USMLE-4-options` mirror.

This repository distributes code, experiment metadata and model outputs. Benchmark passage and question text is retrieved from upstream sources during preparation and is not bundled in the published results. Source dataset licenses continue to apply to downloaded inputs. Historical exam answers are not updated to current medical or legal guidance.

The service was accessed through an early-access account. Model version, access date and measured token charges are disclosed in the report. No speed or accuracy superiority over any other model is claimed.

---

<!-- lang:ko -->

# Jev의 한국어 성능: 100문항 표본 점검

**[Read in English ↑](#jev-in-korean-a-100-question-sample-check)**

TypeSafe Jev를 한국어 텍스트에 그대로 써도 될까요, 아니면 영어로 번역해서 쓰는 편이 나을까요? 이 문서는 그 질문에 답하기 위한 작고 고정된 재현 가능한 점검입니다. 공개 테스트 세트 네 곳에서 셀당 100문항씩 뽑아 평가했고 모든 응답을 기록했습니다. 이것은 벤치마크가 아니라 표본 점검입니다. 100문항은 약 ±8포인트의 불확실성을 가지므로, 여기서 작은 차이는 발견이라고 할 수 없습니다.

## 요약

- **한국어 독해는 문제없습니다.** 동일한 문항에서 한국어 96점, 영어 97점입니다. 의미 있는 손해가 없습니다.
- **세밀한 의미 판단은 두 언어 모두에서 불안정합니다.** 한국어 76점, 영어 80점입니다. 한국어가 조금 낮지만, 80%는 *어느 쪽 언어에서도* 좋은 점수가 아닙니다. 언어와 무관하게 이 과제가 취약점입니다.
- **지시문을 영어로 쓸 필요는 없습니다.** 한국어 내용에 대해 지시문이 한국어든 영어든 점수 차이는 1~2점 안이었습니다. 지시문을 번역해도 얻는 것이 없습니다.
- **두 의학 점수는 서로 비교할 수 없습니다.** 영어 시험 89점과 한국어 시험 80점은 서로 다른 두 시험이며 언어에 대한 근거가 아닙니다. [의학 점수에 대하여](#의학-점수에-대하여)를 참고하세요.
- **입력 순서를 바꾸면 약 8문항 중 1문항의 답이 바뀝니다.** 두 언어에서 동일하게 나타나므로 한국어에 국한된 문제는 아닙니다.

![동일한 문항을 한국어와 영어로 평가한 결과](docs/figures/korean-check.ko.png)

막대 끝은 점수이고, 연결선은 동일 문항에서의 영어와 한국어 차이입니다. 의학 항목은 대응하는 짝이 없으므로 선 아래에 단일 점으로 표시했습니다.

## 무엇을 평가했는가

<!-- results-table-ko-start -->
| 과제 | 언어 | Jev | Luna | Luna − Jev (95% 구간) |
|---|---|---:|---:|---:|
| Belebele 독해 | 영어 | 97/100 | 98/100 | +1 (−3, +6) |
| Belebele 독해 | 한국어 | 96/100 | 95/100 | −1 (−5, +3) |
| PAWS-X 의미 동등성 | 영어 | 80/100 | 83/100 | +3 (−3, +10) |
| PAWS-X 의미 동등성 | 한국어 | 76/100 | 72/100 | −4 (−14, +5) |
| MedQA 시험 | 영어 | 89/100 | 84/100 | −5 (−11, +0) |
| KorMedMCQA 시험 | 한국어 | 80/100 | 88/100 | **+8 (+2, +15)** |
<!-- results-table-ko-end -->

공개 테스트 세트 네 곳을 사용했습니다. **Belebele**은 독해, **PAWS-X**는 두 문장의 의미가 같은지 판단하는 과제, **KorMedMCQA**는 한국 의사 국가시험, **MedQA**는 그에 대응하는 미국 시험입니다. Belebele과 PAWS-X는 동일한 문항을 전문 번역한 것이므로 이 항목들은 실제로 언어 효과를 분리해 줍니다. 두 의학 세트는 서로 관계없는 시험입니다.

Luna는 추론 강도 `none`으로 설정한 `gpt-5.6-luna`이며, 공정한 경쟁 상대라기보다 익숙한 기준점으로 포함했습니다. [주요 LLM과의 비교](#주요-llm과의-비교)를 참고하세요.

모든 셀이 100문항이므로 모든 수치에 약 ±8포인트의 불확실성이 있습니다. 표 전체에서 0을 벗어나는 차이는 하나뿐입니다. 한국어 의학 시험에서 Luna가 8점 높습니다.

<!-- examples-ko-start -->
## 실제 문항은 어떻게 생겼는가

출처별로 실제 문항 하나씩이며, 이 연구에서 채점하지 **않은** 문항 중에서 무작위로 골랐습니다. 형식을 보면 수치의 의미를 이해하는 데 큰 도움이 됩니다.

<details>
<summary><b>Belebele — 독해, 두 언어의 동일 문항</b></summary>

**영어** · 지문

> For some festivals, the vast majority of the attendants to music festivals decide to camp on site, and most attendants consider it a vital part of the experience. If you want to be close to the action you're going to have to get in early to get a camping site close to the music. Remember that even though music on the main stages may have finished, there may be sections of the festival that will keep playing music until late into the night. Some festivals have special camping areas for families with young children.

문항: What aspect of music festivals do some attendants consider to be a crucial part of the experience?

| | 선택지 |
|---|---|
| **1** | Bringing young children |
| **2** | Camping on site ✅ |
| **3** | Music playing late into the night |
| **4** | Getting in early |

**한국어** · 지문

> 몇몇 축제들에서 음악 축제에 참석하는 많은 사람들이 그 자리에서 야영하기로 결정하고, 대부분의 참석자는 야영을 반드시 경험해봐야 하는 일이라 생각한다. 즐거움과 활기를 가까이하려면 일찍 들어가야 음악과 가까운 곳에 캠핑장을 구할 수 있다. 비록 중앙 무대에서 연주하는 곡은 끝날 수 있지만, 축제 곳곳에서는 밤늦게까지 음악을 연주할 수도 있다는 것을 잊지 마세요. 일부 축제들은 어린아이들이 있는 가족들을 위한 특별한 캠핑 공간을 가지고 있습니다.

문항: 일부 참석자들은 음악 축제의 어떤 측면을 경험의 중요한 부분으로 생각합니까?

| | 선택지 |
|---|---|
| **1** | 어린아이 동반 |
| **2** | 야영 ✅ |
| **3** | 밤늦게까지 음악 연주 |
| **4** | 일찍 들어가기 |

<sub>Belebele, Bandarkar et al., ACL 2024, CC BY-SA 4.0</sub>
</details>

<details>
<summary><b>PAWS-X — 이 두 문장은 같은 뜻입니까?</b></summary>

| | 영어 | 한국어 |
|---|---|---|
| **문장 1** | Sulz is a municipality in the district of Vorarlberg in the Austrian province of Feldkirch . | 슐츠는 오스트리아 펠트크릭에 소재한 포르알베르크 구의 지방자치단체이다. |
| **문장 2** | Sulz is a municipality in the district of Feldkirch in the Austrian state of Vorarlberg . | 줄츠(Sulz)는 오스트리아의 포르알베르크(Vorarlberg) 주의 펠트키르히(Feldkirch) 지구에 있는 지자체입니다. |

정답 레이블: **동등하지 않음**

<sub>PAWS-X, Yang et al., EMNLP 2019. 데이터 출처: Google LLC</sub>
</details>

<details>
<summary><b>KorMedMCQA — 한국 의사 국가시험</b></summary>

> 17세 여자가 초경을 하지 않아서 병원에 왔다. 유방 발달은 태너기 Ⅳ, 음모 발달은 태너기 I이다. 골반검사에서 질은 맹관으로 막혀 있고, 골반초음파검사에서 자궁은 보이지 않는다. 검사는?

| | 선택지 |
|---|---|
| **1** | FMR1 유전자검사 |
| **2** | 염색체 핵형검사 ✅ |
| **3** | 골밀도검사 |
| **4** | 뇌 자기공명영상 |
| **5** | 진단복강경술 |

<sub>KorMedMCQA, Kweon et al., 2024, CC BY-NC 2.0</sub>
</details>

<details>
<summary><b>MedQA — 미국 의사 면허시험</b></summary>

> A 29-year-old woman presents to the clinic after several months of weight loss. She noticed a 6.8 kg (15 lb) unintentional weight loss over the preceding several months. She has not changed her diet or exercise habits. She also reports feuding with her boyfriend over the temperature of their shared apartment, as she always feels warmer than he does. The vital signs include: heart rate 110/min and blood pressure 146/78 mm Hg. The physical exam is notable for warm and slightly moist skin. She also exhibits a fine tremor in her hands when her arms are outstretched. The urine pregnancy test is negative. Which of the following is the best single treatment option for this patient?

| | 선택지 |
|---|---|
| **A** | Glucocorticoids |
| **B** | Methimazole ✅ |
| **C** | Propranolol |
| **D** | Radioiodine therapy |

<sub>MedQA, Jin et al., 2020, MIT License</sub>
</details>

문항은 원본 배포 형태 그대로이며 원문 표기를 유지합니다. 네 문항 모두 해당 과제의 채점된 100문항에 포함되지 않습니다.
<!-- examples-ko-end -->

## 의학 점수에 대하여

MedQA 영어가 89점이고 KorMedMCQA 한국어가 80점입니다. **이것은 Jev가 한국어 의학에서 더 나쁘다는 근거가 아닙니다.** 두 시험은 출제 기관도, 난이도도, 과목 구성도 다릅니다. 이 점검에는 대응하는 영어 의학 항목이 없으므로 "더 어려운 시험"과 "더 어려운 언어"를 구분할 수 없습니다. 두 점수를 빼는 것을 뒷받침하는 근거는 여기에 없습니다.

의학 항목이 뒷받침하는 것은 동일한 시험에서의 모델 간 비교이며, 거기서 Jev는 뒤집니다. 한국어 시험에서 **Luna 88점에 대해 Jev 80점**으로, +8포인트 차이입니다(95% 구간 +2 ~ +15). 이 점검에서 자체 불확실성을 넘어서는 유일한 결과이며, Jev에게 유리하지 않습니다.

더 많은 비교 모델을 포함한 435문항 규모의 KorMedMCQA 연구는 별도로 발표될 예정입니다. 여기의 100문항 수치는 그 연구의 결과가 아니라 첫인상으로 보아 주십시오.

## 입력 순서가 중요한가

어느 정도 그렇고, 두 언어에서 비슷합니다. PAWS-X 문항에서 두 문장의 순서를 바꾸어도 정답은 달라지지 않습니다. A가 B와 같은 뜻이면 B도 A와 같은 뜻이기 때문입니다. 따라서 답이 바뀌면 그것은 비일관성입니다.

![두 문장의 순서를 바꾸면 생기는 일](docs/figures/order-sensitivity.ko.png)

Jev는 **한국어 문항의 13%**, 영어 문항의 14%에서 답을 바꿉니다. 비교를 위해 *동일한* 질문을 한 번 더 물었을 때는 1~2%만 바뀌므로, 대부분은 일반적인 서비스 변동이 아니라 순서 변경에 따른 것입니다.

흥미로운 부분은 그 변화의 방향입니다. 영어에서는 정답 쪽으로 치우쳐 있습니다. 오답에서 정답으로 12건, 정답에서 오답으로 2건이므로 한쪽 순서가 단순히 더 쉽습니다. 한국어에서는 동전 던지기에 가깝습니다(6건 대 7건). 답은 바뀌지만 나아지지는 않습니다.

> 이 문서의 이전 판은 5문항에 근거해 훨씬 심각한 수치를 보고했습니다. 100문항에서는 60%가 아니라 13%입니다. 원래의 5문항은 지금도 같은 방식으로 동작하며, 단지 운 나쁜 표본이었을 뿐입니다. 이 문서의 어떤 수치도 정밀한 값으로 읽어서는 안 되는 이유를 잘 보여 줍니다.

## Jev의 응답 방식은 무엇이 다른가

Jev는 대화형 모델이 아니며, 위에서 본 내용의 상당 부분이 여기에서 설명됩니다.

![같은 결정을 돌려주는 두 가지 방식](docs/figures/answer-shape.ko.svg)

일반적인 모델에 객관식 문항을 물으면 토큰을 하나씩 생성하며 답을 씁니다. 각 토큰은 다음 토큰을 고르기 전에 다시 입력으로 들어가고, 완성된 텍스트에서 답을 파싱해야 합니다. 같은 문항을 Jev에 물으면 모든 선택지의 확률을 한 번에 돌려주고 가장 높은 선택지를 함께 제시합니다. 근거 텍스트도 없고 파싱할 것도 없습니다.

여기에서 세 가지 실질적인 차이가 나옵니다.

- **속도.** 중앙값 221ms로, Luna의 1110ms와 대비됩니다.
- **비용.** Jev는 입력에만 과금됩니다. 출력 토큰이 전혀 없으며, Luna는 답변당 약 12개를 사용했습니다.
- **측정할 수 있는 것.** Jev는 확률을 돌려주므로 보정(calibration)이 얼마나 잘 되어 있는지, 확신도가 높은 답만 받아들이면 정확도가 얼마나 오르는지 물을 수 있습니다. 결정만 돌려주는 응답은 그렇게 분석할 수 없으며, 이 저장소의 확신도 분석이 Jev에만 있고 Luna에는 없는 이유가 그것입니다.

이는 각 인터페이스가 무엇을 돌려주는지에 대한 설명이며, 두 모델의 내부 동작에 대한 주장이 아닙니다.

## 주요 LLM과의 비교

한국어와 관련된 네 개 셀에서 둘은 접전이며 어느 쪽도 일관되게 앞서지 않습니다. 두 가지를 짚을 만합니다.

**한국어로의 전환은 Jev가 더 잘 견딥니다.** 대응 과제에서 영어에서 한국어로 옮길 때 Luna는 Belebele에서 3점, PAWS-X에서 11점을 잃습니다(95% 구간 −20 ~ −2로 0을 포함하지 않습니다). 같은 전환에서 Jev는 1점과 4점을 잃으며, 두 구간 모두 0을 포함합니다.

![차이가 실제로 나타나는 지점](docs/figures/differences.ko.png)

**한국어 의학 시험에서는 Luna가 8점 앞섭니다.** 위에서 설명한 대로입니다.

따라서 이 문서가 묻는 좁은 질문, 즉 이 모델이 한국어에서 성능이 떨어지는가에 대해서는 Jev가 잘 버팁니다. 다만 한국어 의학 지식에 한해서는 그렇지 않습니다.

## 이 문서가 답할 수 없는 것

- **이 수치가 일반화되는지.** 셀당 100문항, 1회 실행, 단일 계정, 하루 동안의 결과입니다. 구간은 넓고 다중 비교 보정을 하지 않았습니다.
- **모델이 이 문항들을 학습에서 보았는지.** 네 세트 모두 공개 자료이며, 두 모델 모두 학습 노출 여부를 알 수 없습니다.
- **의학 언어에 대한 것.** 대응하는 영어/한국어 의학 쌍이 여기에 없습니다.
- **더 길거나 생성적인 과제에 대한 것.** 여기의 모든 문항은 대화도 검색도 도구도 없는 단일 결정입니다.
- **완전한 재현성.** 동일한 요청을 같은 모델 버전으로 다시 보냈을 때 약 2%의 답이 달라졌습니다. 비트 단위가 아니라 대략 그 정도의 오차 범위에서 재현됩니다.

## 상세 자료, 데이터, 재현

- [전체 보고서와 평가 방법](docs/methodology.md) — 표집, 통계, 제외 기준, 확률 정규화 수정 사항
- [직접 실험 실행하기](docs/running-experiments.md) — 설치, 공개된 결과 복원, 새 실험 실행
- [기록된 출력과 고정된 원본 메타데이터](results/)
- [임상의 검토 패킷](docs/clinician-review.md) — 직접 작성한 40개의 합성 의학 사례이며, 아직 검토되지 않았고 위 의학 점수에서 제외되었습니다
- [웹 버전](https://ahn-lab.org/jev-korean-benchmark/)

API 호출 없이 모든 그림을 다시 생성하려면 다음을 실행하세요.

```powershell
.venv/Scripts/python.exe -X utf8 -m jevbench.overview_figure
```

## 출처와 라이선스

- Belebele, Bandarkar et al., ACL 2024. [저장소](https://github.com/facebookresearch/belebele). CC BY-SA 4.0.
- PAWS-X, Yang et al., EMNLP 2019. [저장소](https://github.com/google-research-datasets/paws/tree/master/pawsx). 상위 Google PAWS 라이선스를 확인하세요.
- KorMedMCQA, Kweon et al., 2024. [데이터셋](https://huggingface.co/datasets/sean0042/KorMedMCQA). CC BY-NC 2.0.
- MedQA, Jin et al., 2020. [저장소](https://github.com/jind11/MedQA). `GBaker/MedQA-USMLE-4-options` 미러를 통해 접근했습니다.

이 저장소는 코드, 실험 메타데이터, 모델 출력을 배포합니다. 벤치마크 지문과 문항 텍스트는 준비 과정에서 상위 출처로부터 내려받으며 공개된 결과에 포함되지 않습니다. 내려받은 입력에는 원본 데이터셋 라이선스가 계속 적용됩니다. 과거 시험의 정답은 현재의 의학적·법적 지침에 맞추어 갱신하지 않았습니다.

이 서비스는 얼리 액세스 계정으로 접근했습니다. 모델 버전, 접근 일자, 측정된 토큰 요금은 보고서에 공개되어 있습니다. 다른 모델에 대한 속도나 정확도 우위를 주장하지 않습니다.
