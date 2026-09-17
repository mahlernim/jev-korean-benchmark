from __future__ import annotations

import copy
import json
import math
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

import httpx
import pyarrow.parquet as pq

from .common import ROOT, SEED, digest, filehash, frozen, now, read, write_new
from .synthetic import development_cases, medical_cases

SOURCES = {
    "belebele": ("facebook/belebele", ["data/eng_Latn.jsonl", "data/kor_Hang.jsonl"], "CC-BY-SA-4.0"),
    "pawsx": ("google-research-datasets/paws-x", ["en/test-00000-of-00001.parquet", "ko/test-00000-of-00001.parquet"], "See upstream Google PAWS LICENSE"),
    "kormed": ("sean0042/KorMedMCQA", ["doctor/test-00000-of-00001-a16785256f5f42b8.parquet"], "CC-BY-NC-2.0"),
}


def fetch_sources():
    base = ROOT / "data" / "sources"
    lock_path = base / "sources.json"
    if lock_path.exists():
        lock = read(lock_path)
        for source in lock.values():
            for entry in source["files"]:
                if filehash(ROOT / entry["local"]) != entry["sha256"]:
                    raise ValueError("Source checksum mismatch")
        return lock
    public_lock=ROOT/"results"/"source-lock.json"
    if public_lock.exists():
        lock=read(public_lock)
        with httpx.Client(follow_redirects=True,timeout=90) as client:
            for source in lock.values():
                for entry in source["files"]:
                    local=ROOT/entry["local"]
                    if not local.exists():
                        response=client.get(entry["url"]); response.raise_for_status()
                        local.parent.mkdir(parents=True,exist_ok=True)
                        with local.open("xb") as stream: stream.write(response.content)
                    if filehash(local)!=entry["sha256"]: raise ValueError("Pinned source checksum mismatch")
        write_new(lock_path,lock)
        return lock
    lock = {}
    with httpx.Client(follow_redirects=True, timeout=90) as client:
        for name, (repo, paths, license_name) in SOURCES.items():
            response = client.get(f"https://huggingface.co/api/datasets/{repo}")
            response.raise_for_status()
            revision = response.json()["sha"]
            entries = []
            for remote in ["README.md", *paths]:
                url = f"https://huggingface.co/datasets/{repo}/resolve/{revision}/{remote}"
                local = base / name / revision / remote
                if not local.exists():
                    response = client.get(url)
                    response.raise_for_status()
                    local.parent.mkdir(parents=True, exist_ok=True)
                    with local.open("xb") as stream:
                        stream.write(response.content)
                entries.append(dict(url=url, local=local.relative_to(ROOT).as_posix(), sha256=filehash(local)))
            lock[name] = dict(repository=repo, revision=revision, license=license_name, fetched_at=now(), files=entries)
    write_new(lock_path, lock)
    return lock


def rows(source, suffix):
    entry = next(e for e in source["files"] if e["local"].endswith(suffix))
    path = ROOT / entry["local"]
    if suffix.endswith("jsonl"):
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    return pq.read_table(path).to_pylist()


def unique_index(records, key):
    out = {}
    for row in records:
        k = key(row)
        if k in out:
            raise ValueError(f"Duplicate source ID {k}")
        out[k] = row
    return out


def paired_rows(en, ko, key, label, exclusions, task):
    a, b = unique_index(en, key), unique_index(ko, key)
    matched = []
    for k in sorted(a.keys() | b.keys(), key=str):
        if k not in a or k not in b:
            exclusions.append(dict(task=task, id=str(k), reason="unmatched_language_id"))
        elif label(a[k]) != label(b[k]):
            exclusions.append(dict(task=task, id=str(k), reason="cross_language_gold_mismatch"))
        else:
            matched.append((k, a[k], b[k]))
    return matched


def public_cases(lock):
    rng = random.Random(SEED)
    exclusions, audit, cases = [], {}, []
    en = rows(lock["belebele"], "eng_Latn.jsonl")
    ko = rows(lock["belebele"], "kor_Hang.jsonl")
    # This distribution has no split field. `ds` is a language-specific export
    # date, not a join key. (link, question_number) is validated unique below.
    key = lambda r: (r["link"], str(r["question_number"]))
    paired = paired_rows(en, ko, key, lambda r: str(r["correct_answer_num"]), exclusions, "belebele")
    passages = defaultdict(list)
    for item in paired:
        passages[item[0][:1]].append(item)
    for pk in rng.sample(sorted(passages), 100):
        k, a, b = rng.choice(passages[pk])
        options = {lang: {str(i): row[f"mc_answer{i}"] for i in range(1,5)} for lang,row in [("en",a),("ko",b)]}
        cases.append(dict(id="belebele-"+digest(k)[:16], source_id=list(k), passage_id=list(pk), stage=1, task="belebele",
            kind="choice", gold=str(a["correct_answer_num"]), options=options,
            content={lang: {"passage": row["flores_passage"], "question": row["question"]} for lang,row in [("en",a),("ko",b)]}))
    audit["belebele"] = dict(en_rows=len(en), ko_rows=len(ko), matched=len(paired), eligible_passages=len(passages), selected=100)
    en = rows(lock["pawsx"], "en/test-00000-of-00001.parquet")
    ko = rows(lock["pawsx"], "ko/test-00000-of-00001.parquet")
    paired = paired_rows(en, ko, lambda r: str(r["id"]), lambda r: int(r["label"]), exclusions, "pawsx")
    valid = []
    for k,a,b in paired:
        texts = [r[field] for r in [a,b] for field in ["sentence1","sentence2"]]
        if any(not isinstance(t,str) or not t.strip() or t.strip().upper()=="NS" for t in texts):
            exclusions.append(dict(task="pawsx", id=k, reason="missing_or_NS_translation"))
        else:
            valid.append((k,a,b))
    for label in (0,1):
        for k,a,b in rng.sample([v for v in valid if int(v[1]["label"]) == label],50):
            cases.append(dict(id="pawsx-"+k, source_id=k, stage=1, task="pawsx", kind="noul", gold=str(label),
                content={lang: {"sentence1":row["sentence1"],"sentence2":row["sentence2"]} for lang,row in [("en",a),("ko",b)]}))
    audit["pawsx"] = dict(en_rows=len(en),ko_rows=len(ko),matched=len(paired),eligible=len(valid),selected=100)
    records = rows(lock["kormed"], SOURCES["kormed"][1][0])
    unique_index(records, lambda r:(r["year"],r["period"],r["q_number"]))
    years = defaultdict(list)
    # Conservative screening, with all selected items additionally inspected before inference.
    media = re.compile(r"그림|사진|도표|그래프|아래\s*표|다음\s*표|표\s*\d|영상.*(?:보여|보인|같다)|(?:검사|결과|소견|심전도).*(?:다음과 같다|아래와 같다)")
    for r in records:
        identifier = f"{r['year']}-{r['period']}-{r['q_number']}"
        if not all(isinstance(r.get(k),str) and r[k].strip() for k in ["question","A","B","C","D","E"]) or int(r["answer"]) not in range(1,6):
            exclusions.append(dict(task="kormed",id=identifier,reason="missing_text_or_invalid_answer"))
        elif media.search(r["question"]):
            exclusions.append(dict(task="kormed",id=identifier,reason="conservative_missing_media_screen"))
        else:
            years[int(r["year"])].append(r)
    counts = proportional({y:len(v) for y,v in years.items()},100)
    for year in sorted(years):
        for r in rng.sample(years[year],counts[year]):
            identifier=f"{r['year']}-{r['period']}-{r['q_number']}"
            cases.append(dict(id="kormed-"+identifier,source_id=identifier,year=year,stage=2,task="kormed",kind="choice",
                gold=str(int(r["answer"])),content={"ko":{"question":r["question"]}},
                options={"ko":{str(i):r[letter] for i,letter in enumerate("ABCDE",1)}}))
    audit["kormed"] = dict(source_rows=len(records), eligible=sum(map(len,years.values())), eligible_by_year={str(y):len(v) for y,v in years.items()},selected_by_year={str(y):n for y,n in counts.items()}, selected=100)
    return cases, exclusions, audit


def proportional(counts, n):
    total=sum(counts.values())
    if total<n: raise ValueError("Not enough eligible cases")
    result={k:math.floor(v*n/total) for k,v in counts.items()}
    remainder=sorted(counts,key=lambda k:(-(counts[k]*n/total-result[k]),k))
    for k in remainder[:n-sum(result.values())]: result[k]+=1
    return result


def evaluation(case, condition, model):
    content_lang, instruction_lang = condition.split("_")
    task, kind = case["task"],case["kind"]
    instructions = {
        "noul": {"en":"Do sentence1 and sentence2 express the same meaning? Evaluate semantic equivalence, not just shared words.","ko":"sentence1과 sentence2의 의미가 같습니까? 단어의 유사성이 아니라 의미의 동등성을 판단하세요."},
        "choice": {"en":"Select the single correct answer to the question using only the supplied text. If an unknown option is provided, use it when the text does not determine the answer.","ko":"제공된 글만을 근거로 질문의 정답 하나를 고르세요. 알 수 없음 선택지가 있다면 글만으로 답을 판단할 수 없을 때 선택하세요."},
        "kormed": {"en":"Select the single best answer to this Korean medical examination question.","ko":"다음 한국어 의학 시험 문제에서 가장 적절한 정답 하나를 고르세요."},
    }
    instruction=case.get("instructions",instructions["kormed" if task=="kormed" else kind])[instruction_lang]
    question=dict(type=kind,instructions=instruction)
    if kind=="choice":
        option_lang = instruction_lang if task in ("medical_text","development_choice") else content_lang
        question["criteria"]=case["options"][option_lang]
    request=dict(model=model,state=case["content"][content_lang],questions={"answer":question})
    return dict(eval_id=f"{case['id']}__{condition}",case_id=case["id"],stage=case["stage"],task=task,kind=kind,
        condition=condition,gold=case["gold"],category=case.get("category"),pair_id=case.get("pair_id"),
        review_status=case.get("review_status","public_gold"),request=request,request_hash=digest(request))


def robustness(evaluations):
    rng=random.Random(SEED+4)
    chosen=[]
    for task in ("belebele","pawsx","kormed","medical_text"):
        candidates=[e for e in evaluations if e["task"]==task and e["condition"]=="ko_ko"]
        chosen.extend(rng.sample(candidates,5))
    result=[]
    for base in chosen:
        for variant in ("repeat1","repeat2","variant1","variant2"):
            e=copy.deepcopy(base)
            e.update(eval_id=base["eval_id"]+"__"+variant,stage=4,base_eval_id=base["eval_id"],variant=variant)
            if variant.startswith("variant"):
                if e["kind"]=="choice":
                    options=e["request"]["questions"]["answer"]["criteria"]
                    keys=list(options)
                    shift=1 if variant=="variant1" else 2
                    order=keys[shift:]+keys[:shift]
                    # Keep option IDs attached to their meanings and gold label unchanged.
                    e["request"]["questions"]["answer"]["criteria"]={k:options[k] for k in order}
                else:
                    state=e["request"]["state"]
                    state["sentence1"],state["sentence2"]=state["sentence2"],state["sentence1"]
                    # Both variants reverse the two sentences; duplicate variants are intentional repeats.
            e["request_hash"]=digest(e["request"])
            result.append(e)
    return result


def prepare(experiment="pilot-v1",model="jev-latest"):
    path=ROOT/"data"/experiment
    manifest_path=path/"manifest.json"
    if manifest_path.exists():
        from .common import load_manifest
        manifest=load_manifest(manifest_path)
        fetch_sources()
        print(f"Existing frozen manifest verified: {len(manifest['evaluations'])} evaluations")
        return
    sources=fetch_sources()
    public, exclusions, audit=public_cases(sources)
    medical=medical_cases()
    cases=development_cases()+public+medical
    evaluations=[]
    for case in cases:
        for condition in (["ko_en","ko_ko"] if case["stage"]==2 else ["en_en","ko_en","ko_ko"]):
            evaluations.append(evaluation(case,condition,model))
    evaluations+=robustness(evaluations)
    released=ROOT/"results"/"experiment-lock.json"
    release=read(released) if released.exists() else {}
    created=release["created_at"] if release.get("experiment")==experiment else now()
    manifest=dict(schema_version=1,experiment=experiment,created_at=created,seed=SEED,model=model,
        price_per_million_input_usd=0.042,budget_usd=0.25,sources=sources,audit=audit,exclusions=exclusions,
        medical_review_status="unreviewed_exploratory",evaluations=evaluations)
    manifest["sha256"]=digest(manifest)
    if release.get("experiment")==experiment and release["manifest_hash"]!=manifest["sha256"]:
        raise ValueError("Reconstructed manifest differs from released experiment; no file written")
    assert Counter(e["stage"] for e in evaluations)=={0:36,1:600,2:200,3:120,4:80}
    frozen(path/"cases.json",cases)
    write_new(manifest_path,manifest)
    packet=["# Clinician review packet", "", "All cases and English equivalents were authored before inference. None has clinician approval yet.", "", "For each case, check Korean meaning, English equivalence, gold label, and ambiguity. Record reviewer, date, approval or correction in a separate review file. Corrections require a new manifest and experiment. Do not edit the frozen manifest.", ""]
    for c in medical:
        packet += [f"## {c['id']}",f"Category: {c['category']}; minimal pair: {c['pair_id']}",f"Korean: {c['content']['ko']['note']}",f"Query: {c['content']['ko']['query']}",f"English: {c['content']['en']['note']}",f"Query: {c['content']['en']['query']}",f"Options KO: {json.dumps(c['options']['ko'],ensure_ascii=False)}",f"Options EN: {json.dumps(c['options']['en'])}",f"Proposed gold: {c['gold']}","Review: PENDING",""]
    (path/"clinician_review.md").write_text("\n\n".join(packet).rstrip()+"\n",encoding="utf-8")
    selected=["# Medical test input audit", "", "Inspect every item for absent image/table dependencies before Stage 2. Gold labels deliberately omitted here.", ""]
    for c in public:
        if c["task"]=="kormed":
            selected += [f"## {c['id']}", c["content"]["ko"]["question"],json.dumps(c["options"]["ko"],ensure_ascii=False),""]
    (path/"medical_input_audit.md").write_text("\n\n".join(selected),encoding="utf-8")
    print(json.dumps(dict(manifest=str(manifest_path),evaluations=len(evaluations),audit=audit,exclusions=len(exclusions)),ensure_ascii=False,indent=2))
