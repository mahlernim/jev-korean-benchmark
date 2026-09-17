"""Explainer diagram: how a token-generating model and Jev return the same decision.

Describes the observable API contract only. It makes no claim about either
provider's internal architecture, in keeping with the rest of this repository.
Measured figures come from the frozen pilot and the Luna comparison.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs' / 'figures'

INK, MUTED, RULE = '#12202E', '#54626F', '#C8D2DC'
JEV, LUNA, PANEL = '#0072B2', '#D55E00', '#F4F6F9'

TEXT = {
    'en': dict(
        title='Two ways to return the same decision',
        subtitle='What each interface gives back when asked one multiple-choice question.',
        question='"Do these two sentences mean the same thing?"',
        llm_head='A token-generating model (Luna)',
        llm_body='Emits one token at a time. Each token is chosen, then fed back in before the '
                 'next one is chosen. The answer has to be parsed out of the finished text.',
        llm_note='about 12 output tokens per answer, billed for input and output',
        jev_head='Jev',
        jev_body='Returns a probability for every option at once, plus the option with the '
                 'highest probability. There is no rationale channel and nothing to parse.',
        jev_note='0 output tokens, billed for input only',
        parse='parse',
        answer='answer',
        yes='yes', no='no',
        conf='confidence 0.81',
        timing='Median latency measured across 1,036 calls in this study',
        short_llm='Luna'),
    'ko': dict(
        title='같은 결정을 돌려주는 두 가지 방식',
        subtitle='객관식 문항 하나를 물었을 때 각 인터페이스가 돌려주는 것.',
        question='"이 두 문장은 같은 뜻입니까?"',
        llm_head='토큰을 생성하는 모델 (Luna)',
        llm_body='한 번에 토큰 하나씩 생성합니다. 선택된 토큰은 다음 토큰을 고르기 전에 다시 입력으로 '
                 '들어갑니다. 완성된 텍스트에서 답을 파싱해야 합니다.',
        llm_note='답변당 출력 토큰 약 12개, 입력과 출력 모두 과금',
        jev_head='Jev',
        jev_body='모든 선택지의 확률을 한 번에 돌려주고, 확률이 가장 높은 선택지를 함께 제시합니다. '
                 '근거 텍스트 채널이 없으며 파싱할 것도 없습니다.',
        jev_note='출력 토큰 0개, 입력에만 과금',
        parse='파싱',
        answer='답',
        yes='예', no='아니오',
        conf='확신도 0.81',
        timing='이 연구의 1,036회 호출에서 측정한 지연 시간 중앙값',
        short_llm='Luna'),
}

FONT = {
    'en': "'DejaVu Sans', system-ui, -apple-system, sans-serif",
    'ko': "'Malgun Gothic', 'Apple SD Gothic Neo', 'Noto Sans KR', system-ui, sans-serif",
}


def measured():
    luna = json.loads((ROOT / 'results/luna-none-v1/summary.json').read_text(encoding='utf-8'))
    return dict(jev_ms=221, luna_ms=round(luna['median_ms']),
                luna_out=luna['output_tokens'], luna_calls=luna['successful'])


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def wrap(text, width):
    lines, cur = [], ''
    for w in text.split(' '):
        trial = (cur + ' ' + w).strip()
        if len(trial) > width and cur:
            lines.append(cur)
            cur = w
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def build(lang='en'):
    t, m, ff = TEXT[lang], measured(), FONT[lang]
    W = 920
    wrap_w = 64 if lang == 'en' else 40
    p = ['', '']
    p.append('<text x="28" y="40" font-size="20" fill="%s">%s</text>' % (INK, esc(t['title'])))
    p.append('<text x="28" y="63" font-size="12.5" fill="%s">%s</text>' % (MUTED, esc(t['subtitle'])))
    p.append('<rect x="28" y="80" width="%d" height="34" rx="6" fill="%s"/>' % (W - 56, PANEL))
    p.append('<text x="44" y="102" font-size="13" fill="%s">%s</text>' % (INK, esc(t['question'])))

    y0 = 142
    p.append('<text x="28" y="%d" font-size="13.5" font-weight="bold" fill="%s">%s</text>'
             % (y0, LUNA, esc(t['llm_head'])))
    for i, line in enumerate(wrap(t['llm_body'], wrap_w)):
        p.append('<text x="28" y="%d" font-size="11.5" fill="%s">%s</text>'
                 % (y0 + 20 + i * 16, MUTED, esc(line)))
    bx, by = 28, y0 + 78
    for i in range(12):
        x = bx + i * 40
        p.append('<rect x="%d" y="%d" width="30" height="26" rx="4" fill="#FFFFFF" '
                 'stroke="%s" stroke-width="1.3"/>' % (x, by, LUNA))
        p.append('<text x="%d" y="%d" font-size="10" fill="%s" text-anchor="middle">t%d</text>'
                 % (x + 15, by + 18, LUNA, i + 1))
        if i < 11:
            p.append('<path d="M%d %d L%d %d" stroke="%s" stroke-width="1.2" '
                     'marker-end="url(#arrowL)"/>' % (x + 30, by + 13, x + 37, by + 13, LUNA))
    p.append('<path d="M%d %d C%d %d, %d %d, %d %d" fill="none" stroke="%s" stroke-width="1.1" '
             'stroke-dasharray="4 3" marker-end="url(#arrowL)"/>'
             % (bx + 455, by + 26, bx + 455, by + 50, bx + 15, by + 50, bx + 15, by + 28, LUNA))
    p.append('<text x="%d" y="%d" font-size="10.5" fill="%s" text-anchor="middle">%s</text>'
             % (bx + 235, by + 66, MUTED, esc(t['llm_note'])))
    p.append('<text x="%d" y="%d" font-size="11.5" fill="%s">%s</text>'
             % (bx + 500, by + 18, MUTED, esc(t['parse'])))
    p.append('<path d="M%d %d L%d %d" stroke="%s" stroke-width="1.4" marker-end="url(#arrowL)"/>'
             % (bx + 500 + (44 if lang == 'en' else 40), by + 13, bx + 552, by + 13, LUNA))
    p.append('<rect x="%d" y="%d" width="62" height="30" rx="5" fill="%s"/>' % (bx + 558, by - 2, LUNA))
    p.append('<text x="%d" y="%d" font-size="13" fill="#FFFFFF" text-anchor="middle" '
             'font-weight="bold">%s</text>' % (bx + 589, by + 18, esc(t['yes'])))

    y1 = by + 92
    p.append('<line x1="28" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="1"/>'
             % (y1 - 26, W - 28, y1 - 26, RULE))
    p.append('<text x="28" y="%d" font-size="13.5" font-weight="bold" fill="%s">%s</text>'
             % (y1, JEV, esc(t['jev_head'])))
    for i, line in enumerate(wrap(t['jev_body'], wrap_w)):
        p.append('<text x="28" y="%d" font-size="11.5" fill="%s">%s</text>'
                 % (y1 + 20 + i * 16, MUTED, esc(line)))
    gy = y1 + 22 + 16 * len(wrap(t['jev_body'], wrap_w)) + 24
    p.append('<text x="28" y="%d" font-size="10.5" fill="%s">%s</text>' % (gy - 8, MUTED, esc(t['answer'])))
    for i, (label, value, color) in enumerate([(t['yes'], .81, JEV), (t['no'], .19, '#9BB8CE')]):
        y = gy + i * 30
        p.append('<text x="86" y="%d" font-size="11.5" fill="%s" text-anchor="end">%s</text>'
                 % (y + 17, INK, esc(label)))
        p.append('<rect x="96" y="%d" width="%d" height="20" rx="3" fill="%s"/>'
                 % (y + 2, round(380 * value), color))
        p.append('<text x="%d" y="%d" font-size="11.5" fill="%s">%.2f</text>'
                 % (96 + round(380 * value) + 8, y + 17, INK, value))
    p.append('<path d="M540 %d L568 %d" stroke="%s" stroke-width="1.4" marker-end="url(#arrowJ)"/>'
             % (gy + 16, gy + 16, JEV))
    p.append('<rect x="576" y="%d" width="62" height="30" rx="5" fill="%s"/>' % (gy + 1, JEV))
    p.append('<text x="607" y="%d" font-size="13" fill="#FFFFFF" text-anchor="middle" '
             'font-weight="bold">%s</text>' % (gy + 21, esc(t['yes'])))
    p.append('<text x="648" y="%d" font-size="10.5" fill="%s">%s</text>' % (gy + 21, MUTED, esc(t['conf'])))
    p.append('<text x="28" y="%d" font-size="10.5" fill="%s">%s</text>' % (gy + 76, MUTED, esc(t['jev_note'])))

    ly = gy + 108
    scale = 600.0 / m['luna_ms']
    p.append('<text x="28" y="%d" font-size="10.5" fill="%s">%s</text>' % (ly - 10, MUTED, esc(t['timing'])))
    for idx, (label, ms, color) in enumerate(((t['jev_head'], m['jev_ms'], JEV),
                                              (t['short_llm'], m['luna_ms'], LUNA))):
        y = ly + idx * 16
        p.append('<rect x="150" y="%d" width="%d" height="10" rx="2" fill="%s"/>'
                 % (y, round(ms * scale), color))
        p.append('<text x="144" y="%d" font-size="10" fill="%s" text-anchor="end">%s</text>'
                 % (y + 9, INK, esc(label)))
        p.append('<text x="%d" y="%d" font-size="10" fill="%s">%d ms</text>'
                 % (150 + round(ms * scale) + 7, y + 9, MUTED, ms))

    p.append('<defs>'
             '<marker id="arrowL" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">'
             '<path d="M0 0 L6 3 L0 6 z" fill="%s"/></marker>'
             '<marker id="arrowJ" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">'
             '<path d="M0 0 L6 3 L0 6 z" fill="%s"/></marker></defs>' % (LUNA, JEV))
    H = ly + 46
    p[0] = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
            'font-family="%s" role="img" aria-label="%s">' % (W, H, W, H, ff, esc(t['title'])))
    p[1] = '<rect width="%d" height="%d" fill="#FFFFFF"/>' % (W, H)
    p.append('</svg>')
    return '\n'.join(p)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for lang in ('en', 'ko'):
        name = 'answer-shape' + ('' if lang == 'en' else '.ko') + '.svg'
        (OUT / name).write_text(build(lang), encoding='utf-8')
        print('Wrote', name)


if __name__ == '__main__':
    main()
