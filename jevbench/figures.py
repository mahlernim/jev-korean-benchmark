"""Rebuild descriptive, publication-style figures from public frozen results."""
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def main():
    out = ROOT / 'docs' / 'figures'
    out.mkdir(exist_ok=True)
    stages = {s: json.loads((ROOT / f'results/stage-{s}.json').read_text()) for s in (1, 2)}
    rows = list(csv.DictReader((ROOT / 'results/predictions.csv').open(encoding='utf-8')))
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
        'axes.spines.top': False, 'axes.spines.right': False, 'axes.linewidth': .7,
        'svg.fonttype': 'none', 'pdf.fonttype': 42, 'savefig.facecolor': 'white'})
    tasks = [('belebele', 'Belebele'), ('pawsx', 'PAWS-X'), ('kormed', 'KorMedMCQA')]
    conditions = [('en_en', 'English / English', '#222222', 'o'),
                  ('ko_en', 'Korean / English', '#0072B2', 's'),
                  ('ko_ko', 'Korean / Korean', '#D55E00', '^')]
    def get(task, condition):
        return stages[2 if task == 'kormed' else 1]['groups'].get(task + '/' + condition)
    def save(fig, name):
        for ext in ('png', 'svg', 'pdf'):
            fig.savefig(out / f'{name}.{ext}', dpi=300, bbox_inches='tight')
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.2, 4.5), layout='constrained')
    for j, (condition, label, color, marker) in enumerate(conditions):
        for i, (task, _) in enumerate(tasks):
            m = get(task, condition)
            if m is None:
                continue
            p = 100 * m['accuracy']; lo, hi = np.array(m['accuracy_ci95']) * 100
            y = i + (j - 1) * .21
            ax.errorbar(p, y, xerr=[[p-lo], [hi-p]], fmt=marker, color=color,
                        capsize=3, markersize=6, label=label if i == 0 else None)
            ax.text(101, y, f"{m['correct']}/{m['n']}", va='center', fontsize=9)
    ax.set(yticks=range(3), yticklabels=[t[1] for t in tasks], xlim=(0, 110),
           xticks=range(0, 101, 20), xlabel='Accuracy (%)', title='A   Task-specific accuracy and 95% Wilson intervals')
    ax.invert_yaxis(); ax.grid(axis='x', alpha=.18)
    ax.legend(title='Content / instruction language', loc='lower left', frameon=False, fontsize=9)
    plt.close(fig)  # superseded by korean-check

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.3), layout='constrained')
    for ax, contrast, title in zip(axes,
            ('ko_en-en_en', 'ko_ko-ko_en'),
            ('B   Content language effect', 'C   Instruction language effect')):
        valid = [(task, label, stages[2 if task == 'kormed' else 1]['paired'].get(task+'/'+contrast)) for task,label in tasks]
        valid = [v for v in valid if v[2]]
        for i, (_, _, m) in enumerate(valid):
            d = m['difference']*100; lo, hi = np.array(m['ci95'])*100
            ax.errorbar(d, i, xerr=[[d-lo], [hi-d]], fmt='o', color='#222222', capsize=4)
            ax.text(14, i, f'{d:+.0f}', va='center', ha='right')
        ax.axvline(0, color='.6', linestyle='--', linewidth=.8)
        ax.set(yticks=range(len(valid)), yticklabels=[v[1] for v in valid],
               xlim=(-16, 16), ylim=(len(valid)-.5, -.5), title=title,
               xlabel='Korean minus English (percentage points)')
        ax.grid(axis='x', alpha=.18)
    plt.close(fig)  # superseded by differences

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), layout='constrained')
    for (task, label), color, marker in zip(tasks, ('#222222', '#0072B2', '#D55E00'), ('o', 's', '^')):
        m = get(task, 'ko_ko')
        axes[0].plot([50,75,100], [100*m['coverage'][str(f)]['error_rate'] for f in (.5,.75,1.)],
                     marker=marker, color=color, label=label)
        values = sorted(float(r['latency_ms']) for r in rows if r['task']==task and r['condition']=='ko_ko' and r['stage'] in ('1','2'))
        assert len(values) == 100
        axes[1].step(values, np.arange(1,101)/100, where='post', color=color, label=label)
    axes[0].set(xlim=(45,105), ylim=(0,30), xticks=[50,75,100], xlabel='Retained cases (%)',
                ylabel='Error among retained cases (%)', title='D   Selective prediction')
    axes[1].set(xlabel='Client latency (ms)', ylabel='Cumulative fraction', ylim=(0,1),
                title='E   Successful-call latency', xscale='log')
    for ax in axes:
        ax.grid(alpha=.18); ax.legend(frameon=False, fontsize=9)
    save(fig, 'coverage-latency')


if __name__ == '__main__':
    main()
