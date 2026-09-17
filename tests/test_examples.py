"""Guards for the published worked examples.

The point of these examples is that they are real items the study did NOT score.
If that ever stops being true, publishing them would contaminate the very
questions this repository reports on, so it is checked rather than assumed.
"""
import json
import re
from pathlib import Path

import pytest

from jevbench import examples

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'


@pytest.fixture(scope='module')
def chosen():
    return examples.select()[0]


def scored(task):
    index = json.loads((ROOT / 'results/evaluation-index.json').read_text(encoding='utf-8'))
    out = set()
    for entry in index:
        if entry['task'] != task:
            continue
        source_id = entry['source'].get('source_id')
        if source_id is None:
            continue
        out.add(tuple(source_id) if isinstance(source_id, list) else source_id)
    return out


def test_belebele_example_is_not_scored(chosen):
    link, number = chosen['belebele']['id']
    assert (link, str(number)) not in scored('belebele')


def test_pawsx_example_is_not_scored(chosen):
    assert chosen['pawsx']['id'] not in scored('pawsx')


def test_kormed_example_is_not_scored(chosen):
    assert chosen['kormed']['id'] not in scored('kormed')


def test_medqa_example_is_not_scored(chosen):
    manifest = json.loads(
        (ROOT / 'results/medqa-english-v3/request-manifest-index.json').read_text(encoding='utf-8'))
    ids = {r['case_id'] for r in manifest['requests']}
    assert len(ids) == 100, 'scored set looks wrong; the exclusion check would be meaningless'
    assert chosen['medqa']['id'] not in ids


def test_selection_is_deterministic():
    assert examples.select()[0] == examples.select()[0]


def test_every_example_has_a_gold_answer_inside_its_options(chosen):
    for task, item in chosen.items():
        side = item.get('en') or item.get('ko')
        if 'options' in side:
            assert item['gold'] in side['options'], task
        else:
            assert item['gold'] in ('0', '1'), task


def test_lock_records_provenance_for_every_example(chosen):
    lock = json.loads((ROOT / 'results/examples-lock.json').read_text(encoding='utf-8'))
    assert set(lock['selected']) == set(chosen)
    for task in chosen:
        assert lock['revisions'][task]
        assert lock['source_files'][task]
    assert lock['seed'] == examples.SEED


def test_lock_matches_what_is_published(chosen):
    lock = json.loads((ROOT / 'results/examples-lock.json').read_text(encoding='utf-8'))
    for task, item in chosen.items():
        assert lock['selected'][task] == item['id'], (
            f'{task}: the lock disagrees with the current selection; rerun jevbench.examples')


@pytest.mark.parametrize('path', ['README.md', 'docs/index.md'])
def test_examples_are_present_in_both_languages(path):
    text = (ROOT / path).read_text(encoding='utf-8')
    for marker in ('', 'ko-'):
        start, end = f'<!-- examples-{marker}start -->', f'<!-- examples-{marker}end -->'
        assert text.count(start) == 1 and text.count(end) == 1
        block = text.split(start, 1)[1].split(end, 1)[0]
        assert block.strip(), f'{path} {marker} example block is empty'


@pytest.mark.parametrize('path', ['README.md', 'docs/index.md'])
def test_every_example_carries_attribution(path):
    text = (ROOT / path).read_text(encoding='utf-8')
    for credit, _ in examples.ATTRIBUTION.values():
        source = credit.split(',')[0]
        assert f'<sub>{source}' in text, f'{source} is published without attribution in {path}'


def test_published_examples_match_the_generator(chosen):
    """README and index must already contain what the generator would write."""
    for path, detail in (('README.md', False), ('docs/index.md', True)):
        text = (ROOT / path).read_text(encoding='utf-8')
        for marker, lang in (('', 'en'), ('ko-', 'ko')):
            start, end = f'<!-- examples-{marker}start -->', f'<!-- examples-{marker}end -->'
            block = text.split(start, 1)[1].split(end, 1)[0].strip('\n')
            assert block == examples.render(chosen, lang, detail), f'{path} {lang} is stale'


def test_readme_uses_collapsed_form_and_index_does_not(chosen):
    readme = (ROOT / 'README.md').read_text(encoding='utf-8')
    index = (DOCS / 'index.md').read_text(encoding='utf-8')
    readme_block = readme.split('<!-- examples-start -->', 1)[1].split('<!-- examples-end -->', 1)[0]
    index_block = index.split('<!-- examples-start -->', 1)[1].split('<!-- examples-end -->', 1)[0]
    assert '<details>' in readme_block, 'README examples should stay collapsed'
    assert '<details>' not in index_block, 'site examples should be expanded'


def test_korean_render_uses_korean_labels(chosen):
    block = examples.render(chosen, 'ko', True)
    assert '선택지' in block and '지문' in block
    assert re.search(r'[가-힣]', block)
