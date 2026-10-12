"""Source fidelity, progressive SVG views, and actual build-along notebook actions."""
from contextlib import chdir, redirect_stdout
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'book' / 'notebooks'
sys.path.insert(0, str(SOURCE))
from decision_workflow import HATS, ValidationError, export_record, load_record
from six_hats_mindmap import render_mind_map
import decision_workflow

NS = {'s': 'http://www.w3.org/2000/svg'}
STAGES = ['graphic-' + hat for hat in HATS] + ['graphic-purple', 'graphic-outcomes']
PRACTICE = ['graphic-practice-copy', 'graphic-practice-edit', 'graphic-practice-render']


class GraphicSourceTests(unittest.TestCase):
    def test_fixture_matches_every_meaningful_transcribed_panel(self):
        text = (ROOT / 'book/graphic-text.md').read_text(encoding='utf-8')
        panels = dict(re.findall(r'^## ([^\n]+)\n(.*?)(?=^## |\Z)', text, re.M | re.S))
        source = load_record(SOURCE / 'examples/graphic_source.json')
        self.assertIn('**' + source['title'] + '**', panels['Center: subject and purpose'])
        self.assertIn(source['subtitle'], panels['Center: subject and purpose'])
        for hat in HATS:
            panel = panels[source[hat]['label']]
            items, questions = panel.split('### Key Questions')
            self.assertEqual(source[hat]['focus'], panel.strip().splitlines()[0])
            self.assertEqual(source[hat]['items'], re.findall(r'^- (.+)', items, re.M))
            self.assertEqual(source[hat]['questions'], re.findall(r'^- (.+)', questions, re.M))
            self.assertEqual(len(source[hat]['items']), 7)
            self.assertEqual(len(source[hat]['questions']), 4)
        purple = panels['Purple Hat — Orchestrator']
        self.assertEqual(source['question'], re.search(r'### Central Question\n\n(.+)', purple)[1])
        self.assertEqual(source['purple']['focus'], re.search(r'### Role\n\n(.+)', purple)[1])
        self.assertEqual(source['purple']['items'], re.findall(r'^- (.+)', purple.split('### Key Outputs')[1], re.M))
        self.assertEqual(len(source['purple']['items']), 6)
        self.assertNotIn('recommendation', source['purple'])
        self.assertNotIn('author', source['purple'])
        self.assertEqual(source['outcomes'], re.findall(r'^- (.+)', panels['Possible Outcomes'], re.M))
        self.assertEqual(len(source['outcomes']), 6)
        self.assertIn(purple.strip().splitlines()[0], source['context'])

    def test_original_png_is_unchanged_and_identical_to_bundled_copy(self):
        original = (ROOT / 'book/images/plugin-output-example.png').read_bytes()
        self.assertEqual(original, (SOURCE / 'examples/plugin-output-example.png').read_bytes())
        self.assertEqual(hashlib.sha256(original).hexdigest(),
                         '979853bfd774236a6a807d00a826e0cc6fccfc982e21f9fc3b8aa6c2a09a33bf')


class ProgressiveRendererTests(unittest.TestCase):
    def setUp(self):
        self.source = load_record(SOURCE / 'examples/graphic_source.json')

    def test_accumulating_panels_connect_without_clipping_and_describe_omissions(self):
        names = [*HATS, 'purple', 'outcomes']
        for count in range(len(names) + 1):
            with self.subTest(count=count):
                root = ET.fromstring(render_mind_map(self.source, visible_sections=names[:count]))
                cards = root.findall('.//s:g[@role="group"]', NS)
                self.assertEqual(len(cards), count + 1)
                self.assertEqual(len(root.findall('.//s:path', NS)), count)
                labels = {card.get('aria-label') for card in cards}
                expected = {self.source['title']} | {
                    self.source[hat]['label'] if hat != 'outcomes' else 'Possible outcomes'
                    for hat in names[:count]}
                self.assertEqual(labels, expected)
                description = root.find('s:desc', NS).text
                self.assertIn('Partial' if count < len(names) else 'Complete', description)
                if count < len(names):
                    for hat in names[count:]:
                        self.assertIn(hat, description)
                if count == 0:
                    self.assertIn('decision question only', description)
                self.assertEqual(set(root.get('aria-labelledby').split()),
                                 {root.find('s:title', NS).get('id'), root.find('s:desc', NS).get('id')})
                view_height = float(root.get('viewBox').split()[3])
                bounds = []
                for card in cards:
                    rect = card.find('s:rect', NS)
                    x, y, width, height = (float(rect.get(key)) for key in ('x', 'y', 'width', 'height'))
                    self.assertLess(y + height, view_height)
                    bounds.append((x, y, width, height))
                    for node in card.findall('s:text', NS):
                        baseline = float(node.get('y')) + sum(float(span.get('dy')) for span in node)
                        self.assertLess(baseline, y + height)
                for i, a in enumerate(bounds):
                    for b in bounds[i + 1:]:
                        self.assertFalse(max(a[0], b[0]) < min(a[0]+a[2], b[0]+b[2]) and
                                         max(a[1], b[1]) < min(a[1]+a[3], b[1]+b[3]))

    def test_selection_is_explicit_validated_and_does_not_mutate_or_skip_validation(self):
        before = deepcopy(self.source)
        for bad in ('white', True, {}, {'white'}, [1], ['white', 'white'], ['pink'], ['decision'], ['evidence']):
            with self.subTest(bad=bad), self.assertRaisesRegex(ValidationError, 'visible_sections'):
                render_mind_map(self.source, visible_sections=bad)
        with self.assertRaisesRegex(ValidationError, 'conflicts'):
            render_mind_map(self.source, include_purple=False, visible_sections=['purple'])
        invalid = deepcopy(self.source)
        invalid['red']['items'] = False
        with self.assertRaisesRegex(ValidationError, 'red.items'):
            render_mind_map(invalid, visible_sections=[])
        self.assertEqual(self.source, before)
        selected = ET.fromstring(render_mind_map(self.source, visible_sections=('blue', 'white')))
        self.assertEqual([node.get('aria-label') for node in selected.findall('.//s:g[@role="group"]', NS)],
                         [self.source['title'], self.source['white']['label'], self.source['blue']['label']])
        default = ET.fromstring(render_mind_map(self.source))
        explicit = ET.fromstring(render_mind_map(self.source, visible_sections=[*HATS, 'purple', 'outcomes']))
        self.assertEqual(list(default.itertext()), list(explicit.itertext()))
        self.assertEqual(default.get('viewBox'), explicit.get('viewBox'))


class GraphicNotebookTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        shutil.copytree(SOURCE / 'examples', self.directory / 'examples')
        notebook = json.loads((SOURCE / '04_global_health_example.ipynb').read_text(encoding='utf-8'))
        self.cells = {cell['id']: ''.join(cell['source']) for cell in notebook['cells'] if cell['cell_type'] == 'code'}
        self.fixture = self.directory / 'examples/graphic_source.json'
        self.source = load_record(self.fixture)
        self.namespace = {}

    def execute(self, ident, namespace=None, *, replacement=None):
        namespace = self.namespace if namespace is None else namespace
        output = io.StringIO()
        with chdir(self.directory), redirect_stdout(output), patch('IPython.display.display') as display:
            namespace['display'] = display  # Helpers defined by earlier cells use this shared binding.
            exec(compile(replacement or self.cells[ident], ident, 'exec'), namespace)
        return output.getvalue(), display

    def construct(self, practice=False):
        for ident in ['graphic-setup', *STAGES, *(PRACTICE if practice else [])]:
            message, _ = self.execute(ident)
            self.assertNotIn('Action needed:', message)
            if ident in ['graphic-setup', *STAGES]:
                root = ET.fromstring(self.namespace['lesson_svg'])
                expected = 'Complete' if ident == 'graphic-outcomes' else 'Partial'
                self.assertIn(expected, root.find('s:desc', NS).text)

    def test_run_all_never_opens_personal_decision_and_preserves_fixtures_and_prior_exports(self):
        decision = self.directory / 'decision.json'
        decision.write_bytes(b'PRIVATE: not even valid JSON')
        previous = export_record(self.source, self.directory / 'graphic-exports', stem='earlier')
        preserved = {path: path.read_bytes() for path in [decision, *self.directory.glob('examples/*'), *previous.values()]}
        original_open = Path.open

        def guard(path, *args, **kwargs):
            if path.name == 'decision.json':
                raise AssertionError('Notebook 04 must not read or write personal decision.json')
            return original_open(path, *args, **kwargs)

        with patch.object(Path, 'open', guard):
            for ident in self.cells:
                message, _ = self.execute(ident)
                self.assertNotIn('Action needed:', message, ident)
        self.assertEqual(self.namespace['lesson'], self.source)
        self.assertNotIn('recommendation', self.namespace['lesson']['purple'])
        self.assertIn('two-week', self.namespace['synthesis_example']['purple']['recommendation'])
        self.assertEqual(load_record(self.namespace['lesson_paths']['json']), self.namespace['practice'])
        self.assertNotEqual(self.namespace['practice']['green']['items'][0], self.source['green']['items'][0])
        self.assertEqual(load_record(self.namespace['example_paths']['json']),
                         load_record(self.directory / 'examples/global_health.json'))
        self.assertTrue(all(path.read_bytes() == content for path, content in preserved.items()))

    def test_restart_actions_explain_setup_and_independent_views_still_work(self):
        for ident in [*STAGES, 'graphic-synthesis', *PRACTICE, 'graphic-export']:
            with self.subTest(ident=ident):
                message, display = self.execute(ident, {})
                self.assertIn('Action needed:', message)
                display.assert_not_called()
        for ident in ['graphic-original', 'graphic-source-view', 'example-render', 'example-export']:
            with self.subTest(ident=ident):
                message, display = self.execute(ident, {})
                self.assertNotIn('Action needed:', message)
                self.assertTrue(display.called)
        self.assertFalse((self.directory / 'decision.json').exists())
        self.assertFalse((self.directory / 'graphic-exports').exists())

    def test_rerunning_a_hat_replaces_content_and_preserves_other_perspectives(self):
        self.construct()
        self.namespace['lesson']['red']['items'][0] = 'My retained feeling'
        self.namespace['lesson']['white']['items'].append('Temporary extra')
        self.execute('graphic-white')
        self.execute('graphic-white')
        self.assertEqual(self.namespace['lesson']['white'], self.source['white'])
        self.assertEqual(self.namespace['lesson']['red']['items'][0], 'My retained feeling')
        self.assertEqual(len(self.namespace['visible_sections']), 8)
        self.assertEqual(len(set(self.namespace['visible_sections'])), 8)

    def test_invalid_editable_panel_is_transactional_and_corrected_rerun_recovers(self):
        self.construct()
        retained = self.cells['graphic-red'].replace(self.source['red']['items'][0], 'A retained learner feeling')
        self.execute('graphic-red', replacement=retained)
        for name in [*HATS, 'purple', 'outcomes']:
            with self.subTest(name=name):
                ident = 'graphic-' + name
                first = self.source[name][0] if name == 'outcomes' else self.source[name]['items'][0]
                before = deepcopy(self.namespace['lesson'])
                before_sections = self.namespace['visible_sections'].copy()
                invalid = self.cells[ident].replace(first, '', 1)
                message, display = self.execute(ident, replacement=invalid)
                self.assertIn('Action needed:', message)
                self.assertIn('non-empty', message)
                display.assert_not_called()
                self.assertEqual(self.namespace['lesson'], before)
                self.assertEqual(self.namespace['visible_sections'], before_sections)
                corrected = self.cells[ident].replace(first, 'Corrected learner ' + name, 1)
                message, _ = self.execute(ident, replacement=corrected)
                self.assertNotIn('Action needed:', message)
                self.assertIn('Corrected learner ' + name, self.namespace['lesson_svg'])
                self.assertIn('LEARNER-AUTHORED MODIFICATIONS', self.namespace['lesson']['demo_notice'])
                if name != 'outcomes':
                    self.assertIn('[Learner-authored edit]', self.namespace['lesson'][name]['label'])

    def test_invalid_practice_edit_keeps_valid_work_and_corrected_literal_recovers(self):
        self.construct(practice=True)
        self.namespace['practice']['red']['items'][0] = 'Keep this earlier practice edit'
        before = deepcopy(self.namespace['practice'])
        default = before['green']['items'][0]
        message, display = self.execute('graphic-practice-edit', replacement=self.cells['graphic-practice-edit'].replace(default, ''))
        self.assertIn('Action needed:', message)
        display.assert_not_called()
        self.assertEqual(self.namespace['practice'], before)
        message, _ = self.execute('graphic-practice-edit', replacement=self.cells['graphic-practice-edit'].replace(default, 'A corrected practice idea'))
        self.assertNotIn('Action needed:', message)
        self.assertEqual(self.namespace['practice']['red']['items'][0], 'Keep this earlier practice edit')
        self.assertEqual(self.namespace['practice']['green']['items'][0], 'A corrected practice idea')

    def test_later_lesson_edits_are_labeled_and_practice_changes_only_on_explicit_refresh(self):
        self.construct(practice=True)
        before_practice = deepcopy(self.namespace['practice'])
        edited = self.cells['graphic-white'].replace(self.source['white']['items'][0], 'My later reconstruction edit')
        self.execute('graphic-white', replacement=edited)
        self.assertEqual(self.namespace['practice'], before_practice)
        self.assertIn('Learner-authored edit', self.namespace['lesson']['white']['label'])
        self.assertNotIn('SOURCE RECONSTRUCTION', self.namespace['lesson']['demo_notice'])
        self.execute('graphic-synthesis')
        self.assertIn('may include learner-authored edits', self.namespace['synthesis_example']['demo_notice'])
        self.execute('graphic-practice-copy')
        self.assertEqual(self.namespace['practice']['white']['items'][0], 'My later reconstruction edit')
        self.assertEqual(self.namespace['practice']['green']['items'][0], self.source['green']['items'][0])
        self.execute('graphic-practice-edit')
        self.assertTrue(self.namespace['practice']['green']['items'][0].startswith('Learner exercise:'))

    def test_readable_companions_preserve_literal_text_and_have_unique_heading_ids(self):
        self.construct()
        literal = 'A <literal> & value [brackets] _marks_ *stars*'
        self.namespace['lesson']['white']['items'][0] = literal
        seen_ids = set()
        for ident in ('graphic-source-view', 'graphic-outcomes', 'graphic-synthesis', 'example-render'):
            with self.subTest(ident=ident):
                _, display = self.execute(ident)
                companions = [call.args[0].data for call in display.call_args_list
                              if '<main class="decision-record">' in call.args[0].data]
                self.assertEqual(len(companions), 1)
                root = ET.fromstring('<div>' + companions[0] + '</div>')
                headings = root.findall('.//h2')
                self.assertGreaterEqual(len(headings), 8)
                ids = {heading.get('id') for heading in headings}
                self.assertFalse(ids & seen_ids)
                seen_ids.update(ids)
                self.assertEqual({section.get('aria-labelledby') for section in root.findall('.//section')}, ids)
                items = [''.join(item.itertext()) for item in root.findall('.//li')]
                if ident in ('graphic-outcomes', 'graphic-synthesis'):
                    self.assertIn(literal, items)
                if ident == 'graphic-synthesis':
                    self.assertIn(self.namespace['synthesis_example']['purple']['recommendation'], items)

    def test_missing_and_invalid_source_cannot_present_stale_views_or_exports_and_retry_recovers(self):
        original = self.fixture.read_bytes()
        for bad in (None, b'{broken', b'\xff', b'{}'):
            with self.subTest(bad=bad):
                self.fixture.write_bytes(original)
                self.construct(practice=True)
                self.execute('graphic-source-view')
                self.execute('graphic-export')
                previous = {path: path.read_bytes() for path in self.directory.glob('graphic-exports/*/*')}
                if bad is None:
                    self.fixture.unlink()
                else:
                    self.fixture.write_bytes(bad)
                for ident in ['graphic-source-view', 'graphic-white', 'graphic-practice-render', 'graphic-export']:
                    message, display = self.execute(ident)
                    self.assertIn('Action needed:', message)
                    self.assertIn('graphic_source.json', message)
                    display.assert_not_called()
                self.assertIsNone(self.namespace['source_view'])
                self.assertIsNone(self.namespace['lesson_svg'])
                self.assertIsNone(self.namespace['lesson_paths'])
                self.assertEqual(set(self.directory.glob('graphic-exports/*/*')), set(previous))
                self.assertTrue(all(path.read_bytes() == content for path, content in previous.items()))
                self.fixture.write_bytes(original)
                for ident in ['graphic-source-view', 'graphic-practice-render', 'graphic-export']:
                    message, display = self.execute(ident)
                    self.assertNotIn('Action needed:', message)
                    self.assertTrue(display.called)

    def test_incomplete_setup_and_changed_source_are_actionable(self):
        incomplete = deepcopy(self.source)
        del incomplete['subtitle']
        self.fixture.write_text(json.dumps(incomplete), encoding='utf-8')
        message, display = self.execute('graphic-setup')
        self.assertIn('incomplete', message)
        self.assertIsNone(self.namespace['lesson'])
        display.assert_not_called()
        incomplete = deepcopy(self.source)
        del incomplete['purple']['label']
        self.fixture.write_text(json.dumps(incomplete), encoding='utf-8')
        message, display = self.execute('graphic-setup')
        self.assertIn('purple.label', message)
        self.assertIn('restore examples/graphic_source.json', message)
        self.assertIsNone(self.namespace['lesson'])
        display.assert_not_called()
        self.fixture.write_text(json.dumps(self.source), encoding='utf-8')
        self.execute('graphic-setup')
        message, display = self.execute('graphic-purple')
        self.assertIn('preceding steps', message)
        display.assert_not_called()
        changed = deepcopy(self.source)
        changed['question'] = 'A changed source question?'
        self.fixture.write_text(json.dumps(changed), encoding='utf-8')
        message, display = self.execute('graphic-white')
        self.assertIn('source changed since setup', message)
        self.assertIn('Restore canonical examples/graphic_source.json', message)
        self.assertIn('Customize the lesson or practice assignments', message)
        self.assertNotIn('start a new reconstruction', message)
        display.assert_not_called()

    def test_edit_cell_rerender_and_separate_snapshot_contain_learner_change(self):
        self.construct(practice=True)
        self.execute('graphic-export')
        earlier = {path: path.read_bytes() for path in self.namespace['lesson_paths'].values()}
        source_bytes = self.fixture.read_bytes()
        original_text = self.namespace['practice']['green']['items'][0]
        replacement = self.cells['graphic-practice-edit'].replace(original_text, 'My edited learning experiment')
        self.execute('graphic-practice-edit', replacement=replacement)
        self.execute('graphic-practice-render')
        self.assertIn('My edited learning experiment', self.namespace['lesson_svg'])
        self.execute('graphic-export')
        paths = self.namespace['lesson_paths']
        self.assertEqual(load_record(paths['json'])['green']['items'][0], 'My edited learning experiment')
        for suffix in ('svg', 'html', 'md'):
            self.assertIn('My edited learning experiment', paths[suffix].read_text(encoding='utf-8'))
        self.assertTrue(all(path.read_bytes() == content for path, content in earlier.items()))
        self.assertEqual(self.fixture.read_bytes(), source_bytes)
        self.assertEqual(self.namespace['lesson'], self.source)
        self.assertFalse((self.directory / 'decision.json').exists())

    def test_lesson_write_failure_and_download_link_failure_preserve_snapshots(self):
        self.construct(practice=True)
        self.execute('graphic-export')
        earlier = {path: path.read_bytes() for path in self.namespace['lesson_paths'].values()}
        original_write = decision_workflow._atomic_write
        writes = 0

        def failure(path, content):
            nonlocal writes
            writes += 1
            if writes == 3:
                raise OSError('storage unavailable')
            original_write(path, content)

        with patch('decision_workflow._atomic_write', side_effect=failure):
            message, display = self.execute('graphic-export')
        self.assertIn('Action needed:', message)
        self.assertIsNone(self.namespace['lesson_paths'])
        display.assert_not_called()
        self.assertEqual(set(self.directory.glob('graphic-exports/*/*')), set(earlier))
        self.assertTrue(all(path.read_bytes() == content for path, content in earlier.items()))
        with patch('decision_workflow.download_links', side_effect=OSError('link failure')):
            message, display = self.execute('graphic-export')
        self.assertIn('Files saved, but embedded download links', message)
        self.assertIsNotNone(self.namespace['lesson_paths'])
        display.assert_not_called()


if __name__ == '__main__':
    unittest.main()
