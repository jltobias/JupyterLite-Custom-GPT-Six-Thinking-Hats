"""Targeted checks for clean notebook publishing inputs and the Lite inventory."""
from copy import deepcopy
import ast
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest

import nbformat

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from verify_notebooks import INVENTORY, NAMES, SOURCE, validate_clean_sources


class PublishingSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name) / 'notebooks'
        for relative in INVENTORY:
            destination = self.source / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(SOURCE / relative, destination)

    def test_clean_defaults_pass_without_changing_sources(self):
        before = {path: path.read_bytes() for path in self.source.rglob('*') if path.is_file()}
        validate_clean_sources(self.source)
        self.assertTrue(all(path.read_bytes() == content for path, content in before.items()))

    def test_saved_outputs_and_execution_state_fail_without_erasing_work(self):
        path = self.source / NAMES['03']
        original = nbformat.read(path, as_version=4)
        for field in ('outputs', 'execution_count'):
            notebook = deepcopy(original)
            cell = next(cell for cell in notebook.cells if cell.cell_type == 'code')
            if field == 'outputs':
                cell.outputs = [nbformat.v4.new_output('stream', name='stdout', text='PRIVATE learner output')]
            else:
                cell.execution_count = 1
            nbformat.write(notebook, path)
            before = path.read_bytes()
            with self.assertRaisesRegex(ValueError, 'saved outputs or execution state'):
                validate_clean_sources(self.source)
            self.assertEqual(path.read_bytes(), before)

    def test_nondefault_response_and_settings_fail_without_erasing_work(self):
        edits = [
            ('02', "GPT_RESPONSE = '{\"private\": \"response\"}'"),
            ('02', 'USE_DEMO = True'),
            ('02', 'REPLACE_SAVED = True'),
            ('02', "CENTRAL_QUESTION = 'Private decision question'"),
            ('02', "CONTEXT = 'Private context'"),
            ('06', "PURPLE_RESPONSE = '{\"private\": \"synthesis\"}'"),
            ('06', "PURPLE_RESPONSE = Path('private.json').read_text()"),
        ]
        for number, assignment in edits:
            with self.subTest(assignment=assignment):
                path = self.source / NAMES[number]
                original = (SOURCE / NAMES[number]).read_bytes()
                path.write_bytes(original)
                notebook = nbformat.read(path, as_version=4)
                cell = next(cell for cell in notebook.cells if 'workflow-input' in cell.metadata.get('tags', []))
                variable = assignment.split('=', 1)[0].strip()
                statement = next(node for node in ast.parse(cell.source).body
                                 if isinstance(node, ast.Assign) and node.targets[0].id == variable)
                lines = cell.source.splitlines()
                lines[statement.lineno - 1:statement.end_lineno] = [assignment]
                cell.source = '\n'.join(lines)
                nbformat.write(notebook, path)
                before = path.read_bytes()
                with self.assertRaisesRegex(ValueError, 'clean learner sources'):
                    validate_clean_sources(self.source)
                self.assertEqual(path.read_bytes(), before)
                path.write_bytes(original)

    def test_lite_configuration_admits_only_the_explicit_inventory(self):
        config = json.loads((ROOT / 'jupyter_lite_config.json').read_text(encoding='utf-8'))
        patterns = config['LiteBuildConfig']['extra_ignore_contents']
        allowed = set(INVENTORY) | {'examples'}
        candidates = allowed | {
            'decision.json', 'response.json', 'purple-response.json', 'exports',
            'exports/six-hats-secret/six-hats.json', 'example-exports',
            '07_private.ipynb', '02_prompt_and_capture.ipynb.backup',
            'private.py', 'examples/private.json', 'examples/global_health.json.backup',
            'private/02_prompt_and_capture.ipynb', 'private', '__pycache__',
        }
        actual = {path for path in candidates if not any(re.findall(pattern, '/' + path) for pattern in patterns)}
        self.assertEqual(actual, allowed)
        self.assertEqual(len(INVENTORY), 9)


if __name__ == '__main__':
    unittest.main()
