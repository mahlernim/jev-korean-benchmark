import json
import pytest
from jevbench import order_sensitivity as os_

STATE = {'sentence1': 'A first sentence.', 'sentence2': 'A second sentence.'}


def jev_raw(p, tokens=120):
    return {'model': 'jev-1.13.0', 'answers': {'answer': {'type': 'noul', 'noul': p}},
            'usage': {'input_tokens': tokens}}


def luna_raw(answer=True, i=100, o=10, cached=0, reasoning=0):
    return {'model': 'gpt-5.6-luna', 'status': 'completed',
            'usage': {'input_tokens': i, 'output_tokens': o,
                      'input_tokens_details': {'cached_tokens': cached},
                      'output_tokens_details': {'reasoning_tokens': reasoning}},
            'output': [{'type': 'message', 'content': [
                {'type': 'output_text', 'text': json.dumps({'answer': answer})}]}]}


def test_reversal_swaps_sentences_without_mutating_source():
    out = os_.reverse_state(STATE)
    assert out == {'sentence1': STATE['sentence2'], 'sentence2': STATE['sentence1']}
    assert STATE['sentence1'] == 'A first sentence.'


def test_reversal_is_an_involution():
    assert os_.reverse_state(os_.reverse_state(STATE)) == STATE


def test_luna_request_carries_no_gold_and_pins_effort():
    r = os_.luna_request('Are these equivalent?', STATE)
    assert r['reasoning'] == {'effort': 'none'}
    assert 'gold' not in json.dumps(r)
    assert r['text']['format']['schema']['properties']['answer']['type'] == 'boolean'


def test_jev_validation_thresholds_at_half_and_bills_input_only():
    assert os_.validate_jev(jev_raw(.5))['prediction'] == '1'
    assert os_.validate_jev(jev_raw(.49))['prediction'] == '0'
    scored = os_.validate_jev(jev_raw(.8, tokens=1000))
    assert scored['output_tokens'] == 0
    assert scored['estimated_cost_usd'] == pytest.approx(1000*os_.PRICE)


@pytest.mark.parametrize('bad', [1.5, -0.1, True, 'x', None])
def test_jev_rejects_invalid_probability(bad):
    with pytest.raises(ValueError):
        os_.validate_jev(jev_raw(bad))


def test_luna_validation_prices_cache_and_rejects_reasoning():
    scored = os_.validate_luna(luna_raw(True, i=100, o=10, cached=20))
    assert scored['prediction'] == '1' and scored['probability'] is None
    assert scored['estimated_cost_usd'] == pytest.approx(
        80*os_.LUNA_INPUT + 20*os_.LUNA_CACHED + 10*os_.LUNA_OUTPUT)
    with pytest.raises(ValueError):
        os_.validate_luna(luna_raw(reasoning=5))
    with pytest.raises(ValueError):
        os_.validate_luna(luna_raw(i=10, cached=50))


def test_luna_rejects_incomplete_response():
    with pytest.raises(ValueError):
        os_.validate_luna(luna_raw() | {'status': 'incomplete'})


def test_manifest_covers_every_cell_once_and_is_hash_stable(tmp_path, monkeypatch):
    monkeypatch.setattr(os_, 'DIRECTORY', tmp_path/'run')
    m = os_.prepare()
    assert len(m['evaluations']) == 800
    keys = {(e['case_id'], e['condition'], e['orientation'], e['role']) for e in m['evaluations']}
    assert len(keys) == 800
    assert len({e['eval_id'] for e in m['evaluations']}) == 800
    monkeypatch.setattr(os_, 'DIRECTORY', tmp_path/'run2')
    assert os_.prepare()['sha256'] == m['sha256']


def test_reversed_evaluation_differs_only_in_state(tmp_path, monkeypatch):
    monkeypatch.setattr(os_, 'DIRECTORY', tmp_path/'run')
    m = os_.prepare()
    by = {(e['case_id'], e['condition'], e['orientation']): e
          for e in m['evaluations'] if e['role'] == 'jev'}
    case, condition, _ = next(iter(by))
    a = by[(case, condition, 'original')]['request']
    b = by[(case, condition, 'reversed')]['request']
    assert a['questions'] == b['questions'] and a['model'] == b['model']
    assert b['state'] == os_.reverse_state(a['state'])


def test_gold_is_preserved_across_orientations(tmp_path, monkeypatch):
    monkeypatch.setattr(os_, 'DIRECTORY', tmp_path/'run')
    m = os_.prepare()
    golds = {}
    for e in m['evaluations']:
        golds.setdefault((e['case_id'], e['condition']), set()).add(e['gold'])
    assert all(len(v) == 1 for v in golds.values())


def test_analyze_counts_flips_and_total_variation(tmp_path, monkeypatch):
    monkeypatch.setattr(os_, 'DIRECTORY', tmp_path/'run')
    m = os_.prepare()
    wanted = [e for e in m['evaluations']
              if e['role'] == 'jev' and e['condition'] == 'ko_ko'][:4]
    cases = sorted({e['case_id'] for e in wanted})[:2]
    probs = {(cases[0], 'original'): .9, (cases[0], 'reversed'): .2,
             (cases[1], 'original'): .8, (cases[1], 'reversed'): .7}
    for e in m['evaluations']:
        p = probs.get((e['case_id'], e['orientation']))
        if p is None or e['role'] != 'jev' or e['condition'] != 'ko_ko':
            continue
        from jevbench.common import write_new
        write_new(tmp_path/'run'/'attempts'/f'{e["eval_id"].replace("__","-")}.json',
                  dict(eval_id=e['eval_id'], status='success', role=e['role'],
                       condition=e['condition'], orientation=e['orientation'],
                       case_id=e['case_id'], gold=e['gold'], prediction='1' if p >= .5 else '0',
                       probability=p, estimated_cost_usd=0.0))
    cell = os_.analyze()['cells']['jev/ko_ko']
    assert cell['n'] == 2 and cell['flips'] == 1
    assert cell['mean_total_variation'] == pytest.approx((0.7+0.1)/2)
