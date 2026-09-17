"""Pick one worked example per benchmark and render it for the documentation.

Examples are drawn from items **outside** the scored set. Every source here has
far more items than the 100 used, so an unscored item shows the format exactly
while contaminating nothing: publishing it cannot degrade the questions this
study reports, nor any rerun of them.

Selection is seeded and recorded in results/examples-lock.json together with the
source revision and file hash, so the chosen items are reproducible rather than
hand-picked. No API calls are made.
"""
import json
import random
import re

from .common import ROOT, digest, filehash, read
from .prepare import rows

SEED = 20260917 + 11
LOCK = ROOT / 'results' / 'examples-lock.json'

# Every source permits redistributing an item with attribution. Verified 2026-09-17:
# Belebele CC BY-SA 4.0; PAWS "may be freely used for any purpose", acknowledgement
# appreciated; KorMedMCQA CC BY-NC 2.0 (this is non-commercial research); MedQA MIT.
ATTRIBUTION = {
    'belebele': ('Belebele, Bandarkar et al., ACL 2024, CC BY-SA 4.0',
                 'Belebele, Bandarkar et al., ACL 2024, CC BY-SA 4.0'),
    'pawsx': ('PAWS-X, Yang et al., EMNLP 2019. Data source: Google LLC',
              'PAWS-X, Yang et al., EMNLP 2019. 데이터 출처: Google LLC'),
    'kormed': ('KorMedMCQA, Kweon et al., 2024, CC BY-NC 2.0',
               'KorMedMCQA, Kweon et al., 2024, CC BY-NC 2.0'),
    'medqa': ('MedQA, Jin et al., 2020, MIT License',
              'MedQA, Jin et al., 2020, MIT License'),
}

TEXT = {
    'en': dict(
        heading='What the questions actually look like',
        intro='One real item per source, chosen at random from questions this study did **not** '
              'score. Seeing the format explains a lot about what the numbers mean.',
        belebele='Belebele — reading comprehension, same item in both languages',
        pawsx='PAWS-X — do these two sentences mean the same thing?',
        kormed='KorMedMCQA — Korean medical licensing exam',
        medqa='MedQA — United States medical licensing exam',
        passage='Passage', question='Question', options='Options', answer='Correct answer',
        english='English', korean='Korean', s1='Sentence 1', s2='Sentence 2',
        label='Gold label', equivalent='equivalent', not_equivalent='not equivalent',
        note='Items are shown exactly as distributed upstream, including original spelling. '
             'None of these four is among the 100 scored questions for its task.'),
    'ko': dict(
        heading='실제 문항은 어떻게 생겼는가',
        intro='출처별로 실제 문항 하나씩이며, 이 연구에서 채점하지 **않은** 문항 중에서 무작위로 골랐습니다. '
              '형식을 보면 수치의 의미를 이해하는 데 큰 도움이 됩니다.',
        belebele='Belebele — 독해, 두 언어의 동일 문항',
        pawsx='PAWS-X — 이 두 문장은 같은 뜻입니까?',
        kormed='KorMedMCQA — 한국 의사 국가시험',
        medqa='MedQA — 미국 의사 면허시험',
        passage='지문', question='문항', options='선택지', answer='정답',
        english='영어', korean='한국어', s1='문장 1', s2='문장 2',
        label='정답 레이블', equivalent='동등함', not_equivalent='동등하지 않음',
        note='문항은 원본 배포 형태 그대로이며 원문 표기를 유지합니다. 네 문항 모두 해당 과제의 '
             '채점된 100문항에 포함되지 않습니다.'),
}


def scored_ids():
    index = read(ROOT / 'results' / 'evaluation-index.json')
    out = {}
    for entry in index:
        task = entry['task']
        source_id = entry['source'].get('source_id')
        if source_id is None:
            continue
        key = tuple(source_id) if isinstance(source_id, list) else source_id
        out.setdefault(task, set()).add(key)
    return out


def pick(candidates, task, rng):
    """Deterministic choice over a sorted candidate list."""
    if not candidates:
        raise ValueError(f'No unscored candidate available for {task}')
    return rng.choice(candidates)


def select():
    lock = read(ROOT / 'results' / 'source-lock.json')
    used = scored_ids()
    rng = random.Random(SEED)
    chosen, provenance = {}, {}

    # Belebele: join the two language exports the same way prepare.py does.
    en = {(r['link'], r['question_number']): r for r in rows(lock['belebele'], 'eng_Latn.jsonl')}
    ko = {(r['link'], r['question_number']): r for r in rows(lock['belebele'], 'kor_Hang.jsonl')}
    shared = sorted(set(en) & set(ko))
    candidates = [k for k in shared if (k[0], str(k[1])) not in used.get('belebele', set())]
    key = pick(candidates, 'belebele', rng)
    a, b = en[key], ko[key]
    chosen['belebele'] = dict(
        id=list(key),
        en=dict(passage=a['flores_passage'], question=a['question'],
                options={str(i): a[f'mc_answer{i}'] for i in range(1, 5)}),
        ko=dict(passage=b['flores_passage'], question=b['question'],
                options={str(i): b[f'mc_answer{i}'] for i in range(1, 5)}),
        gold=str(a['correct_answer_num']))
    provenance['belebele'] = lock['belebele']['revision']

    # PAWS-X
    pen = {str(r['id']): r for r in rows(lock['pawsx'], 'en/test-00000-of-00001.parquet')}
    pko = {str(r['id']): r for r in rows(lock['pawsx'], 'ko/test-00000-of-00001.parquet')}
    shared = sorted(set(pen) & set(pko))
    candidates = [k for k in shared
                  if k not in used.get('pawsx', set())
                  and int(pen[k]['label']) == int(pko[k]['label'])
                  and all(isinstance(pen[k][f], str) and pen[k][f].strip() for f in ('sentence1', 'sentence2'))
                  and all(isinstance(pko[k][f], str) and pko[k][f].strip() for f in ('sentence1', 'sentence2'))]
    key = pick(candidates, 'pawsx', rng)
    chosen['pawsx'] = dict(
        id=key,
        en=dict(sentence1=pen[key]['sentence1'], sentence2=pen[key]['sentence2']),
        ko=dict(sentence1=pko[key]['sentence1'], sentence2=pko[key]['sentence2']),
        gold=str(int(pen[key]['label'])))
    provenance['pawsx'] = lock['pawsx']['revision']

    # KorMedMCQA, applying the same media screen used for scoring.
    media = re.compile(r"그림|사진|도표|그래프|아래\s*표|다음\s*표|표\s*\d|영상.*(?:보여|보인|같다)|"
                       r"(?:검사|결과|소견|심전도).*(?:다음과 같다|아래와 같다)")
    records = rows(lock['kormed'], 'doctor/test-00000-of-00001-a16785256f5f42b8.parquet')
    candidates = []
    for r in sorted(records, key=lambda r: (r['year'], r['period'], r['q_number'])):
        identifier = f"{r['year']}-{r['period']}-{r['q_number']}"
        if identifier in used.get('kormed', set()):
            continue
        if not all(isinstance(r.get(k), str) and r[k].strip() for k in ['question', 'A', 'B', 'C', 'D', 'E']):
            continue
        if int(r['answer']) not in range(1, 6) or media.search(r['question']):
            continue
        candidates.append((identifier, r))
    identifier, r = pick(candidates, 'kormed', rng)
    chosen['kormed'] = dict(
        id=identifier,
        ko=dict(question=r['question'],
                options={str(i): r[letter] for i, letter in enumerate('ABCDE', 1)}),
        gold=str(int(r['answer'])))
    provenance['kormed'] = lock['kormed']['revision']

    # MedQA
    medqa_source = read(ROOT / 'results' / 'medqa-english-v3' / 'source-manifest-index.json')
    entry = medqa_source['sources']['medqa']
    path = ROOT / 'data' / 'medqa-english-v3' / entry['filename']
    records = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line]
    # case_id is the zero-padded row index of the pinned source file, set in
    # medqa_prepare.py:95. Excluded rows recorded there are skipped too, because a
    # row rejected for a defect is a bad worked example regardless of scoring.
    manifest = read(ROOT / 'results' / 'medqa-english-v3' / 'request-manifest-index.json')
    scored = {r['case_id'] for r in manifest['requests']}
    if not scored:
        raise ValueError('MedQA scored set is empty; refusing to risk showing a scored item')
    candidates = [(i, r) for i, r in enumerate(records)
                  if f'medqa-us-test-{i:04d}' not in scored
                  and isinstance(r.get('question'), str) and r['question'].strip()
                  and isinstance(r.get('options'), dict) and r.get('answer_idx') in r.get('options', {})]
    i, r = pick(candidates, 'medqa', rng)
    chosen['medqa'] = dict(
        id=f'medqa-us-test-{i:04d}',
        en=dict(question=r['question'], options=dict(r['options'])),
        gold=r['answer_idx'])
    provenance['medqa'] = entry['revision']

    return chosen, provenance, lock, entry


def build_lock():
    chosen, provenance, lock, medqa_entry = select()
    files = {name: {e['local']: e['sha256'] for e in source['files']}
             for name, source in lock.items()}
    files['medqa'] = {medqa_entry['filename']: medqa_entry['sha256']}
    value = dict(
        seed=SEED,
        note='Items selected from outside the scored set so that publishing them cannot '
             'contaminate the reported questions or any rerun of them.',
        revisions=provenance, source_files=files,
        selected={task: item['id'] for task, item in chosen.items()})
    value['sha256'] = digest(value)
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    LOCK.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return chosen, value


def options_table(t, options, gold):
    lines = [f"| | {t['options']} |", '|---|---|']
    for key, value in options.items():
        mark = ' ✅' if key == gold else ''
        lines.append(f'| **{key}** | {value}{mark} |')
    return lines


def render(chosen, lang, detail=True):
    """detail=False produces the compact README form inside <details> blocks."""
    t = TEXT[lang]
    out = [f"## {t['heading']}", '', t['intro'], '']

    def section(title, body, task):
        credit = ATTRIBUTION[task][0 if lang == 'en' else 1]
        if detail:
            return [f'### {title}', '', *body, '', f'<sub>{credit}</sub>', '']
        return ['<details>', f'<summary><b>{title}</b></summary>', '', *body, '',
                f'<sub>{credit}</sub>', '</details>', '']

    b = chosen['belebele']
    body = [f"**{t['english']}** · {t['passage']}", '', f"> {b['en']['passage']}", '',
            f"{t['question']}: {b['en']['question']}", '',
            *options_table(t, b['en']['options'], b['gold']), '',
            f"**{t['korean']}** · {t['passage']}", '', f"> {b['ko']['passage']}", '',
            f"{t['question']}: {b['ko']['question']}", '',
            *options_table(t, b['ko']['options'], b['gold'])]
    out += section(t['belebele'], body, 'belebele')

    p = chosen['pawsx']
    verdict = t['equivalent'] if p['gold'] == '1' else t['not_equivalent']
    body = [f"| | {t['english']} | {t['korean']} |", '|---|---|---|',
            f"| **{t['s1']}** | {p['en']['sentence1']} | {p['ko']['sentence1']} |",
            f"| **{t['s2']}** | {p['en']['sentence2']} | {p['ko']['sentence2']} |", '',
            f"{t['label']}: **{verdict}**"]
    out += section(t['pawsx'], body, 'pawsx')

    k = chosen['kormed']
    body = [f"> {k['ko']['question']}", '', *options_table(t, k['ko']['options'], k['gold'])]
    out += section(t['kormed'], body, 'kormed')

    m = chosen['medqa']
    body = [f"> {m['en']['question']}", '', *options_table(t, m['en']['options'], m['gold'])]
    out += section(t['medqa'], body, 'medqa')

    out += [t['note']]
    return '\n'.join(out)


def replace(text, marker, block):
    start, end = f'<!-- examples-{marker}start -->', f'<!-- examples-{marker}end -->'
    if start not in text or end not in text:
        raise ValueError(f'Missing {start} / {end} markers')
    before, rest = text.split(start, 1)
    _, after = rest.split(end, 1)
    return before + start + '\n' + block + '\n' + end + after


def build():
    chosen, lock = build_lock()
    for path, detail in ((ROOT / 'README.md', False), (ROOT / 'docs' / 'index.md', True)):
        text = path.read_text(encoding='utf-8')
        text = replace(text, '', render(chosen, 'en', detail))
        text = replace(text, 'ko-', render(chosen, 'ko', detail))
        path.write_text(text, encoding='utf-8', newline='\n')
    print(f"Wrote worked examples for {', '.join(sorted(chosen))}; lock {lock['sha256'][:16]}")


if __name__ == '__main__':
    build()
