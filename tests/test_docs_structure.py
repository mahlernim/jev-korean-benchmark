"""Guards for the merged four-page documentation set.

The docs merge removed seven generated pages. Three publishers kept reading and
writing them, which broke those entry points silently because no test exercised
them. These tests fail loudly if that situation returns.
"""
import importlib
import pkgutil
import re
from pathlib import Path

import pytest

import jevbench
from jevbench.publish import PAGES

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'

REMOVED = ['aggregate', 'comparison-design', 'korean-supplement',
           'kormedmcqa-context', 'luna-comparison', 'medqa-english', 'report']

# 'report' never had its own html page; it rendered to index.html. Every module
# legitimately writes a report.md into its own results directory, so the markdown
# check has to be qualified by the docs/ prefix.
REMOVED_HTML = [n for n in REMOVED if n != 'report']

# Pages that live in docs/ without being published. Drafts for the separate
# 435-question study belong here and must never enter PAGES.
UNPUBLISHED = {'kormed-jev-literature-notes'}


def modules():
    return [importlib.import_module('jevbench.' + m.name)
            for m in pkgutil.iter_modules(jevbench.__path__)]


def sources():
    return {p.name: p.read_text(encoding='utf-8') for p in (ROOT / 'jevbench').glob('*.py')}


def test_every_module_imports():
    """A publisher that references a deleted page usually fails at import or first call."""
    assert modules()


@pytest.mark.parametrize('name', REMOVED)
def test_no_module_writes_a_removed_page(name):
    offenders = [f for f, text in sources().items() if f'docs/{name}.md' in text]
    assert not offenders, f'docs/{name}.md was removed in the docs merge but {offenders} still write it'


@pytest.mark.parametrize('name', REMOVED_HTML)
def test_no_module_links_a_removed_page(name):
    """publish.py is exempt: it owns the redirect table that names these pages."""
    offenders = [f for f, text in sources().items()
                 if f'{name}.html' in text and f != 'publish.py']
    assert not offenders, f'{name}.html was removed in the docs merge but {offenders} still link to it'


def test_every_removed_page_still_redirects():
    from jevbench.publish import REDIRECTS
    assert set(REDIRECTS) == {f'{n}.html' for n in REMOVED}, (
        'every page removed by the merge must keep a redirect, because its URL was published')
    for name, (target, _) in REDIRECTS.items():
        stub = DOCS / name
        assert stub.exists(), f'{name} has no rendered redirect'
        text = stub.read_text(encoding='utf-8')
        assert f'url={target}' in text and f'canonical" href="{target}"' in text
        path, _, fragment = target.partition('#')
        assert (DOCS / path).exists(), f'{name} redirects to a missing page'
        if fragment:
            ids = set(re.findall(r'id="([^"]+)"', (DOCS / path).read_text(encoding='utf-8')))
            assert fragment in ids, f'{name} redirects to a missing anchor #{fragment}'


def test_only_publish_writes_into_docs():
    """Generated narrative belongs in results/; docs/ holds hand-written pages."""
    pattern = re.compile(r"""docs[/'"]+[a-z0-9-]+\.md""")
    offenders = {}
    for name, text in sources().items():
        if name in ('publish.py',):
            continue
        hits = pattern.findall(text)
        if hits:
            offenders[name] = hits
    assert not offenders, offenders


def test_published_pages_exist_and_are_unique():
    stems = [s for s, _, _ in PAGES]
    assert len(stems) == len(set(stems))
    for stem, out, _ in PAGES:
        assert (DOCS / f'{stem}.md').exists(), f'{stem}.md is listed in PAGES but missing'
        assert (DOCS / out).exists(), f'{out} has not been rendered'


def test_no_markdown_in_docs_is_silently_unpublished():
    listed = {s for s, _, _ in PAGES}
    present = {p.stem for p in DOCS.glob('*.md')}
    orphans = present - listed - UNPUBLISHED
    assert not orphans, f'{orphans} sit in docs/ but are neither published nor declared unpublished'


def test_drafts_for_the_separate_study_are_not_published():
    listed = {s for s, _, _ in PAGES}
    assert not (listed & UNPUBLISHED)


@pytest.mark.parametrize('stem', ['index', 'methodology', 'running-experiments'])
def test_narrative_pages_are_bilingual(stem):
    text = (DOCS / f'{stem}.md').read_text(encoding='utf-8')
    assert text.count('<!-- lang:ko -->') == 1, f'{stem}.md must carry exactly one language marker'
    english, korean = text.split('<!-- lang:ko -->')
    assert english.strip().startswith('# ')
    assert korean.strip().startswith('# ')
    assert re.search(r'[가-힣]', korean), 'Korean half contains no Hangul'


def test_korean_headings_keep_unicode_anchors():
    """The default markdown slugify strips non-ASCII and breaks every Korean anchor."""
    html = (DOCS / 'index.html').read_text(encoding='utf-8')
    ids = re.findall(r'<h2 id="([^"]+)"', html)
    assert any(re.search(r'[가-힣]', i) for i in ids), 'Korean headings lost their anchors'
    assert '_1' not in ids, 'slugify fell back to positional ids'
