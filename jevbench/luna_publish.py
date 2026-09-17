"""Export completed Luna evidence and descriptive matched comparisons."""
import csv
import io
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import NullLocator
import numpy as np

from .common import ROOT, canonical, digest, filehash, read
from .luna import DIRECTORY, prepare, records, report
from .report import quantile, wilson


def main():
    m=prepare(); good=report(m)
    rr=records()
    if len({r['eval_id'] for r in rr if r['terminal']})!=len(m['evaluations']):
        raise RuntimeError('Complete the run before publishing a comparison')
    out=ROOT/'results/luna-none-v1'; out.mkdir(exist_ok=True)
    def write(name,value):
        (out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    # Full inputs remain local. Public frozen hashes support exact regeneration.
    lock={k:v for k,v in m.items() if k!='evaluations'}
    lock['evaluation_index']=[{k:v for k,v in e.items() if k!='request'} for e in m['evaluations']]
    write('experiment-lock.json',lock)
    public_records=[]
    for r in rr:
        exported={**r,'original_record_sha256':r.get('original_record_sha256',digest(r))}
        if 'raw_response' in r:
            exported['raw_response']={k:v for k,v in r['raw_response'].items()
                if k not in ('billing','user','safety_identifier','metadata','moderation','prompt_cache_key')}
        public_records.append(exported)
    (out/'responses.jsonl').write_text(''.join(canonical(r)+'\n' for r in public_records),encoding='utf-8',newline='\n')
    for s in range(5):
        write(f'stage-{s}.json',read(DIRECTORY/f'reports/stage-{s}.json'))
    timings=[read(p) for p in sorted((DIRECTORY/'timing').glob('*.json'))]
    write('timing.json',timings)
    write('runtime.json',[read(p) for p in sorted((DIRECTORY/'invocations').glob('*.json'))])
    write('usage-after-10.json',read(DIRECTORY/'usage_after_10.json'))
    jev={r['eval_id']:r for r in map(json.loads,(ROOT/'results/responses.jsonl').read_text().splitlines()) if r['status']=='success'}
    selected=list(good.values())
    if any(r['raw_response'].get('reasoning',{}).get('effort')!='none' or
           r['raw_response'].get('service_tier')!='default' for r in selected):
        raise RuntimeError('Returned service/reasoning configuration differs from protocol')
    total=dict(successful=len(good),attempts=len(rr),input_tokens=sum(r['score']['input_tokens'] for r in selected),
        output_tokens=sum(r['score']['output_tokens'] for r in selected),cached_tokens=sum(r['score']['cached_tokens'] for r in selected),
        reasoning_tokens=sum(r['score']['reasoning_tokens'] for r in selected),
        estimated_cost_usd=sum(r['score']['estimated_cost_usd'] for r in selected),
        ledger_usd=sum(r['budget_charge_usd'] for r in rr),
        median_ms=quantile([r['latency_ms'] for r in selected],.5),p95_ms=quantile([r['latency_ms'] for r in selected],.95),
        api_seconds=sum(r['latency_ms'] for r in rr)/1000,runner_seconds=sum(t['wall_seconds'] for t in timings))
    write('summary.json',total)
    discrepancies=[]
    for e in m['evaluations']:
        r=good.get(e['eval_id'])
        if r and e['stage'] in (1,2,3) and r['score']['prediction']!=jev[e['eval_id']]['score']['prediction']:
            discrepancies.append(dict(eval_id=e['eval_id'],task=e['task'],condition=e['condition'],gold=e['gold'],
                luna=r['score']['prediction'],jev=jev[e['eval_id']]['score']['prediction'],
                luna_correct=r['score']['correct'],jev_correct=jev[e['eval_id']]['score']['correct']))
    write('disagreements.json',discrepancies)
    tasks=[('belebele','Belebele',1),('pawsx','PAWS-X',1),('kormed','KorMedMCQA',2)]
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
                        'axes.spines.right':False,'pdf.fonttype':42,'svg.fonttype':'none'})
    fig,axes=plt.subplots(1,3,figsize=(12,4),layout='constrained')
    for i,(task,label,stage) in enumerate(tasks):
        es=[e for e in m['evaluations'] if e['task']==task and e['stage']==stage and e['condition']=='ko_ko' and e['eval_id'] in good]
        for j,(source,name,color,marker) in enumerate(((jev,'Jev','#0072B2','o'),(good,'Luna none','#D55E00','s'))):
            rs=[source[e['eval_id']] for e in es]; n=len(rs); k=sum(r['score']['correct'] for r in rs)
            p=100*k/n; lo,hi=np.array(wilson(k,n))*100; y=i+(j-.5)*.2
            axes[0].errorbar(p,y,xerr=[[p-lo],[hi-p]],fmt=marker,color=color,capsize=3,label=name if i==0 else None)
            lat=quantile([r['latency_ms'] for r in rs],.5)
            cost=sum(r['score']['estimated_cost_usd'] for r in rs)/n*1000
            axes[1].plot(lat,y,marker,color=color)
            axes[2].plot(cost,y,marker,color=color)
    for ax in axes:
        ax.set_yticks(range(3),[t[1] for t in tasks]); ax.invert_yaxis(); ax.grid(axis='x',alpha=.18)
    axes[0].set(xlim=(0,100),xlabel='Accuracy (%)',title='A   Accuracy and 95% Wilson CI'); axes[0].legend(frameon=False,loc='lower left')
    axes[1].set(xscale='log',xlabel='Median client latency (ms)',title='B   Median latency')
    axes[2].set(xscale='log',xlabel='Estimated USD per 1,000 calls',title='C   Token cost')
    axes[1].set_xticks([200,500,1000],['200','500','1,000'])
    axes[2].set_xticks([.02,.04,.08],['0.02','0.04','0.08'])
    for ax in axes[1:]: ax.xaxis.set_minor_locator(NullLocator())
    for ext in ('png','svg','pdf'):
        fig.savefig(ROOT/f'docs/figures/luna-comparison.{ext}',dpi=300,bbox_inches='tight')
    svg=ROOT/'docs/figures/luna-comparison.svg'
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n')
    plt.close(fig)
    lines=['# Jev versus Luna without reasoning','',
        '## Abstract','',
        'This paired extension compares Jev with GPT-5.6 Luna at explicit reasoning effort `none` on the same frozen Korean and English cases. It measures task accuracy, client latency and token cost. The comparison was designed after Jev results were inspected and is an exploratory replication, not a preregistered confirmatory study. No higher-reasoning Luna run was performed.','',
        '## Methods','',
        'Luna used the Responses API, standard service tier, one isolated request per case and a strict JSON schema returning only an answer ID or boolean. The original instructions, state and choice order were retained. State and criteria were serialized as UTF-8 JSON, an interface difference from Jev. No tools, retrieval, explanation, probability elicitation or conversation history was used. Output was capped at 128 tokens. All 1,036 conditions were frozen before the first Luna call. Jev returns probabilities natively as well as its decision. This comparison measures the cost of obtaining a decision, not equal amounts of output information.','',
        'The same seed, source IDs and gold labels as the original pilot were used. General tasks and medical knowledge remain separate. The 40 synthetic medical cases remain unreviewed and exploratory. Their minimal pairs are dependent, which the displayed case-level intervals do not account for. Stage 4 repeats earlier cases and receives flip counts rather than an independent accuracy interval. Wilson intervals describe task accuracy. Paired percentile bootstrap intervals use 4,000 resamples and are exploratory, unadjusted for multiple comparisons. Degenerate intervals for identical observed correctness do not establish equivalence.','',
        'The API returned `gpt-5.6-luna`, without a dated snapshot. Requests specify `none`, and reported reasoning-token counts are audited. Sampling parameters were left at provider defaults and are retained in the raw responses. Calls run sequentially through httpx 0.28.1 with a 30-second timeout and at most two transient retries. Immutable intents prevent automatic resending of uncertain interrupted requests.','',
        'Jev timing wraps its SDK call and decoding. Luna timing wraps HTTP response decoding and answer validation, with a small additional local parsing component. Both include network latency and exclude disk writes. The runs occurred at different times and used different provider transports. These measurements describe the observed services, not architecture-only speed or server compute. Conditions were not randomly interleaved across providers.','',
        '## Results','',
        '![Matched Korean-instruction accuracy, latency and cost](figures/luna-comparison.png)','',
        '**Figure 1.** Korean content and Korean instructions, 100 matched cases per task. Bars show 95% Wilson accuracy intervals. Median latency and estimated token cost use the same successful cases. Latency and cost axes are logarithmic. Point estimates have no uncertainty bars in those panels and should not be interpreted as stable population ratios. Synthetic medical cases are excluded.','']
    for stage in (1,2,3,4):
        lines += [f'### Stage {stage}','']+(DIRECTORY/f'reports/stage-{stage}.md').read_text().splitlines()[2:]+['']
    primary=[]
    for task,label,stage in tasks:
        group=read(DIRECTORY/f'reports/stage-{stage}.json')['groups'][task+'/ko_ko']
        original=read(ROOT/f'results/stage-{stage}.json')['groups'][task+'/ko_ko']
        primary.append(f"{label} {group['accuracy']:.0%} versus {original['accuracy']:.0%}")
    lines.insert(lines.index('## Methods'),
        'With Korean content and Korean instructions, Luna versus Jev accuracy was '+', '.join(primary)+
        f". Luna's total observed-usage cost was ${total['estimated_cost_usd']:.5f}, and summed API attempt time was {total['api_seconds']:.1f} seconds. These task-specific results do not establish a single ordering of model capability.\n")
    lines+=['## Runtime and cost','',
        '| Measure | Luna none |','|---|---:|']
    names={'successful':'Successful evaluations','attempts':'API attempts','input_tokens':'Input tokens',
        'output_tokens':'Output tokens','cached_tokens':'Cached input tokens','reasoning_tokens':'Reasoning tokens',
        'estimated_cost_usd':'Observed-usage cost estimate (USD)','ledger_usd':'Conservative ledger (USD)',
        'median_ms':'Median successful-call latency (ms)','p95_ms':'p95 successful-call latency (ms)',
        'api_seconds':'Summed API attempt duration (seconds)','runner_seconds':'Recorded runner duration (seconds)'}
    for k,v in total.items(): lines.append(f'| {names[k]} | {v:.6f} |' if isinstance(v,float) else f'| {names[k]} | {v:,} |')
    lines += ['', '## Answer disagreements','',
        'The downloadable disagreements file lists every differing primary or exploratory prediction with its frozen gold label. The table below shows the first 20 in frozen evaluation order, not a curated selection of favorable examples.','',
        '| Evaluation | Gold | Jev | Luna |','|---|---|---|---|']
    for d in discrepancies[:20]:
        lines.append(f"| {d['eval_id']} | {d['gold']} | {d['jev']} | {d['luna']} |")
    lines += ['',
        'USD estimates use $0.20 per million uncached input tokens, $0.02 cached input and $1.20 output. Each provider uses its own reported token counts, which can differ because of tokenization and request overhead. Reasoning tokens, if any, are part of output and must not be billed twice. Failed attempts with unknown usage retain conservative reservations. Estimates are not invoice reconciliation. Runner wall time excludes preparation, reporting performed after its timing boundary, and human gaps. Jev runner timing omitted its first ten development calls, so summed API duration is the more complete comparison.','',
        '## Limitations and next decision','',
        'No pooled cross-task winner is defined. Public benchmark training exposure is unknown, and medical media screening changes the target population. No matched English medical examination arm exists. Neither synthetic performance nor exam accuracy establishes clinical readiness.','',
        'Complete response records remain immutable locally. The public export omits billing and account-related metadata, retaining original-record hashes, model answers, generation settings, usage, latency and scoring evidence. Benchmark input text is reconstructed from pinned upstream sources rather than redistributed here.','',
        'Luna returns decisions only. Brier scores, log loss and confidence-based coverage cannot be computed for Luna in this protocol. Fabricating one-hot probabilities or eliciting confidence after the fact would change the question being measured. A higher-reasoning experiment should be separately frozen and budgeted after reviewing these results, rather than replacing this run.','',
        '[Original Jev report](index.html) · [Comparison rationale and literature](comparison-design.html) · [Medical benchmark context infographic](kormedmcqa-context.html) · [Public Luna evidence](https://github.com/mahlernim/jev-korean-benchmark/tree/main/results/luna-none-v1)']
    (ROOT/'docs/luna-comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    readme=ROOT/'README.md'
    block=['<!-- luna-summary-start -->','## Luna-none comparison','',
        'Luna was tested on the same 1,036 conditions with reasoning effort `none` and decision-only structured output. The table shows Korean content with Korean instructions, 100 cases per task.','',
        '| Task | Jev | Luna none | Luna minus Jev, pp (95% paired interval) |',
        '|---|---:|---:|---:|']
    for task,label,stage in tasks:
        g=read(DIRECTORY/f'reports/stage-{stage}.json')['groups'][task+'/ko_ko']
        j=read(ROOT/f'results/stage-{stage}.json')['groups'][task+'/ko_ko']; d=g['paired']
        block.append(f"| {label} | {j['accuracy']:.0%} | {g['accuracy']:.0%} | {d['difference']*100:+.0f} ({d['ci95'][0]*100:+.0f}, {d['ci95'][1]*100:+.0f}) |")
    block+=['', '![Jev and Luna-none accuracy, latency and cost](docs/figures/luna-comparison.png)','',
        '**Comparison figure.** Matched Korean-instruction cases. Accuracy bars are 95% Wilson intervals. Latency and cost use logarithmic axes and have no uncertainty intervals. Cost per 1,000 calls is a scaling of observed token charges, not a separate 1,000-call experiment. Different execution times and provider transports limit causal speed comparisons.','',
        f"Across all stages, Luna used **${total['estimated_cost_usd']:.5f}** in estimated API charges and **{total['api_seconds']:.1f} seconds** of summed API attempt time. Successful-call median / p95 latency was **{total['median_ms']:.0f} / {total['p95_ms']:.0f} ms**. Jev's corresponding figures were $0.02056, 262.0 seconds and 221 / 306 ms. These are observed service measurements, not guaranteed performance. No higher-reasoning Luna condition has been run.",'',
        '[Full comparison report](https://ahn-lab.org/jev-korean-benchmark/luna-comparison.html) · [Recorded Luna evidence](results/luna-none-v1/) · [Design and existing comparisons](docs/comparison-design.md) · [Medical benchmark context infographic](docs/kormedmcqa-context.md)','',
        'The original Jev-only findings follow. Synthetic medical results remain unreviewed and exploratory.','<!-- luna-summary-end -->','']
    text=readme.read_text(encoding='utf-8')
    if '<!-- luna-summary-start -->' in text:
        before,rest=text.split('<!-- luna-summary-start -->',1)
        _,after=rest.split('<!-- luna-summary-end -->',1)
        text=before+'\n'.join(block)+after.lstrip('\n')
    else:
        text=text.replace('## Read the findings','\n'.join(block)+'\n## Read the findings',1)
    readme.write_text(text,encoding='utf-8')
    design=ROOT/'docs/comparison-design.md'
    design.write_text(design.read_text(encoding='utf-8').replace(
        'This is a proposed extension. No Luna measurements are included in the current results.',
        'This records the rationale prepared before the Luna run. The [completed Luna-none comparison](luna-comparison.html) is reported separately.'),encoding='utf-8')
    original=ROOT/'docs/report.md'
    original_text=original.read_text(encoding='utf-8')
    link='A subsequent [Luna-none comparison](luna-comparison.html) evaluates the same cases. This page preserves the original Jev-only pilot.\n\n'
    if link not in original_text:
        heading,rest=original_text.split('\n\n',1)
        original.write_text(heading+'\n\n'+link+rest,encoding='utf-8')
    from .publish import render_web
    render_web()
    write('checksums.json',{p.name:filehash(p) for p in sorted(out.iterdir()) if p.is_file() and p.name!='checksums.json'})
    print(json.dumps(total,indent=2))


if __name__=='__main__': main()
