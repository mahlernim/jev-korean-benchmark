"""Sentence-order sensitivity on PAWS-X, English and Korean, Jev and Luna.

Paraphrase equivalence is symmetric, so reversing sentence1 and sentence2
leaves the gold label unchanged. Any prediction change is therefore an
inconsistency rather than a different question. Never modifies earlier
experiments: both orientations are re-run here so the comparison is
internally matched instead of paired across experiments.
"""
import argparse
import copy
import json
import platform
import time
from collections import defaultdict

import httpx

from .common import PRICE, ROOT, canonical, digest, filehash, frozen, load_manifest, now, read, write_new
from .report import quantile, wilson
from .runner import run_lock

DIRECTORY = ROOT / 'runs/order-sensitivity-v1'
EXPERIMENT = 'order-sensitivity-v1'
BUDGET_USD = .25
LUNA_INPUT, LUNA_CACHED, LUNA_OUTPUT = .20/1e6, .02/1e6, 1.20/1e6
CONDITIONS = ('en_en', 'ko_ko')
ORIENTATIONS = ('original', 'reversed')
ROLES = ('jev', 'luna')


def credential(name):
    values = {}
    for line in (ROOT/'typesafe.env').read_text(encoding='utf-8-sig').splitlines():
        if '=' in line and not line.strip().startswith('#'):
            k, v = line.strip().removeprefix('export ').split('=', 1)
            values[k.strip()] = v.strip().strip('"\'')
    if not values.get(name):
        raise RuntimeError(f'{name} missing from credential file')
    return values[name]


def reverse_state(state):
    out = copy.deepcopy(state)
    out['sentence1'], out['sentence2'] = out['sentence2'], out['sentence1']
    return out


def luna_request(instructions, state):
    content = instructions + '\n\n' + canonical(state)
    return dict(model='gpt-5.6-luna', reasoning={'effort': 'none'}, store=False,
        service_tier='default', max_output_tokens=128,
        input=[{'role': 'user', 'content': content}],
        text={'format': {'type': 'json_schema', 'name': 'decision', 'strict': True,
            'schema': {'type': 'object', 'properties': {'answer': {'type': 'boolean'}},
                       'required': ['answer'], 'additionalProperties': False}}})


def prepare():
    source = load_manifest(ROOT/'data/pilot-v1/manifest.json')
    base = {}
    for e in source['evaluations']:
        if e['task'] == 'pawsx' and e['stage'] == 1 and e['condition'] in CONDITIONS:
            base[(e['case_id'], e['condition'])] = e
    expected = 100*len(CONDITIONS)
    if len(base) != expected:
        raise ValueError(f'Expected {expected} source evaluations, found {len(base)}')
    evaluations = []
    for (case_id, condition), e in sorted(base.items()):
        instructions = e['request']['questions']['answer']['instructions']
        for orientation in ORIENTATIONS:
            state = e['request']['state'] if orientation == 'original' else reverse_state(e['request']['state'])
            for role in ROLES:
                if role == 'jev':
                    request = dict(model=source['model'], state=state,
                                   questions={'answer': dict(type='noul', instructions=instructions)})
                else:
                    request = luna_request(instructions, state)
                evaluations.append(dict(
                    eval_id=f'{case_id}__{condition}__{orientation}__{role}',
                    case_id=case_id, condition=condition, orientation=orientation, role=role,
                    task='pawsx', kind='noul', gold=e['gold'],
                    source_eval_id=e['eval_id'], source_request_hash=e['request_hash'],
                    request=request, request_hash=digest(request)))
    m = dict(experiment=EXPERIMENT, source_manifest_hash=source['sha256'], model=source['model'],
             budget_usd=BUDGET_USD, jev_input_price=PRICE,
             luna_input_price=LUNA_INPUT, luna_cached_price=LUNA_CACHED, luna_output_price=LUNA_OUTPUT,
             conditions=list(CONDITIONS), orientations=list(ORIENTATIONS), roles=list(ROLES),
             evaluations=evaluations)
    m['sha256'] = digest(m)
    frozen(DIRECTORY/'manifest.json', m)
    return m


def validate_jev(raw):
    if not isinstance(raw.get('model'), str) or not raw['model']:
        raise ValueError('Missing response model')
    if set(raw.get('answers', {})) != {'answer'}:
        raise ValueError('Unexpected answer keys')
    a = raw['answers']['answer']
    if a.get('type') != 'noul':
        raise ValueError('Answer type mismatch')
    p = a['noul']
    if not isinstance(p, (int, float)) or isinstance(p, bool) or not 0 <= p <= 1:
        raise ValueError('Invalid probability')
    n = raw.get('usage', {}).get('input_tokens')
    if not isinstance(n, int) or isinstance(n, bool) or n < 0:
        raise ValueError('Missing or invalid token usage')
    return dict(prediction='1' if p >= .5 else '0', probability=float(p),
                input_tokens=n, output_tokens=0, estimated_cost_usd=n*PRICE)


def validate_luna(raw):
    if raw.get('status') != 'completed':
        raise ValueError('Response not completed')
    texts = [c['text'] for o in raw.get('output', []) if o.get('type') == 'message'
             for c in o.get('content', []) if c.get('type') == 'output_text']
    if len(texts) != 1:
        raise ValueError('Expected one structured answer')
    value = json.loads(texts[0])
    if set(value) != {'answer'} or type(value['answer']) is not bool:
        raise ValueError('Invalid answer')
    usage = raw['usage']
    i, o = usage['input_tokens'], usage['output_tokens']
    c = usage.get('input_tokens_details', {}).get('cached_tokens', 0)
    reasoning = usage.get('output_tokens_details', {}).get('reasoning_tokens', 0)
    if any(type(v) is not int or v < 0 for v in (i, o, c, reasoning)) or c > i or reasoning > o:
        raise ValueError('Invalid usage')
    if reasoning:
        raise ValueError('Unexpected reasoning tokens with none')
    if not raw.get('model'):
        raise ValueError('Missing model')
    return dict(prediction=str(int(value['answer'])), probability=None,
                input_tokens=i, output_tokens=o,
                estimated_cost_usd=(i-c)*LUNA_INPUT + c*LUNA_CACHED + o*LUNA_OUTPUT)


def write_summary(path, value):
    """Derived analysis output, regenerable from the frozen attempts."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n',
                    encoding='utf-8')


def records():
    return [read(p) for p in sorted((DIRECTORY/'attempts').glob('*.json'))]


def run(role=None, limit=None):
    m = load_manifest(DIRECTORY/'manifest.json')
    with run_lock(DIRECTORY):
        started = now(); tick = time.perf_counter()
        try:
            return run_locked(m, role, limit)
        finally:
            write_new(DIRECTORY/'timing'/(started.replace(':', '-')+'.json'),
                      dict(role=role, started_at=started, finished_at=now(),
                           wall_seconds=time.perf_counter()-tick))


def run_locked(m, role, limit):
    from typesafe_sdk import Noul, RetryPolicy, TypeSafeClient
    write_new(DIRECTORY/'invocations'/(now().replace(':', '-')+'.json'),
              dict(manifest_hash=m['sha256'], runner_source_hash=filehash(__file__),
                   python_version=platform.python_version(), os=platform.system(),
                   concurrency=1, timeout_seconds=30, role=role,
                   latency_definition='Client-observed synchronous call duration including network and decoding'))
    prior = records()
    done = {r['eval_id'] for r in prior if r['status'] == 'success'}
    tries = defaultdict(int)
    for r in prior:
        tries[r['eval_id']] += 1
    spent = sum(r.get('estimated_cost_usd', 0) for r in prior)
    selected = [e for e in m['evaluations'] if role in (None, e['role'])]
    jev = TypeSafeClient(api_key=credential('TYPESAFE_KEY'), model=m['model'],
                         retry=RetryPolicy(max_retries=0), timeout=30)
    luna = httpx.Client(timeout=60, headers={'Authorization': 'Bearer '+credential('OPENAI_API_KEY')})
    called = 0
    try:
        for e in selected:
            if e['eval_id'] in done:
                continue
            attempt = tries[e['eval_id']] + 1
            if attempt > 3:
                raise RuntimeError(f'Attempt ceiling reached for {e["eval_id"]}')
            if limit is not None and called >= limit:
                break
            reserve = (len(canonical(e['request']).encode('utf-8'))+2048) * (
                PRICE if e['role'] == 'jev' else LUNA_INPUT+LUNA_OUTPUT)
            if spent + reserve > m['budget_usd']:
                raise RuntimeError('Estimated budget ceiling reached')
            stem = digest(e['eval_id'])[:24]+f'-{attempt}'
            intent = DIRECTORY/'intents'/(stem+'.json')
            result = DIRECTORY/'attempts'/(stem+'.json')
            if intent.exists() and not result.exists():
                raise RuntimeError('Uncertain interrupted request. Inspect intent; do not silently resend')
            write_new(intent, dict(eval_id=e['eval_id'], request_hash=e['request_hash'],
                                   manifest_hash=m['sha256'], attempt=attempt, started_at=now()))
            tick = time.perf_counter()
            try:
                if e['role'] == 'jev':
                    q = e['request']['questions']['answer']
                    raw = jev.system_one(state=e['request']['state'],
                                         questions={'answer': Noul(instructions=q['instructions'])},
                                         model=e['request']['model'])
                    raw = raw.raw_http_response.json()
                    score = validate_jev(raw)
                else:
                    response = luna.post('https://api.openai.com/v1/responses', json=e['request'])
                    response.raise_for_status()
                    raw = response.json()
                    score = validate_luna(raw)
                status, error = 'success', None
            except Exception as exc:
                raw, score, status, error = None, {}, 'error', f'{type(exc).__name__}: {exc}'
            latency = (time.perf_counter()-tick)*1000
            write_new(result, dict(eval_id=e['eval_id'], request_hash=e['request_hash'],
                                   manifest_hash=m['sha256'], role=e['role'], attempt=attempt,
                                   condition=e['condition'], orientation=e['orientation'],
                                   case_id=e['case_id'], gold=e['gold'], status=status, error=error,
                                   latency_ms=latency, recorded_at=now(),
                                   raw_response=raw, **score))
            spent += score.get('estimated_cost_usd', 0)
            called += 1
            if status == 'error':
                raise RuntimeError(f'Stopping on failure for {e["eval_id"]}: {error}')
    finally:
        jev.close(); luna.close()
    return called


def paired_rate_difference(left, right, seed=20260917+5):
    """Bootstrap the difference in flip rate over the same case_ids."""
    import random
    ids = sorted(set(left) & set(right))
    if not ids:
        return None
    diffs = [int(right[k])-int(left[k]) for k in ids]
    rng = random.Random(seed)
    boot = sorted(sum(rng.choices(diffs, k=len(diffs)))/len(diffs) for _ in range(4000))
    return dict(n=len(ids), difference=sum(diffs)/len(diffs),
                ci95=[quantile(boot, .025), quantile(boot, .975)])


def analyze():
    m = load_manifest(DIRECTORY/'manifest.json')
    good = {r['eval_id']: r for r in records() if r['status'] == 'success'}
    index = {}
    for e in m['evaluations']:
        r = good.get(e['eval_id'])
        if r:
            index[(e['role'], e['condition'], e['orientation'], e['case_id'])] = r
    cells, flips_by = {}, {}
    for role in ROLES:
        for condition in CONDITIONS:
            cases = sorted({k[3] for k in index if k[0] == role and k[1] == condition})
            paired = [c for c in cases
                      if (role, condition, 'original', c) in index
                      and (role, condition, 'reversed', c) in index]
            flips, tvs, acc = {}, [], {}
            for orientation in ORIENTATIONS:
                rs = [index[(role, condition, orientation, c)] for c in paired]
                acc[orientation] = dict(correct=sum(r['prediction'] == r['gold'] for r in rs), n=len(rs))
            w2r = r2w = 0
            for c in paired:
                a = index[(role, condition, 'original', c)]
                b = index[(role, condition, 'reversed', c)]
                flips[c] = a['prediction'] != b['prediction']
                if flips[c]:
                    ac = a['prediction'] == a['gold']
                    bc = b['prediction'] == b['gold']
                    if not ac and bc:
                        w2r += 1
                    elif ac and not bc:
                        r2w += 1
                if a['probability'] is not None and b['probability'] is not None:
                    tvs.append(abs(a['probability']-b['probability']))
            k, n = sum(flips.values()), len(flips)
            cells[f'{role}/{condition}'] = dict(
                role=role, condition=condition, n=n, flips=k,
                flip_rate=k/n if n else None, flip_ci95=wilson(k, n),
                mean_total_variation=sum(tvs)/len(tvs) if tvs else None,
                wrong_to_right=w2r, right_to_wrong=r2w,
                accuracy=acc)
            flips_by[(role, condition)] = flips
    language = {}
    for role in ROLES:
        d = paired_rate_difference(flips_by.get((role, 'en_en'), {}), flips_by.get((role, 'ko_ko'), {}))
        if d:
            language[role] = d
    summary = dict(experiment=EXPERIMENT, generated_at=now(), manifest_hash=m['sha256'],
                   successful=len(good), planned=len(m['evaluations']),
                   estimated_cost_usd=sum(r.get('estimated_cost_usd', 0) for r in records()),
                   cells=cells, korean_minus_english_flip_rate=language)
    write_summary(DIRECTORY/'summary.json', summary)
    return summary


def report():
    s = analyze()
    pct = lambda v: '—' if v is None else f'{100*v:.0f}%'
    ci = lambda v: '—' if not v or v[0] is None else f'({100*v[0]:.0f}, {100*v[1]:.0f})'
    lines = ['# Sentence-order sensitivity on PAWS-X', '',
             'Reversing sentence1 and sentence2 leaves paraphrase equivalence unchanged, so a changed',
             'prediction is an inconsistency. Both orientations were run inside this experiment.', '',
             '| Model / condition | n | Flips | Flip rate (95% CI) | Mean prob. total variation |',
             '|---|---:|---:|---:|---:|']
    for key in sorted(s['cells']):
        c = s['cells'][key]
        tv = '—' if c['mean_total_variation'] is None else f'{c["mean_total_variation"]:.3f}'
        lines.append(f'| {key} | {c["n"]} | {c["flips"]} | {pct(c["flip_rate"])} {ci(c["flip_ci95"])} | {tv} |')
    lines += ['', '| Model / condition | Accuracy original | Accuracy reversed |', '|---|---:|---:|']
    for key in sorted(s['cells']):
        a = s['cells'][key]['accuracy']
        lines.append(f'| {key} | {a["original"]["correct"]}/{a["original"]["n"]} | '
                     f'{a["reversed"]["correct"]}/{a["reversed"]["n"]} |')
    if s['korean_minus_english_flip_rate']:
        lines += ['', '| Model | Korean minus English flip rate, pp (95% paired interval) |', '|---|---:|']
        for role, d in sorted(s['korean_minus_english_flip_rate'].items()):
            lines.append(f'| {role} | {100*d["difference"]:+.0f} ({100*d["ci95"][0]:+.0f}, {100*d["ci95"][1]:+.0f}) |')
    lines += ['', f'Successful {s["successful"]} of {s["planned"]}. '
                  f'Estimated cost ${s["estimated_cost_usd"]:.5f}.',
              '', 'Luna returns a decision only, so no probability total variation is available for it.', '']
    (DIRECTORY/'report.md').write_text('\n'.join(lines), encoding='utf-8')
    return '\n'.join(lines)


def main():
    p = argparse.ArgumentParser(description='PAWS-X sentence-order sensitivity')
    p.add_argument('command', choices=['prepare', 'run', 'report', 'export'])
    p.add_argument('--role', choices=list(ROLES))
    p.add_argument('--limit', type=int)
    a = p.parse_args()
    if a.command == 'prepare':
        m = prepare(); print(f'Frozen manifest {m["sha256"][:16]} with {len(m["evaluations"])} evaluations')
    elif a.command == 'run':
        print(f'Completed {run(a.role, a.limit)} calls')
    elif a.command == 'report':
        print(report())
    else:
        print(f'Exported evidence to {export()}')




def export_evidence(directory, experiment, records_fn):
    """Copy frozen evidence into results/ for publication. runs/ is not committed."""
    out = ROOT / 'results' / experiment
    out.mkdir(parents=True, exist_ok=True)
    manifest = read(directory / 'manifest.json')
    (out / 'manifest.json').write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    rows = sorted(records_fn(), key=lambda r: (r['eval_id'], r.get('attempt', 1)))
    (out / 'responses.jsonl').write_text(
        ''.join(canonical(r) + '\n' for r in rows), encoding='utf-8', newline='\n')
    for name in ('summary.json', 'report.md'):
        source = directory / name
        if source.exists():
            (out / name).write_text(source.read_text(encoding='utf-8'), encoding='utf-8')
    (out / 'timing.json').write_text(
        json.dumps([read(p) for p in sorted((directory / 'timing').glob('*.json'))],
                   ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    checksums = {p.name: filehash(p) for p in sorted(out.iterdir())
                 if p.is_file() and p.name != 'checksums.json'}
    (out / 'checksums.json').write_text(
        json.dumps(checksums, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return out


def export():
    return export_evidence(DIRECTORY, EXPERIMENT, records)


if __name__ == '__main__':
    main()
