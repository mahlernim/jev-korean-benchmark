"""Bilingual overview figure: Korean accuracy, Jev against Luna, English as a reference caret.

Bar length encodes Korean accuracy because that is the question the report answers.
The caret marks the same model's English score on the same items, so the language
gap reads as a short distance rather than competing for attention as a second bar.
Medical rows carry no caret: KorMedMCQA has no English arm and MedQA has no Korean
one, so they are fenced into a separate zone instead of implying a comparison.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs' / 'figures'
JEV, LUNA = '#0072B2', '#D55E00'
KOREAN_FONTS = ['Malgun Gothic', 'NanumGothic', 'Noto Sans KR', 'DejaVu Sans']

TEXT = {
    'en': dict(
        title='The same questions in Korean and in English',
        xlabel='Accuracy on 100 questions (%)',
        matched='Matched bilingual tasks — same questions in both languages',
        medical='Medical exams — different tests, not a language comparison',
        korean_key='Korean', english_key='English (same items)',
        jev='Jev', luna='Luna',
        labels={'belebele': 'Belebele\nreading', 'pawsx': 'PAWS-X\nparaphrase',
                'kormed': 'KorMedMCQA\n(Korean)', 'medqa': 'MedQA\n(English)'},
        note='All bars are 100 questions with Wilson 95% intervals. Medical rows are two different exams, so the pair below the line is not a language comparison.'),
    'ko': dict(
        title='동일한 문항을 한국어와 영어로 평가한 결과',
        xlabel='100문항 기준 정확도 (%)',
        matched='대응 이중언어 과제 — 두 언어에서 동일한 문항',
        medical='의학 시험 — 서로 다른 시험이며 언어 비교가 아님',
        korean_key='한국어', english_key='영어 (동일 문항)',
        jev='Jev', luna='Luna',
        labels={'belebele': 'Belebele\n독해', 'pawsx': 'PAWS-X\n의미 동등성',
                'kormed': 'KorMedMCQA\n(한국어)', 'medqa': 'MedQA\n(영어)'},
        note='모든 막대는 100문항 기준이며 Wilson 95% 구간을 표시합니다. 의학 항목은 서로 다른 시험이므로 선 아래 두 항목은 언어 비교가 아닙니다.'),
}

ROWS = [('belebele', 'matched'), ('pawsx', 'matched'), ('kormed', 'medical'), ('medqa', 'medical')]


def cells():
    data = json.loads((ROOT / 'results/aggregate/summary.json').read_text(encoding='utf-8'))
    out = {}
    for c in data['cells']:
        out[(c['task'], c['language'])] = {
            k: dict(correct=v['correct'], n=v['n'], accuracy=v['accuracy'], ci95=v['ci95'])
            for k, v in c['providers'].items()}
    return out


def build(lang='en'):
    t = TEXT[lang]
    data = cells()
    family = KOREAN_FONTS if lang == 'ko' else ['DejaVu Sans']
    plt.rcParams.update({'font.family': family, 'font.size': 10,
        'axes.spines.top': False, 'axes.spines.right': False, 'axes.linewidth': .7,
        'svg.fonttype': 'none', 'pdf.fonttype': 42, 'savefig.facecolor': 'white'})
    ypos = {'belebele': 0.0, 'pawsx': 1.15, 'kormed': 2.75, 'medqa': 3.75}
    fence = 2.05
    fig, ax = plt.subplots(figsize=(9.4, 6.2), layout='constrained')
    ax.axhspan(fence, 4.25, color='#F2F4F7', zorder=0)

    def bar(y, m, color, english):
        p_ = 100 * m['accuracy']
        lo, hi = np.array(m['ci95']) * 100
        ax.barh(y, p_, height=.19, zorder=2,
                color='white' if english else color,
                edgecolor=color, linewidth=1.4,
                hatch='////' if english else None)
        if english:
            ax.bar(0, 0, color=color, alpha=.18)
        ax.errorbar(p_, y, xerr=[[p_ - lo], [hi - p_]], fmt='none', ecolor='#31404F',
                    elinewidth=1.0, capsize=2.5, zorder=3)
        ax.text(hi + 1.6, y, f"{m['correct']}", va='center', ha='left', fontsize=9,
                color='#12202E', fontweight='bold', zorder=4)

    for task, zone in ROWS:
        i = ypos[task]
        offsets = {'jev': -.255, 'luna': .135}
        for role, color in (('jev', JEV), ('luna', LUNA)):
            o = offsets[role]
            if zone == 'matched':
                bar(i + o, data[(task, 'English')][role], color, True)
                bar(i + o + .21, data[(task, 'Korean')][role], color, False)
                ax.text(-1.5, i + o + .105, t[role], va='center', ha='right',
                        fontsize=8.5, color=color, fontweight='bold')
            else:
                primary = 'English' if task == 'medqa' else 'Korean'
                bar(i + o + .105, data[(task, primary)][role], color, primary == 'English')
                ax.text(-1.5, i + o + .105, t[role], va='center', ha='right',
                        fontsize=8.5, color=color, fontweight='bold')

    ax.axhline(fence, color='#9AA7B4', linewidth=.9, linestyle=(0, (4, 3)), zorder=6)
    ax.text(1, -.72, t['matched'], ha='left', va='center', fontsize=9, color='#435261')
    ax.text(1, 2.28, t['medical'], ha='left', va='center', fontsize=9, color='#435261')
    ax.set(yticks=list(ypos.values()), yticklabels=[t['labels'][k] for k in ypos],
           xlim=(0, 100), xticks=range(0, 101, 20), ylim=(4.3, -.95), xlabel=t['xlabel'])
    ax.set_title(t['title'], fontsize=12.5, loc='left', pad=30)
    ax.grid(axis='x', alpha=.18, zorder=1)
    ax.set_axisbelow(True)
    ax.tick_params(axis='y', length=0, pad=42)

    handles = [Patch(facecolor='#6E7B88', edgecolor='#6E7B88', label=t['korean_key']),
               Patch(facecolor='white', edgecolor='#6E7B88', hatch='////', label=t['english_key'])]
    ax.legend(handles=handles, loc='lower left', bbox_to_anchor=(0, 1.005),
              frameon=False, fontsize=9.5, ncol=2)
    fig.text(0, -.015, t['note'], fontsize=8.5, color='#54626F')
    return fig


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    for ext in ('png', 'svg', 'pdf'):
        fig.savefig(OUT / f'{name}.{ext}', dpi=300, bbox_inches='tight')
    plt.close(fig)


def main():
    for lang in ('en', 'ko'):
        suffix = '' if lang == 'en' else '.ko'
        save(build_dumbbell(lang), 'korean-check' + suffix)
        save(build_forest(lang), 'differences' + suffix)
        save(build_order(lang), 'order-sensitivity' + suffix)
    print('Wrote korean-check and differences, both languages')




FOREST = {
    'en': dict(title='Where the differences actually lie',
               a='A   Cost of switching to Korean (same items, same model)',
               b='B   Luna minus Jev, by task',
               xa='Korean minus English (percentage points)',
               xb='Luna minus Jev (percentage points)',
               favours_ko='← Korean worse        Korean better →',
               favours_luna='← Jev better          Luna better →',
               note='Paired bootstrap 95% intervals, 4,000 resamples. Intervals crossing zero do not establish equivalence.',
               tasks={'belebele': 'Belebele', 'pawsx': 'PAWS-X',
                      'kormed': 'KorMedMCQA (KO)', 'medqa': 'MedQA (EN)'}),
    'ko': dict(title='차이가 실제로 나타나는 지점',
               a='A   한국어로 전환할 때의 비용 (동일 문항, 동일 모델)',
               b='B   Luna 빼기 Jev, 과제별',
               xa='한국어 빼기 영어 (백분율 포인트)',
               xb='Luna 빼기 Jev (백분율 포인트)',
               favours_ko='← 한국어가 낮음        한국어가 높음 →',
               favours_luna='← Jev이 높음          Luna가 높음 →',
               note='대응 부트스트랩 95% 구간, 4,000회 재표본. 구간이 0을 지나도 동등성이 입증되는 것은 아닙니다.',
               tasks={'belebele': 'Belebele', 'pawsx': 'PAWS-X',
                      'kormed': 'KorMedMCQA (한국어)', 'medqa': 'MedQA (영어)'}),
}


def build_forest(lang='en'):
    t = FOREST[lang]
    data = json.loads((ROOT / 'results/aggregate/summary.json').read_text(encoding='utf-8'))
    family = KOREAN_FONTS if lang == 'ko' else ['DejaVu Sans']
    plt.rcParams.update({'font.family': family, 'font.size': 10,
        'axes.spines.top': False, 'axes.spines.right': False, 'axes.linewidth': .7,
        'svg.fonttype': 'none', 'pdf.fonttype': 42, 'savefig.facecolor': 'white'})
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.4), layout='constrained')

    rows = []
    for entry in data['matched_language_differences']:
        d = entry['korean_minus_english']
        rows.append((t['tasks'][entry['task']], entry['provider'], d['difference']*100,
                     np.array(d['ci95'])*100))
    ax = axes[0]
    for i, (label, provider, d, ci) in enumerate(rows):
        color = JEV if provider == 'jev' else LUNA
        ax.errorbar(d, i, xerr=[[d-ci[0]], [ci[1]-d]], fmt='o', color=color,
                    capsize=4, markersize=6.5, elinewidth=1.3)
        ax.text(ci[1]+.9, i, f'{d:+.0f}', ha='left', va='center', fontsize=9.5,
                color=color, fontweight='bold')
    ax.set(yticks=range(len(rows)),
           yticklabels=[f'{l}\n{p.capitalize()}' for l, p, _, _ in rows],
           xlabel=t['xa'], xlim=(-24, 14))
    ax.set_title(t['a'], fontsize=10.5, loc='left', pad=10)
    ax.axvline(0, color='#54626F', linestyle='--', linewidth=.9)
    ax.invert_yaxis(); ax.grid(axis='x', alpha=.18)
    ax.text(.5, -.20, t['favours_ko'], ha='center', fontsize=8.5, color='#54626F',
            transform=ax.transAxes)

    ax = axes[1]
    cells_ = [c for c in data['cells']]
    seen, brows = set(), []
    for c in cells_:
        key = (c['task'], c['language'])
        if key in seen:
            continue
        seen.add(key)
        if c['task'] in ('belebele', 'pawsx') and c['language'] != 'Korean':
            continue
        d = c['luna_minus_jev']
        brows.append((t['tasks'][c['task']], d['difference']*100, np.array(d['ci95'])*100))
    for i, (label, d, ci) in enumerate(brows):
        crosses = ci[0] <= 0 <= ci[1]
        ax.errorbar(d, i, xerr=[[d-ci[0]], [ci[1]-d]], fmt='o',
                    color='#54626F' if crosses else '#8A3FFC',
                    capsize=4, markersize=6.5, elinewidth=1.3)
        ax.text(ci[1]+.9, i, f'{d:+.0f}', ha='left', va='center', fontsize=9.5,
                color='#54626F' if crosses else '#8A3FFC', fontweight='bold')
    ax.set(yticks=range(len(brows)), yticklabels=[r[0] for r in brows],
           xlabel=t['xb'], xlim=(-17, 23))
    ax.set_title(t['b'], fontsize=10.5, loc='left', pad=10)
    ax.axvline(0, color='#54626F', linestyle='--', linewidth=.9)
    ax.invert_yaxis(); ax.grid(axis='x', alpha=.18)
    ax.text(.5, -.20, t['favours_luna'], ha='center', fontsize=8.5, color='#54626F',
            transform=ax.transAxes)

    fig.suptitle(t['title'], fontsize=12.5, x=.008, ha='left')
    fig.text(0, -.04, t['note'], fontsize=8.5, color='#54626F')
    return fig




DUMBBELL = {
    'en': dict(axis_note='Axis starts at 60 to show the gaps; dots are point estimates, '
                         'thin bars are Wilson 95% intervals.',
               english='English', korean='Korean',
               gap='gap'),
    'ko': dict(axis_note='차이를 보이기 위해 축은 60에서 시작합니다. 점은 점추정치이고 '
                         '가는 선은 Wilson 95% 구간입니다.',
               english='영어', korean='한국어',
               gap='차이'),
}


def build_dumbbell(lang='en'):
    t, d = TEXT[lang], DUMBBELL[lang]
    data = cells()
    family = KOREAN_FONTS if lang == 'ko' else ['DejaVu Sans']
    plt.rcParams.update({'font.family': family, 'font.size': 10,
        'axes.spines.top': False, 'axes.spines.right': False, 'axes.spines.left': False,
        'axes.linewidth': .7, 'svg.fonttype': 'none', 'pdf.fonttype': 42,
        'savefig.facecolor': 'white'})
    order = [('belebele', 'jev'), ('belebele', 'luna'), ('pawsx', 'jev'), ('pawsx', 'luna'),
             ('kormed', 'jev'), ('kormed', 'luna'), ('medqa', 'jev'), ('medqa', 'luna')]
    ypos = {k: i + (1.0 if i >= 4 else 0) for i, k in enumerate(order)}
    fence = 3.5 + 1.0 / 2
    lo_x = 60
    fig, ax = plt.subplots(figsize=(9.4, 5.6), layout='constrained')
    ax.axhspan(fence, 9.1, color='#F2F4F7', zorder=0)

    for (task, role) in order:
        y = ypos[(task, role)]
        color = JEV if role == 'jev' else LUNA
        matched = task in ('belebele', 'pawsx')
        primary = 'English' if task == 'medqa' else 'Korean'
        ko = data[(task, primary)][role]
        kx = 100 * ko['accuracy']
        klo, khi = np.array(ko['ci95']) * 100
        if matched:
            en = data[(task, 'English')][role]
            ex = 100 * en['accuracy']
            ax.plot([ex, kx], [y, y], color=color, linewidth=5.0, alpha=.55,
                    solid_capstyle='round', zorder=4)
            ax.plot(ex, y, 'o', markerfacecolor='white', markeredgecolor=color,
                    markeredgewidth=1.8, markersize=9, zorder=6)
            ax.text(ex, y - .34, f"{en['correct']}", ha='center', va='bottom',
                    fontsize=8.5, color=color)
            ax.text(lo_x - 1.2, y, f'{kx - ex:+.0f}', ha='right', va='center',
                    fontsize=9.5, color=color, fontweight='bold')
        ax.hlines(y, klo, khi, color=color, linewidth=1.0, alpha=.22, zorder=1)
        ax.plot(kx, y, 'o', color=color, markersize=9, zorder=6)
        ax.text(kx, y + .20, f"{ko['correct']}", ha='center', va='top',
                fontsize=9, color='#12202E', fontweight='bold')

    ax.axhline(fence, color='#9AA7B4', linewidth=.9, linestyle=(0, (4, 3)), zorder=6)
    labels = []
    for (task, role) in order:
        labels.append(f"{t['labels'][task].replace(chr(10), ' ')} · {t[role]}")
    ax.set(yticks=[ypos[k] for k in order], yticklabels=labels,
           xlim=(lo_x - 6, 101), xticks=range(lo_x, 101, 10),
           ylim=(9.15, -1.15), xlabel=t['xlabel'])
    ax.set_title(t['title'], fontsize=12.5, loc='left', pad=30)
    ax.grid(axis='x', alpha=.18, zorder=1)
    ax.set_axisbelow(True)
    ax.tick_params(axis='y', length=0)
    ax.text(lo_x - 1.2, -.85, d['gap'], ha='right', va='center', fontsize=8.5,
            color='#435261', fontweight='bold')
    ax.text(lo_x, -.85, t['matched'], ha='left', va='center', fontsize=9, color='#435261')
    ax.text(lo_x, fence + .42, t['medical'], ha='left', va='center', fontsize=9, color='#435261')

    handles = [Line2D([], [], marker='o', linestyle='none', markerfacecolor='white',
                      markeredgecolor='#6E7B88', markeredgewidth=1.8, markersize=9,
                      label=d['english']),
               Line2D([], [], marker='o', linestyle='none', color='#6E7B88',
                      markersize=9, label=d['korean'])]
    ax.legend(handles=handles, loc='lower left', bbox_to_anchor=(0, 1.005),
              frameon=False, fontsize=9.5, ncol=2)
    fig.text(0, -.015, d['axis_note'] + '  ' + t['note'].split('. ', 1)[-1],
             fontsize=8.5, color='#54626F')
    return fig




ORDER = {
    'en': dict(title='What happens when the two sentences are swapped',
               a='A   How often the answer changes',
               b='B   What those changes do to accuracy',
               xa='Answers that changed (%)',
               xb='Questions',
               floor_key='○ = the identical question asked a second time',
               w2r='wrong → right', r2w='right → wrong',
               note='PAWS-X, 100 questions per cell. Swapping sentence1 and sentence2 leaves '
                    'paraphrase equivalence unchanged, so a changed answer is an inconsistency.',
               note2='The hollow marker is Jev answering the identical question a second time, '
                     'which bounds ordinary service variation. Luna returns no probability, so it has no such control.',
               rows={'jev/en_en': 'Jev · English', 'jev/ko_ko': 'Jev · Korean',
                     'luna/en_en': 'Luna · English', 'luna/ko_ko': 'Luna · Korean'}),
    'ko': dict(title='두 문장의 순서를 바꾸면 생기는 일',
               a='A   답이 바뀌는 빈도',
               b='B   그 변화가 정확도에 미치는 영향',
               xa='답이 바뀐 문항 (%)',
               xb='문항 수',
               floor_key='○ = 동일한 질문을 한 번 더 물었을 때',
               w2r='오답 → 정답', r2w='정답 → 오답',
               note='PAWS-X, 셀당 100문항. sentence1과 sentence2를 바꾸어도 의미 동등성은 변하지 '
                    '않으므로, 답이 바뀌면 그것은 비일관성입니다.',
               note2='속이 빈 표시는 Jev에게 동일한 질문을 한 번 더 물었을 때의 값으로, 일반적인 '
                     '서비스 변동 폭을 나타냅니다. Luna는 확률을 돌려주지 않아 해당 대조가 없습니다.',
               rows={'jev/en_en': 'Jev · 영어', 'jev/ko_ko': 'Jev · 한국어',
                     'luna/en_en': 'Luna · 영어', 'luna/ko_ko': 'Luna · 한국어'}),
}


def build_order(lang='en'):
    t = ORDER[lang]
    s = json.loads((ROOT/'runs/order-sensitivity-v1/summary.json').read_text(encoding='utf-8'))
    ctrl = json.loads((ROOT/'runs/order-repeat-v1/summary.json').read_text(encoding='utf-8'))
    family = KOREAN_FONTS if lang == 'ko' else ['DejaVu Sans']
    plt.rcParams.update({'font.family': family, 'font.size': 10,
        'axes.spines.top': False, 'axes.spines.right': False, 'axes.linewidth': .7,
        'svg.fonttype': 'none', 'pdf.fonttype': 42, 'savefig.facecolor': 'white'})
    keys = ['jev/en_en', 'jev/ko_ko', 'luna/en_en', 'luna/ko_ko']
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.5), layout='constrained')

    ax = axes[0]
    for i, k in enumerate(keys):
        c = s['cells'][k]
        color = JEV if k.startswith('jev') else LUNA
        v = 100*c['flip_rate']
        lo, hi = np.array(c['flip_ci95'])*100
        ax.barh(i, v, height=.5, color=color, alpha=.9, zorder=2)
        ax.errorbar(v, i, xerr=[[v-lo], [hi-v]], fmt='none', ecolor='#31404F',
                    elinewidth=1.1, capsize=3, zorder=3)
        ax.text(v+1.2, i, f'{v:.0f}%', va='center', ha='left', fontsize=9.5,
                fontweight='bold', color='#12202E')
        if k in ctrl['cells']:
            f = 100*ctrl['cells'][k]['flip_rate']
            ax.plot(f, i, 'o', markerfacecolor='white', markeredgecolor='#12202E',
                    markeredgewidth=1.6, markersize=8, zorder=5)
    ax.set(yticks=range(4), yticklabels=[t['rows'][k] for k in keys],
           xlim=(0, 34), xlabel=t['xa'])
    ax.set_title(t['a'], fontsize=10.5, loc='left', pad=10)
    ax.invert_yaxis(); ax.grid(axis='x', alpha=.18); ax.set_axisbelow(True)
    ax.text(.5, -.20, t['floor_key'], ha='center', fontsize=8.5, color='#12202E',
            transform=ax.transAxes)

    ax = axes[1]
    for i, k in enumerate(keys):
        c = s['cells'][k]
        ax.barh(i, c['wrong_to_right'], height=.5, color='#2E8B6F', alpha=.92, zorder=2)
        ax.barh(i, -c['right_to_wrong'], height=.5, color='#B5476B', alpha=.92, zorder=2)
        if c['wrong_to_right']:
            ax.text(c['wrong_to_right']+.35, i, str(c['wrong_to_right']), va='center',
                    fontsize=9, color='#2E8B6F', fontweight='bold')
        if c['right_to_wrong']:
            ax.text(-c['right_to_wrong']-.35, i, str(c['right_to_wrong']), va='center',
                    ha='right', fontsize=9, color='#B5476B', fontweight='bold')
    ax.axvline(0, color='#54626F', linewidth=.9)
    ax.set(yticks=range(4), yticklabels=[t['rows'][k] for k in keys],
           xlim=(-15, 15), xlabel=t['xb'])
    ax.set_title(t['b'], fontsize=10.5, loc='left', pad=10)
    ax.invert_yaxis(); ax.grid(axis='x', alpha=.18); ax.set_axisbelow(True)
    ax.text(.75, -.20, t['w2r'], ha='center', fontsize=8.5, color='#2E8B6F',
            fontweight='bold', transform=ax.transAxes)
    ax.text(.25, -.20, t['r2w'], ha='center', fontsize=8.5, color='#B5476B',
            fontweight='bold', transform=ax.transAxes)

    fig.suptitle(t['title'], fontsize=12.5, x=.008, ha='left')
    fig.text(0, -.055, t['note'] + '\n' + t['note2'], fontsize=8.5, color='#54626F')
    return fig


if __name__ == '__main__':
    main()
