import copy
import json
from pathlib import Path

import pytest

from jevbench.common import digest, load_manifest, write_new
from jevbench.prepare import evaluation, paired_rows, proportional, robustness, unique_index
from jevbench.report import metrics, paired_difference, wilson
from jevbench.runner import credential, history, transient, validated
from jevbench.synthetic import development_cases, medical_cases


def sample():
    e=evaluation(development_cases()[0],"ko_ko","fixture")
    raw=dict(model="fixture",usage={"input_tokens":100},answers={"answer":dict(type="choice",choice="red",confidence=.6,probabilities={"red":.8,"blue":.1,"unknown":.1})})
    return e,raw


def test_utf8_and_credentials(tmp_path):
    value={"text":"환자는 흉통을 부인한다."}
    p=tmp_path/"fixture.json"; write_new(p,value)
    assert json.loads(p.read_text(encoding="utf-8"))==value
    env=tmp_path/"fixture.env"; env.write_text("TYPESAFE_KEY='test-only-dummy'\n",encoding="utf-8-sig")
    assert credential(env)=="test-only-dummy"


def test_join_label_mismatch_and_duplicates():
    ex=[]
    matched=paired_rows([dict(id=1,label=0),dict(id=2,label=1)],[dict(id=1,label=1),dict(id=3,label=0)],lambda r:r['id'],lambda r:r['label'],ex,"fixture")
    assert not matched and len(ex)==3
    with pytest.raises(ValueError): unique_index([dict(id=1),dict(id=1)],lambda r:r['id'])


def test_probabilities_and_metrics():
    e,raw=sample(); score=validated(e,raw)
    assert score['brier']==pytest.approx(.06)
    assert score['log_loss']==pytest.approx(.2231435513142097)
    assert score['correct']
    m=metrics([(e,dict(score=score,latency_ms=100))])
    assert m['coverage']['0.5']['error_rate']==0
    assert wilson(0,10)[1]==pytest.approx(.2775327998628892)
    assert wilson(10,10)[0]==pytest.approx(.7224672001371107)


@pytest.mark.parametrize('change',["nan","keys","sum","choice","tokens","confidence","argmax"])
def test_reject_invalid(change):
    e,r=sample(); a=r['answers']['answer']
    if change=='nan': a['probabilities']['red']=float('nan')
    if change=='keys': a['probabilities']['other']=a['probabilities'].pop('red')
    if change=='sum': a['probabilities']['red']=.3
    if change=='choice': a['choice']='other'
    if change=='tokens': r['usage']={}
    if change=='confidence': a['confidence']=1.1
    if change=='argmax': a['choice']='blue'
    with pytest.raises(ValueError): validated(e,r)


def test_noul():
    e=evaluation(development_cases()[6],'ko_ko','fixture')
    s=validated(e,dict(model='fixture',usage={'input_tokens':2},answers={'answer':{'type':'noul','noul':.9}}))
    assert s['prediction']=='1' and s['brier']==pytest.approx(.02)


def test_gold_and_variant_mapping():
    cases=medical_cases(); evaluations=[]
    for task in ('belebele','pawsx','kormed','medical_text'):
        for i in range(5):
            c=copy.deepcopy(development_cases()[6] if task=='pawsx' else cases[i])
            c.update(id=f'{task}-{i}',task=task)
            evaluations.append(evaluation(c,'ko_ko','fixture'))
    out=robustness(evaluations)
    assert len(out)==80
    base={e['eval_id']:e for e in evaluations}
    for e in out:
        original=base[e['base_eval_id']]
        assert e['gold']==original['gold']
        if e['kind']=='choice':
            assert e['request']['questions']['answer']['criteria']==original['request']['questions']['answer']['criteria']
            if e['variant'].startswith('variant'): assert e['request_hash']!=original['request_hash']
        elif e['variant'].startswith('variant'):
            assert e['request']['state']['sentence1']==original['request']['state']['sentence2']


def test_resume_integrity(tmp_path):
    e,_=sample(); manifest={'sha256':'fixture','evaluations':[e]}
    r=dict(eval_id=e['eval_id'],request_hash=e['request_hash'],manifest_hash='fixture',attempt=1,status='success',terminal=True)
    write_new(tmp_path/'attempts'/'one.json',r)
    assert history(manifest,tmp_path)[e['eval_id']][-1]['terminal']
    r['request_hash']='tampered'; (tmp_path/'attempts'/'one.json').write_text(json.dumps(r))
    with pytest.raises(ValueError): history(manifest,tmp_path)


def test_retry_classification():
    class HTTPError(Exception): pass
    for status,want in [(429,True),(503,True),(401,False),(400,False)]:
        e=HTTPError(); e.status_code=status
        assert transient(e)==want


def test_proportional():
    assert proportional({2022:90,2023:86,2024:83},100)=={2022:35,2023:33,2024:32}


def test_paired_metric():
    a={str(i):{'score':{'correct':True}} for i in range(10)}
    b={str(i):{'score':{'correct':False}} for i in range(10)}
    m=paired_difference(a,b)
    assert m['difference']==-1 and m['left_only_correct']==10


def test_frozen_manifest():
    path=Path('data/pilot-v1/manifest.json')
    if not path.exists(): pytest.skip('Prepare source data first')
    m=load_manifest(path)
    assert len(m['evaluations'])==1036
    for e in m['evaluations']:
        assert 'gold' not in e['request'] and 'cot' not in e['request']['state']
        if e['task']=='medical_text': assert e['review_status']=='unreviewed'


def test_three_attempt_limit_and_resume(tmp_path,monkeypatch):
    from jevbench import runner,report
    import types
    e,raw=sample(); calls=[]
    manifest={'sha256':'fixture','experiment':'fixture','model':'fixture','budget_usd':.25,'evaluations':[e]}
    class TypeSafeAPIConnectionError(Exception): pass
    class FakeClient:
        def __init__(self,**kwargs): assert kwargs['retry'].max_retries==0
        def close(self): pass
        def system_one(self,**kwargs):
            calls.append(kwargs)
            raise TypeSafeAPIConnectionError()
    monkeypatch.setattr(runner,'TypeSafeClient',FakeClient)
    monkeypatch.setattr(runner,'credential',lambda p:'dummy')
    monkeypatch.setattr(runner.time,'sleep',lambda _:None)
    monkeypatch.setattr(report,'report',lambda *a:None)
    runner.run_locked(manifest,tmp_path,0)
    assert len(calls)==3
    assert len(runner.records(tmp_path))==3
    assert runner.records(tmp_path)[-1]['terminal']
    runner.run_locked(manifest,tmp_path,0)
    assert len(calls)==3


def test_successful_resume_and_budget(tmp_path,monkeypatch):
    from jevbench import runner,report
    from types import SimpleNamespace
    e,raw=sample(); calls=[]
    manifest={'sha256':'fixture','experiment':'fixture','model':'fixture','budget_usd':.25,'evaluations':[e]}
    class FakeClient:
        def __init__(self,**kwargs): pass
        def close(self): pass
        def system_one(self,**kwargs):
            calls.append(kwargs)
            return SimpleNamespace(raw_http_response=SimpleNamespace(json=lambda:raw))
    monkeypatch.setattr(runner,'TypeSafeClient',FakeClient)
    monkeypatch.setattr(runner,'credential',lambda p:'dummy')
    monkeypatch.setattr(report,'report',lambda *a:None)
    runner.run_locked(manifest,tmp_path,0)
    runner.run_locked(manifest,tmp_path,0)
    assert len(calls)==1
    manifest['budget_usd']=0
    with pytest.raises(RuntimeError,match='budget'): runner.run_locked(manifest,tmp_path/'limited',0)
    assert len(calls)==1


def test_rounding_amendment():
    e,r=sample()
    r['answers']['answer']['probabilities']={'red':.79,'blue':.1,'unknown':.1}
    s=validated(e,r)
    assert s['reported_probability_sum']==pytest.approx(.99)
    assert s['probabilities_renormalized']
    assert sum(s['probabilities'].values())==pytest.approx(1)
    assert r['answers']['answer']['probabilities']['red']==.79
    r['answers']['answer']['probabilities']['red']=.75
    with pytest.raises(ValueError): validated(e,r)


def test_sdk_wire_option_order():
    import httpx2
    from typesafe_sdk import TypeSafeClient,Choice,RetryPolicy
    e,r=sample(); captured=[]
    def handler(request):
        captured.append(json.loads(request.content))
        return httpx2.Response(200,json=r)
    with TypeSafeClient(api_key='test-only-dummy',transport=httpx2.MockTransport(handler),retry=RetryPolicy(max_retries=0)) as client:
        client.system_one(state={'text':'한국어'},questions={'answer':Choice(criteria={'unknown':'Unknown','red':'Red','blue':'Blue'},instructions='Choose')},model='fixture')
    assert list(captured[0]['questions']['answer']['criteria'])==['unknown','red','blue']
