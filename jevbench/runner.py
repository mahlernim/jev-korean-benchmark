from __future__ import annotations

import importlib.metadata
import math
import os
import platform
import time
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path

from typesafe_sdk import Choice, Noul, RetryPolicy, TypeSafeClient

from .common import ROOT, PRICE, canonical, digest, filehash, frozen, load_manifest, now, read, write_new


def credential(path):
    values={}
    for line in Path(path).read_text(encoding="utf-8-sig").splitlines():
        line=line.strip()
        if not line or line.startswith("#") or "=" not in line: continue
        key,value=line.removeprefix("export ").split("=",1)
        values[key.strip()]=value.strip().strip("\"'")
    key=values.get("TYPESAFE_API_KEY") or values.get("TYPESAFE_KEY")
    if not key: raise ValueError("No supported credential variable in credential file")
    return key


def validated(e, raw):
    if not isinstance(raw.get("model"),str) or not raw["model"]:
        raise ValueError("Missing response model")
    if set(raw.get("answers",{}))!={"answer"}: raise ValueError("Unexpected answer keys")
    answer=raw["answers"]["answer"]
    if answer.get("type")!=e["kind"]: raise ValueError("Answer type mismatch")
    def probability(x):
        if not isinstance(x,(int,float)) or isinstance(x,bool) or not math.isfinite(x) or not 0<=x<=1:
            raise ValueError("Invalid probability/confidence")
        return float(x)
    if e["kind"]=="noul":
        p=probability(answer["noul"])
        probs={"0":1-p,"1":p}
        prediction="1" if p>=0.5 else "0"
        confidence=abs(p-0.5)
        raw_probs=probs.copy()
        mass=1.0
    else:
        expected=set(e["request"]["questions"]["answer"]["criteria"])
        if set(answer["probabilities"])!=expected: raise ValueError("Probability keys do not match options")
        probs={k:probability(v) for k,v in answer["probabilities"].items()}
        raw_probs=probs.copy()
        mass=sum(probs.values())
        # Observed early-access responses have probabilities on a 0.01 grid.
        # Bounded rounding tolerance is a disclosed analysis amendment, not a
        # claim about undocumented server internals. Preserve original values.
        on_grid=all(abs(v*100-round(v*100))<1e-8 for v in probs.values())
        tolerance=.005*len(probs)+1e-8 if on_grid else 1e-4
        if mass<=0 or abs(mass-1)>tolerance: raise ValueError("Probabilities do not sum to one within rounding tolerance")
        if abs(mass-1)>1e-8: probs={k:v/mass for k,v in probs.items()}
        prediction=answer["choice"]
        if prediction not in expected: raise ValueError("Choice outside options")
        if probs[prediction]+1e-4<max(probs.values()): raise ValueError("Choice inconsistent with probabilities")
        confidence=probability(answer["confidence"])
    usage=raw.get("usage",{})
    n=usage.get("input_tokens")
    if not isinstance(n,int) or isinstance(n,bool) or n<0: raise ValueError("Missing or invalid token usage")
    gold=e["gold"]
    return dict(prediction=prediction,probabilities=probs,rank_confidence=confidence,
        reported_probability_sum=mass,probabilities_renormalized=abs(mass-1)>1e-8,
        raw_vector_brier=sum((p-int(k==gold))**2 for k,p in raw_probs.items()),
        raw_gold_log_loss=-math.log(max(raw_probs[gold],1e-15)),
        correct=prediction==gold,brier=sum((p-int(k==gold))**2 for k,p in probs.items()),
        log_loss=-math.log(max(probs[gold],1e-15)),input_tokens=n,estimated_cost_usd=n*PRICE)


def transient(error):
    status=getattr(error,"status_code",None)
    return status in (408,429) or (isinstance(status,int) and 500<=status<=599) or type(error).__name__ in ("TypeSafeAPIConnectionError","TypeSafeAPITimeoutError")


def retry_delay(error, attempt):
    headers=getattr(error,"headers",{}) or {}
    try:
        delay=float(headers.get("retry-after",2**attempt))
    except (ValueError,TypeError):
        delay=2**attempt
    return min(max(delay,2**attempt),30)


def raw_records(run_dir):
    return [read(p) for p in sorted((Path(run_dir)/"attempts").glob("*.json"))]


def records(run_dir):
    result=raw_records(run_dir)
    for resolution_path in sorted((Path(run_dir)/"adjudications").glob("*.json")):
        resolution=read(resolution_path)
        matching=[i for i,r in enumerate(result) if r['eval_id']==resolution['eval_id'] and r['attempt']==resolution['attempt']]
        if len(matching)!=1: raise ValueError('Adjudication must refer to exactly one saved attempt')
        i=matching[0]; original=result[i]
        if digest(original)!=resolution['original_record_hash']: raise ValueError('Adjudication evidence mismatch')
        result[i]={**original,**resolution['effective_fields'],'adjudication':resolution_path.name,'original_status':original['status']}
    return result


def history(manifest, run_dir):
    expected={e["eval_id"]:e for e in manifest["evaluations"]}
    result=defaultdict(list)
    for r in records(run_dir):
        e=expected.get(r["eval_id"])
        if e is None or r["request_hash"]!=e["request_hash"] or r["manifest_hash"]!=manifest["sha256"]:
            raise ValueError("Attempt does not belong to this manifest")
        result[r["eval_id"]].append(r)
    for attempts in result.values():
        attempts.sort(key=lambda r:r["attempt"])
        if [r["attempt"] for r in attempts]!=list(range(1,len(attempts)+1)):
            raise ValueError("Noncontiguous attempt history")
    return result


@contextmanager
def run_lock(run_dir):
    """OS advisory lock releases on crashes without deleting lock files."""
    import msvcrt
    path=Path(run_dir)/"runner.lock"
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("a+b") as stream:
        if path.stat().st_size==0:
            stream.write(b"0"); stream.flush()
        stream.seek(0)
        try: msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1)
        except OSError: raise RuntimeError("Another runner owns this experiment") from None
        try: yield
        finally:
            stream.seek(0); msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)


def run(experiment="pilot-v1",stage=0,limit=None):
    directory=ROOT/"data"/experiment
    manifest=load_manifest(directory/"manifest.json")
    run_dir=ROOT/"runs"/experiment
    with run_lock(run_dir):
        started=now(); tick=time.perf_counter()
        try:
            return run_locked(manifest,run_dir,stage,limit)
        finally:
            write_new(run_dir/"timing"/(started.replace(":","-")+".json"),dict(stage=stage,started_at=started,
                finished_at=now(),wall_seconds=time.perf_counter()-tick,
                definition="Runner invocation wall time, including SDK initialization, requests, retries, local persistence and report generation; excludes preparation and human gaps"))
            from .report import report
            report(experiment,stage)


def run_locked(manifest,run_dir,stage,limit=None):
    from .report import report
    runtime=dict(manifest_hash=manifest["sha256"],sdk_version=importlib.metadata.version("typesafe-sdk"),
        runner_source_hash=filehash(Path(__file__)),price_per_input_token=PRICE,budget_usd=manifest["budget_usd"],
        python_version=platform.python_version(),os=platform.system(),os_release=platform.release(),
        local_timezone=time.tzname,concurrency=1,timeout_seconds=30,max_retries=2,
        latency_definition="Client-observed synchronous SDK call duration, including network and decoding; excludes local disk writes and retry sleep",
        client_geography="Not measured; workspace timezone Asia/Seoul",pricing_source="https://typesafe.ai/blog/introducing-system-one-models-and-jev")
    # Record implementation snapshots for every invocation, while preserving previous ones.
    write_new(run_dir/"invocations"/(now().replace(":","-")+".json"),runtime)
    hist=history(manifest,run_dir)
    if any(r.get("fatal") for attempts in hist.values() for r in attempts):
        raise RuntimeError("A fatal integrity/API failure exists. Inspect evidence before a new experiment")
    if stage>0:
        previous=[e for e in manifest["evaluations"] if e["stage"]<stage]
        if any(not hist.get(e["eval_id"]) or not hist[e["eval_id"]][-1].get("terminal") for e in previous):
            raise RuntimeError("Complete previous stages first")
        for s in range(stage):
            if not (run_dir/"reports"/f"stage-{s}.md").exists(): raise RuntimeError("Previous stage report missing")
    if stage==2:
        audit_path=ROOT/"data"/manifest["experiment"]/"medical_input_review.json"
        if not audit_path.exists() or read(audit_path).get("manifest_hash")!=manifest["sha256"] or not read(audit_path).get("all_selected_text_complete"):
            raise RuntimeError("Selected medical inputs require a recorded media-dependency audit")
    selected=[e for e in manifest["evaluations"] if e["stage"]==stage]
    all_records=[r for attempts in hist.values() for r in attempts]
    spent=sum(r.get("budget_charge_usd",0) for r in all_records)
    models={r["raw_response"]["model"] for r in all_records if r.get("status")=="success"}
    if len(models)>1: raise RuntimeError("Mixed resolved model versions")
    expected_model=next(iter(models),None)
    called=0
    client=TypeSafeClient(api_key=credential(ROOT/"typesafe.env"),model=manifest["model"],retry=RetryPolicy(max_retries=0),timeout=30)
    try:
        for e in selected:
            previous=hist.get(e["eval_id"],[])
            if previous and previous[-1].get("terminal"): continue
            if limit is not None and called>=limit: break
            for attempt in range(len(previous)+1,4):
                # UTF-8 byte count plus overhead is deliberately conservative before sending.
                reserve=(len(canonical(e["request"]).encode("utf-8"))+2048)*PRICE
                if spent+reserve>manifest["budget_usd"]:
                    report(manifest["experiment"],stage)
                    raise RuntimeError("Estimated budget ceiling reached")
                stem=digest(e["eval_id"])[:24]+f"-{attempt}"
                intent_path=run_dir/"intents"/(stem+".json")
                result_path=run_dir/"attempts"/(stem+".json")
                if intent_path.exists() and not result_path.exists():
                    raise RuntimeError("Uncertain interrupted request. Inspect intent; do not silently resend")
                write_new(intent_path,dict(eval_id=e["eval_id"],request_hash=e["request_hash"],manifest_hash=manifest["sha256"],attempt=attempt,started_at=now()))
                rec=dict(eval_id=e["eval_id"],request_hash=e["request_hash"],manifest_hash=manifest["sha256"],attempt=attempt,started_at=now())
                start=time.perf_counter()
                stop=False
                try:
                    q=e["request"]["questions"]["answer"]
                    question=Choice(instructions=q["instructions"],criteria=q["criteria"]) if e["kind"]=="choice" else Noul(instructions=q["instructions"])
                    response=client.system_one(state=e["request"]["state"],questions={"answer":question},model=e["request"]["model"])
                    rec["latency_ms"]=(time.perf_counter()-start)*1000
                    raw=response.raw_http_response.json()
                    rec["raw_response"]=raw
                    score=validated(e,raw)
                    if expected_model is not None and raw["model"]!=expected_model: raise ValueError("Resolved model changed")
                    expected_model=raw["model"]
                    rec.update(status="success",terminal=True,score=score,budget_charge_usd=score["estimated_cost_usd"])
                except Exception as error:
                    rec.setdefault("latency_ms",(time.perf_counter()-start)*1000)
                    retryable=transient(error)
                    # Never serialize exception messages, HTTP headers, or request objects.
                    rec.update(status="error",error_type=type(error).__name__,http_status=getattr(error,"status_code",None),
                        retryable=retryable,terminal=not retryable or attempt==3,fatal=not retryable,budget_charge_usd=reserve)
                    if isinstance(error,ValueError): rec["validation_error"]=str(error)
                    stop=not retryable
                    delay=retry_delay(error,attempt)
                rec["finished_at"]=now()
                write_new(result_path,rec)
                spent+=rec["budget_charge_usd"]
                called+=1
                hist[e["eval_id"]].append(rec)
                success_count=sum(r.get("status")=="success" for attempts in hist.values() for r in attempts)
                if success_count==10 and not (run_dir/"usage_after_10.json").exists():
                    good=[r for attempts in hist.values() for r in attempts if r.get("status")=="success"]
                    average=sum(r["score"]["input_tokens"] for r in good)/len(good)
                    write_new(run_dir/"usage_after_10.json",dict(average_input_tokens=average,observed_cost_usd=sum(r["score"]["estimated_cost_usd"] for r in good),
                        projected_1036_cost_usd=average*1036*PRICE,note="Development sample only; public medical questions can be longer"))
                    print(f"First 10 successful calls: {average:.1f} input tokens/call; extrapolated pilot ${average*1036*PRICE:.4f}",flush=True)
                if called%20==0 or stop: print(f"Stage {stage}: {called} calls this invocation, budget charged ${spent:.5f}, last {rec['status']}",flush=True)
                if stop:
                    report(manifest["experiment"],stage)
                    raise RuntimeError(f"Stopped on {rec['error_type']}; see saved sanitized attempt")
                if rec["terminal"]: break
                time.sleep(delay)
            # Report at a bounded interval so partial progress is inspectable.
            if called%100==0: report(manifest["experiment"],stage)
    finally:
        client.close()
    report(manifest["experiment"],stage)
    print(f"Stage {stage} invocation finished; {called} calls; total budget charged ${spent:.5f}",flush=True)
