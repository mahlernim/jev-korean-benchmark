import csv
import json
import math
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote

import pytest


def test_public_artifact_links():
    root=Path('docs')
    if not (root/'index.html').exists(): pytest.skip('Build publication first')
    class Links(HTMLParser):
        def __init__(self): super().__init__(); self.links=[]; self.ids=set()
        def handle_starttag(self,tag,attrs):
            a=dict(attrs)
            if 'id' in a: self.ids.add(a['id'])
            if tag=='a' and 'href' in a: self.links.append(a['href'])
    pages={}
    for path in root.glob('*.html'):
        parser=Links(); parser.feed(path.read_text(encoding='utf-8')); pages[path.name]=parser
    for name,page in pages.items():
        for link in page.links:
            parts=urlsplit(link)
            if parts.scheme or parts.netloc: continue
            target=unquote(parts.path) or name
            assert (root/target).exists(),(name,link)
            if parts.fragment:
                assert unquote(parts.fragment) in pages[target].ids,(name,link)


def test_published_scores_independently():
    root=Path('results')
    if not (root/'responses.jsonl').exists(): pytest.skip('Export results first')
    rows=[json.loads(line) for line in (root/'responses.jsonl').read_text(encoding='utf-8').splitlines()]
    metadata={e['eval_id']:e for e in json.loads((root/'evaluation-index.json').read_text(encoding='utf-8'))}
    assert len(metadata)==1036
    seen=set()
    for r in rows:
        if r['status']!='success': continue
        assert r['eval_id'] not in seen; seen.add(r['eval_id'])
        e=metadata[r['eval_id']]; a=r['raw_response']['answers']['answer']; score=r['score']
        if a['type']=='choice':
            vector=a['probabilities']; total=sum(vector.values()); vector={k:v/total for k,v in vector.items()}
            label=a['choice']
        else:
            vector={'0':1-a['noul'],'1':a['noul']}; label=str(int(a['noul']>=.5))
        assert label==score['prediction']
        assert (label==e['gold'])==score['correct']
        assert sum((p-(k==e['gold']))**2 for k,p in vector.items())==pytest.approx(score['brier'])
        assert -math.log(max(vector[e['gold']],1e-15))==pytest.approx(score['log_loss'])
        assert r['raw_response']['usage']['input_tokens']*.042/1e6==pytest.approx(score['estimated_cost_usd'])
    assert len(seen)==1036


def test_clean_replay():
    replica=Path('verification/replay/runs/pilot-v1/reports')
    if not replica.exists(): pytest.skip('Run clean replay first')
    for s in range(5):
        original=json.loads(Path(f'results/stage-{s}.json').read_text(encoding='utf-8'))
        copied=json.loads((replica/f'stage-{s}.json').read_text(encoding='utf-8'))
        for item in (original,copied): item.pop('generated_at')
        assert original==copied
