import json
import re

import pytest

from jevbench import readme
from jevbench.common import ROOT

MARKERS = [('<!-- results-table-start -->', '<!-- results-table-end -->'),
           ('<!-- results-table-ko-start -->', '<!-- results-table-ko-end -->')]


def text():
    return (ROOT / 'README.md').read_text(encoding='utf-8')


def test_both_language_tables_are_marked():
    t = text()
    for start, end in MARKERS:
        assert t.count(start) == 1 and t.count(end) == 1
        assert t.index(start) < t.index(end)


def test_generated_tables_match_the_committed_readme():
    """The README on disk must already be what the generator would produce."""
    t = text()
    for (start, end), lang in zip(MARKERS, ('en', 'ko')):
        block = t.split(start, 1)[1].split(end, 1)[0].strip('\n')
        assert block == readme.table(lang)


def test_both_languages_report_identical_numbers():
    en, ko = readme.table('en').splitlines()[2:], readme.table('ko').splitlines()[2:]
    assert len(en) == len(ko) == 6
    for a, b in zip(en, ko):
        numbers = lambda row: re.findall(r'\d+', row)
        assert numbers(a) == numbers(b)


def test_only_intervals_excluding_zero_are_emphasised():
    data = json.loads((ROOT / 'results/aggregate/summary.json').read_text(encoding='utf-8'))
    expected = sum(1 for c in data['cells']
                   if c['luna_minus_jev']['ci95'][0] > 0 or c['luna_minus_jev']['ci95'][1] < 0)
    assert readme.table('en').count('**') == 2 * expected


def test_typographic_minus_is_used_consistently():
    """Task names may contain hyphens; the difference column must not."""
    for lang in ('en', 'ko'):
        for row in readme.table(lang).splitlines()[2:]:
            difference = row.rstrip('|').rsplit('|', 1)[1]
            assert '-' not in difference, difference
            if '−' in difference or '+' in difference:
                continue
            pytest.fail(f'no signed value found in {difference!r}')


def test_replace_refuses_a_readme_without_markers():
    with pytest.raises(ValueError, match='missing'):
        readme.replace('# Title\n\nno markers here\n', '', 'block')


def test_generator_is_idempotent(tmp_path, monkeypatch):
    original = text()
    readme.build()
    assert text() == original
