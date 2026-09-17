"""Speed and cost comparison, generated from the frozen per-task results.

Replaces the orphaned three-panel luna-comparison figure that the documentation
merge left behind. No API calls: every number here is already recorded.

The two providers were measured at different times through different transports
and were not interleaved, so provider load and date are confounders. These are
observed service measurements on the run dates, not architecture-only speed.
"""
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from .common import ROOT

OUT = ROOT / 'docs' / 'figures'
JEV, LUNA = '#0072B2', '#D55E00'
KOREAN_FONTS = ['Malgun Gothic', 'NanumGothic', 'Noto Sans KR', 'DejaVu Sans']

# (task, stage, label_en, label_ko, concurrent)
TASKS = [
    ('belebele', 1, 'Belebele', 'Belebele', False),
    ('pawsx', 1, 'PAWS-X', 'PAWS-X', False),
    ('kormed', 2, 'KorMedMCQA', 'KorMedMCQA', False),
    ('medqa', None, 'MedQA', 'MedQA', True),
]

TEXT = {
    'en': dict(
        heading='Speed and cost',
        intro='Jev answers faster and costs less on this workload, by a wide enough margin that '
              'it is worth weighing against the accuracy numbers above.',
        header='| Task | Jev median | Luna median | Jev per 1,000 | Luna per 1,000 |',
        title='Observed speed and cost on the same questions',
        a='A   Median response time', b='B   Estimated cost per 1,000 calls',
        xa='Milliseconds', xb='US dollars',
        concurrent='measured at four concurrent requests per provider, so not comparable with the rows above',
        note='Korean conditions except MedQA, which is English only. Cost per 1,000 calls scales the '
             'observed token charges; it is not a separate 1,000-call experiment, and it is an estimate '
             'from published prices rather than an invoice.',
        caveat='The two providers ran at different times through different transports and were not '
               'interleaved, so provider load and date are confounders. These describe the observed '
               'services on the run dates, not architecture-only speed.'),
    'ko': dict(
        heading='속도와 비용',
        intro='이 작업에서 Jev는 더 빠르고 더 저렴하며, 그 차이가 충분히 커서 위의 정확도 수치와 '
              '함께 저울질할 가치가 있습니다.',
        header='| 과제 | Jev 중앙값 | Luna 중앙값 | Jev 1,000회 | Luna 1,000회 |',
        title='동일 문항에서 관측된 속도와 비용',
        a='A   응답 시간 중앙값', b='B   1,000회 호출당 추정 비용',
        xa='밀리초', xb='미국 달러',
        concurrent='공급자당 4개의 동시 요청으로 측정하여 위 항목들과 비교할 수 없음',
        note='MedQA를 제외하면 모두 한국어 조건이며 MedQA는 영어만 있습니다. 1,000회당 비용은 관측된 '
             '토큰 요금을 비례 환산한 값으로, 별도의 1,000회 실험이 아니며 청구서가 아니라 공개 가격에 '
             '기반한 추정치입니다.',
        caveat='두 공급자는 서로 다른 시점에 다른 전송 경로로 실행되었고 교차 배치되지 않았으므로 '
               '공급자 부하와 날짜가 교란 요인입니다. 이 값들은 실행일에 관측된 서비스를 기술할 뿐이며 '
               '아키텍처만의 속도가 아닙니다.'),
}


def cells():
    out = {}
    for task, stage, _, _, concurrent in TASKS:
        if task == 'medqa':
            providers = json.loads(
                (ROOT / 'results/medqa-english-v3/summary.json').read_text(encoding='utf-8'))['providers']
            out[task] = {
                role: dict(median=providers[role]['median_ms'], p95=providers[role]['p95_ms'],
                           cost=providers[role]['estimated_cost_usd'], n=providers[role]['successful'])
                for role in ('jev', 'luna')}
            continue
        jev = json.loads((ROOT / f'results/stage-{stage}.json').read_text(encoding='utf-8'))
        luna = json.loads((ROOT / f'results/luna-none-v1/stage-{stage}.json').read_text(encoding='utf-8'))
        key = f'{task}/ko_ko'
        out[task] = {}
        for role, data in (('jev', jev), ('luna', luna)):
            g = data['groups'][key]
            out[task][role] = dict(median=g['median_latency_ms'], p95=g['p95_latency_ms'],
                                   cost=g['cost_usd'], n=g['n'])
    return out


def per_thousand(cell):
    return cell['cost'] / cell['n'] * 1000


def table(lang):
    t, data = TEXT[lang], cells()
    lines = [t['header'], '|---|---:|---:|---:|---:|']
    for task, _, label_en, label_ko, concurrent in TASKS:
        c = data[task]
        label = (label_en if lang == 'en' else label_ko) + (' †' if concurrent else '')
        lines.append(
            f"| {label} | {c['jev']['median']:.0f} ms | {c['luna']['median']:.0f} ms | "
            f"${per_thousand(c['jev']):.3f} | ${per_thousand(c['luna']):.3f} |")
    lines += ['', f"† {t['concurrent']}", '', t['note'], '', t['caveat']]
    return '\n'.join(lines)


def build_figure(lang='en'):
    t, data = TEXT[lang], cells()
    family = KOREAN_FONTS if lang == 'ko' else ['DejaVu Sans']
    plt.rcParams.update({'font.family': family, 'font.size': 10,
        'axes.spines.top': False, 'axes.spines.right': False, 'axes.linewidth': .7,
        'svg.fonttype': 'none', 'pdf.fonttype': 42, 'savefig.facecolor': 'white'})
    labels = [(label_en if lang == 'en' else label_ko) + (' †' if concurrent else '')
              for _, _, label_en, label_ko, concurrent in TASKS]
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 3.9), layout='constrained')

    for ax, key, title, xlabel, fmt in (
            (axes[0], 'median', t['a'], t['xa'], lambda v: f'{v:.0f}'),
            (axes[1], 'cost', t['b'], t['xb'], lambda v: f'${v:.3f}')):
        for i, (task, _, _, _, _) in enumerate(TASKS):
            for j, (role, color) in enumerate((('jev', JEV), ('luna', LUNA))):
                c = data[task][role]
                value = c['median'] if key == 'median' else per_thousand(c)
                y = i + (.2 if j else -.2)
                ax.barh(y, value, height=.34, color=color, alpha=.92, zorder=2,
                        label=role.capitalize() if i == 0 else None)
                ax.text(value * 1.02, y, fmt(value), va='center', ha='left',
                        fontsize=8.5, color='#12202E')
        ax.set(yticks=range(len(TASKS)), yticklabels=labels, xlabel=xlabel)
        ax.set_title(title, fontsize=10.5, loc='left', pad=10)
        ax.invert_yaxis()
        ax.grid(axis='x', alpha=.18)
        ax.set_axisbelow(True)
        ax.margins(x=.16)
    axes[0].legend(loc='lower right', frameon=False, fontsize=9)

    fig.suptitle(t['title'], fontsize=12.5, x=.008, ha='left')
    fig.text(0, -.06, f"† {t['concurrent']}\n{t['caveat']}", fontsize=8.5, color='#54626F')
    return fig


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    for ext in ('png', 'svg', 'pdf'):
        fig.savefig(OUT / f'{name}.{ext}', dpi=300, bbox_inches='tight')
    plt.close(fig)


def replace(text, marker, block):
    start, end = f'<!-- efficiency-{marker}start -->', f'<!-- efficiency-{marker}end -->'
    if start not in text or end not in text:
        raise ValueError(f'Missing {start} / {end} markers')
    before, rest = text.split(start, 1)
    _, after = rest.split(end, 1)
    return before + start + '\n' + block + '\n' + end + after


def section(lang, figure):
    t = TEXT[lang]
    return '\n'.join([f"## {t['heading']}", '', t['intro'], '',
                      f"![{t['title']}]({figure})", '', table(lang)])


def build():
    for lang in ('en', 'ko'):
        save(build_figure(lang), 'speed-cost' + ('' if lang == 'en' else '.ko'))
    for path, prefix in ((ROOT / 'README.md', 'docs/figures/'),
                         (ROOT / 'docs' / 'index.md', 'figures/')):
        text = path.read_text(encoding='utf-8')
        text = replace(text, '', section('en', prefix + 'speed-cost.png'))
        text = replace(text, 'ko-', section('ko', prefix + 'speed-cost.ko.png'))
        path.write_text(text, encoding='utf-8', newline='\n')
    print('Wrote speed-cost figures and both efficiency sections')


if __name__ == '__main__':
    build()
