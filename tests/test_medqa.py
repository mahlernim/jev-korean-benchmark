from concurrent.futures import ThreadPoolExecutor
import pytest
from jevbench.medqa_run import Ledger, reservation
from jevbench import luna


def test_parallel_budget_admission():
    ledger=Ledger(.25)
    def attempt(_):
        try:
            ledger.reserve(.10)
            return True
        except RuntimeError:
            return False
    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(attempt,range(20)))==2
    assert ledger.inflight==pytest.approx(.2)
    ledger.settle(.1,.01)
    ledger.reserve(.1)
    assert ledger.spent+ledger.inflight==pytest.approx(.21)


def test_english_choice_mapping_and_reserve():
    e={'kind':'choice','request':{'model':'jev-latest','state':{'question':'A text-only question?'},
        'questions':{'answer':{'instructions':'Choose one.','criteria':{'A':'Alpha','B':'Beta','C':'Gamma','D':'Delta'}}}}}
    converted=luna.request(e)
    assert converted['text']['format']['schema']['properties']['answer']['enum']==['A','B','C','D']
    assert 'Alpha' in converted['input'][0]['content']
    assert reservation({**e,'provider':'jev'})>0
    assert reservation({'provider':'luna','request':converted})>128*1.20/1e6


def test_parallel_runner_retry_resume_and_uncertain_intent(tmp_path,monkeypatch):
    import json
    import threading
    from types import SimpleNamespace
    import httpx
    from jevbench import medqa_run as run
    from jevbench.common import digest, write_new
    directory=tmp_path/'run'; monkeypatch.setattr(run,'DIRECTORY',directory)
    monkeypatch.setattr(run,'ROOT',tmp_path)
    write_new(tmp_path/'data'/run.EXPERIMENT/'input-review.json',{'manifest_hash':'source','all_selected_text_complete':True})
    q={'type':'choice','instructions':'Choose.','criteria':{'A':'First','B':'Second','C':'Third','D':'Fourth'}}
    base={'kind':'choice','request':{'model':'jev-latest','state':{'question':'First?'},'questions':{'answer':q}}}
    items=[]
    for i in range(2):
        for provider in ('jev','luna'):
            payload=base['request'] if provider=='jev' else luna.request(base)
            items.append(dict(eval_id=f'{provider}-{i}',case_id=str(i),provider=provider,gold='A',kind='choice',request=payload,request_hash=digest(payload)))
    m={'sha256':'manifest','source_manifest_hash':'source','requests':items,'budget_usd':.25}
    monkeypatch.setattr(run,'prepare',lambda:m)
    monkeypatch.setattr(run,'jev_credential',lambda p:'test-placeholder')
    monkeypatch.setattr(run.luna,'credential',lambda:'test-placeholder')
    monkeypatch.setattr(run.time,'sleep',lambda n:None)
    calls=[]; lock=threading.Lock()
    class Jev:
        def __init__(self,**kwargs): pass
        def close(self): pass
        def system_one(self,**kwargs):
            with lock: calls.append('jev')
            raw={'model':'jev-test','answers':{'answer':{'type':'choice','choice':'A','confidence':1,
                'probabilities':{'A':1,'B':0,'C':0,'D':0}}},'usage':{'input_tokens':10,'output_tokens':5}}
            return SimpleNamespace(raw_http_response=SimpleNamespace(json=lambda:raw))
    class Luna:
        def __init__(self,**kwargs): pass
        def close(self): pass
        def post(self,*args,**kwargs):
            with lock:
                first='luna' not in calls; calls.append('luna')
            if first:
                request=httpx.Request('POST','https://example.invalid')
                raise httpx.HTTPStatusError('transient',request=request,response=httpx.Response(503,request=request))
            raw={'model':'luna-test','status':'completed','reasoning':{'effort':'none'},'service_tier':'default',
                'output':[{'type':'message','content':[{'type':'output_text','text':json.dumps({'answer':'A'})}]}],
                'usage':{'input_tokens':10,'output_tokens':5}}
            return SimpleNamespace(raise_for_status=lambda:None,json=lambda:raw)
    monkeypatch.setattr(run,'TypeSafeClient',Jev); monkeypatch.setattr(run.httpx,'Client',Luna)
    run.run(); assert len(calls)==5
    assert len([r for r in run.records() if r['status']=='success'])==4
    run.run(); assert len(calls)==5
    write_new(directory/'intents/uncertain.json',{'eval_id':'unknown'})
    with pytest.raises(RuntimeError,match='Uncertain'): run.run()
    assert len(calls)==5
