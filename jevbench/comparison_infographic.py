"""Render sourced contextual scores, without running models."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
# label, percentage, evidence group. Source IDs correspond to the footer.
ROWS = [
    ('Claude Opus 4 · thinking [2]', 96.55, 'external'),
    ('Claude Opus 4 · direct [2]', 93.33, 'external'),
    ('o1-preview [3]', 92.41, 'paper'),
    ('Gemini 2.5 Pro · thinking [2]', 90.80, 'external'),
    ('GPT-5.1 · direct [2]', 90.11, 'external'),
    ('Luna none · EN instructions [1]', 89.00, 'luna'),
    ('Gemini 2.5 Flash · direct [2]', 88.51, 'external'),
    ('Qwen3-235B-A22B · thinking [2]', 88.28, 'external'),
    ('Claude 3.5 Sonnet [3]', 88.05, 'paper'),
    ('Luna none · KO instructions [1]', 88.00, 'luna'),
    ('GPT-4o [3]', 85.98, 'paper'),
    ('Jev · English instructions [1]', 82.00, 'jev'),
    ('Jev · Korean instructions [1]', 80.00, 'jev'),
    ('Gemini 1.5 Pro [3]', 79.31, 'paper'),
    ('Qwen2.5-72B-Instruct [3]', 77.24, 'paper'),
    ('GPT-4o-mini [3]', 63.22, 'paper'),
]

def main():
    plt.rcParams.update({'font.family':'DejaVu Sans','svg.fonttype':'none',
                         'pdf.fonttype':42,'font.size':10})
    fig = plt.figure(figsize=(10, 8.5), facecolor='white')
    fig.text(.045,.952,'Jev and Luna in context',fontsize=25,weight='bold',color='#152638')
    fig.text(.045,.916,'KorMedMCQA doctor-exam accuracy (%)',fontsize=14,color='#354558')
    fig.text(.045,.882,'Published and vendor-reported scores • Different protocols, not a matched ranking',fontsize=10,color='#526173')
    ax=fig.add_axes([.355,.245,.575,.60])
    colors={'jev':'#007E87','luna':'#AC641D','external':'#526C91','paper':'#A5AFBC'}
    for i,(label,value,group) in enumerate(ROWS):
        if group in ('jev','luna'): ax.axhspan(i-.46,i+.46,color='#E8F4F3' if group=='jev' else '#FFF3E6',zorder=0)
        ax.barh(i,value,height=.56,color=colors[group],zorder=2)
        ax.text(value+1,i,f'{value:.2f}',va='center',fontsize=10,
                weight='bold' if group in ('jev','luna') else 'normal',color='#152638')
    ax.set_yticks(range(len(ROWS)),[r[0] for r in ROWS])
    ax.invert_yaxis(); ax.set_xlim(0,105)
    ax.set_xticks([0,20,40,60,80,100]); ax.set_xlabel('Accuracy (%)',fontsize=10)
    ax.grid(axis='x',color='#E5E9EE',linewidth=.7,zorder=0)
    ax.tick_params(axis='y',length=0,pad=10,labelsize=10)
    ax.tick_params(axis='x',length=0,labelsize=9,colors='#526173')
    for spine in ax.spines.values(): spine.set_visible(False)
    for tick,row in zip(ax.get_yticklabels(),ROWS):
        if row[2] in ('jev','luna'): tick.set_color(colors[row[2]]);tick.set_weight('bold')
    fig.text(.045,.178,'READ WITH CONTEXT',fontsize=9,weight='bold',color='#152638')
    fig.text(.045,.153,'Jev and GPT-5.6-Luna (reasoning none): same 100 screened Korean questions; EN/KO instructions.',fontsize=9,color='#354558')
    fig.text(.045,.132,'[2] Vendor-reported, 435 questions, mixed reasoning. [3] Original paper, 5-shot. External protocols differ.',fontsize=9,color='#354558')
    fig.text(.045,.111,'Medical stage complete. Point estimates shown; intervals and paired differences in linked evidence.',fontsize=9,color='#354558')
    sources=[
      ('[1] Our matched pilot · github.com/mahlernim/jev-korean-benchmark','https://github.com/mahlernim/jev-korean-benchmark'),
      ('[2] Acryl vendor evaluation · allm.acryl.ai/benchmarks','https://allm.acryl.ai/benchmarks'),
      ('[3] Kweon et al. (2024), Table 1 · arxiv.org/abs/2403.01469','https://arxiv.org/abs/2403.01469')]
    for i,(label,url) in enumerate(sources):
        fig.text(.045,.078-i*.020,label,fontsize=8,color='#526173',url=url)
    fig.text(.955,.038,'Checked 17 Sep 2026',ha='right',fontsize=8,color='#526173')
    out=ROOT/'results'/'aggregate'; out.mkdir(parents=True,exist_ok=True)
    for ext in ('png','svg','pdf'):
        fig.savefig(out/f'kormedmcqa-context.{ext}',dpi=200,facecolor='white')
    plt.close(fig)

if __name__=='__main__': main()
