import pytest
from jevbench import order_repeat as orp
from jevbench import order_sensitivity as os_


def test_repeat_reuses_the_exact_source_request(tmp_path, monkeypatch):
    monkeypatch.setattr(os_, 'DIRECTORY', tmp_path / 'src')
    source = os_.prepare()
    monkeypatch.setattr(orp, 'SOURCE_DIR', tmp_path / 'src')
    monkeypatch.setattr(orp, 'DIRECTORY', tmp_path / 'rep')
    m = orp.prepare()
    assert len(m['evaluations']) == 200
    by_source = {e['eval_id']: e for e in source['evaluations']}
    for e in m['evaluations']:
        src = by_source[e['source_eval_id']]
        assert e['request'] == src['request']
        assert e['request_hash'] == src['request_hash']
        assert e['role'] == 'jev' and e['orientation'] == 'original'


def test_repeat_covers_only_jev_originals_once(tmp_path, monkeypatch):
    monkeypatch.setattr(os_, 'DIRECTORY', tmp_path / 'src')
    os_.prepare()
    monkeypatch.setattr(orp, 'SOURCE_DIR', tmp_path / 'src')
    monkeypatch.setattr(orp, 'DIRECTORY', tmp_path / 'rep')
    m = orp.prepare()
    keys = {(e['case_id'], e['condition']) for e in m['evaluations']}
    assert len(keys) == 200
    assert {e['condition'] for e in m['evaluations']} == {'en_en', 'ko_ko'}


def test_manifest_hash_is_stable(tmp_path, monkeypatch):
    monkeypatch.setattr(os_, 'DIRECTORY', tmp_path / 'src')
    os_.prepare()
    monkeypatch.setattr(orp, 'SOURCE_DIR', tmp_path / 'src')
    monkeypatch.setattr(orp, 'DIRECTORY', tmp_path / 'rep')
    a = orp.prepare()
    monkeypatch.setattr(orp, 'DIRECTORY', tmp_path / 'rep2')
    assert orp.prepare()['sha256'] == a['sha256']


def test_analyze_refuses_a_changed_source_manifest(tmp_path, monkeypatch):
    monkeypatch.setattr(os_, 'DIRECTORY', tmp_path / 'src')
    os_.prepare()
    monkeypatch.setattr(orp, 'SOURCE_DIR', tmp_path / 'src')
    monkeypatch.setattr(orp, 'DIRECTORY', tmp_path / 'rep')
    m = orp.prepare()
    from jevbench.common import read, write_new
    path = tmp_path / 'rep' / 'manifest.json'
    value = read(path)
    value['source_manifest_hash'] = 'f' * 64
    value.pop('sha256')
    from jevbench.common import digest
    value['sha256'] = digest(value)
    path.unlink()
    write_new(path, value)
    with pytest.raises(ValueError, match='Source manifest changed'):
        orp.analyze()


def test_analyze_counts_same_input_flips(tmp_path, monkeypatch):
    monkeypatch.setattr(os_, 'DIRECTORY', tmp_path / 'src')
    source = os_.prepare()
    monkeypatch.setattr(orp, 'SOURCE_DIR', tmp_path / 'src')
    monkeypatch.setattr(orp, 'DIRECTORY', tmp_path / 'rep')
    m = orp.prepare()
    from jevbench.common import write_new
    wanted = [e for e in m['evaluations'] if e['condition'] == 'ko_ko'][:2]
    probs = {0: (.9, .2), 1: (.8, .75)}  # first pair flips, second does not
    for i, e in enumerate(wanted):
        a, b = probs[i]
        write_new(tmp_path / 'src' / 'attempts' / f'src{i}.json',
                  dict(eval_id=e['source_eval_id'], status='success', role='jev',
                       condition=e['condition'], orientation='original',
                       case_id=e['case_id'], gold=e['gold'],
                       prediction='1' if a >= .5 else '0', probability=a,
                       estimated_cost_usd=0.0))
        write_new(tmp_path / 'rep' / 'attempts' / f'rep{i}.json',
                  dict(eval_id=e['eval_id'], source_eval_id=e['source_eval_id'],
                       status='success', role='jev', condition=e['condition'],
                       case_id=e['case_id'], gold=e['gold'],
                       prediction='1' if b >= .5 else '0', probability=b,
                       estimated_cost_usd=0.0))
    cell = orp.analyze()['cells']['jev/ko_ko']
    assert cell['n'] == 2 and cell['flips'] == 1
    assert cell['mean_total_variation'] == pytest.approx((0.7 + 0.05) / 2)
