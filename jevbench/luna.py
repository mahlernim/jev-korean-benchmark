"""Decision-only Luna comparison. Never modifies the original Jev experiment."""
import argparse
import json
import platform
import time
from collections import defaultdict

import httpx

from .common import ROOT, canonical, digest, filehash, frozen, load_manifest, now, read, write_new
from .report import paired_difference, quantile, wilson
from .runner import run_lock

DIRECTORY = ROOT / 'runs/luna-none-v1'


def credential():
    values = {}
    for line in (ROOT/'typesafe.env').read_text(encoding='utf-8-sig').splitlines():
        if '=' in line and not line.strip().startswith('#'):
            k,v = line.strip().removeprefix('export ').split('=',1)
            values[k.strip()] = v.strip().strip('\"\'')
    if not values.get('OPENAI_API_KEY'):
        raise RuntimeError('OPENAI_API_KEY missing from credential file')
    return values['OPENAI_API_KEY']


def request(e):
    q = e['request']['questions']['answer']
    options = q.get('criteria')
    answer = {'type':'string','enum':list(options)} if options else {'type':'boolean'}
    content = q['instructions'] + '\n\n' + canonical(e['request']['state'])
    if options:
        content += '\n\n' + canonical(options)
    return dict(model='gpt-5.6-luna', reasoning={'effort':'none'}, store=False,
        service_tier='default', max_output_tokens=128,
        input=[{'role':'user','content':content}],
        text={'format':{'type':'json_schema','name':'decision','strict':True,
            'schema':{'type':'object','properties':{'answer':answer},
                      'required':['answer'],'additionalProperties':False}}})


def prepare():
    original = load_manifest(ROOT/'data/pilot-v1/manifest.json')
    evaluations = []
    for e in original['evaluations']:
        r = request(e)
        evaluations.append({**{k:e[k] for k in ('eval_id','case_id','stage','task','condition','kind','gold')},
                            'source_request_hash':e['request_hash'],'request':r,'request_hash':digest(r)})
    m = dict(experiment='luna-none-v1', source_manifest_hash=original['sha256'],
        budget_usd=.25, input_price=.20/1e6, cached_input_price=.02/1e6, output_price=1.20/1e6,
        evaluations=evaluations)
    m['sha256'] = digest(m)
    frozen(DIRECTORY/'manifest.json',m)
    return m


def validate(e,raw):
    if raw.get('status')!='completed':
        raise ValueError('Response not completed')
    texts = [c['text'] for o in raw.get('output',[]) if o.get('type')=='message'
             for c in o.get('content',[]) if c.get('type')=='output_text']
    if len(texts)!=1:
        raise ValueError('Expected one structured answer')
    value = json.loads(texts[0])
    if set(value)!= {'answer'}:
        raise ValueError('Invalid answer keys')
    a = value['answer']
    if e['kind']=='noul':
        if type(a) is not bool: raise ValueError('Invalid boolean')
        prediction = str(int(a))
    else:
        if a not in e['request']['text']['format']['schema']['properties']['answer']['enum']:
            raise ValueError('Invalid choice')
        prediction = a
    usage=raw['usage']; i=usage['input_tokens']; o=usage['output_tokens']
    c=usage.get('input_tokens_details',{}).get('cached_tokens',0)
    reasoning=usage.get('output_tokens_details',{}).get('reasoning_tokens',0)
    if any(type(v) is not int or v<0 for v in (i,o,c,reasoning)) or c>i or reasoning>o:
        raise ValueError('Invalid usage')
    if reasoning: raise ValueError('Unexpected reasoning tokens with none')
    if not raw.get('model'): raise ValueError('Missing model')
    return dict(prediction=prediction,correct=prediction==e['gold'],input_tokens=i,
                output_tokens=o,cached_tokens=c,reasoning_tokens=reasoning,
                estimated_cost_usd=((i-c)*.20+c*.02+o*1.20)/1e6)


def records():
    return [read(p) for p in sorted((DIRECTORY/'attempts').glob('*.json'))]


def report(m):
    rr=records(); good={r['eval_id']:r for r in rr if r['status']=='success'}
    jev={r['eval_id']:r for r in map(json.loads,(ROOT/'results/responses.jsonl').read_text().splitlines()) if r['status']=='success'}
    for stage in range(5):
        es=[e for e in m['evaluations'] if e['stage']==stage]
        groups=defaultdict(list)
        for e in es:
            if e['eval_id'] in good: groups[e['task']+'/'+e['condition']].append(e)
        ids={e['eval_id'] for e in es}
        failed={r['eval_id'] for r in rr if r['eval_id'] in ids and r['status']=='error' and r['terminal']}-set(good)
        result=dict(stage=stage,planned=len(es),successful=sum(e['eval_id'] in good for e in es),
                    failed=len(failed),pending=sum(e['eval_id'] not in good and e['eval_id'] not in failed for e in es),groups={})
        lines=[f'# Luna none comparison, stage {stage}', '',
            'Decision-only responses. No probabilities, Brier score or confidence-based coverage are available.', '',
            '| Task / condition | n | Luna accuracy (95% CI) | Jev accuracy | Luna minus Jev (95% paired interval) | Median / p95 ms | USD |',
            '|---|---:|---:|---:|---:|---:|---:|']
        for key,items in groups.items():
            if stage==4: continue
            selected=[good[e['eval_id']] for e in items]; n=len(selected)
            k=sum(r['score']['correct'] for r in selected); ci=wilson(k,n)
            left={e['eval_id']:jev[e['eval_id']] for e in items}
            right={e['eval_id']:good[e['eval_id']] for e in items}
            paired=paired_difference(left,right)
            lat=[r['latency_ms'] for r in selected]
            cost=sum(r['score']['estimated_cost_usd'] for r in selected)
            v=dict(n=n,correct=k,accuracy=k/n,ci95=ci,paired=paired,
                   median_latency_ms=quantile(lat,.5),p95_latency_ms=quantile(lat,.95),cost_usd=cost)
            result['groups'][key]=v
            lines.append(f"| {key} | {n} | {k/n:.1%} ({ci[0]:.1%}, {ci[1]:.1%}) | {sum(r['score']['correct'] for r in left.values())/n:.1%} | {paired['difference']*100:+.1f} ({paired['ci95'][0]*100:+.1f}, {paired['ci95'][1]*100:+.1f}) pp | {v['median_latency_ms']:.0f} / {v['p95_latency_ms']:.0f} | {cost:.6f} |")
        if stage==4:
            lines=lines[:3]+['','| Task / perturbation | n | Luna answer flips | Jev answer flips |','|---|---:|---:|---:|']
            robust=defaultdict(list)
            for e in es:
                base=e['case_id']+'__ko_ko'
                if e['eval_id'] in good and base in good:
                    robust[e['task']+'/'+e['eval_id'].rsplit('__',1)[-1]].append(dict(
                        eval_id=e['eval_id'],luna_flip=good[e['eval_id']]['score']['prediction']!=good[base]['score']['prediction'],
                        jev_flip=jev[e['eval_id']]['score']['prediction']!=jev[base]['score']['prediction']))
            result['robustness']=dict(robust)
            for key,values in robust.items():
                lines.append(f"| {key} | {len(values)} | {sum(v['luna_flip'] for v in values)} | {sum(v['jev_flip'] for v in values)} |")
        if stage in (1,2):
            result['language_differences']={}
            lines+=['','## Within-Luna paired language differences','',
                    '| Task / contrast | Difference (95% paired interval), pp |','|---|---:|']
            for task in sorted({e['task'] for e in es}):
                for left,right in [('en_en','ko_en'),('ko_en','ko_ko')]:
                    a={e['case_id']:good[e['eval_id']] for e in es if e['task']==task and e['condition']==left and e['eval_id'] in good}
                    b={e['case_id']:good[e['eval_id']] for e in es if e['task']==task and e['condition']==right and e['eval_id'] in good}
                    d=paired_difference(a,b)
                    if d:
                        result['language_differences'][task+'/'+right+'-'+left]=d
                        lines.append(f"| {task}, {right} minus {left} | {d['difference']*100:+.1f} ({d['ci95'][0]*100:+.1f}, {d['ci95'][1]*100:+.1f}) |")
        lines+=['',f"Successful {result['successful']}/{len(es)}, terminal failures {result['failed']}, pending {result['pending']}. Stage 3 is unreviewed and exploratory. Stage 4 reuses cases and is not a primary accuracy estimate."]
        directory=DIRECTORY/'reports'; directory.mkdir(exist_ok=True)
        (directory/f'stage-{stage}.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        (directory/f'stage-{stage}.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return good


def run(m,stage,limit=None):
    with run_lock(DIRECTORY):
        start=time.perf_counter(); started=now()
        try:
            rr=records(); hist=defaultdict(list)
            expected={e['eval_id']:e for e in m['evaluations']}
            for r in rr:
                if r['manifest_hash']!=m['sha256'] or r['request_hash']!=expected[r['eval_id']]['request_hash']:
                    raise RuntimeError('History integrity failure')
                hist[r['eval_id']].append(r)
            for attempts in hist.values():
                if sorted(r['attempt'] for r in attempts)!=list(range(1,len(attempts)+1)):
                    raise RuntimeError('Noncontiguous attempt history')
            if any(r.get('fatal') for r in rr): raise RuntimeError('Unresolved fatal attempt')
            if any(not hist[e['eval_id']] or not any(r['terminal'] for r in hist[e['eval_id']]) for e in m['evaluations'] if e['stage']<stage):
                raise RuntimeError('Previous stages incomplete')
            if stage==2:
                audit=read(ROOT/'data/pilot-v1/medical_input_review.json')
                if audit['manifest_hash']!=m['source_manifest_hash'] or not audit['all_selected_text_complete']:
                    raise RuntimeError('Medical source audit mismatch')
            spent=sum(r['budget_charge_usd'] for r in rr)
            models={r['raw_response']['model'] for r in rr if r['status']=='success'}
            called=0
            write_new(DIRECTORY/'invocations'/(started.replace(':','-')+'.json'),dict(started_at=started,
                python=platform.python_version(),httpx=httpx.__version__,timeout_seconds=30,concurrency=1,
                runner_source_sha256=filehash(__file__),
                latency_boundary='HTTP POST through response decode and answer validation, excluding persistence',
                stage=stage,model='gpt-5.6-luna',reasoning='none'))
            with httpx.Client(timeout=30,headers={'Authorization':'Bearer '+credential()}) as client:
                for e in m['evaluations']:
                    if e['stage']!=stage or any(r['terminal'] for r in hist[e['eval_id']]): continue
                    if limit is not None and called>=limit: break
                    for attempt in range(len(hist[e['eval_id']])+1,4):
                        reserve=(len(canonical(e['request']).encode('utf-8'))+2048)*.20/1e6+128*1.20/1e6
                        if spent+reserve>m['budget_usd']: raise RuntimeError('Budget ceiling reached')
                        stem=digest(e['eval_id'])[:24]+f'-{attempt}'
                        ip=DIRECTORY/'intents'/(stem+'.json'); rp=DIRECTORY/'attempts'/(stem+'.json')
                        if ip.exists(): raise RuntimeError('Uncertain existing request intent')
                        rec=dict(eval_id=e['eval_id'],request_hash=e['request_hash'],manifest_hash=m['sha256'],attempt=attempt,started_at=now())
                        write_new(ip,rec); tick=time.perf_counter(); retryable=False
                        try:
                            response=client.post('https://api.openai.com/v1/responses',json=e['request'])
                            response.raise_for_status()
                            raw=response.json(); rec['raw_response']=raw
                            score=validate(e,raw)
                            if models and raw['model'] not in models: raise ValueError('Resolved model changed')
                            models.add(raw['model'])
                            rec.update(status='success',terminal=True,score=score,budget_charge_usd=score['estimated_cost_usd'])
                        except Exception as error:
                            status=error.response.status_code if isinstance(error,httpx.HTTPStatusError) else None
                            retryable=isinstance(error,httpx.TransportError) or status in (408,429) or (status is not None and status>=500)
                            rec.update(status='error',http_status=status,error_type=type(error).__name__,retryable=retryable,
                                       terminal=not retryable or attempt==3,fatal=not retryable,budget_charge_usd=reserve)
                            # No exception text, headers or request data are serialized.
                        rec.update(latency_ms=(time.perf_counter()-tick)*1000,finished_at=now())
                        write_new(rp,rec); spent+=rec['budget_charge_usd']; called+=1
                        hist[e['eval_id']].append(rec)
                        if called%10==0: print(f'Stage {stage}: {called} calls, ledger USD {spent:.6f}',flush=True)
                        if rec.get('fatal'): raise RuntimeError('API or validation failure; see sanitized record')
                        if rec['terminal']: break
                        time.sleep(min(2**attempt,30))
        finally:
            write_new(DIRECTORY/'timing'/(started.replace(':','-')+'.json'),dict(stage=stage,started_at=started,finished_at=now(),wall_seconds=time.perf_counter()-start))
            report(m)


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('command',choices=['prepare','run','report','restore'])
    parser.add_argument('--stage',type=int,choices=range(5),default=0); parser.add_argument('--limit',type=int)
    args=parser.parse_args(); m=prepare()
    if args.command=='restore':
        public=ROOT/'results/luna-none-v1'
        if read(public/'experiment-lock.json')['sha256']!=m['sha256']:
            raise RuntimeError('Published manifest mismatch')
        for r in map(json.loads,(public/'responses.jsonl').read_text(encoding='utf-8').splitlines()):
            stem=digest(r['eval_id'])[:24]+f"-{r['attempt']}"
            target=DIRECTORY/'attempts'/(stem+'.json')
            if target.exists() and digest(read(target))==r.get('original_record_sha256'):
                continue
            frozen(target,r)
        report(m)
    elif args.command=='run': run(m,args.stage,args.limit)
    elif args.command=='report': report(m)
    else: print(f"Frozen {len(m['evaluations'])} requests, {m['sha256']}")


if __name__=='__main__': main()
