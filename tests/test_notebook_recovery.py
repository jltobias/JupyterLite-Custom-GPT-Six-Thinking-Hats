"""Exercise actual notebook cells in fresh namespaces and isolated learner folders."""
from contextlib import chdir, redirect_stdout
import io
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / 'book' / 'notebooks'
sys.path.insert(0, str(SOURCE))
from decision_workflow import load_record, save_record
import decision_workflow


class NotebookRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        shutil.copytree(SOURCE / 'examples', self.directory / 'examples')
        self.decision = self.directory / 'decision.json'
        self.rich = load_record(SOURCE / 'examples/global_health.json')
        self.cells = {}
        for path in SOURCE.glob('*.ipynb'):
            for cell in json.loads(path.read_text(encoding='utf-8'))['cells']:
                if cell['cell_type'] == 'code':
                    self.cells[cell['id']] = ''.join(cell['source'])

    def execute(self, cell, namespace=None):
        namespace = {} if namespace is None else namespace
        output = io.StringIO()
        with chdir(self.directory), redirect_stdout(output), patch('IPython.display.display') as display:
            exec(compile(self.cells[cell], cell, 'exec'), namespace)
        return namespace, output.getvalue(), display

    def test_action_cells_after_restart_explain_prerequisites(self):
        for cell in ('capture-prompt', 'capture-save', 'render-map', 'render-accessible',
                     'export-files', 'purple-load', 'purple-save'):
            with self.subTest(cell=cell):
                _, message, display = self.execute(cell)
                self.assertIn('Action needed:', message)
                display.assert_not_called()
                self.assertFalse(self.decision.exists())
                self.assertFalse((self.directory / 'exports').exists())

    def test_independent_example_export_does_not_need_previous_cell(self):
        save_record(self.rich, self.decision)
        before = self.decision.read_bytes()
        namespace, message, display = self.execute('example-export')
        self.assertIn('Example snapshot folder:', message)
        self.assertEqual(set(namespace['example_paths']), {'json', 'svg', 'md', 'html'})
        self.assertEqual(load_record(namespace['example_paths']['json']), self.rich)
        display.assert_called_once()
        self.assertEqual(self.decision.read_bytes(), before)

    def test_failed_reload_never_displays_previous_successful_record(self):
        save_record(self.rich, self.decision)
        for cell in ('render-map', 'render-accessible', 'export-files', 'purple-load'):
            with self.subTest(cell=cell):
                save_record(self.rich, self.decision, overwrite=True)
                namespace, _, _ = self.execute(cell)
                self.decision.write_text('{broken', encoding='utf-8')
                _, message, display = self.execute(cell, namespace)
                self.assertIn('Action needed:', message)
                self.assertIn('JSON line', message)
                display.assert_not_called()
                key = 'source_record' if cell == 'purple-load' else 'record'
                self.assertIsNone(namespace[key])
                self.assertEqual(self.decision.read_text(), '{broken')

    def test_capture_reports_bad_json_and_protected_overwrite_without_changes(self):
        save_record(self.rich, self.decision)
        before = self.decision.read_bytes()
        for response, expected in (('{broken', 'JSON line'), ('```json\n{}\n```', 'JSON line'),
                                   (json.dumps(self.rich), 'already exists')):
            with self.subTest(expected=expected):
                namespace = {'GPT_RESPONSE': response, 'USE_DEMO': False, 'REPLACE_SAVED': False,
                             'data': self.rich}
                _, message, _ = self.execute('capture-save', namespace)
                self.assertIn(expected, message)
                self.assertIsNone(namespace['data'])
                self.assertEqual(self.decision.read_bytes(), before)

    def test_synthesis_needs_successful_prompt_and_preserves_decision(self):
        six_hats = {key: value for key, value in self.rich.items() if key != 'purple'}
        save_record(six_hats, self.decision)
        before = self.decision.read_bytes()
        response = json.dumps(self.rich['purple'])
        for source in ({}, {'source_record': None}):
            with self.subTest(source=source):
                namespace = {**source, 'PURPLE_RESPONSE': response}
                _, message, display = self.execute('purple-save', namespace)
                self.assertIn('run the prompt cell first', message)
                display.assert_not_called()
                self.assertEqual(self.decision.read_bytes(), before)
        namespace, _, _ = self.execute('purple-load')
        namespace['PURPLE_RESPONSE'] = '{broken'
        _, message, display = self.execute('purple-save', namespace)
        self.assertIn('JSON line', message)
        display.assert_not_called()
        self.assertEqual(self.decision.read_bytes(), before)
        # A corrected response recovers in the same kernel without losing the prompt snapshot.
        namespace['PURPLE_RESPONSE'] = response
        _, message, display = self.execute('purple-save', namespace)
        self.assertIn('Saved reviewed Purple synthesis', message)
        display.assert_called_once()
        self.assertEqual(load_record(self.decision), self.rich)
        before_retry = self.decision.read_bytes()
        _, message, display = self.execute('purple-save', namespace)
        self.assertIn('already saved; no file changed', message)
        self.assertEqual(self.decision.read_bytes(), before_retry)

    def test_quoted_false_cannot_enable_demo_or_overwrite(self):
        for switch in ('USE_DEMO', 'REPLACE_SAVED'):
            for exists in (False, True):
                with self.subTest(switch=switch, exists=exists):
                    self.decision.unlink(missing_ok=True)
                    if exists:
                        save_record(self.rich, self.decision)
                    before = self.decision.read_bytes() if exists else None
                    changed = {**self.rich, 'title': 'Must not replace saved work'}
                    namespace = {'GPT_RESPONSE': json.dumps(changed) if exists else '',
                                 'USE_DEMO': False, 'REPLACE_SAVED': False, switch: 'False'}
                    _, message, _ = self.execute('capture-save', namespace)
                    self.assertIn('True or False without quotes', message)
                    self.assertEqual(self.decision.read_bytes() if self.decision.exists() else None, before)

    def test_documented_upload_clears_old_response_on_failed_read_and_recovers(self):
        six_hats = {key: value for key, value in self.rich.items() if key != 'purple'}
        for number, variable, filename, action in (
            ('02', 'GPT_RESPONSE', 'response.json', 'capture-save'),
            ('06', 'PURPLE_RESPONSE', 'purple-response.json', 'purple-save')):
            with self.subTest(number=number):
                save_record(six_hats, self.decision, overwrite=True)
                before = self.decision.read_bytes()
                path = next(SOURCE.glob(number + '*.ipynb'))
                markdown = '\n'.join(''.join(c['source']) for c in
                                     json.loads(path.read_text(encoding='utf-8'))['cells']
                                     if c['cell_type'] == 'markdown')
                blocks = re.findall(r'```python\n(.*?)\n```', markdown, re.S)
                source = next(block for block in blocks if f'{variable} = None' in block)
                response = json.dumps(self.rich if number == '02' else self.rich['purple'])
                namespace = {variable: response, 'USE_DEMO': False, 'REPLACE_SAVED': True,
                             'source_record': six_hats}
                with chdir(self.directory), redirect_stdout(io.StringIO()):
                    exec(source, namespace)
                self.assertIsNone(namespace[variable])
                _, message, display = self.execute(action, namespace)
                self.assertIn('Action needed:', message)
                self.assertEqual(self.decision.read_bytes(), before)
                (self.directory / filename).write_text(response, encoding='utf-8')
                with chdir(self.directory):
                    exec(source, namespace)
                self.execute(action, namespace)
                self.assertEqual(load_record(self.decision), self.rich)

    def test_download_link_failure_preserves_successful_snapshot(self):
        save_record(self.rich, self.decision)
        for cell, key in (('export-files', 'paths'), ('example-export', 'example_paths')):
            with self.subTest(cell=cell), patch('decision_workflow.download_links', side_effect=OSError('read failed')):
                namespace, message, display = self.execute(cell)
                self.assertIn('Files saved, but embedded download links', message)
                self.assertIn('file browser', message)
                self.assertNotIn('did not finish', message)
                self.assertTrue(all(path.is_file() for path in namespace[key].values()))
                self.assertEqual(load_record(namespace[key]['json']), self.rich)
                display.assert_not_called()

    def test_write_failures_preserve_data_and_allow_retry(self):
        six_hats = {key: value for key, value in self.rich.items() if key != 'purple'}
        for cell, key in (('capture-save', 'data'), ('purple-save', 'updated'),
                          ('export-files', 'paths'), ('example-export', 'example_paths')):
            with self.subTest(cell=cell):
                save_record(six_hats, self.decision, overwrite=True)
                before = self.decision.read_bytes()
                previous = decision_workflow.export_record(self.rich, self.directory / 'earlier-exports')
                previous_bytes = {path: path.read_bytes() for path in previous.values()}
                namespace = {'GPT_RESPONSE': json.dumps(self.rich), 'USE_DEMO': False,
                             'REPLACE_SAVED': True, 'PURPLE_RESPONSE': json.dumps(self.rich['purple']),
                             'source_record': six_hats}
                original_write = decision_workflow._atomic_write
                writes = 0

                def fail_write(path, content):
                    nonlocal writes
                    writes += 1
                    if writes == (3 if 'export' in cell else 1):
                        raise OSError('storage unavailable')
                    return original_write(path, content)

                before_files = set(self.directory.rglob('*'))
                with patch('decision_workflow._atomic_write', side_effect=fail_write):
                    _, message, display = self.execute(cell, namespace)
                self.assertIn('Action needed:', message)
                self.assertIn('storage unavailable', message)
                self.assertIsNone(namespace[key])
                self.assertEqual(self.decision.read_bytes(), before)
                self.assertTrue(all(path.read_bytes() == value for path, value in previous_bytes.items()))
                self.assertFalse(any(path.is_file() for path in set(self.directory.rglob('*')) - before_files))
                display.assert_not_called()
                _, message, _ = self.execute(cell, namespace)
                self.assertNotIn('Action needed:', message)
                self.assertIsNotNone(namespace[key])

    def test_capture_default_then_explicit_demo_recovers_without_restart(self):
        namespace, _, _ = self.execute('capture-input')
        _, message, _ = self.execute('capture-save', namespace)
        self.assertIn('no decision saved yet', message)
        self.assertFalse(self.decision.exists())
        namespace['USE_DEMO'] = True
        _, message, _ = self.execute('capture-save', namespace)
        self.assertIn('ILLUSTRATIVE DEMO saved', message)
        expected = {key: value for key, value in self.rich.items() if key != 'purple'}
        self.assertEqual(load_record(self.decision), expected)
        for cell in ('render-map', 'render-accessible', 'export-files'):
            with self.subTest(cell=cell):
                _, message, display = self.execute(cell)
                self.assertNotIn('Action needed:', message)
                display.assert_called_once()


if __name__ == '__main__':
    unittest.main()
