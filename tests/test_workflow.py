"""Deterministic record, synthesis, renderer and export regression coverage."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import chdir, redirect_stdout
from copy import deepcopy
from html import unescape
from html.parser import HTMLParser
import io
import json
import re
from threading import Barrier
from unittest.mock import patch

from markdown_it import MarkdownIt
from pathlib import Path
import sys
import tempfile
import unittest
from xml.etree import ElementTree as ET

NOTEBOOKS = Path(__file__).resolve().parents[1] / 'book' / 'notebooks'
sys.path.insert(0, str(NOTEBOOKS))
from decision_workflow import (ValidationError, apply_synthesis, capture_response,
    download_links, export_record, load_record, new_record, parse_record,
    save_record, synthesis_prompt, to_html, to_markdown, validate_record)
from six_hats_mindmap import render_mind_map
import decision_workflow


class SemanticText(HTMLParser):
    """Collect actual semantic blocks, excluding the redundant SVG/details and head."""
    def __init__(self):
        super().__init__()
        self.stack = []
        self.blocks = []
        self.sections = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('meta', 'link', 'br', 'hr', 'img', 'input'):
            return
        excluded = tag in ('head', 'details', 'svg', 'script', 'style') or any(entry[2] for entry in self.stack)
        block = [] if not excluded and tag in ('h1', 'h2', 'h3', 'p', 'li') else None
        if block is not None:
            self.blocks.append((tag, block))
        if tag == 'section' and not excluded:
            self.sections += 1
        self.stack.append((tag, block, excluded))

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break

    def handle_data(self, text):
        if any(entry[2] for entry in self.stack):
            return
        for _, block, _ in self.stack:
            if block is not None:
                block.append(text)

    def texts(self, tag=None):
        return [' '.join(''.join(parts).split()) for name, parts in self.blocks if tag is None or name == tag]


def all_text_values(value):
    """Independent of the production content inventory so omissions fail tests."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from all_text_values(child)
    elif isinstance(value, list):
        for child in value:
            yield from all_text_values(child)


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.record = load_record(NOTEBOOKS / 'examples/global_health.json')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'decision.json'

    def test_unicode_round_trip_and_complete_exports(self):
        self.record['title'] += ' — santé 健康 🌍'
        save_record(self.record, self.path)
        self.assertEqual(load_record(self.path), self.record)
        paths = export_record(self.record, Path(self.temp.name) / 'exports')
        self.assertEqual(load_record(paths['json']), self.record)
        self.assertEqual(set(paths), {'json', 'svg', 'md', 'html'})
        svg = ET.fromstring(paths['svg'].read_text(encoding='utf-8'))
        labels = [node.get('aria-label') for node in svg.iter() if node.get('aria-label')]
        html = unescape(paths['html'].read_text(encoding='utf-8'))
        for hat in ('white', 'red', 'black', 'yellow', 'green', 'blue', 'purple'):
            for value in self.record[hat].values():
                for text in value if isinstance(value, list) else [value]:
                    self.assertIn(text, labels)
                    self.assertIn(text, html)
        for outcome in self.record['outcomes']:
            self.assertIn(outcome, labels)
            self.assertIn(outcome, html)
        for evidence in self.record['evidence']:
            for key, value in evidence.items():
                self.assertIn(f'{key.capitalize()}: {value}', labels)
        for key in ('title', 'question', 'subtitle', 'context', 'demo_notice'):
            self.assertIn(self.record[key], labels)
        self.assertIn('santé 健康 🌍', paths['json'].read_text(encoding='utf-8'))
        links = download_links(paths)
        self.assertEqual(links.count(' download='), 4)
        self.assertEqual(links.count(';base64,'), 4)
        self.assertIn('<main class="decision-record">', html)
        self.assertIn('<h2', html)
        self.assertIn('<ul>', html)

    def test_minimal_legacy_six_hat_record_remains_supported(self):
        record = {'title': 'A decision', 'question': 'How?'}
        record.update({hat: {'items': []} for hat in ('white', 'red', 'black', 'yellow', 'green', 'blue')})
        self.assertEqual(validate_record(record), record)
        ET.fromstring(render_mind_map(record))

    def test_validation_reports_nested_fields_and_preserves_saved_bytes(self):
        save_record(self.record, self.path)
        before = self.path.read_bytes()
        cases = [([], 'record'), ({}, 'missing required'),
                 ({**self.record, 'title': 7}, 'title'),
                 ({**self.record, 'question': ' '}, 'question'),
                 ({**self.record, 'white': []}, 'white'),
                 ({**self.record, 'white': {'items': 'abc'}}, 'white.items'),
                 ({**self.record, 'white': {'items': [9]}}, 'white.items[0]'),
                 ({**self.record, 'red': {'items': [], 'questions': [False]}}, 'red.questions[0]'),
                 ({**self.record, 'purple': {'items': [], 'recommendation': []}}, 'purple.recommendation'),
                 ({**self.record, 'outcomes': None}, 'outcomes'),
                 ({**self.record, 'evidence': [3]}, 'evidence[0]'),
                 ({**self.record, 'evidence': [{'claim': 'x', 'source': 5, 'status': 'draft'}]}, 'evidence[0].source'),
                 ({**self.record, 'title': 'bad\x00xml'}, 'U+0000'),
                 ({**self.record, 'title': 'bad\ud800unicode'}, 'U+D800'),
                 ({**self.record, 'extra': 'must not be dropped'}, 'unrecognized')]
        for data, message in cases:
            with self.subTest(message=message):
                with self.assertRaises(ValidationError) as err:
                    save_record(data, self.path, overwrite=True)
                self.assertIn(message, str(err.exception))
                self.assertEqual(self.path.read_bytes(), before)
                with self.assertRaises(ValidationError):
                    render_mind_map(data)
                destination = Path(self.temp.name) / 'invalid-exports'
                with self.assertRaises(ValidationError):
                    export_record(data, destination)
                self.assertFalse(destination.exists())

    def test_malformed_json_duplicate_keys_and_invalid_load(self):
        with self.assertRaisesRegex(ValidationError, 'line 1, column'):
            parse_record('{broken')
        with self.assertRaisesRegex(ValidationError, 'duplicate field'):
            parse_record('{"title":"a","title":"b"}')
        self.path.write_text('[]', encoding='utf-8')
        with self.assertRaisesRegex(ValidationError, 'record'):
            load_record(self.path)
        self.path.write_bytes(b'\xff')
        with self.assertRaisesRegex(ValidationError, 'UTF-8'):
            load_record(self.path)

    def test_blank_capture_and_empty_synthesis_do_not_write(self):
        self.assertIsNone(capture_response('  ', self.path))
        self.assertFalse(self.path.exists())
        save_record(self.record, self.path)
        before = self.path.read_bytes()
        self.assertIsNone(capture_response('', self.path, overwrite=True))
        self.assertIsNone(apply_synthesis(self.record, '\n'))
        self.assertEqual(before, self.path.read_bytes())
        with self.assertRaises(FileExistsError):
            capture_response(json.dumps(self.record), self.path)
        with self.assertRaises(ValidationError):
            capture_response('{', self.path, overwrite=True)
        self.assertEqual(before, self.path.read_bytes())

    def test_missing_file_explains_start(self):
        with self.assertRaisesRegex(FileNotFoundError, 'Notebook 02'):
            load_record(self.path)

    def test_authored_synthesis_preserves_all_other_content(self):
        original = deepcopy(self.record)
        purple = deepcopy(self.record.pop('purple'))
        updated = apply_synthesis(self.record, json.dumps(purple))
        self.assertEqual(updated, original)
        self.assertNotIn('purple', self.record)
        self.assertIn(self.record['red']['items'][0], synthesis_prompt(self.record))
        for field in ('author', 'recommendation', 'uncertainties', 'decision_pivots'):
            broken = deepcopy(purple)
            broken.pop(field)
            with self.assertRaisesRegex(ValidationError, field):
                apply_synthesis(self.record, json.dumps(broken))

    def test_xml_and_html_escaping_and_long_content_layout(self):
        dangerous = '<script>alert("x")</script> & literal > text'
        self.record['title'] = dangerous
        self.record['white']['label'] = 'Long heading ' * 35
        self.record['white']['items'].append('Long text 健康 ' * 180)
        self.record['white']['items'].append('https://example.org/' + 'x' * 600)
        svg = ET.fromstring(render_mind_map(self.record))
        ns = {'s': 'http://www.w3.org/2000/svg'}
        cards = svg.findall('.//s:g[@role="group"]', ns)
        bounds = []
        for card in cards:
            rect = card.find('s:rect', ns)
            x, y, width, height = (float(rect.get(key)) for key in ('x', 'y', 'width', 'height'))
            bounds.append((x, y, width, height))
            for node in card.findall('s:text', ns):
                final_y = float(node.get('y')) + sum(float(span.get('dy')) for span in node)
                self.assertLess(final_y, y + height)
                self.assertGreater(float(node.get('x')), x)
                self.assertLess(float(node.get('x')), x + width)
        for i, a in enumerate(bounds):
            for b in bounds[i+1:]:
                overlap_x = max(a[0], b[0]) < min(a[0]+a[2], b[0]+b[2])
                overlap_y = max(a[1], b[1]) < min(a[1]+a[3], b[1]+b[3])
                self.assertFalse(overlap_x and overlap_y)
        html = to_html(self.record)
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)
        self.assertNotIn('<script>', to_markdown(self.record))

    def test_display_dimensions_do_not_change_drawing(self):
        full = ET.fromstring(render_mind_map(self.record))
        small = ET.fromstring(render_mind_map(self.record, width=350, height=220))
        self.assertEqual(full.get('viewBox'), small.get('viewBox'))
        self.assertEqual(list(full.itertext()), list(small.itertext()))
        self.assertEqual(small.get('width'), '350')
        for bad in (0, -1, True, '100%', float('nan'), float('inf')):
            for name in ('width', 'height'):
                with self.subTest(name=name, value=bad):
                    with self.assertRaisesRegex(ValidationError, name):
                        render_mind_map(self.record, **{name: bad})

    def test_explicit_purple_exclusion_keeps_source_and_other_sections(self):
        before = deepcopy(self.record)
        svg = render_mind_map(self.record, include_purple=False)
        self.assertNotIn('aria-label="Recommendation"', svg)
        self.assertIn('Possible outcomes', svg)
        self.assertEqual(self.record, before)

    def test_export_rejects_bad_stem_before_writing(self):
        for stem in ('../escape', 'a/b', 'a\\b', '', '..'):
            with self.assertRaises(ValidationError):
                export_record(self.record, Path(self.temp.name) / 'out', stem=stem)
        self.assertFalse((Path(self.temp.name) / 'out').exists())

    def test_competing_default_saves_have_only_one_winner(self):
        barrier = Barrier(2)
        original_write = decision_workflow._exclusive_write

        def synchronized_write(path, content):
            barrier.wait(timeout=10)
            return original_write(path, content)

        records = [deepcopy(self.record), deepcopy(self.record)]
        records[0]['title'] = 'First contender'
        records[1]['title'] = 'Second contender'

        def compete(record):
            try:
                save_record(record, self.path)
                return record
            except FileExistsError:
                return None

        with patch.object(decision_workflow, '_exclusive_write', side_effect=synchronized_write):
            with ThreadPoolExecutor(max_workers=2) as executor:
                results = list(executor.map(compete, records))
        winners = [result for result in results if result is not None]
        self.assertEqual(len(winners), 1)
        self.assertEqual(load_record(self.path), winners[0])
        save_record(self.record, self.path, overwrite=True)
        self.assertEqual(load_record(self.path), self.record)

    def test_export_write_failure_preserves_prior_complete_snapshots(self):
        directory = Path(self.temp.name) / 'exports'
        previous = export_record(self.record, directory)
        old_bytes = {path: path.read_bytes() for path in previous.values()}
        original_write = decision_workflow._atomic_write
        writes = 0

        def failing_write(path, content):
            nonlocal writes
            writes += 1
            if writes == 3:
                raise OSError('injected third-write failure')
            return original_write(path, content)

        updated = deepcopy(self.record)
        updated['title'] = 'Newer decision'
        with patch.object(decision_workflow, '_atomic_write', side_effect=failing_write):
            with self.assertRaisesRegex(OSError, 'third-write'):
                export_record(updated, directory)
        self.assertEqual(set(directory.iterdir()), {previous['json'].parent})
        self.assertTrue(all(path.read_bytes() == content for path, content in old_bytes.items()))
        current = export_record(updated, directory)
        self.assertNotEqual(current['json'].parent, previous['json'].parent)
        self.assertEqual({path.parent for path in current.values()}, {current['json'].parent})
        self.assertEqual(load_record(current['json']), updated)
        self.assertTrue(all(path.read_bytes() == content for path, content in old_bytes.items()))

    def test_notebook_refuses_synthesis_when_prompt_source_changes(self):
        notebook = json.loads((NOTEBOOKS / '06_purple_hat_orchestrator.ipynb').read_text(encoding='utf-8'))
        cells = {cell['id']: ''.join(cell['source']) for cell in notebook['cells']}
        for change in ('different question', 'edited evidence'):
            changed = deepcopy(self.record)
            if change == 'different question':
                changed['question'] = 'A different decision B?'
            else:
                changed['white']['items'].append('New evidence changes the same decision.')
            with self.subTest(change=change), chdir(self.temp.name), redirect_stdout(io.StringIO()):
                save_record(self.record, self.path, overwrite=True)
                namespace = {}
                exec(cells['purple-load'], namespace)
                save_record(changed, self.path, overwrite=True)
                before = self.path.read_bytes()
                namespace['PURPLE_RESPONSE'] = json.dumps(self.record['purple'])
                with self.assertRaisesRegex(ValidationError, 'changed since this prompt'):
                    exec(cells['purple-save'], namespace)
                self.assertEqual(self.path.read_bytes(), before)

    def test_uploaded_response_can_contain_triple_apostrophes(self):
        self.record['white']['items'].append("Valid JSON can preserve ''' literally.")
        response_path = Path(self.temp.name) / 'response.json'
        response_path.write_text(json.dumps(self.record, ensure_ascii=False), encoding='utf-8')
        capture_response(response_path.read_text(encoding='utf-8'), self.path)
        self.assertEqual(load_record(self.path), self.record)

    def test_new_synthesis_requires_author_but_legacy_loading_does_not(self):
        legacy = deepcopy(self.record)
        del legacy['purple']['author']
        self.assertEqual(validate_record(legacy), legacy)
        with self.assertRaisesRegex(ValidationError, 'purple.author'):
            apply_synthesis(self.record, json.dumps(legacy['purple']))

    def test_each_render_has_independent_accessible_ids(self):
        other = deepcopy(self.record)
        other['title'] = 'Another decision'
        maps = [ET.fromstring(render_mind_map(record)) for record in (self.record, other)]
        identities = [{node.get('id') for node in root.iter() if node.get('id')} for root in maps]
        self.assertFalse(identities[0] & identities[1])
        for root, ids in zip(maps, identities):
            self.assertEqual(set(root.get('aria-labelledby').split()), ids)

    def test_markdown_blank_lines_stay_inside_the_original_item(self):
        for newline in ('\n', '\r\n', '\r'):
            with self.subTest(newline=repr(newline)):
                first = 'First paragraph.\n\nSecond paragraph — café & 健康.\nLast line.'.replace('\n', newline)
                self.record['white']['items'] = [first, 'Next item.']
                rendered = MarkdownIt('commonmark').render(to_markdown(self.record))
                root = ET.fromstring('<div>' + rendered + '</div>')
                matching = [item for item in root.findall('.//li') if 'First paragraph.' in ''.join(item.itertext())]
                self.assertEqual(len(matching), 1)
                item = matching[0]
                self.assertEqual(' '.join(''.join(item.itertext()).split()), ' '.join(first.split()))
                self.assertEqual(len(item.findall('p')), 2)
                self.assertNotIn('Next item.', ''.join(item.itertext()))

    def test_all_views_preserve_every_supported_field_as_visible_content(self):
        punctuation = ' — café 健康 🌍 & <literal> [brackets] *stars* _underscores_ #hash `code` \\slash'

        def decorate(value):
            if isinstance(value, str):
                return value + punctuation
            if isinstance(value, dict):
                return {key: decorate(child) for key, child in value.items()}
            return [decorate(child) for child in value]

        record = decorate(self.record)
        record['purple']['next_steps'].append('A final eighth-plus conclusion' + punctuation)
        svg = ET.fromstring(render_mind_map(record))
        ns = {'s': 'http://www.w3.org/2000/svg'}
        # Aria attributes and SVG title/desc are deliberately excluded from this check.
        visible_svg = [''.join(''.join(span.itertext()) for span in text.findall('s:tspan', ns))
                       for text in svg.findall('.//s:text', ns)]
        compact_svg = [''.join(text.split()) for text in visible_svg]
        semantic = SemanticText()
        semantic.feed(to_html(record))
        self.assertEqual(semantic.sections, 9)
        markdown = SemanticText()
        markdown.feed(MarkdownIt('commonmark').render(to_markdown(record)))
        for text in all_text_values(record):
            with self.subTest(text=text[:70]):
                self.assertTrue(any(''.join(text.split()) in value for value in compact_svg), 'Missing visible SVG text')
                expected = ' '.join(text.split())
                self.assertTrue(any(expected in value for value in semantic.texts()), 'Missing semantic HTML text outside the map')
                self.assertTrue(any(expected in value for value in markdown.texts()), 'Missing rendered Markdown text')

    def test_html_css_is_scoped_to_the_decision_container(self):
        styles = re.findall(r'<style>(.*?)</style>', to_html(self.record), re.S)
        self.assertTrue(styles)
        for style in styles:
            for selectors in re.findall(r'([^{}]+)\{[^{}]*\}', style):
                # Commas within :is(...) do not start a new selector.
                for selector in re.split(r',(?![^(]*\))', selectors):
                    self.assertRegex(selector.strip(), r'^\.decision-record(?:$|[\s.:>#\[])')


if __name__ == '__main__':
    unittest.main()
