"""Reproduce the descriptive six-cell overview from published evidence only."""
import json
import random

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from .common import ROOT, filehash
from .report import paired_difference, quantile, wilson

BREAK = chr(10)


def read(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))


def records(path):
    return [json.loads(line) for line in (ROOT/path).read_text(encoding='utf-8').splitlines()]


def replace_block(path, name, block):
    text=path.read_text(encoding='utf-8')
    start,end=f'<!-- {name}-start -->',f'<!-- {name}-end -->'
    if start in text:
        before,rest=text.split(start,1); _,after=rest.split(end,1)
        text=before+start+'\n'+block+'\n'+end+after
    else:
        first,rest=text.split('\n',1)
        text=first+'\n\n'+start+'\n'+block+'\n'+end+'\n'+rest
    path.write_text(text,encoding='utf-8',newline='\n')


def build():
    paths=['results/responses.jsonl','results/luna-none-v1/responses.jsonl',
           'results/medqa-english-v3/responses.jsonl']
    raw={p:records(path) for p,path in zip(('jev','luna','medqa'),paths)}
    cells=[]; selected={}
    for task,label,language,condition in [
        ('belebele','Belebele','English','en_en'),('belebele','Belebele','Korean','ko_ko'),
        ('pawsx','PAWS-X','English','en_en'),('pawsx','PAWS-X','Korean','ko_ko'),
        ('medqa','MedQA','English','en_en'),('kormed','KorMedMCQA','Korean','ko_ko')]:
        cell=dict(task=task,label=label,language=language,condition=condition,providers={})
        for provider in ('jev','luna'):
            rr=([r for r in raw['medqa'] if r['provider']==provider] if task=='medqa' else
                [r for r in raw[provider] if r['eval_id'].startswith(task+'-') and r['eval_id'].endswith('__'+condition)])
            good={r.get('case_id',r['eval_id'].split('__')[0]):r for r in rr if r['status']=='success'}
            assert len(good)==100
            selected[(task,language,provider)]=good
            n=len(good); k=sum(r['score']['correct'] for r in good.values())
            cell['providers'][provider]=dict(n=n,correct=k,accuracy=k/n,ci95=wilson(k,n),
                case_ids=sorted(good),
                attempts=len(rr),cost_usd=sum(r['budget_charge_usd'] for r in rr),
                median_latency_ms=quantile([r['latency_ms'] for r in good.values()],.5),
                summed_call_seconds=sum(r['latency_ms'] for r in rr)/1000,
                concurrency=4 if task=='medqa' else 1)
        cell['luna_minus_jev']=paired_difference(selected[(task,language,'jev')],selected[(task,language,'luna')])
        cells.append(cell)
    # Resample original questions jointly across models AND translated conditions.
    # Four independent source strata, with both language observations kept together.
    strata=[]
    for task,languages in [('belebele',['English','Korean']),('pawsx',['English','Korean']),
                           ('medqa',['English']),('kormed',['Korean'])]:
        ids=sorted(selected[(task,languages[0],'jev')])
        assert all(set(ids)==set(selected[(task,lang,p)]) for lang in languages for p in ('jev','luna'))
        strata.append([[sum(int(selected[(task,lang,p)][i]['score']['correct']) for lang in languages)
                        for p in ('jev','luna')] for i in ids])
    def macro(count):
        active=strata[:count]; denominator=400 if count==2 else 600
        point=[sum(sum(row[p] for row in s) for s in active)/denominator for p in range(2)]
        rng=random.Random(20260917); boot=[]
        for _ in range(4000):
            totals=[0,0]
            for s in active:
                for row in rng.choices(s,k=len(s)):
                    for p in range(2): totals[p]+=row[p]
            boot.append((totals[1]-totals[0])/denominator)
        boot.sort()
        return dict(jev=point[0],luna=point[1],luna_minus_jev=point[1]-point[0],
                    difference_ci95=[quantile(boot,.025),quantile(boot,.975)],
                    evaluated_answers_per_model=denominator,unique_questions_per_model=count*100)
    result=dict(cells=cells,descriptive_six_cell_macro=macro(4),general_four_cell_macro=macro(2),
        selection='Content and instruction languages match. Excludes development, robustness, synthetic notes and ko_en sensitivity conditions.',
        bootstrap='4000 stratified paired cluster resamples, seed 20260917. General-task translations stay with their source question. Fixed task composition, no multiplicity adjustment.',
        source_sha256={p:filehash(ROOT/p) for p in paths})
    language=[]
    for task in ('belebele','pawsx'):
        for provider in ('jev','luna'):
            language.append(dict(task=task,provider=provider,korean_minus_english=paired_difference(
                selected[(task,'English',provider)],selected[(task,'Korean',provider)])))
    result['matched_language_differences']=language
    result['english_instruction_sensitivity']={p:{k:v['accuracy'] for s in (1,2)
        for k,v in read(f'results/{"luna-none-v1/" if p=="luna" else ""}stage-{s}.json')['groups'].items()
        if k.endswith('/ko_en')} for p in ('jev','luna')}
    out=ROOT/'results/aggregate'; out.mkdir(exist_ok=True)
    (out/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.fonttype':'none'})
    fig,axes=plt.subplots(1,2,figsize=(11,5.3),gridspec_kw={'width_ratios':[1.25,1]})
    for p,color,marker,offset in [('jev','#2474A5','o',.12),('luna','#CF6B27','s',-.12)]:
        for i,c in enumerate(cells):
            g=c['providers'][p]; x=g['accuracy']*100; lo,hi=[v*100 for v in g['ci95']]
            axes[0].errorbar(x,5-i+offset,xerr=[[x-lo],[hi-x]],fmt=marker,color=color,capsize=3,
                             label=('Jev' if p=='jev' else 'Luna-none') if i==0 else None)
    axes[0].set_yticks(range(5,-1,-1),[c['label']+' · '+c['language'] for c in cells])
    axes[0].set(xlim=(50,101),ylim=(-.5,5.5),xlabel='Accuracy (%)',title='A  Individual benchmark cells')
    axes[0].legend(loc='lower left',fontsize=9)
    for i,c in enumerate(cells):
        d=c['luna_minus_jev']; x=d['difference']*100; lo,hi=[v*100 for v in d['ci95']]
        axes[1].errorbar(x,5-i,xerr=[[x-lo],[hi-x]],fmt='o',color='#444444',capsize=3)
    axes[1].axvline(0,color='#888888',linestyle=':',linewidth=1)
    axes[1].set(yticks=range(6),yticklabels=[],ylim=(-.5,5.5),xlim=(-16,17),
                xlabel='Luna-none minus Jev (percentage points)',title='B  Paired model differences')
    for ax in axes:
        ax.spines[['top','right']].set_visible(False); ax.grid(axis='x',alpha=.15)
        ax.axhline(1.5,color='#BBBBBB',linewidth=.8)
    fig.suptitle('English and Korean benchmark overview',fontweight='bold')
    fig.text(.5,.02,'100 questions per cell. A: Wilson 95% intervals. B: paired bootstrap 95% intervals.\nMedical rows use different English and Korean exams; no paired medical language comparison.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.08,1,.96))
    for ext in ('png','svg','pdf'):
        path=ROOT/f'docs/figures/aggregate.{ext}'; fig.savefig(path,dpi=180)
        if ext=='svg': path.write_text('\n'.join(s.rstrip() for s in path.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n')
    plt.close(fig)
    table=['| Task | Language | Jev | Luna-none | Luna − Jev, pp (95% CI) |',
           '|---|---|---:|---:|---:|']
    for c in cells:
        j,l=c['providers']['jev'],c['providers']['luna']; d=c['luna_minus_jev']
        table.append(f"| {c['label']} | {c['language']} | {j['correct']}/100 | {l['correct']}/100 | {d['difference']*100:+.0f} ({d['ci95'][0]*100:+.0f}, {d['ci95'][1]*100:+.0f}) |")
    a=result['descriptive_six_cell_macro']; g=result['general_four_cell_macro']
    overview=f"The equal-weight six-cell descriptive average is **Jev {a['jev']:.2%} and Luna-none {a['luna']:.2%}**. Luna minus Jev is {a['luna_minus_jev']*100:+.2f} percentage points (exploratory cluster-bootstrap 95% interval {a['difference_ci95'][0]*100:+.2f} to {a['difference_ci95'][1]*100:+.2f}). This summarizes this chosen battery, not general model ability or a medical language effect."
    general=f"Restricting the average to matched Belebele and PAWS-X gives Jev {g['jev']:.2%} and Luna-none {g['luna']:.2%}, a difference of {g['luna_minus_jev']*100:+.2f} points (95% interval {g['difference_ci95'][0]*100:+.2f} to {g['difference_ci95'][1]*100:+.2f})."
    lines=['# English and Korean benchmark overview','',overview,'',general,'',
        '![Benchmark accuracy and paired model differences](figures/aggregate.png)','',*table,'',
        '## Methods and interpretation','',
        'This is a retrospective aggregation of frozen results, with no additional model calls. Each cell uses 100 questions with the same items for both models. The primary display uses English instructions for English content and Korean instructions for Korean content. Therefore its general-task language differences combine content and instruction language. The earlier Korean-content, English-instruction condition is retained as a sensitivity analysis below.','',
        'The six cells have equal weight. With 100 answers per cell, this equals 518/600 correct for Jev and 520/600 for Luna. These are 400 unique source questions per model because the 100 Belebele and 100 PAWS-X questions each appear in two languages. A naive independent-binomial interval over 600 answers would ignore that dependence.','',
        'The exploratory aggregate difference interval uses 4,000 stratified paired cluster bootstrap draws, seed 20260917. Each source dataset is a fixed stratum. Source questions are sampled within strata, keeping both models and both translations together. Task weights remain fixed. This captures question-sampling variation within this battery, not uncertainty about which tasks to include. Intervals are not adjusted for multiple comparisons.','',
        'Belebele and PAWS-X are matched across languages. MedQA and KorMedMCQA are separate original-language examinations, with different curricula, difficulties, source selection and four versus five options. Medical scores are never treated as paired English/Korean items. A cross-exam ranking reversal does not establish a language effect. The aggregate is descriptive and must not replace the individual task results.','',
        '## General-task language differences','',
        '| Task | Model | Korean − English, pp (paired 95% CI) |','|---|---|---:|']
    for row in language:
        d=row['korean_minus_english']; lines.append(f"| {row['task']} | {row['provider']} | {d['difference']*100:+.0f} ({d['ci95'][0]*100:+.0f}, {d['ci95'][1]*100:+.0f}) |")
    lines+=['','## English-instruction sensitivity','',
        'For Korean content with English instructions, Jev/Luna accuracy was Belebele 95%/93%, PAWS-X 75%/76%, and KorMedMCQA 82%/89%. These conditions are reported separately and are not counted again in the primary average. With all content using English instructions, the six-cell descriptive average is Jev 86.33% and Luna 87.17%. This sensitivity reinforces that a small aggregate difference depends on protocol choices.','',
        '## Cost and timing by cell','',
        '| Task | Language | Concurrency per model | Jev / Luna median ms | Jev / Luna estimated USD |',
        '|---|---|---:|---:|---:|']
    for c in cells:
        j,l=c['providers']['jev'],c['providers']['luna']
        lines.append(f"| {c['label']} | {c['language']} | {j['concurrency']} | {j['median_latency_ms']:.0f} / {l['median_latency_ms']:.0f} | {j['cost_usd']:.6f} / {l['cost_usd']:.6f} |")
    costs={p:sum(c['providers'][p]['cost_usd'] for c in cells) for p in ('jev','luna')}
    lines+=['',f"The selected six cells cost an estimated ${costs['jev']:.6f} for Jev and ${costs['luna']:.6f} for Luna, including recorded attempts. This is {costs['luna']/costs['jev']:.2f} times the Jev cost for this battery. Token accounting is provider-specific and prices are estimates, not invoices.",'',
        'English MedQA used four concurrent requests per provider. Earlier tasks ran sequentially. No pooled elapsed-time speedup is reported across these protocols. The MedQA report records combined wall time separately from summed call durations. No new API cost was incurred to generate this overview.','',
        '## Reproduction and evidence','',
        'Run `python -m jevbench.aggregate` against the published repository. The output records source response-file checksums, cell membership, aggregate methodology and sensitivity results. Development items, repeated or perturbed robustness items, and unreviewed synthetic medical notes are excluded. Luna supplied categorical answers without probability vectors, so cross-model calibration scores cannot be computed from this run.','',
        '[Machine-readable aggregation](https://github.com/mahlernim/jev-korean-benchmark/blob/main/results/aggregate/summary.json) · [Sample check](https://ahn-lab.org/jev-korean-benchmark/index.html) · [Methodology](https://ahn-lab.org/jev-korean-benchmark/methodology.html)']
    # Detailed report kept as regenerable evidence; narrative pages are hand-written.
    (ROOT/'results/aggregate/report.md').write_text(BREAK.join(lines)+BREAK,encoding='utf-8',newline=BREAK)
    from .publish import render_web
    render_web()
    print(json.dumps({'six_cell':a,'general_only':g,'cost':costs},indent=2))


if __name__=='__main__':
    build()
