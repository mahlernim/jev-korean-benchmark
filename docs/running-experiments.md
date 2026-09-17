# Running the experiments

Everything on the [main page](../README.md) can be reproduced without spending anything: the published responses are recorded, and both the reports and the figures rebuild offline. Live runs are only needed if you want new inference.

## Install

Tested with Python 3.14.2 on Windows. Python 3.10 or newer is required by the SDK. Offline analysis and preparation are portable. Live runs currently use a Windows advisory process lock.

```powershell
uv venv .venv
uv pip install --python .venv/Scripts/python.exe -r requirements.txt
.venv/Scripts/python.exe -X utf8 -m pytest -q
```

For live calls, put a `TYPESAFE_API_KEY` or `TYPESAFE_KEY` assignment in a local `typesafe.env`. The Luna comparison additionally needs `OPENAI_API_KEY` in the same file. `typesafe.env` is ignored by Git — never commit credentials. The live runner reads it directly, disables SDK retries, and implements two logged retries of transient failures itself.

## Reproduce without any model calls

```powershell
# Download pinned sources and reconstruct the exact manifest.
.venv/Scripts/python.exe -X utf8 -m jevbench prepare

# Import the published responses and rebuild the reports.
.venv/Scripts/python.exe -X utf8 -m jevbench restore
.venv/Scripts/python.exe -X utf8 -m jevbench report

# Rebuild every figure.
.venv/Scripts/python.exe -X utf8 -m jevbench.figures
.venv/Scripts/python.exe -X utf8 -m jevbench.overview_figure
.venv/Scripts/python.exe -X utf8 -m jevbench.answer_shape
```

## The rule that governs every experiment here

**A completed experiment is immutable.** New inference, or any change to reasoning settings, prompts, output format or source cases, requires a *new* experiment rather than editing or rerunning completed records.

Successful or terminally failed evaluations are never called again by resume. An intent file without a corresponding outcome is treated as uncertain and stops the runner rather than silently resending. Fatal validation or API failures require inspection and a new experiment. The budget ceiling is an estimate from published prices, conservative for failed calls; it is not an account-side spending limit.

## The original pilot

Five stages, run in order, inspecting each stage report before continuing.

```powershell
.venv/Scripts/python.exe -X utf8 -m jevbench prepare --experiment replication-01 --model jev-1.13.0
.venv/Scripts/python.exe -X utf8 -m jevbench run --experiment replication-01 --stage 0
.venv/Scripts/python.exe -X utf8 -m jevbench run --experiment replication-01 --stage 1
```

Before Stage 2, inspect the generated `medical_input_audit.md` and record a `medical_input_review.json` alongside the manifest. It must contain the manifest's SHA-256 in `manifest_hash`, `all_selected_text_complete: true`, and the reviewer, date, scope and any caveats. This is an input-completeness audit, not a clinical correctness endorsement. Do not mark it complete without checking every selected input.

```powershell
.venv/Scripts/python.exe -X utf8 -m jevbench run --experiment replication-01 --stage 2
.venv/Scripts/python.exe -X utf8 -m jevbench run --experiment replication-01 --stage 3
.venv/Scripts/python.exe -X utf8 -m jevbench run --experiment replication-01 --stage 4
.venv/Scripts/python.exe -X utf8 -m jevbench report --experiment replication-01
```

## English MedQA extension

100 frozen questions, four concurrent requests per provider.

```powershell
.venv/Scripts/python.exe -X utf8 -m jevbench.medqa_prepare
.venv/Scripts/python.exe -X utf8 -m jevbench.medqa_publish --restore
```

The live runner is `python -m jevbench.medqa_run`, with `--limit 10` for an initial usage check. Successful calls are preserved on resume. Generate its report with `python -m jevbench.medqa_publish`.

## Luna comparison

Fixed experiment `luna-none-v1`: reasoning effort `none`, decision-only structured output, sequential requests, $0.25 estimated-cost ceiling.

```powershell
# Rebuild the original Jev inputs first.
.venv/Scripts/python.exe -X utf8 -m jevbench.luna prepare
.venv/Scripts/python.exe -X utf8 -m jevbench.luna run --stage 0 --limit 10
# Inspect usage, then finish Stage 0 and run Stages 1 through 4 separately.
.venv/Scripts/python.exe -X utf8 -m jevbench.luna run --stage 0
.venv/Scripts/python.exe -X utf8 -m jevbench.luna run --stage 1
```

After downloading the published Luna evidence, `python -m jevbench.luna restore` reconstructs its local response records and reports without API calls.

## Sentence-order experiment

800 evaluations: the 100 PAWS-X questions in both orientations, both languages, both models. Both orientations are re-run inside this experiment so the comparison is internally matched rather than paired across experiments.

```powershell
.venv/Scripts/python.exe -X utf8 -m jevbench.order_sensitivity prepare
.venv/Scripts/python.exe -X utf8 -m jevbench.order_sensitivity run --limit 10
# Inspect usage, then run the remainder.
.venv/Scripts/python.exe -X utf8 -m jevbench.order_sensitivity run
.venv/Scripts/python.exe -X utf8 -m jevbench.order_sensitivity report
```

Its control sends the unchanged requests a second time, which bounds ordinary service nondeterminism. It refuses to run unless the source manifest hash and every request hash still match.

```powershell
.venv/Scripts/python.exe -X utf8 -m jevbench.order_repeat prepare
.venv/Scripts/python.exe -X utf8 -m jevbench.order_repeat run
.venv/Scripts/python.exe -X utf8 -m jevbench.order_repeat report
```

## Unreviewed synthetic medical cases

The 40 authored medical cases have not been reviewed by a clinician. Their proposed labels and translations are in the generated review packet and the [source file](../jevbench/synthetic.py). They must not be presented as a validated clinical benchmark. Preserve the original results when adding review or correcting cases.

<!-- lang:ko -->

# 실험 실행하기

[메인 페이지](../README.md)의 모든 내용은 비용 없이 재현할 수 있습니다. 공개된 응답이 기록되어 있으며 보고서와 그림 모두 오프라인에서 다시 생성됩니다. 라이브 실행은 새로운 추론이 필요할 때만 사용합니다.

## 설치

Windows에서 Python 3.14.2로 테스트했습니다. SDK는 Python 3.10 이상을 요구합니다. 오프라인 분석과 준비 과정은 이식 가능합니다. 라이브 실행은 현재 Windows 권고 프로세스 잠금을 사용합니다.

```powershell
uv venv .venv
uv pip install --python .venv/Scripts/python.exe -r requirements.txt
.venv/Scripts/python.exe -X utf8 -m pytest -q
```

라이브 호출을 하려면 로컬 `typesafe.env`에 `TYPESAFE_API_KEY` 또는 `TYPESAFE_KEY`를 지정하세요. Luna 비교에는 같은 파일에 `OPENAI_API_KEY`도 필요합니다. `typesafe.env`는 Git에서 무시되며, 자격 증명은 절대 커밋하지 마십시오. 라이브 러너는 이 파일을 직접 읽고, SDK 재시도를 비활성화한 뒤, 일시적 실패에 대해 자체적으로 두 번의 기록된 재시도를 수행합니다.

## 모델 호출 없이 재현하기

```powershell
# 고정된 원본을 내려받아 매니페스트를 그대로 재구성합니다.
.venv/Scripts/python.exe -X utf8 -m jevbench prepare

# 공개된 응답을 가져와 보고서를 다시 만듭니다.
.venv/Scripts/python.exe -X utf8 -m jevbench restore
.venv/Scripts/python.exe -X utf8 -m jevbench report

# 모든 그림을 다시 생성합니다.
.venv/Scripts/python.exe -X utf8 -m jevbench.figures
.venv/Scripts/python.exe -X utf8 -m jevbench.overview_figure
.venv/Scripts/python.exe -X utf8 -m jevbench.answer_shape
```

## 모든 실험에 적용되는 원칙

**완료된 실험은 변경하지 않습니다.** 새로운 추론, 또는 추론 설정·프롬프트·출력 형식·원본 사례의 변경은 기존 기록을 수정하거나 다시 실행하는 대신 *새로운* 실험을 요구합니다.

성공했거나 최종적으로 실패한 평가는 재개 시 다시 호출되지 않습니다. 결과가 없는 의도(intent) 파일은 불확실한 것으로 간주되어, 조용히 재전송하지 않고 러너를 중단시킵니다. 치명적인 검증 또는 API 실패는 점검과 새 실험을 필요로 합니다. 예산 상한은 공개 가격에 기반한 추정치로 실패한 호출에 대해 보수적이며, 계정 차원의 지출 한도가 아닙니다.

## 원래의 파일럿

다섯 단계를 순서대로 실행하며, 다음 단계로 넘어가기 전에 각 단계 보고서를 확인합니다.

```powershell
.venv/Scripts/python.exe -X utf8 -m jevbench prepare --experiment replication-01 --model jev-1.13.0
.venv/Scripts/python.exe -X utf8 -m jevbench run --experiment replication-01 --stage 0
.venv/Scripts/python.exe -X utf8 -m jevbench run --experiment replication-01 --stage 1
```

Stage 2 이전에 생성된 `medical_input_audit.md`를 검토하고 매니페스트와 함께 `medical_input_review.json`을 기록해야 합니다. 이 파일에는 매니페스트의 SHA-256이 `manifest_hash`에 들어가야 하며, `all_selected_text_complete: true`와 검토자, 날짜, 범위, 유의 사항이 포함되어야 합니다. 이것은 입력 완전성 감사이며 임상적 정확성에 대한 보증이 아닙니다. 선택된 모든 입력을 확인하지 않고 완료로 표시하지 마십시오.

```powershell
.venv/Scripts/python.exe -X utf8 -m jevbench run --experiment replication-01 --stage 2
.venv/Scripts/python.exe -X utf8 -m jevbench run --experiment replication-01 --stage 3
.venv/Scripts/python.exe -X utf8 -m jevbench run --experiment replication-01 --stage 4
.venv/Scripts/python.exe -X utf8 -m jevbench report --experiment replication-01
```

## 영어 MedQA 확장

고정된 100문항, 제공자당 4개의 동시 요청을 사용합니다.

```powershell
.venv/Scripts/python.exe -X utf8 -m jevbench.medqa_prepare
.venv/Scripts/python.exe -X utf8 -m jevbench.medqa_publish --restore
```

라이브 러너는 `python -m jevbench.medqa_run`이며, 최초 사용량 확인에는 `--limit 10`을 씁니다. 성공한 호출은 재개 시 보존됩니다. 보고서는 `python -m jevbench.medqa_publish`로 생성합니다.

## Luna 비교

고정 실험 `luna-none-v1`입니다. 추론 강도 `none`, 결정만 포함하는 구조화 출력, 순차 요청, 추정 비용 상한 $0.25를 사용합니다.

```powershell
# 먼저 원래의 Jev 입력을 다시 만듭니다.
.venv/Scripts/python.exe -X utf8 -m jevbench.luna prepare
.venv/Scripts/python.exe -X utf8 -m jevbench.luna run --stage 0 --limit 10
# 사용량을 확인한 뒤 Stage 0을 마치고 Stage 1부터 4까지 개별적으로 실행합니다.
.venv/Scripts/python.exe -X utf8 -m jevbench.luna run --stage 0
.venv/Scripts/python.exe -X utf8 -m jevbench.luna run --stage 1
```

공개된 Luna 증거를 내려받은 뒤에는 `python -m jevbench.luna restore`가 API 호출 없이 로컬 응답 기록과 보고서를 재구성합니다.

## 문장 순서 실험

800개 평가입니다. PAWS-X 100문항을 두 가지 순서, 두 언어, 두 모델에 대해 실행합니다. 두 순서 모두 이 실험 안에서 다시 실행하므로, 실험 간 대응이 아니라 내부적으로 대응된 비교가 됩니다.

```powershell
.venv/Scripts/python.exe -X utf8 -m jevbench.order_sensitivity prepare
.venv/Scripts/python.exe -X utf8 -m jevbench.order_sensitivity run --limit 10
# 사용량을 확인한 뒤 나머지를 실행합니다.
.venv/Scripts/python.exe -X utf8 -m jevbench.order_sensitivity run
.venv/Scripts/python.exe -X utf8 -m jevbench.order_sensitivity report
```

대조 실험은 변경하지 않은 요청을 한 번 더 보내 일반적인 서비스 비결정성의 범위를 측정합니다. 원본 매니페스트 해시와 모든 요청 해시가 일치하지 않으면 실행을 거부합니다.

```powershell
.venv/Scripts/python.exe -X utf8 -m jevbench.order_repeat prepare
.venv/Scripts/python.exe -X utf8 -m jevbench.order_repeat run
.venv/Scripts/python.exe -X utf8 -m jevbench.order_repeat report
```

## 검토되지 않은 합성 의학 사례

직접 작성한 40개의 의학 사례는 임상의의 검토를 받지 않았습니다. 제안된 레이블과 번역은 생성된 검토 패킷과 [소스 파일](../jevbench/synthetic.py)에 있습니다. 이를 검증된 임상 벤치마크로 제시해서는 안 됩니다. 검토를 추가하거나 사례를 수정할 때에도 원래 결과는 보존하십시오.
