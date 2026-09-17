import pytest
from jevbench.luna import request, validate


def fixture(kind='choice'):
    q={'instructions':'한국어 질문'}
    if kind=='choice': q['criteria']={'b':'둘','a':'하나'}
    e={'kind':kind,'gold':'a' if kind=='choice' else '1',
       'request':{'state':{'text':'한국어'},'questions':{'answer':q}}}
    e['request']=request(e)
    return e


def raw(answer):
    import json
    return {'status':'completed','model':'gpt-5.6-luna',
        'output':[{'type':'message','content':[{'type':'output_text','text':json.dumps({'answer':answer})}]}],
        'usage':{'input_tokens':100,'output_tokens':10,'input_tokens_details':{'cached_tokens':20}}}


def test_mapping_and_usage():
    e=fixture()
    assert e['request']['text']['format']['schema']['properties']['answer']['enum']==['b','a']
    assert '한국어' in e['request']['input'][0]['content']
    s=validate(e,raw('a'))
    assert s['correct'] and s['estimated_cost_usd']==pytest.approx(.0000284)
    assert e['request']['reasoning']=={'effort':'none'}
    assert validate(fixture('noul'),raw(True))['correct']


def test_reject_invalid_answers_and_usage():
    with pytest.raises(ValueError): validate(fixture(),raw('c'))
    with pytest.raises(ValueError): validate(fixture('noul'),raw(1))
    r=raw('a'); r['usage']['output_tokens_details']={'reasoning_tokens':2}
    with pytest.raises(ValueError): validate(fixture(),r)


def test_retry_resume_and_budget(tmp_path,monkeypatch):
    import contextlib
    import httpx
    from jevbench import luna
    from jevbench.common import digest
    e=fixture(); e.update(eval_id='test',stage=0); e['request_hash']=digest(e['request'])
    m={'sha256':'test-manifest','budget_usd':.25,'evaluations':[e]}
    monkeypatch.setattr(luna,'DIRECTORY',tmp_path)
    monkeypatch.setattr(luna,'credential',lambda:'test-placeholder')
    monkeypatch.setattr(luna,'run_lock',lambda p:contextlib.nullcontext())
    monkeypatch.setattr(luna,'report',lambda m:None)
    monkeypatch.setattr(luna.time,'sleep',lambda n:None)
    calls=[]
    class Client:
        def __init__(self,**kw): pass
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def post(self,*args,**kw):
            calls.append(1)
            raise httpx.ConnectError('no secrets')
    monkeypatch.setattr(luna.httpx,'Client',Client)
    luna.run(m,0)
    assert len(calls)==3
    luna.run(m,0)
    assert len(calls)==3
    other=tmp_path/'budget'; monkeypatch.setattr(luna,'DIRECTORY',other)
    with pytest.raises(RuntimeError,match='Budget'): luna.run({**m,'budget_usd':0},0)
    assert len(calls)==3
