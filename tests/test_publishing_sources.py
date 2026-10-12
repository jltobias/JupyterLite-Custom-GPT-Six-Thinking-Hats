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
from verify_notebooks import (GRAPHIC_PRACTICE_ITEM, GRAPHIC_PRACTICE_NOTICE,
    INVENTORY, NAMES, SOURCE, code_fingerprint, normalize_ast,
    validate_clean_sources, verify_graphic_exports)
sys.path.insert(0, str(SOURCE))
from decision_workflow import export_record, load_record


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

    def test_ast_normalization_ignores_absent_empty_fields_and_locations_but_preserves_content(self):
        source = "def example():\n    return [b'PNG', None, 1j, ...]\n"
        complete = ast.parse(source)
        sparse = deepcopy(complete)
        for node in ast.walk(sparse):
            for name, child in list(ast.iter_fields(node)):
                if child is None or child == []:
                    delattr(node, name)
        ast.increment_lineno(complete, 10)
        self.assertEqual(normalize_ast(complete), normalize_ast(sparse))
        normalized = normalize_ast(ast.parse("items = []"))
        self.assertEqual(normalized, {'node': 'Module', 'fields': {'body': [
            {'node': 'Assign', 'fields': {
                'targets': [{'node': 'Name', 'fields': {'id': 'items', 'ctx': {'node': 'Store', 'fields': {}}}}],
                'value': {'node': 'List', 'fields': {'ctx': {'node': 'Load', 'fields': {}}}}}}]}})
        self.assertEqual(code_fingerprint(source), code_fingerprint('# comment\n' + source.replace("b'PNG'", 'b"PNG"')))
        self.assertNotEqual(code_fingerprint(source), code_fingerprint(source.replace('PNG', 'PRIVATE')))
        self.assertNotEqual(code_fingerprint('items = []'), code_fingerprint('items = [None]'))

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
            'exports/six-hats-secret/six-hats.json', 'example-exports', 'graphic-exports',
            'graphic-exports/graphic-practice-secret/graphic-practice.json',
            '07_private.ipynb', '02_prompt_and_capture.ipynb.backup',
            'private.py', 'examples/private.json', 'examples/global_health.json.backup',
            'examples/graphic_source.json.backup', 'examples/plugin-output-example.png.backup',
            'examples/private.png',
            'private/02_prompt_and_capture.ipynb', 'private', '__pycache__',
        }
        actual = {path for path in candidates if not any(re.findall(pattern, '/' + path) for pattern in patterns)}
        self.assertEqual(actual, allowed)
        self.assertEqual(len(INVENTORY), 11)

    def test_edited_graphic_literals_fail_without_erasing_private_work(self):
        source = load_record(SOURCE / 'examples/graphic_source.json')
        edits = [('graphic-' + hat, source[hat]['items'][0], 'Private learner statement')
                 for hat in ('white', 'red', 'black', 'yellow', 'green', 'blue', 'purple')]
        edits += [('graphic-outcomes', source['outcomes'][0], 'Private outcome'),
                  ('graphic-synthesis', 'Try a two-week teaching exercise', 'Private recommendation'),
                  ('graphic-practice-copy', GRAPHIC_PRACTICE_NOTICE, 'Private practice context'),
                  ('graphic-practice-edit', GRAPHIC_PRACTICE_ITEM, 'Learner exercise: PRIVATE retained prefix')]
        path = self.source / NAMES['04']
        original = path.read_bytes()
        for ident, before, after in edits:
            with self.subTest(ident=ident):
                path.write_bytes(original)
                notebook = nbformat.read(path, as_version=4)
                cell = next(cell for cell in notebook.cells if cell.id == ident)
                self.assertIn(before, cell.source)
                cell.source = cell.source.replace(before, after, 1)
                nbformat.write(notebook, path)
                private_bytes = path.read_bytes()
                with self.assertRaisesRegex(ValueError, 'nondefault graphic lesson'):
                    validate_clean_sources(self.source)
                self.assertEqual(path.read_bytes(), private_bytes)

    def test_export_check_rejects_prefix_preserving_private_text_and_other_record_changes(self):
        source = load_record(SOURCE / 'examples/graphic_source.json')
        expected = deepcopy(source)
        expected['demo_notice'] = GRAPHIC_PRACTICE_NOTICE
        expected['green']['items'][0] = GRAPHIC_PRACTICE_ITEM
        directory = Path(self.temp.name) / 'execution'
        paths = export_record(expected, directory / 'graphic-exports', stem='graphic-practice')
        verify_graphic_exports(directory, source)
        for section in ('green', 'red'):
            with self.subTest(section=section):
                private = deepcopy(expected)
                private[section]['items'][0] = 'Learner exercise: PRIVATE retained prefix'
                paths['json'].write_text(json.dumps(private), encoding='utf-8')
                before = paths['json'].read_bytes()
                with self.assertRaisesRegex(AssertionError, 'full clean default record'):
                    verify_graphic_exports(directory, source)
                self.assertEqual(paths['json'].read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
