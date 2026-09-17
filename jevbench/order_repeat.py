"""Repeat-condition control for the sentence-order experiment.

Sends the unchanged original-orientation requests a second time, so the
order-reversal flip rate can be separated from ordinary service
nondeterminism. Compares against the frozen order-sensitivity-v1 records
and refuses to proceed unless the request hashes match exactly, so this
measures the same request and not a rebuilt one.

Jev only: Luna returns a decision with no probability, and its own
nondeterminism is out of scope for this control.
"""
import argparse
import json
import platform
import time
from collections import defaultdict

from .common import PRICE, ROOT, canonical, digest, filehash, frozen, load_manifest, now, read, write_new
from .order_sensitivity import DIRECTORY as SOURCE_DIR
from .order_sensitivity import credential, records as source_records, validate_jev
from .report import wilson
from .runner import run_lock

DIRECTORY = ROOT / 'runs/order-repeat-v1'
EXPERIMENT = 'order-repeat-v1'
BUDGET_USD = .10


def prepare():
    source = load_manifest(SOURCE_DIR / 'manifest.json')
    picked = [e for e in source['evaluations']
              if e['role'] == 'jev' and e['orientation'] == 'original']
    if len(picked) != 200:
        raise ValueError(f'Expected 200 source evaluations, found {len(picked)}')
    evaluations = []
    for e in sorted(picked, key=lambda x: x['eval_id']):
        evaluations.append(dict(
            eval_id=e['eval_id'] + '__repeat',
            source_eval_id=e['eval_id'],
            case_id=e['case_id'], condition=e['condition'], role='jev',
            orientation='original', task='pawsx', kind='noul', gold=e['gold'],
            request=e['request'], request_hash=e['request_hash']))
    m = dict(experiment=EXPERIMENT, source_manifest_hash=source['sha256'],
             model=source['model'], budget_usd=BUDGET_USD, jev_input_price=PRICE,
             evaluations=evaluations)
    m['sha256'] = digest(m)
    frozen(DIRECTORY / 'manifest.json', m)
    return m


def write_summary(path, value):
    """Derived analysis output, regenerable from the frozen attempts."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n',
                    encoding='utf-8')


def records():
    return [read(p) for p in sorted((DIRECTORY / 'attempts').glob('*.json'))]


def run(limit=None):
    m = load_manifest(DIRECTORY / 'manifest.json')
    with run_lock(DIRECTORY):
        started = now()
        tick = time.perf_counter()
        try:
            return run_locked(m, limit)
        finally:
            write_new(DIRECTORY / 'timing' / (started.replace(':', '-') + '.json'),
                      dict(started_at=started, finished_at=now(),
                           wall_seconds=time.perf_counter() - tick))


def run_locked(m, limit):
    from typesafe_sdk import Noul, RetryPolicy, TypeSafeClient
    write_new(DIRECTORY / 'invocations' / (now().replace(':', '-') + '.json'),
              dict(manifest_hash=m['sha256'], runner_source_hash=filehash(__file__),
                   python_version=platform.python_version(), os=platform.system(),
                   concurrency=1, timeout_seconds=30))
    prior = records()
    done = {r['eval_id'] for r in prior if r['status'] == 'success'}
    tries = defaultdict(int)
    for r in prior:
        tries[r['eval_id']] += 1
    spent = sum(r.get('estimated_cost_usd', 0) for r in prior)
    client = TypeSafeClient(api_key=credential('TYPESAFE_KEY'), model=m['model'],
                            retry=RetryPolicy(max_retries=0), timeout=30)
    called = 0
    try:
        for e in m['evaluations']:
            if e['eval_id'] in done:
                continue
            attempt = tries[e['eval_id']] + 1
            if attempt > 3:
                raise RuntimeError(f'Attempt ceiling reached for {e["eval_id"]}')
            if limit is not None and called >= limit:
                break
            reserve = (len(canonical(e['request']).encode('utf-8')) + 2048) * PRICE
            if spent + reserve > m['budget_usd']:
                raise RuntimeError('Estimated budget ceiling reached')
            stem = digest(e['eval_id'])[:24] + f'-{attempt}'
            intent = DIRECTORY / 'intents' / (stem + '.json')
            result = DIRECTORY / 'attempts' / (stem + '.json')
            if intent.exists() and not result.exists():
                raise RuntimeError('Uncertain interrupted request. Inspect intent; do not silently resend')
            write_new(intent, dict(eval_id=e['eval_id'], request_hash=e['request_hash'],
                                   manifest_hash=m['sha256'], attempt=attempt, started_at=now()))
            tick = time.perf_counter()
            try:
                q = e['request']['questions']['answer']
                raw = client.system_one(state=e['request']['state'],
                                        questions={'answer': Noul(instructions=q['instructions'])},
                                        model=e['request']['model']).raw_http_response.json()
                score = validate_jev(raw)
                status, error = 'success', None
            except Exception as exc:
                raw, score, status, error = None, {}, 'error', f'{type(exc).__name__}: {exc}'
            write_new(result, dict(eval_id=e['eval_id'], source_eval_id=e['source_eval_id'],
                                   request_hash=e['request_hash'], manifest_hash=m['sha256'],
                                   role='jev', condition=e['condition'], case_id=e['case_id'],
                                   gold=e['gold'], attempt=attempt, status=status, error=error,
                                   latency_ms=(time.perf_counter() - tick) * 1000,
                                   recorded_at=now(), raw_response=raw, **score))
            spent += score.get('estimated_cost_usd', 0)
            called += 1
            if status == 'error':
                raise RuntimeError(f'Stopping on failure for {e["eval_id"]}: {error}')
    finally:
        client.close()
    return called


def analyze():
    m = load_manifest(DIRECTORY / 'manifest.json')
    source_manifest = load_manifest(SOURCE_DIR / 'manifest.json')
    if m['source_manifest_hash'] != source_manifest['sha256']:
        raise ValueError('Source manifest changed since this control was frozen')
    source_hashes = {e['eval_id']: e['request_hash'] for e in source_manifest['evaluations']}
    first = {r['eval_id']: r for r in source_records() if r['status'] == 'success'}
    second = {r['eval_id']: r for r in records() if r['status'] == 'success'}
    cells, per_case = {}, {}
    for condition in ('en_en', 'ko_ko'):
        pairs = []
        for e in m['evaluations']:
            if e['condition'] != condition:
                continue
            a = first.get(e['source_eval_id'])
            b = second.get(e['eval_id'])
            if not a or not b:
                continue
            if source_hashes[e['source_eval_id']] != e['request_hash']:
                raise ValueError(f'Request hash mismatch for {e["eval_id"]}')
            pairs.append((e['case_id'], a, b))
        flips = [c for c, a, b in pairs if a['prediction'] != b['prediction']]
        tvs = [abs(a['probability'] - b['probability']) for _, a, b in pairs]
        k, n = len(flips), len(pairs)
        cells[f'jev/{condition}'] = dict(
            condition=condition, n=n, flips=k,
            flip_rate=k / n if n else None, flip_ci95=wilson(k, n),
            mean_total_variation=sum(tvs) / len(tvs) if tvs else None,
            flipped_case_ids=sorted(flips))
        per_case[condition] = {c: a['prediction'] != b['prediction'] for c, a, b in pairs}
    summary = dict(experiment=EXPERIMENT, generated_at=now(), manifest_hash=m['sha256'],
                   source_manifest_hash=m['source_manifest_hash'],
                   successful=len(second), planned=len(m['evaluations']),
                   estimated_cost_usd=sum(r.get('estimated_cost_usd', 0) for r in records()),
                   cells=cells)
    write_summary(DIRECTORY / 'summary.json', summary)
    return summary


def report():
    from .order_sensitivity import analyze as order_analyze
    s = analyze()
    order = order_analyze()
    pct = lambda v: '—' if v is None else f'{100 * v:.0f}%'
    ci = lambda v: '—' if not v or v[0] is None else f'({100 * v[0]:.0f}, {100 * v[1]:.0f})'
    lines = ['# Repeat-condition control', '',
             'The same requests were sent a second time without any change. This separates ordinary',
             'service nondeterminism from the effect of reversing sentence order.', '',
             '| Jev condition | n | Same input, flip rate | Reversed order, flip rate |',
             '|---|---:|---:|---:|']
    for condition in ('en_en', 'ko_ko'):
        r = s['cells'][f'jev/{condition}']
        o = order['cells'][f'jev/{condition}']
        lines.append(f'| {condition} | {r["n"]} | {pct(r["flip_rate"])} {ci(r["flip_ci95"])} | '
                     f'{pct(o["flip_rate"])} {ci(o["flip_ci95"])} |')
    lines += ['', '| Jev condition | Mean probability total variation, same input | Reversed order |',
              '|---|---:|---:|']
    for condition in ('en_en', 'ko_ko'):
        r = s['cells'][f'jev/{condition}']
        o = order['cells'][f'jev/{condition}']
        lines.append(f'| {condition} | {r["mean_total_variation"]:.3f} | {o["mean_total_variation"]:.3f} |')
    lines += ['', f'Successful {s["successful"]} of {s["planned"]}. '
                  f'Estimated cost ${s["estimated_cost_usd"]:.5f}.',
              '', 'Both columns use the same 100 source questions per condition. The repeat column is',
              'a floor for the reversal column: any flip that a repeated identical request produces',
              'is not attributable to sentence order.', '']
    (DIRECTORY / 'report.md').write_text('\n'.join(lines), encoding='utf-8')
    return '\n'.join(lines)


def main():
    p = argparse.ArgumentParser(description='Repeat-condition control')
    p.add_argument('command', choices=['prepare', 'run', 'report', 'export'])
    p.add_argument('--limit', type=int)
    a = p.parse_args()
    if a.command == 'prepare':
        m = prepare()
        print(f'Frozen manifest {m["sha256"][:16]} with {len(m["evaluations"])} evaluations')
    elif a.command == 'run':
        print(f'Completed {run(a.limit)} calls')
    elif a.command == 'report':
        print(report())
    else:
        print(f'Exported evidence to {export()}')




def export():
    from .order_sensitivity import export_evidence
    return export_evidence(DIRECTORY, EXPERIMENT, records)


if __name__ == '__main__':
    main()
