"""Build a reviewable, static report and an allowlisted reproducibility bundle."""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path

import markdown

from .common import ROOT, canonical, digest, filehash, load_manifest, now, read, write_new
from .report import metrics, report
from .runner import records,raw_records


GENERATED = ROOT / 'results' / 'generated'


def export(experiment="pilot-v1"):
    report(experiment)
    manifest=load_manifest(ROOT/"data"/experiment/"manifest.json")
    run_dir=ROOT/"runs"/experiment
    attempts=records(run_dir)
    if len({r['eval_id'] for r in attempts if r.get('terminal')})!=len(manifest['evaluations']):
        raise ValueError("Finish planned evaluations before publication export")
    dest=ROOT/"results"; dest.mkdir(exist_ok=True)
    docs=ROOT/"docs"; docs.mkdir(exist_ok=True)
    def put(path,value):
        path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    put(dest/"source-lock.json",manifest['sources'])
    put(dest/"experiment-lock.json",dict(experiment=experiment,created_at=manifest['created_at'],manifest_hash=manifest['sha256'],seed=manifest['seed'],model=manifest['model']))
    cases=read(ROOT/"data"/experiment/"cases.json")
    case_index={c['id']:{k:c[k] for k in ('id','source_id','passage_id','task','year','category','pair_id','review_status') if k in c} for c in cases}
    public_evals=[]
    for e in manifest['evaluations']:
        row={k:v for k,v in e.items() if k!='request'}
        row['source']=case_index[e['case_id']]
        row['instructions']=e['request']['questions']['answer']['instructions']
        row['option_ids']=list(e['request']['questions']['answer'].get('criteria',{}))
        public_evals.append(row)
    put(dest/"evaluation-index.json",public_evals)
    put(dest/"exclusions.json",manifest['exclusions'])
    put(dest/"sampling-audit.json",manifest['audit'])
    # Attempt records contain no request body, credentials, headers, or exception text.
    (dest/"responses.jsonl").write_text("".join(canonical(r)+"\n" for r in sorted(attempts,key=lambda r:r['started_at'])),encoding="utf-8")
    (dest/"original-attempts.jsonl").write_text("".join(canonical(r)+"\n" for r in sorted(raw_records(run_dir),key=lambda r:r['started_at'])),encoding="utf-8")
    put(dest/'adjudications.json',[read(p) for p in sorted((run_dir/'adjudications').glob('*.json'))])
    put(dest/"timing.json",[read(p) for p in sorted((run_dir/'timing').glob('*.json'))])
    put(dest/"runtime-environment.json",[read(p) for p in sorted((run_dir/'invocations').glob('*.json'))])
    put(dest/"medical-input-review.json",read(ROOT/'data'/experiment/'medical_input_review.json'))
    for s in range(5):
        put(dest/f"stage-{s}.json",read(run_dir/'reports'/f'stage-{s}.json'))
        (docs/f"stage-{s}.md").write_text((run_dir/'reports'/f'stage-{s}.md').read_text(encoding='utf-8'),encoding='utf-8')
    lookup={e['eval_id']:e for e in manifest['evaluations']}
    fields=['eval_id','case_id','stage','task','condition','model','started_at','latency_ms','input_tokens','output_tokens','estimated_cost_usd','gold','prediction','correct','rank_confidence','brier','log_loss']
    with (dest/'predictions.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields); writer.writeheader()
        for r in sorted(attempts,key=lambda r:r['started_at']):
            if r['status']!='success': continue
            e=lookup[r['eval_id']]; score=r['score']
            writer.writerow({**{k:e[k] for k in ['eval_id','case_id','stage','task','condition','gold']},
                **{k:r[k] for k in ['started_at','latency_ms']},
                **{k:score[k] for k in ['input_tokens','estimated_cost_usd','prediction','correct','rank_confidence','brier','log_loss']},
                'model':r['raw_response']['model'],'output_tokens':r['raw_response']['usage']['output_tokens']})
    build_narrative(manifest,attempts)
    # A downloadable bundle only includes reviewed result files, never workspace globs.
    import zipfile
    with zipfile.ZipFile(docs/'results.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(dest.iterdir()):
            if p.is_file(): z.write(p,'results/'+p.name)
    render_web()
    print('Publication package built in docs/ and results/. No external publication performed.')


def restore(experiment="pilot-v1"):
    from .prepare import prepare
    prepare(experiment)
    manifest=load_manifest(ROOT/'data'/experiment/'manifest.json')
    lock=read(ROOT/'results'/'experiment-lock.json')
    if manifest['sha256']!=lock['manifest_hash']: raise ValueError('Released manifest mismatch')
    run_dir=ROOT/'runs'/experiment
    for line in (ROOT/'results'/'original-attempts.jsonl').read_text(encoding='utf-8').splitlines():
        r=json.loads(line)
        if r['manifest_hash']!=manifest['sha256']: raise ValueError('Response manifest mismatch')
        p=run_dir/'attempts'/(digest(r['eval_id'])[:24]+f"-{r['attempt']}.json")
        if p.exists():
            if read(p)!=r: raise ValueError('Existing attempt differs')
        else: write_new(p,r)
    for r in read(ROOT/'results'/'adjudications.json'):
        p=run_dir/'adjudications'/(digest(r['eval_id'])[:24]+f"-{r['attempt']}.json")
        if not p.exists(): write_new(p,r)
    for i,t in enumerate(read(ROOT/'results'/'timing.json')):
        p=run_dir/'timing'/(t['started_at'].replace(':','-')+'.json')
        if not p.exists(): write_new(p,t)
    report(experiment)
    print('Restored recorded outputs and regenerated reports without model calls.')


def build_narrative(manifest,attempts):
    docs=ROOT/'docs'
    stages={s:read(ROOT/'results'/f'stage-{s}.json') for s in range(5)}
    look={e['eval_id']:e for e in manifest['evaluations']}
    good=[(look[r['eval_id']],r) for r in attempts if r['status']=='success']
    total=metrics(good)
    model=', '.join(sorted({r['raw_response']['model'] for e,r in good}))
    api_seconds=sum(r['latency_ms'] for r in attempts)/1000
    wall=sum(s['runtime']['recorded_invocation_wall_seconds'] for s in stages.values())
    get=lambda stage,key:stages[stage]['groups'][key]
    b_en,b_ko=get(1,'belebele/en_en'),get(1,'belebele/ko_ko')
    p_en,p_ko=get(1,'pawsx/en_en'),get(1,'pawsx/ko_ko')
    med=get(2,'kormed/ko_ko')
    lines=["# An early look at Jev on Korean and medical text", "", "## A small early-access pilot", "",
        f"We evaluated TypeSafe **{model}** on September 17, 2026, using 1,036 planned evaluations and {len(attempts):,} sequential API attempts including retries. The study compares English and Korean reading comprehension and paraphrase decisions, tests Korean medical examination knowledge, and separately explores simple synthetic medical-note interpretation.","",
        f"On 100 matched questions, Belebele accuracy was **{b_en['accuracy']:.0%} in English and {b_ko['accuracy']:.0%} in Korean with Korean instructions**. On 100 matched PAWS-X pairs, the corresponding values were **{p_en['accuracy']:.0%} and {p_ko['accuracy']:.0%}**. Korean medical examination accuracy was **{med['accuracy']:.0%}** on a screened 100-question doctor subset.","",
        f"The analysis contains {len(good):,} scored responses after the disclosed probability-rounding amendment. The total token-based cost estimate was **${total['cost_usd']:.5f} USD**, and summed client-observed API call time was **{api_seconds:.1f} seconds**. These measurements describe this service, account, workload and run. No other model was evaluated, so this report makes no comparative speed or cost claim.","",
        "The central finding is task dependence. Good reading-comprehension performance does not establish equally strong semantic discrimination, medical competence, or dependable confidence estimates. The small sample and unknown training exposure limit generalization.","",
        "[Detailed methodology](methodology.html) · [Download recorded results](results.zip)","",
        "## Experiment design", "",
        "The sample, labels, prompts and 20 robustness cases were frozen before inference. Jev received one question per request and no tools, retrieval or generated rationale. Choice handled multiple-choice questions; Noul returned a yes/no equivalence probability. This evaluates an observable decision task without requiring Jev to behave like a chat model.","",
        "| Component | Source cases | Conditions / calls |", "|---|---:|---:|",
        "| Development only | 12 | 3 / 36 |","| Belebele reading comprehension | 100 | 3 / 300 |","| PAWS-X paraphrase identification | 100 | 3 / 300 |","| KorMedMCQA doctor questions | 100 | 2 / 200 |","| Synthetic medical notes, unreviewed | 40 | 3 / 120 |","| Robustness | 20 reused cases | 4 extra / 80 |","",
        "There are 340 scored source cases, plus 12 development cases. The 1,036 calls are not independent questions. Synthetic medical examples include related minimal pairs.","",
        "## General language understanding", "",
        "EN/EN means English content and instructions. KO/EN means Korean content with English instructions. KO/KO means Korean content and instructions. Public answer-option text follows content language.","",
        "| Task | Condition | Correct / 100 | Accuracy, 95% Wilson interval | Brier | Log loss |","|---|---|---:|---:|---:|---:|"]
    for key,m in stages[1]['groups'].items():
        task,cond=key.split('/'); lo,hi=m['accuracy_ci95']
        lines.append(f"| {task} | {cond.upper().replace('_','/')} | {m['correct']} | {m['accuracy']:.0%}, {lo:.1%}–{hi:.1%} | {m['brier']:.3f} | {m['log_loss']:.3f} |")
    lines += ["", "The English-to-Korean comparison holds the underlying item fixed, using existing translations. Switching instruction language is a separate comparison. A one-point difference here is just one answer and should not be interpreted as evidence that one prompt language is generally better.","",
        "| Paired comparison | Difference in percentage points | 95% paired bootstrap interval |", "|---|---:|---:|"]
    for key,d in stages[1]['paired'].items():
        lines.append(f"| {key} | {d['difference']*100:+.1f} | {d['ci95'][0]*100:+.1f} to {d['ci95'][1]*100:+.1f} |")
    lines += ["", "Bootstrap intervals are descriptive and can have boundary artifacts when there are very few discordant pairs. This pilot is not powered for small language differences, and no multiple-comparison-adjusted claims are made.","",
        "## Medical knowledge", "", "The KorMedMCQA doctor sample uses original Korean examination questions and historical gold labels. It has no matched English translation, so its errors cannot be assigned specifically to Korean language understanding.","",
        "| Instructions | Correct / 100 | Accuracy, 95% Wilson interval | Brier | Log loss |","|---|---:|---:|---:|---:|"]
    for key,m in stages[2]['groups'].items():
        lo,hi=m['accuracy_ci95']; lines.append(f"| {key.split('/')[1]} | {m['correct']} | {m['accuracy']:.0%}, {lo:.1%}–{hi:.1%} | {m['brier']:.3f} | {m['log_loss']:.3f} |")
    audit=manifest['audit']['kormed']
    lines += ["",f"The pinned doctor test split has {audit['source_rows']} questions. A conservative text screen retained {audit['eligible']} candidates, from which 35, 33 and 32 were sampled from 2022, 2023 and 2024 respectively. The selected inputs were inspected for missing media dependencies. The screen also excludes some potentially usable text questions, so this is a selected subset rather than an official full-benchmark score.","",
        "The sample includes clinical, public-health, ethics and medical-law questions. Excluding media-dependent items can shift the subject mix away from image-heavy clinical questions. Historical answers are evaluated as provided, not reinterpreted as current clinical or legal recommendations.","",
        "## Exploratory medical-note interpretation", "", "Forty synthetic bilingual cases cover negation, time, patient versus family history, medication status, and support for a claim. All answers are intended to follow from the supplied note. The cases and translations were AI-authored before inference and **have not received clinician review**. These results are excluded from primary medical scoring.","",
        "| Condition | Correct / 40 | Exploratory accuracy |","|---|---:|---:|"]
    for key,m in stages[3]['groups'].items(): lines.append(f"| {key.split('/')[1]} | {m['correct']} | {m['accuracy']:.1%} |")
    lines += ["", "These are short, deliberately simple probes, not representative clinical records. They do not test diagnosis, treatment safety, long-note processing, or real patient workflows. The [case review packet](clinician-review.html) exposes every proposed label and translation for review.","",
        "## Does uncertainty identify mistakes?", "", "We ranked Choice answers by returned confidence and Noul answers by distance from 0.5. The table shows errors among the retained fraction, not the fraction of errors removed.","",
        "| Task, Korean instructions | 50% retained | 75% retained | All retained |", "|---|---:|---:|---:|"]
    for task,stage in [('belebele',1),('pawsx',1),('kormed',2)]:
        m=get(stage,task+'/ko_ko')
        lines.append('| '+task+' | '+' | '.join(f"{m['coverage'][str(f)]['error_rate']:.1%}" for f in (.5,.75,1.))+' |')
    lines += ["", "Returned confidence summarizes a distribution and is not itself measured correctness probability. Noul has no separate confidence field. Brier scores and log loss evaluate the actual returned probabilities against labels. No thresholds were tuned on these test results.","",
        "The initial strict sum-to-one validator stopped on one five-option vector summing to 0.99. We preserved that event and amended the analysis to allow only bounded rounding-compatible vectors, normalizing them for probability metrics. The [methodology amendment](methodology.html#probability-validation-amendment) documents the rule and timing. This is consistent with observed two-decimal precision, but server rounding has not been independently confirmed.","",
        "Three primary medical distributions and one robustness distribution needed normalization. For the medical groups, normalization changed mean Brier score by less than 0.0001 and mean log loss by less than 0.00021. Accuracy and confidence-based coverage were unchanged. Raw-vector sensitivity metrics are included in the downloadable JSON.","",
        "## Runtime and cost", "", f"The resolved model was `{model}` throughout. The requested alias was `jev-latest`. Requests ran sequentially through Python SDK 0.6.0 on Windows, with a 30-second timeout and at most two logged retries for transient failures.","",
        "| Stage | Calls | API call seconds | Recorded runner seconds | Input tokens | Output tokens | Estimated USD |","|---|---:|---:|---:|---:|---:|---:|"]
    for s,data in stages.items():
        r=data['runtime']; lines.append(f"| {s} | {r['attempts']} | {r['api_call_seconds']:.3f} | {r['recorded_invocation_wall_seconds']:.3f} | {r['input_tokens']:,} | {r['output_tokens']:,} | {r['observed_cost_usd']:.6f} |")
    lines += ["", f"Across successful responses, median client latency was {total['median_latency_ms']:.0f} ms and p95 was {total['p95_latency_ms']:.0f} ms. Summed API duration, including failed attempts, was {api_seconds:.3f} seconds. Recorded runner invocation time was {wall:.3f} seconds, but it omits the first ten development calls because wall-time instrumentation was added afterward. Complete per-request timing exists for all attempts. Dataset preparation, coding, review and human gaps are excluded from these execution-time figures.","",
        f"Transient failed attempts: {sum(r['status']=='error' for r in attempts)}. Retry attempts: {sum(r['attempt']>1 for r in attempts)}. Failed attempts without reported token usage are excluded from the observed token-cost estimate; the conservative local budget ledger reserves ${sum(r.get('budget_charge_usd',0) for r in attempts):.6f} including those attempts. A local validation stop was resolved without repeating its request.","",
        "Latency is measured around the synchronous SDK call and includes network travel and decoding. It is not server compute time. Client geography was not measured; the workspace timezone was Asia/Seoul. Runs were not randomized by condition order, and no concurrency sweep was performed.","",
        "Cost is calculated from reported input tokens at the September 17, 2026 published rate of $0.042 per million input tokens; output tokens were advertised as free. It is a usage estimate rather than a billing invoice, and excludes minimum purchases or account credits. [TypeSafe pricing statement](https://typesafe.ai/blog/introducing-system-one-models-and-jev).", "",
        "For future model comparisons, use these same source IDs, conditions and answer choices; keep concurrency and latency boundaries identical; disclose token pricing and reasoning settings separately. Do not compare self-reported LLM confidence directly with Jev's distribution-derived confidence.","",
        "## Robustness", "", "Five cases from each scored task were selected before viewing results. Each Korean-instruction condition was repeated twice and tested with two option-order rotations. PAWS-X instead reversed sentence order twice. Option IDs remained attached to their original meanings.","",
        "| Task / variant | Calls | Answer flips from base | Mean probability total variation |","|---|---:|---:|---:|"]
    for key,values in sorted(stages[4].get('robustness',{}).items()):
        lines.append(f"| {key} | {len(values)} | {sum(v['flip'] for v in values)} | {sum(v['total_variation'] for v in values)/len(values):.4f} |")
    lines += ["", "This small check probes repeated predictions and option ordering. It does not establish general determinism or robustness to other paraphrases.","",
        "## Limitations and disclosure", "",
        "- This is a convenience-scale early-access pilot, not a leaderboard or clinical validation study. The model can change after this run.",
        "- Public benchmark training exposure is unknown. Strong scores could partly reflect familiarity with public items.",
        "- Translated paired benchmarks can contain translation artifacts. Disagreements identify cases to inspect, not proof of mistranslation.",
        "- Medical question screening changes the target population. Original source typographical errors and historical labels were preserved.",
        "- Synthetic medical labels and English equivalents are unreviewed. Perfect performance, if observed, would not establish clinical reliability.",
        "- Repeated conditions and minimal pairs are dependent. No overall accuracy is pooled across tasks.",
        "- The run used an early-access account. No third-party model baseline was run. This is a technical pilot report, not a peer-reviewed study.",
        "- Code and English/Korean drafts were prepared with AI assistance. Benchmark answers were scored deterministically against frozen labels.","",
        "## Reproducibility and corrections", "", f"The original manifest hash is `{manifest['sha256']}`. The repository includes frozen source revisions and checksums, sample IDs, prompts, request hashes, response bodies, timing and per-item scores. Public benchmark input text is fetched from its original sources rather than redistributed in the results bundle.","",
        "[Methodology](methodology.html) · [Recorded outputs](results.zip) · [Stage 0](stage-0.html) · [Stage 1](stage-1.html) · [Stage 2](stage-2.html) · [Stage 3](stage-3.html) · [Stage 4](stage-4.html)","",
        "Corrections should identify the item and preserve the original results. Reviewed synthetic cases or revised prompts belong to a separately versioned experiment."]
    order_check=stages[4]['robustness']['pawsx/variant1']
    flipped=sum(v['flip'] for v in order_check)
    lines.insert(lines.index('## Robustness')+2, f"**Sentence-order sensitivity was visible even in this small check.** Reversing the two sentences changed {flipped} of {len(order_check)} PAWS-X predictions relative to the base condition. The same cases flipped in both reversed runs. Semantic equivalence is symmetric, so this is a useful failure mode to investigate on a larger held-out set. It is not an estimate of the population-wide flip rate.")
    lines.insert(lines.index('## Experiment design'), f"A small robustness check also found that reversing sentence order changed {flipped}/{len(order_check)} paraphrase predictions. This observation is more actionable than interpreting a one-point instruction-language difference as a general advantage.\n")
    # Narrative pages are hand-written (docs/index.md, docs/methodology.md). This
    # generated long form is kept as regenerable evidence, not as a published page.
    GENERATED.mkdir(parents=True,exist_ok=True)
    (GENERATED/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    ko=f'''# Jev 한국어 및 의학 평가 부록

2026년 9월 17일 얼리 액세스 모델 `{model}`을 평가했습니다. 1,036개의 평가 조건을 실행했고, 연결 오류 재시도 1회를 포함한 API 시도는 1,037회였습니다. 같은 문항의 언어별 조건과 반복 실험이 포함되므로 서로 독립적인 1,036개 문항을 평가한 것은 아닙니다.

## 주요 결과

| 평가 | 영어 본문·영어 지시문 | 한국어 본문·한국어 지시문 |
|---|---:|---:|
| Belebele 독해 100문항 | {b_en['accuracy']:.0%} | {b_ko['accuracy']:.0%} |
| PAWS-X 의미 동등성 100쌍 | {p_en['accuracy']:.0%} | {p_ko['accuracy']:.0%} |
| KorMedMCQA 의사 시험 100문항 | 평가하지 않음 | {med['accuracy']:.0%} |

독해와 정교한 의미 구별의 성능이 달랐습니다. 의학 시험 결과는 한국어 원문만 평가한 것으로, 오답의 원인을 한국어 이해 부족으로 단정할 수 없습니다. 그림이나 표가 필요한 것으로 의심되는 문항을 보수적으로 제외하여 전체 시험의 과목 구성과도 다를 수 있습니다.

## 실행 시간과 비용

- 호출별 클라이언트 지연시간 중앙값은 {total['median_latency_ms']:.0f} ms, 95백분위수는 {total['p95_latency_ms']:.0f} ms였습니다.
- API 호출 시간의 합은 {api_seconds:.1f}초였습니다. 네트워크와 SDK 응답 처리가 포함되며 서버 계산 시간만을 뜻하지 않습니다.
- 입력 토큰 기반 추정 비용은 ${total['cost_usd']:.5f} USD였습니다. 실제 청구서를 확인한 금액은 아닙니다.
- 첫 개발용 10회는 전체 실행시간 계측을 추가하기 전에 실행했습니다. 호출별 지연시간은 모든 요청에 기록되어 있습니다.

일부 소수 둘째 자리 확률값의 합이 1이 아니어서 검증기가 한 차례 중단되었습니다. 원본과 중단 기록을 보존한 뒤, 반올림으로 설명 가능한 제한된 오차만 허용하고 확률 지표 계산 시 정규화했습니다. 서버의 반올림 방식은 확인되지 않았으며 이 분석 변경은 평가 방법에 공개했습니다. 정답 판정과 원본 확률값은 바꾸지 않았습니다.

## 의학 문장 실험의 한계

합성 의학 문장 40개와 영어 번역은 아직 임상의 검토를 받지 않았습니다. 해당 결과는 탐색적 부록이며 주된 의학 점수에서 제외합니다. 실제 환자 기록, 진단 안전성, 치료 결정, 긴 의무기록 처리 능력을 검증한 연구가 아닙니다.

추가 점검에서 PAWS-X 문장 순서를 뒤집자 5쌍 중 3쌍의 판단이 바뀌었습니다. 의미 동등성은 문장 순서와 무관해야 하므로 후속 검증 가치가 있는 실패 양상입니다. 다만 5쌍으로 전체 오류율을 추정할 수는 없습니다.

공개 벤치마크의 학습 노출 여부는 알 수 없습니다. 다른 모델과 비교 실험을 하지 않았으므로 속도·비용·정확도 우월성을 주장하지 않습니다. 작은 표본에서 1~2문항 차이를 일반적인 언어 성능 차이로 확대 해석해서는 안 됩니다.

[전체 보고서](index.html) · [평가 방법](methodology.html) · [원시 응답 및 결과 다운로드](results.zip) · [임상의 검토용 문항](clinician-review.html)
'''
    # Korean is no longer a separate supplement page; every published page carries
    # both languages. This generated Korean long form is kept as evidence only.
    (GENERATED/'report-ko.md').write_text(ko,encoding='utf-8')
    (docs/'clinician-review.md').write_text((ROOT/'data'/manifest['experiment']/'clinician_review.md').read_text(encoding='utf-8').rstrip()+'\n',encoding='utf-8')


PAGES = [
    # (markdown stem, output name, nav label or None to omit from the nav)
    ('index', 'index.html', 'Sample check'),
    ('methodology', 'methodology.html', 'Methods'),
    ('running-experiments', 'running-experiments.html', 'Run it yourself'),
    ('clinician-review', 'clinician-review.html', 'Clinician packet'),
    ('stage-0', 'stage-0.html', None),
    ('stage-1', 'stage-1.html', None),
    ('stage-2', 'stage-2.html', None),
    ('stage-3', 'stage-3.html', None),
    ('stage-4', 'stage-4.html', None),
]

LANG_MARKER = '<!-- lang:ko -->'

STYLE = (
    "body{margin:0;background:#f7f8fa;color:#192434;"
    "font:17px/1.7 system-ui,-apple-system,'Malgun Gothic',sans-serif}"
    "main{max-width:1020px;margin:auto;padding:48px 28px 80px}"
    "nav{font-size:14px;display:flex;gap:22px;flex-wrap:wrap;align-items:center;"
    "border-bottom:1px solid #cad2dc;padding-bottom:18px}"
    "h1{font-size:clamp(30px,5vw,48px);line-height:1.15;letter-spacing:-.035em;margin:40px 0 18px}"
    "h2{font-size:25px;margin-top:44px;line-height:1.3}h3{font-size:21px}"
    "p,li{max-width:880px}a{color:#125ac4;text-underline-offset:3px}"
    "table{border-collapse:collapse;width:100%;font-size:14px;line-height:1.5;margin:20px 0;background:white}"
    "th,td{text-align:left;padding:10px 12px;border-bottom:1px solid #d7dee7;vertical-align:top}"
    "th{background:#e9eef5}code{font-size:.85em;overflow-wrap:anywhere}"
    "pre{padding:16px;background:#e9eef5;overflow:auto}"
    "blockquote{margin:20px 0;padding:2px 18px;border-left:3px solid #c3ccd6;color:#42505f}"
    "footer{border-top:1px solid #cad2dc;margin-top:50px;padding-top:16px;font-size:13px;color:#526173}"
    ".table-wrap{overflow-x:auto}img{max-width:100%;height:auto}"
    "#langtoggle{margin-left:auto;display:none}"
    "#langtoggle button{font:inherit;font-size:13px;padding:3px 11px;margin-left:6px;cursor:pointer;"
    "border:1px solid #c3ccd6;background:white;color:#42505f;border-radius:4px}"
    "#langtoggle button[aria-pressed=true]{background:#192434;color:white;border-color:#192434}"
    "@media(max-width:600px){main{padding:24px 16px 50px}body{font-size:16px}"
    "th,td{padding:8px;min-width:65px}}"
)

# Progressive enhancement: without JavaScript both halves stay visible.
SCRIPT = (
    "(function(){var t=document.getElementById('langtoggle');"
    "var h=document.querySelectorAll('.lang');if(!t||!h.length)return;"
    "t.style.display='block';"
    "function set(l){document.querySelectorAll('.lang').forEach(function(d){"
    "d.style.display=d.dataset.lang===l?'block':'none'});"
    "t.querySelectorAll('button').forEach(function(b){"
    "b.setAttribute('aria-pressed',String(b.dataset.lang===l))});"
    "document.documentElement.lang=l;"
    "try{localStorage.setItem('jevlang',l)}catch(e){}}"
    "var saved=null;try{saved=localStorage.getItem('jevlang')}catch(e){}"
    "set(saved||((navigator.language||'en').slice(0,2)==='ko'?'ko':'en'));"
    "t.addEventListener('click',function(e){"
    "if(e.target.dataset&&e.target.dataset.lang)set(e.target.dataset.lang)})})();"
)


# Pages removed by the documentation merge. Their URLs were published, and at least
# one (korean-supplement) is linked from an external post, so they keep working as
# redirects rather than turning into 404s. Each points at where its content went.
REDIRECTS = {
    'aggregate.html': ('index.html#results', 'Results'),
    'medqa-english.html': ('index.html#about-the-medical-numbers', 'About the medical numbers'),
    'kormedmcqa-context.html': ('index.html#about-the-medical-numbers', 'About the medical numbers'),
    'luna-comparison.html': ('index.html#results', 'Results'),
    'comparison-design.html': ('methodology.html#comparator-protocol', 'Comparator protocol'),
    'korean-supplement.html': ('index.html', 'Jev in Korean / Jev의 한국어 성능'),
    'report.html': ('index.html', 'Jev in Korean'),
}


def write_redirects(docs):
    """Keep previously published URLs alive after the page merge."""
    for name, (target, label) in REDIRECTS.items():
        (docs / name).write_text(
            '<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta http-equiv="refresh" content="0; url={target}">'
            f'<link rel="canonical" href="{target}">'
            '<meta name="robots" content="noindex">'
            '<title>This page has moved</title>'
            '<style>body{font:17px/1.7 system-ui,sans-serif;margin:0;background:#f7f8fa;'
            'color:#192434}main{max-width:640px;margin:auto;padding:64px 28px}'
            'a{color:#125ac4}</style></head><body><main>'
            '<h1>This page has moved</h1>'
            f'<p>Its content is now part of <a href="{target}">{label}</a>. '
            'You should be redirected automatically.</p>'
            '<p>The English and Korean versions are now on the same page, '
            'with a language switch in the navigation bar.</p>'
            '</main></body></html>', encoding='utf-8')


def render_markdown(text):
    # The default toc slugify strips non-ASCII, which turns Korean headings into
    # meaningless ids like _1 and breaks in-page links. slugify_unicode keeps them
    # and matches how GitHub anchors the same headings in the markdown source.
    from markdown.extensions.toc import slugify_unicode
    body = markdown.markdown(text, extensions=['tables', 'fenced_code', 'toc'],
                             extension_configs={'toc': {'slugify': slugify_unicode}})
    return body.replace('<table>', '<div class="table-wrap"><table>').replace('</table>', '</table></div>')


def render_web():
    """Render the explicit page list. A glob would publish untracked drafts."""
    import html
    docs = ROOT / 'docs'
    nav = ''.join(f'<a href="{out}">{label}</a>' for _, out, label in PAGES if label)
    nav += ('<a href="results.zip">Download results</a>'
            '<a href="https://github.com/mahlernim/jev-korean-benchmark">Code and data</a>')
    for stem, out, _ in PAGES:
        source = docs / f'{stem}.md'
        if not source.exists():
            continue
        text = source.read_text(encoding='utf-8')
        title = text.splitlines()[0].lstrip('# ').strip()
        if LANG_MARKER in text:
            en, ko = text.split(LANG_MARKER, 1)
            body = (f'<div class="lang" data-lang="en">{render_markdown(en)}</div>'
                    f'<div class="lang" data-lang="ko">{render_markdown(ko)}</div>')
            toggle = ('<span id="langtoggle"><button data-lang="en" aria-pressed="true">English</button>'
                      '<button data-lang="ko" aria-pressed="false">한국어</button></span>')
        else:
            body, toggle = render_markdown(text), ''
        page = (
            '<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<meta name="description" content="A 100-question sample check of TypeSafe Jev on '
            'Korean reading, paraphrase decisions and medical exam questions.">'
            f'<title>{html.escape(title)}</title><style>{STYLE}</style></head><body><main>'
            f'<nav>{nav}{toggle}</nav>{body}'
            '<footer>100-question sample check · September 17, 2026 · '
            'Synthetic medical cases await clinician review.</footer>'
            f'</main><script>{SCRIPT}</script></body></html>')
        (docs / out).write_text(page, encoding='utf-8')
    write_redirects(docs)
    (docs / '.nojekyll').write_text('', encoding='utf-8')
