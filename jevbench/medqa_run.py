"""Paired original-English MedQA with bounded parallel provider pools."""
import argparse
import concurrent.futures
import json
import threading
import time
from collections import defaultdict

import httpx
from typesafe_sdk import Choice, RetryPolicy, TypeSafeClient

from . import luna
from .common import ROOT, canonical, digest, filehash, frozen, load_manifest, now, read, write_new
from .runner import credential as jev_credential, run_lock, transient, validated
from .medqa_prepare import EXPERIMENT

DIRECTORY=ROOT/'runs'/EXPERIMENT
THREADS=4


def prepare():
    m=load_manifest(ROOT/'data'/EXPERIMENT/'manifest.json')
    requests=[]
    for e in m['evaluations']:
        for provider in ('jev','luna'):
            payload=e['request'] if provider=='jev' else luna.request(e)
            requests.append(dict(eval_id=provider+'__'+e['eval_id'],case_id=e['case_id'],provider=provider,
                gold=e['gold'],kind='choice',request=payload,request_hash=digest(payload)))
    manifest=dict(experiment=EXPERIMENT,source_manifest_hash=m['sha256'],requests=requests,
        concurrency_per_provider=THREADS,budget_usd=.25,max_retries=2,timeout_seconds=30,
        prices_per_million={'jev_input':.042,'luna_input':.20,'luna_cached_input':.02,'luna_output':1.20})
    manifest['sha256']=digest(manifest)
    frozen(DIRECTORY/'request-manifest.json',manifest)
    return manifest


def records():
    return [read(p) for p in sorted((DIRECTORY/'attempts').glob('*.json'))]


def reservation(e):
    n=len(canonical(e['request']).encode('utf-8'))+2048
    return n*.042/1e6 if e['provider']=='jev' else (n*.20+128*1.20)/1e6


class Ledger:
    def __init__(self,limit,spent=0):
        self.limit=limit; self.spent=spent; self.inflight=0; self.lock=threading.Lock()
    def reserve(self,amount):
        with self.lock:
            if self.spent+self.inflight+amount>self.limit: raise RuntimeError('Budget ceiling reached')
            self.inflight+=amount
    def settle(self,reserved,charge):
        with self.lock:
            self.inflight-=reserved; self.spent+=charge


def run(limit=None):
    m=prepare()
    audit=read(ROOT/'data'/EXPERIMENT/'input-review.json')
    if audit.get('manifest_hash')!=m['source_manifest_hash'] or not audit.get('all_selected_text_complete'):
        raise RuntimeError('Selected-input completeness review required')
    with run_lock(DIRECTORY):
        history=defaultdict(list); lookup={e['eval_id']:e for e in m['requests']}
        for r in records():
            if r['manifest_hash']!=m['sha256'] or r['request_hash']!=lookup[r['eval_id']]['request_hash']:
                raise RuntimeError('History integrity failure')
            history[r['eval_id']].append(r)
        for rs in history.values():
            if sorted(r['attempt'] for r in rs)!=list(range(1,len(rs)+1)): raise RuntimeError('Invalid retry history')
            if any(r.get('fatal') for r in rs): raise RuntimeError('Unresolved fatal failure')
        pending=[e for e in m['requests'] if not any(r['terminal'] for r in history[e['eval_id']])]
        if limit is not None: pending=pending[:limit]
        ledger=Ledger(m['budget_usd'],sum(r['budget_charge_usd'] for rs in history.values() for r in rs))
        expected={p:{r['raw_response']['model'] for rs in history.values() for r in rs if r['provider']==p and r['status']=='success'} for p in ('jev','luna')}
        if any(len(v)>1 for v in expected.values()): raise RuntimeError('Mixed model versions')
        # Check all outstanding intents before launching any new work.
        for intent in (DIRECTORY/'intents').glob('*.json'):
            if not (DIRECTORY/'attempts'/intent.name).exists(): raise RuntimeError('Uncertain interrupted request')
        stop=threading.Event(); model_lock=threading.Lock(); clients=[]; client_lock=threading.Lock()
        local=threading.local(); keys={'jev':jev_credential(ROOT/'typesafe.env'),'luna':luna.credential()}
        def client(provider):
            if not hasattr(local,'client'):
                local.client=(TypeSafeClient(api_key=keys[provider],model='jev-latest',retry=RetryPolicy(max_retries=0),timeout=30)
                    if provider=='jev' else httpx.Client(timeout=30,headers={'Authorization':'Bearer '+keys[provider]}))
                with client_lock: clients.append(local.client)
            return local.client
        def work_inner(e,submitted_tick):
            provider=e['provider']; current=client(provider)
            for attempt in range(len(history[e['eval_id']])+1,4):
                if stop.is_set(): return
                reserve=reservation(e)
                try: ledger.reserve(reserve)
                except RuntimeError: stop.set(); raise
                stem=digest(e['eval_id'])[:24]+f'-{attempt}'
                rec=dict(eval_id=e['eval_id'],case_id=e['case_id'],provider=provider,attempt=attempt,
                    request_hash=e['request_hash'],manifest_hash=m['sha256'],started_at=now(),
                    dispatch_wait_ms=(time.perf_counter()-submitted_tick)*1000 if attempt==1 else None)
                write_new(DIRECTORY/'intents'/(stem+'.json'),rec)
                tick=time.perf_counter(); retryable=False
                try:
                    if provider=='jev':
                        q=e['request']['questions']['answer']
                        response=current.system_one(state=e['request']['state'],questions={'answer':Choice(instructions=q['instructions'],criteria=q['criteria'])},model=e['request']['model'])
                        raw=response.raw_http_response.json(); rec['raw_response']=raw
                        score=validated(e,raw)
                    else:
                        response=current.post('https://api.openai.com/v1/responses',json=e['request']); response.raise_for_status()
                        raw=response.json(); rec['raw_response']=raw; score=luna.validate(e,raw)
                        if raw.get('reasoning',{}).get('effort')!='none' or raw.get('service_tier')!='default':
                            raise ValueError('Unexpected Luna configuration')
                    with model_lock:
                        if expected[provider] and raw['model'] not in expected[provider]: raise ValueError('Model version changed')
                        expected[provider].add(raw['model'])
                    rec.update(status='success',terminal=True,score=score,budget_charge_usd=score['estimated_cost_usd'])
                except Exception as error:
                    status=error.response.status_code if isinstance(error,httpx.HTTPStatusError) else getattr(error,'status_code',None)
                    retryable=transient(error) if provider=='jev' else isinstance(error,httpx.TransportError) or status in (408,429) or (status is not None and status>=500)
                    rec.update(status='error',error_type=type(error).__name__,http_status=status,retryable=retryable,
                        terminal=not retryable or attempt==3,fatal=not retryable,budget_charge_usd=reserve)
                    if not retryable: stop.set()
                rec.update(finished_at=now(),latency_ms=(time.perf_counter()-tick)*1000)
                write_new(DIRECTORY/'attempts'/(stem+'.json'),rec)
                ledger.settle(reserve,rec['budget_charge_usd'])
                if rec.get('fatal'): raise RuntimeError('Fatal API or validation failure; inspect sanitized record')
                if rec['terminal']: return
                time.sleep(min(2**attempt,30))
        def work(e,submitted_tick):
            try: return work_inner(e,submitted_tick)
            except Exception:
                stop.set()
                raise
        started=now(); tick=time.perf_counter(); failures=[]; completed=0
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=THREADS) as jev_pool, concurrent.futures.ThreadPoolExecutor(max_workers=THREADS) as luna_pool:
                pools={'jev':jev_pool,'luna':luna_pool}
                futures=[pools[e['provider']].submit(work,e,time.perf_counter()) for e in pending]
                for future in concurrent.futures.as_completed(futures):
                    try: future.result()
                    except Exception as error: failures.append(type(error).__name__); stop.set()
                    completed+=1
                    if completed%20==0: print(f'{completed}/{len(pending)} scheduled evaluations finished, ledger ${ledger.spent:.6f}',flush=True)
        finally:
            close_errors=[]
            for c in clients:
                try: c.close()
                except Exception as error: close_errors.append(type(error).__name__)
            write_new(DIRECTORY/'timing'/(started.replace(':','-')+'.json'),dict(started_at=started,finished_at=now(),wall_seconds=time.perf_counter()-tick,
                scheduled=len(pending),concurrency_per_provider=THREADS,max_total_concurrency=2*THREADS,
                client_close_errors=close_errors,
                runner_sha256=filehash(__file__),request_manifest_hash=m['sha256'],
                transport={'jev':'typesafe-sdk 0.6.0','luna':'httpx 0.28.1'},
                timing_definition='Latency includes provider call, decoding and validation; excludes client construction, dispatch wait and persistence. Dispatch wait includes queueing, client initialization and admission. Invocation wall includes client initialization, retry delays, persistence and client closure. Up to eight admitted requests may finish after a fatal stop.'))
            failures.extend(close_errors)
        if failures: raise RuntimeError('Run stopped with recorded failures')
        good=[r for r in records() if r['status']=='success']
        print(json.dumps(dict(successful=len(good),estimated_cost_usd=sum(r['score']['estimated_cost_usd'] for r in good),ledger_usd=ledger.spent)))


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--limit',type=int)
    args=parser.parse_args(); run(args.limit)
