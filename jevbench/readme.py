"""Regenerate the README results tables from the frozen summaries.

Both language tables are emitted from the same numbers, so the English and
Korean halves cannot silently drift apart. Prose is hand-written and is never
touched by this module; only the marked table blocks are replaced.

Replaces the three separate README injections that each experiment publisher
used to perform, which appended sections in reverse-chronological order.
"""
import json

from .common import ROOT

START = '<!-- results-table-{}start -->'
END = '<!-- results-table-{}end -->'

ROWS = [
    ('belebele', 'English', 'Belebele reading', 'Belebele 독해', '영어'),
    ('belebele', 'Korean', 'Belebele reading', 'Belebele 독해', '한국어'),
    ('pawsx', 'English', 'PAWS-X paraphrase', 'PAWS-X 의미 동등성', '영어'),
    ('pawsx', 'Korean', 'PAWS-X paraphrase', 'PAWS-X 의미 동등성', '한국어'),
    ('medqa', 'English', 'MedQA exam', 'MedQA 시험', '영어'),
    ('kormed', 'Korean', 'KorMedMCQA exam', 'KorMedMCQA 시험', '한국어'),
]

HEAD = {
    'en': ('| Task | Language | Jev | Luna | Luna − Jev (95% CI) |',
           '|---|---|---:|---:|---:|'),
    'ko': ('| 과제 | 언어 | Jev | Luna | Luna − Jev (95% 구간) |',
           '|---|---|---:|---:|---:|'),
}


def minus(value):
    """Use a typographic minus so the two language tables align identically."""
    return f'{value:+.0f}'.replace('-', '−')


def cells():
    data = json.loads((ROOT / 'results/aggregate/summary.json').read_text(encoding='utf-8'))
    return {(c['task'], c['language']): c for c in data['cells']}


def table(lang):
    data = cells()
    head = HEAD[lang]
    lines = [head[0], head[1]]
    for task, language, en_label, ko_label, ko_language in ROWS:
        c = data[(task, language)]
        jev, luna = c['providers']['jev'], c['providers']['luna']
        d = c['luna_minus_jev']
        point = minus(100 * d['difference'])
        lo, hi = (minus(100 * v) for v in d['ci95'])
        cell = f'{point} ({lo}, {hi})'
        # The one interval that excludes zero carries emphasis in both languages.
        if d['ci95'][0] > 0 or d['ci95'][1] < 0:
            cell = f'**{cell}**'
        label = en_label if lang == 'en' else ko_label
        shown = language if lang == 'en' else ko_language
        lines.append(f"| {label} | {shown} | {jev['correct']}/{jev['n']} | "
                     f"{luna['correct']}/{luna['n']} | {cell} |")
    return '\n'.join(lines)


def replace(text, marker, block):
    start, end = START.format(marker), END.format(marker)
    if start not in text or end not in text:
        raise ValueError(f'README is missing the {start} / {end} markers')
    before, rest = text.split(start, 1)
    _, after = rest.split(end, 1)
    return before + start + '\n' + block + '\n' + end + after


def build():
    path = ROOT / 'README.md'
    text = path.read_text(encoding='utf-8')
    text = replace(text, '', table('en'))
    text = replace(text, 'ko-', table('ko'))
    path.write_text(text, encoding='utf-8', newline='\n')
    print('Regenerated both README results tables from results/aggregate/summary.json')


if __name__ == '__main__':
    build()
