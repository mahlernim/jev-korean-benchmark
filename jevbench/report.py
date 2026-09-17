from __future__ import annotations

import json
import math
import random
import statistics
from collections import defaultdict

from .common import ROOT, SEED, load_manifest, now, read


def wilson(k,n):
    if n==0: return [None,None]
    z=1.959963984540054
    p=k/n; d=1+z*z/n
    center=(p+z*z/(2*n))/d
    radius=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return [max(0,center-radius),min(1,center+radius)]


def quantile(values,p):
    a=sorted(values)
    if not a: return None
    position=(len(a)-1)*p
    lo=math.floor(position); hi=math.ceil(position)
    return a[lo]+(a[hi]-a[lo])*(position-lo)


def metrics(items):
    n=len(items)
    if not n: return dict(n=0)
    scores=[r["score"] for e,r in items]
    correct=sum(s["correct"] for s in scores)
    ranks=sorted(items,key=lambda x:(-x[1]["score"]["rank_confidence"],x[0]["eval_id"]))
    coverage={}
    for fraction in (.5,.75,1.):
        count=math.ceil(n*fraction)
        errors=sum(not r["score"]["correct"] for e,r in ranks[:count])
        coverage[str(fraction)]=dict(n=count,errors=errors,error_rate=errors/count)
    return dict(n=n,correct=correct,accuracy=correct/n,accuracy_ci95=wilson(correct,n),
        rounded_distribution_count=sum(s.get('probabilities_renormalized',False) for s in scores),
        raw_vector_brier=sum(s.get('raw_vector_brier',s['brier']) for s in scores)/n,
        raw_gold_log_loss=sum(s.get('raw_gold_log_loss',s['log_loss']) for s in scores)/n,
        brier=sum(s["brier"] for s in scores)/n,log_loss=sum(s["log_loss"] for s in scores)/n,
        median_latency_ms=quantile([r["latency_ms"] for e,r in items],.5),p95_latency_ms=quantile([r["latency_ms"] for e,r in items],.95),
        input_tokens=sum(s["input_tokens"] for s in scores),cost_usd=sum(s["estimated_cost_usd"] for s in scores),coverage=coverage)


def paired_difference(left,right,seed=SEED):
    ids=sorted(set(left)&set(right))
    if not ids: return None
    diffs=[int(right[k]["score"]["correct"])-int(left[k]["score"]["correct"]) for k in ids]
    rng=random.Random(seed)
    boot=sorted(sum(rng.choices(diffs,k=len(diffs)))/len(diffs) for _ in range(4000))
    return dict(n=len(ids),difference=sum(diffs)/len(diffs),ci95=[quantile(boot,.025),quantile(boot,.975)],
        left_only_correct=sum(left[k]["score"]["correct"] and not right[k]["score"]["correct"] for k in ids),
        right_only_correct=sum(right[k]["score"]["correct"] and not left[k]["score"]["correct"] for k in ids))


def report(experiment="pilot-v1",stage=None):
    from .runner import history
    manifest=load_manifest(ROOT/"data"/experiment/"manifest.json")
    run_dir=ROOT/"runs"/experiment
    hist=history(manifest,run_dir)
    evaluations=manifest["evaluations"]
    success={k:next((r for r in attempts if r["status"]=="success"),None) for k,attempts in hist.items()}
    stages=range(5) if stage is None else [stage]
    report_dir=run_dir/"reports"; report_dir.mkdir(parents=True,exist_ok=True)
    for s in stages:
        planned=[e for e in evaluations if e["stage"]==s]
        items=[(e,success[e["eval_id"]]) for e in planned if success.get(e["eval_id"])]
        failures=[e["eval_id"] for e in planned if hist.get(e["eval_id"]) and hist[e["eval_id"]][-1].get("terminal") and not success.get(e["eval_id"])]
        pending=[e["eval_id"] for e in planned if not hist.get(e["eval_id"]) or not hist[e["eval_id"]][-1].get("terminal")]
        summary=dict(stage=s,generated_at=now(),manifest_hash=manifest["sha256"],planned=len(planned),successful=len(items),failed=len(failures),pending=len(pending),failures=failures,pending_ids=pending,groups={})
        stage_attempts=[r for e in planned for r in hist.get(e["eval_id"],[])]
        timing=[read(p) for p in (run_dir/"timing").glob("*.json") if read(p)["stage"]==s]
        summary["runtime"]=dict(api_call_seconds=sum(r["latency_ms"] for r in stage_attempts)/1000,
            recorded_invocation_wall_seconds=sum(t["wall_seconds"] for t in timing),
            attempts=len(stage_attempts),retries=sum(r["attempt"]>1 for r in stage_attempts),
            input_tokens=sum(r.get("score",{}).get("input_tokens",0) for r in stage_attempts),
            output_tokens=sum(r.get("raw_response",{}).get("usage",{}).get("output_tokens",0) for r in stage_attempts),
            observed_cost_usd=sum(r.get("score",{}).get("estimated_cost_usd",0) for r in stage_attempts))
        if stage_attempts:
            summary["runtime"]["first_request_at"]=min(r["started_at"] for r in stage_attempts)
            summary["runtime"]["last_request_at"]=max(r["finished_at"] for r in stage_attempts)
        lines=[f"# Stage {s} report","",f"Planned {len(planned)}. Successful {len(items)}. Failed {len(failures)}. Pending {len(pending)}.","",f"Frozen manifest `{manifest['sha256']}`.",""]
        rt=summary["runtime"]
        lines += [f"API call time {rt['api_call_seconds']:.3f} seconds. Recorded runner wall time {rt['recorded_invocation_wall_seconds']:.3f} seconds. Attempts {rt['attempts']}, retries {rt['retries']}. Input tokens {rt['input_tokens']:,}, output tokens {rt['output_tokens']:,}. Estimated successful-call cost ${rt['observed_cost_usd']:.6f}.","","Per-call latency includes network and SDK decoding at concurrency one. Runner wall time also includes initialization, disk writes, retries and report generation, and excludes human gaps. The first ten development calls preceded invocation timing instrumentation, so Stage 0 wall time is incomplete. Token charges use published pricing, not an invoice.",""]
        amended=sum(r['score'].get('probabilities_renormalized',False) for e,r in items)
        adjudicated=sum('adjudication' in r for e,r in items)
        lines += [f"Rounding-compatible distributions normalized for probability metrics: {amended}. Previously stopped local-validation records admitted by a preserved adjudication: {adjudicated}. This is a disclosed analysis amendment after one five-option vector summed to 0.99 on a 0.01 grid. Original vectors and labels remain unchanged. See methodology for tolerance and sensitivity metrics.",""]
        if s==0: lines += ["Development checks only. These scores are not benchmark results.",""]
        if s==3:
            lines += ["**Exploratory only. All 40 authored medical cases and translations await clinician review. Primary medical text score is unavailable.**","","Intervals below treat items as independent and may be too narrow because minimal pairs are related. Category results have only eight cases.",""]
        if s==2:
            lines += ["Korean medical exam knowledge, not a paired language comparison or evidence of clinical readiness. Historical official gold answers are scored as provided. Conservative media screening changes the test population.",""]
        if s!=4:
            grouped=defaultdict(list)
            for e,r in items: grouped[(e["task"],e["condition"])].append((e,r))
            lines += ["| Task / condition | n | Accuracy (95% Wilson CI) | Brier | Log loss | Median / p95 ms | Cost USD |","|---|---:|---:|---:|---:|---:|---:|"]
            for (task,condition),group in sorted(grouped.items()):
                m=metrics(group); summary["groups"][task+"/"+condition]=m
                lo,hi=m["accuracy_ci95"]
                lines.append(f"| {task} / {condition} | {m['n']} | {m['accuracy']:.1%} ({lo:.1%}–{hi:.1%}) | {m['brier']:.4f} | {m['log_loss']:.4f} | {m['median_latency_ms']:.0f} / {m['p95_latency_ms']:.0f} | {m['cost_usd']:.6f} |")
            lines += ["","Conditions name content language first, instruction language second. Brier is the sum across classes (range 0–2); log loss uses natural logarithms and clips zero gold probability to 1e-15. Metrics exclude API failures, which are counted above.","","## Error versus coverage","","| Task / condition | 50% | 75% | 100% |","|---|---:|---:|---:|"]
            for key,m in summary["groups"].items():
                cells=[f"{m['coverage'][str(f)]['error_rate']:.1%} ({m['coverage'][str(f)]['n']} retained)" for f in (.5,.75,1.)]
                lines.append("| "+key+" | "+" | ".join(cells)+" |")
            lines += ["","Coverage uses returned Choice confidence or absolute Noul distance from 0.5. Ties break by evaluation ID. These are descriptive rankings, not calibrated deployment thresholds.","","## Paired differences",""]
            summary["paired"]={}
            for task in sorted({e["task"] for e,r in items}):
                for left,right in [("en_en","ko_en"),("ko_en","ko_ko")]:
                    a={e["case_id"]:r for e,r in items if e["task"]==task and e["condition"]==left}
                    b={e["case_id"]:r for e,r in items if e["task"]==task and e["condition"]==right}
                    d=paired_difference(a,b)
                    if d:
                        summary["paired"][f"{task}/{right}-{left}"]=d
                        lines.append(f"- {task}, {right} minus {left}: {d['difference']*100:+.1f} percentage points, paired bootstrap 95% interval [{d['ci95'][0]*100:+.1f}, {d['ci95'][1]*100:+.1f}]. {left}-only correct {d['left_only_correct']}; {right}-only correct {d['right_only_correct']}.")
            lines += ["","Small-sample intervals are exploratory. For authored minimal pairs, case-level bootstrap does not account for pair dependence.",""]
            if s==3:
                summary["categories"]={}
                for category in sorted({e["category"] for e,r in items}):
                    for condition in ("en_en","ko_en","ko_ko"):
                        group=[(e,r) for e,r in items if e["category"]==category and e["condition"]==condition]
                        summary["categories"][category+"/"+condition]=metrics(group)
                lines += ["## Exploratory categories","","| Category / condition | Correct / n |","|---|---:|"]
                for key,m in summary["categories"].items():
                    if m["n"]: lines.append(f"| {key} | {m['correct']} / {m['n']} |")
            errors=sorted([(e,r) for e,r in items if not r["score"]["correct"]],key=lambda x:-x[1]["score"]["rank_confidence"])
            summary["errors"]=[dict(eval_id=e["eval_id"],gold=e["gold"],prediction=r["score"]["prediction"],confidence=r["score"]["rank_confidence"]) for e,r in errors]
            lines += ["","## Highest-ranked errors","","| Evaluation | Gold | Prediction | Ranking signal |","|---|---|---|---:|"]
            for e,r in errors[:20]: lines.append(f"| {e['eval_id']} | {e['gold']} | {r['score']['prediction']} | {r['score']['rank_confidence']:.4f} |")
            disagreements=[]
            for case_id in sorted({e["case_id"] for e,r in items}):
                by_condition={e["condition"]:r["score"]["prediction"] for e,r in items if e["case_id"]==case_id}
                if len(set(by_condition.values()))>1: disagreements.append(dict(case_id=case_id,predictions=by_condition))
            summary["condition_disagreements"]=disagreements
            lines += ["",f"There are {len(disagreements)} cases with different predictions across conditions. Full error and disagreement lists are in the adjacent JSON report. Disagreement alone does not establish a translation defect.",""]
        else:
            variants=defaultdict(list)
            for e,r in items:
                base=success.get(e["base_eval_id"])
                if not base: continue
                a,b=base["score"],r["score"]
                delta=sum(abs(a["probabilities"][k]-b["probabilities"][k]) for k in a["probabilities"])/2
                variants[(e["task"],e["variant"])].append(dict(eval_id=e["eval_id"],flip=a["prediction"]!=b["prediction"],total_variation=delta))
            summary["robustness"]={"/".join(k):v for k,v in variants.items()}
            lines += ["These 20 cases were chosen before inference, five from each scored task. Medical-text cases remain exploratory. Two Noul variants use the same reversal and measure repeated response to that reversal.","","| Task / variant | n | Answer flips | Mean probability total variation |","|---|---:|---:|---:|"]
            for key,values in sorted(variants.items()):
                lines.append(f"| {' / '.join(key)} | {len(values)} | {sum(v['flip'] for v in values)} | {statistics.mean(v['total_variation'] for v in values):.5f} |")
        (report_dir/f"stage-{s}.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
        (report_dir/f"stage-{s}.md").write_text("\n".join(lines),encoding="utf-8")
    attempts=[r for values in hist.values() for r in values]
    observed=sum(r.get("score",{}).get("estimated_cost_usd",0) for r in attempts)
    charged=sum(r.get("budget_charge_usd",0) for r in attempts)
    index=["# Jev Korean pilot","",f"Updated {now()}","",f"Observed successful-call token cost ${observed:.6f}. Conservative budget charges including failed attempts ${charged:.6f} of ${manifest['budget_usd']:.2f}.","",f"Models observed: {', '.join(sorted({r['raw_response']['model'] for r in attempts if r.get('status')=='success'})) or 'none'}.","","| Stage | Planned | Success | Failure | Pending |","|---|---:|---:|---:|---:|"]
    for s in range(5):
        p=report_dir/f"stage-{s}.json"
        if p.exists():
            data=json.loads(p.read_text(encoding="utf-8"))
            index.append(f"| [Stage {s}](stage-{s}.md) | {data['planned']} | {data['successful']} | {data['failed']} | {data['pending']} |")
    index += ["","The synthetic medical set awaits clinician review and is excluded from primary medical scoring. No patient records were used. Published benchmark training exposure is unknown. No cross-task composite score is calculated.","","Sources, revisions, exclusions and all requests are frozen in the manifest. Licensing metadata is retained with the source snapshots. Stage reports and JSON are reproducible derived files; source files, manifest, request intents and attempt records are preserved."]
    (report_dir/"README.md").write_text("\n".join(index),encoding="utf-8")
