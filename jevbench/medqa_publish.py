"""Publish paired English MedQA evidence and separate parallel timing measures."""
import argparse
from collections import defaultdict
from datetime import datetime
import hashlib
import json
import math

import httpx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import NullLocator

from .common import ROOT, canonical, digest, filehash, frozen, load_manifest, read
from .medqa_run import DIRECTORY, prepare, records
from .medqa_prepare import EXPERIMENT
from .report import paired_difference, quantile, wilson

BREAK = chr(10)

PUBLIC=ROOT/'results'/EXPERIMENT


def summarize(m,rr):
    good={r['eval_id']:r for r in rr if r['status']=='success'}
    result={'planned':len(m['requests']),'successful':len(good),'providers':{}}
    for provider in ('jev','luna'):
        es=[e for e in m['requests'] if e['provider']==provider]
        rs=[r for r in rr if r['provider']==provider]
        valid=[good[e['eval_id']] for e in es if e['eval_id'] in good]
        k=sum(r['score']['correct'] for r in valid)
        failed={r['eval_id'] for r in rs if r['terminal'] and r['status']=='error'}-set(good)
        total=len(es); lat=[r['latency_ms'] for r in valid]
        result['providers'][provider]=dict(planned=total,successful=len(valid),terminal_failures=len(failed),
            pending=total-len(valid)-len(failed),correct=k,accuracy=k/total,ci95=wilson(k,total),
            valid_response_accuracy=k/len(valid) if valid else None,attempts=len(rs),
            estimated_cost_usd=sum(r['score']['estimated_cost_usd'] for r in valid),
            ledger_usd=sum(r['budget_charge_usd'] for r in rs),
            api_seconds=sum(r['latency_ms'] for r in rs)/1000,
            median_ms=quantile(lat,.5),p95_ms=quantile(lat,.95),
            input_tokens=sum(r['score']['input_tokens'] for r in valid),
            output_tokens=sum(r['raw_response']['usage']['output_tokens'] for r in valid),
            cached_tokens=sum(r['raw_response']['usage'].get('input_tokens_details',{}).get('cached_tokens',0) for r in valid),
            reasoning_tokens=sum(r['raw_response']['usage'].get('output_tokens_details',{}).get('reasoning_tokens',0) for r in valid),
            models=sorted({r['raw_response']['model'] for r in valid}))
    left={r['case_id']:r for r in good.values() if r['provider']=='jev'}
    right={r['case_id']:r for r in good.values() if r['provider']=='luna'}
    result['paired_valid']=paired_difference(left,right)
    ids=set(left)&set(right)
    table={'both_correct':0,'jev_only_correct':0,'luna_only_correct':0,'both_incorrect':0}
    for i in ids:
        a=left[i]['score']['correct']; b=right[i]['score']['correct']
        table['both_correct' if a and b else 'jev_only_correct' if a else 'luna_only_correct' if b else 'both_incorrect']+=1
    discordant=table['jev_only_correct']+table['luna_only_correct']
    result['paired_table']=table
    result['exact_mcnemar_p']=min(1,2*sum(math.comb(discordant,k) for k in range(min(table['jev_only_correct'],table['luna_only_correct'])+1))/2**discordant) if discordant else 1.
    return result


def publish():
    m=prepare(); rr=records(); summary=summarize(m,rr)
    if summary['successful']!=200: raise RuntimeError('Resolve all planned results before publication')
    source=load_manifest(ROOT/'data'/EXPERIMENT/'manifest.json')
    PUBLIC.mkdir(exist_ok=True)
    def write(name,value):
        (PUBLIC/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    source_index={**source,'evaluations':[{k:v for k,v in e.items() if k!='request'} for e in source['evaluations']]}
    write('source-manifest-index.json',source_index)
    write('request-manifest-index.json',{**m,'requests':[{k:v for k,v in e.items() if k!='request'} for e in m['requests']]})
    write('input-review.json',read(ROOT/'data'/EXPERIMENT/'input-review.json'))
    write('summary.json',summary)
    export=[]
    for r in rr:
        item={**r,'original_record_sha256':r.get('original_record_sha256',digest(r))}
        if r.get('raw_response'):
            item['raw_response']={k:v for k,v in r['raw_response'].items() if k not in ('billing','user','safety_identifier','metadata','moderation','prompt_cache_key')}
        export.append(item)
    (PUBLIC/'responses.jsonl').write_text(''.join(canonical(r)+'\n' for r in export),encoding='utf-8',newline='\n')
    timings=[read(p) for p in sorted((DIRECTORY/'timing').glob('*.json'))]
    write('timing.json',timings)
    write('usage-after-10.json',read(DIRECTORY/'usage-after-10.json'))
    # A provider span is first-to-last request within each invocation, including retry gaps.
    for provider,g in summary['providers'].items():
        spans=[]
        for t in timings:
            selected=[r for r in rr if r['provider']==provider and t['started_at']<=r['started_at']<=t['finished_at']]
            if selected:
                begin=min(datetime.fromisoformat(r['started_at']) for r in selected)
                end=max(datetime.fromisoformat(r['finished_at']) for r in selected)
                spans.append((end-begin).total_seconds())
        g['active_spans_seconds']=sum(spans)
        g['successful_per_active_second']=g['successful']/sum(spans) if sum(spans) else None
    summary['combined_invocation_wall_seconds']=sum(t['wall_seconds'] for t in timings)
    write('summary.json',summary)
    good={r['eval_id']:r for r in rr if r['status']=='success'}
    disagreements=[]
    for e in source['evaluations']:
        a=good['jev__'+e['eval_id']]; b=good['luna__'+e['eval_id']]
        if a['score']['prediction']!=b['score']['prediction']:
            disagreements.append(dict(case_id=e['case_id'],gold=e['gold'],jev=a['score']['prediction'],luna=b['score']['prediction']))
    write('disagreements.json',disagreements)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'svg.fonttype':'none'})
    fig,axes=plt.subplots(1,3,figsize=(11,3.8),layout='constrained')
    for i,(provider,name,color,marker) in enumerate([('jev','Jev','#0072B2','o'),('luna','Luna none','#D55E00','s')]):
        g=summary['providers'][provider]; p=100*g['accuracy']; lo,hi=[x*100 for x in g['ci95']]
        axes[0].errorbar(p,i,xerr=[[p-lo],[hi-p]],fmt=marker,color=color,capsize=4)
        axes[1].plot(g['median_ms'],i,marker,color=color)
        axes[2].plot(g['estimated_cost_usd'],i,marker,color=color)
    for ax in axes:
        ax.set_yticks([0,1],['Jev','Luna none']); ax.set_ylim(1.5,-.5); ax.grid(axis='x',alpha=.2)
    axes[0].set(xlim=(0,100),xlabel='Accuracy (%)',title='A   Accuracy and 95% Wilson CI')
    axes[1].set(xlabel='Median client latency (ms)',title='B   Latency, concurrency 4')
    axes[2].set(xlabel='Estimated USD, 100 questions',title='C   Observed usage cost')
    for ax in axes[1:]: ax.set_xlim(left=0); ax.locator_params(axis='x',nbins=4)
    figures=ROOT/'results'/EXPERIMENT; figures.mkdir(parents=True,exist_ok=True)
    for ext in ('png','pdf','svg'): fig.savefig(figures/f'medqa-english.{ext}',dpi=300,bbox_inches='tight')
    plt.close(fig)
    svg=figures/'medqa-english.svg'
    svg.write_text('\n'.join(s.rstrip() for s in svg.read_text().splitlines())+'\n',encoding='utf-8',newline='\n')
    j=summary['providers']['jev']; l=summary['providers']['luna']; d=summary['paired_valid']
    lines=['# Original-English MedQA comparison','',
        '## Abstract','',
        f"On 100 matched original-English four-option MedQA test questions, Jev scored {j['correct']}/100 and Luna-none scored {l['correct']}/100. Luna minus Jev was {d['difference']*100:+.0f} percentage points, with a paired 95% bootstrap interval from {d['ci95'][0]*100:+.0f} to {d['ci95'][1]*100:+.0f}. This is an exploratory benchmark estimate, not clinical validation or a controlled language comparison.",'',
        '![Matched English MedQA accuracy, latency and cost](medqa-english.png)','',
        '**Figure 1.** Both models receive the same 100 questions and four original options. Accuracy bars are Wilson 95% intervals. Latency and token cost are observed point estimates from four concurrent requests per provider. They do not describe the earlier sequential experiments.','',
        '## Data and methods','',
        '[MedQA](https://github.com/jind11/MedQA) contains original English USMLE-style questions. We used the four-option test split via a [pinned documented mirror](https://huggingface.co/datasets/GBaker/MedQA-USMLE-4-options). Source provenance, revision, SHA256, row IDs and selection rules are preserved in the downloadable evidence. Byte identity with the primary Google Drive release was not independently verified.','',
        f"The source contains {source['audit']['source_rows']} rows. Conservative screening excluded {source['audit']['excluded_rows']}, leaving {source['audit']['eligible_rows']} eligible rows. Selection uses seed 20260917, preserving A-D order and original answer keys. The rejected v1 sample had missing visual references missed by its initial automated screen. An expanded screen produced v2; independent review found two further incomplete stems. Final v3 retains 98 reviewed items and replaces those two using a frozen seeded rule. Neither rejected version was scored. Every final input was checked through independent AI-assisted, gold-blinded review. This checks input completeness, not clinical correctness or gold-label validity; nonblocking source wording and unit issues remain documented.",'',
        'Both models receive the same English question, options and instruction to select the single best answer. Gold answers are excluded from inputs. Jev uses Choice; Luna uses the Responses API with reasoning effort none, standard service and a strict decision-only JSON schema capped at 128 output tokens. No retrieval, tools or explanations are requested. Jev supplies probabilities natively. We do not fabricate comparable probabilities for Luna.','',
        'The full 200-request manifest was frozen before inference. Four worker threads per provider run contemporaneously in separate pools, with a shared $0.25 estimated-spend ceiling that reserves in-flight costs. The first five items per provider form the initial ten-call usage check and remain part of the frozen score. There is no post-result prompt tuning. At most two transient retries are retained; fatal validation or model changes stop new admissions while already admitted calls may finish.','',
        'Accuracy is correct/planned, with terminal failures counted as incorrect if present. Valid-response accuracy is also retained. Paired item bootstrap intervals use 4,000 resamples and the fixed seed. The discordance table and two-sided exact McNemar test are descriptive, without multiplicity adjustment. Small pilot intervals do not establish equivalence.','',
        '## Results','', '| Model | Correct / planned | Accuracy (95% CI) | Attempts | Terminal failures |','|---|---:|---:|---:|---:|']
    for name,g in [('Jev',j),('Luna none',l)]:
        lines.append(f"| {name} | {g['correct']}/{g['planned']} | {g['accuracy']:.0%} ({g['ci95'][0]:.1%}, {g['ci95'][1]:.1%}) | {g['attempts']} | {g['terminal_failures']} |")
    table=summary['paired_table']
    lines+=['','| Paired correctness | Luna correct | Luna incorrect |','|---|---:|---:|',
        f"| Jev correct | {table['both_correct']} | {table['jev_only_correct']} |",
        f"| Jev incorrect | {table['luna_only_correct']} | {table['both_incorrect']} |",'',
        f"Two-sided exact McNemar p = {summary['exact_mcnemar_p']:.4f}. The direction of the point estimate should not be treated as an established model ranking.",'',
        '## Parallel timing and cost','',
        '| Model | Median / p95 latency, ms | Sum of call seconds | Sum of active spans, seconds | Valid responses per active second | Estimated USD | Input / output tokens |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for name,g in [('Jev',j),('Luna none',l)]:
        lines.append(f"| {name} | {g['median_ms']:.0f} / {g['p95_ms']:.0f} | {g['api_seconds']:.2f} | {g['active_spans_seconds']:.2f} | {g['successful_per_active_second']:.2f} | {g['estimated_cost_usd']:.6f} | {g['input_tokens']:,} / {g['output_tokens']:,} |")
    lines+=['',f"Combined invocation wall time was {summary['combined_invocation_wall_seconds']:.2f} seconds. It includes both providers running concurrently, initialization, persistence, retry delays and closure, but excludes preparation, review and human gaps. Summed call duration is not elapsed batch time. Provider active spans run from the first to last recorded request within each invocation, then sum across invocations.",'',
        'Per-call latency wraps network calls, decoding and answer validation. Dispatch and initialization wait are recorded separately. Concurrent measurements reflect contention, provider limits and shared client/network conditions. Do not compare their batch elapsed time with the previous concurrency-one experiment or interpret the difference as a model speed improvement.','',
        'Costs use reported provider-specific tokens at $0.042/million Jev input tokens, output free, and $0.20/million Luna input, $0.02 cached input and $1.20 output. These are published-price estimates, not invoices. Unknown-usage failures retain conservative reservations in the ledger.','',
        '## Relation to the Korean results','',
        'The Korean KorMedMCQA pilot and this original-English MedQA sample are different item sets. They differ in curriculum, difficulty, selection and number of options. A model ranking reversal across them would be a task-specific finding, not proof that English caused it. Do not subtract the two benchmark accuracies to estimate a language effect or pool them into one medical score.','',
        f"The observed point estimates do reverse: Korean KorMedMCQA with Korean instructions was Jev 80% versus Luna 88%, while this English MedQA sample is Jev {j['accuracy']:.0%} versus Luna {l['accuracy']:.0%}. The English paired interval includes zero, and the independent question sets prevent attributing that reversal specifically to language.",'',
        'Public benchmark training exposure is unknown. Source screening affects representativeness. Historical examination answers were preserved. This pilot evaluates multiple-choice benchmark performance, not diagnostic safety or clinical readiness.','',
        f'[Public evidence](https://github.com/mahlernim/jev-korean-benchmark/tree/main/results/{EXPERIMENT}) · [Sample check](https://ahn-lab.org/jev-korean-benchmark/index.html)']
    # Detailed report kept as regenerable evidence; narrative pages are hand-written.
    (ROOT/'results'/EXPERIMENT/'report.md').write_text(BREAK.join(lines)+BREAK,encoding='utf-8')
    from .publish import render_web
    render_web()
    write('checksums.json',{p.name:filehash(p) for p in sorted(PUBLIC.iterdir()) if p.is_file() and p.name!='checksums.json'})
    print(json.dumps(summary,indent=2))


def restore():
    from .medqa_prepare import restore_from_public
    for name,sha in read(PUBLIC/'checksums.json').items():
        if filehash(PUBLIC/name)!=sha: raise ValueError('Public checksum mismatch')
    restore_from_public()
    m=prepare()
    if m['sha256']!=read(PUBLIC/'request-manifest-index.json')['sha256']:
        raise ValueError('Reconstructed provider request manifest mismatch')
    expected={e['eval_id']:e for e in m['requests']}
    for r in map(json.loads,(PUBLIC/'responses.jsonl').read_text(encoding='utf-8').splitlines()):
        if r['manifest_hash']!=m['sha256'] or r['request_hash']!=expected[r['eval_id']]['request_hash']:
            raise ValueError('Response hash mismatch')
        path=DIRECTORY/'attempts'/(digest(r['eval_id'])[:24]+f"-{r['attempt']}.json")
        if path.exists() and digest(read(path))==r.get('original_record_sha256'): continue
        frozen(path,r)
    for t in read(PUBLIC/'timing.json'):
        frozen(DIRECTORY/'timing'/(t['started_at'].replace(':','-')+'.json'),t)
    frozen(DIRECTORY/'usage-after-10.json',read(PUBLIC/'usage-after-10.json'))
    print(json.dumps(summarize(m,records()),indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--restore',action='store_true')
    args=parser.parse_args(); restore() if args.restore else publish()
