"""Execute the learning path in separate kernels and one isolated shared directory.

Optionally stage an entire book with clearly labeled demonstration outputs.
Learner notebooks and decision.json files in the source tree are never executed or changed.
"""
import argparse
import ast
from copy import deepcopy
import json
from pathlib import Path
import shutil
import tempfile

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'book' / 'notebooks'
NAMES = {
    '01': '01_six_thinking_hats_method.ipynb',
    '02': '02_prompt_and_capture.ipynb',
    '03': '03_render_mind_map.ipynb',
    '04': '04_global_health_example.ipynb',
    '05': '05_export_and_share.ipynb',
    '06': '06_purple_hat_orchestrator.ipynb',
}
SUPPORT_FILES = ('decision_workflow.py', 'six_hats_mindmap.py', 'examples/global_health.json')
INVENTORY = (*NAMES.values(), *SUPPORT_FILES)
INPUT_DEFAULTS = {
    '02': {'CENTRAL_QUESTION': 'What decision should we examine?',
           'CONTEXT': 'Describe the stakeholders, constraints, timescale, and evidence.',
           'GPT_RESPONSE': '', 'USE_DEMO': False, 'REPLACE_SAVED': False},
    '06': {'PURPLE_RESPONSE': ''},
}


def validate_clean_sources(source=SOURCE):
    """Fail rather than publish or erase saved learner inputs and execution outputs."""
    for relative in INVENTORY:
        if not (source / relative).is_file():
            raise ValueError(f'Missing required learner source: {relative}')
    for number, filename in NAMES.items():
        notebook = nbformat.read(source / filename, as_version=4)

        def reject(reason):
            raise ValueError(f'{filename}: {reason}. Build from clean learner sources in a separate checkout; '
                             'back up your work first. No learner content has been cleared.')

        if notebook.metadata.get('widgets'):
            reject('contains saved widget output')
        ids = [cell.get('id') for cell in notebook.cells]
        if any(not value for value in ids) or len(ids) != len(set(ids)):
            reject('cells require stable unique IDs')
        expected = INPUT_DEFAULTS.get(number)
        input_cells = []
        for cell in notebook.cells:
            if cell.cell_type != 'code':
                continue
            if cell.get('outputs') or cell.get('execution_count') is not None:
                reject('contains saved outputs or execution state')
            tagged = 'workflow-input' in cell.metadata.get('tags', [])
            if tagged:
                input_cells.append(cell)
            try:
                parsed = ast.parse(cell.source)
            except SyntaxError:
                reject('contains invalid Python or an edited response literal')
            if expected and not tagged and any(isinstance(node, ast.Name) and
                    isinstance(node.ctx, ast.Store) and node.id in expected for node in ast.walk(parsed)):
                reject('assigns response/settings outside the default input cell')
        if expected:
            if len(input_cells) != 1:
                reject('requires exactly one default input cell')
            values = {}
            for statement in ast.parse(input_cells[0].source).body:
                if not isinstance(statement, ast.Assign) or len(statement.targets) != 1 or not isinstance(statement.targets[0], ast.Name):
                    reject('contains nondefault input code')
                name = statement.targets[0].id
                if name in values:
                    reject('contains repeated input assignments')
                try:
                    values[name] = ast.literal_eval(statement.value)
                except (ValueError, TypeError):
                    reject('contains a nondefault response or file-read input')
            if values.keys() != expected.keys():
                reject('contains missing or additional input settings')
            for name, default in expected.items():
                value = values[name]
                if name.endswith('_RESPONSE') and isinstance(value, str):
                    value = value.strip()
                if type(value) is not type(default) or value != default:
                    reject(f'contains nondefault {name}')
        nbformat.validate(notebook)


def run(number, directory, input_source=None, *, demo=False):
    notebook = nbformat.read(SOURCE / NAMES[number], as_version=4)
    if demo:
        notebook.cells.insert(1, nbformat.v4.new_markdown_cell(
            '**BUILD DEMONSTRATION:** Outputs below were generated from the fictional '
            'global-health example in an isolated temporary folder. Open JupyterLite for your own decision.',
            id=f'build-demo-{number}'))
    if input_source is not None:
        cells = [cell for cell in notebook.cells if 'workflow-input' in cell.metadata.get('tags', [])]
        if len(cells) != 1:
            raise AssertionError(f'{number}: expected exactly one tagged input cell')
        cells[0].source = input_source
    nbformat.validate(notebook)
    NotebookClient(notebook, timeout=120, kernel_name='python3',
                   resources={'metadata': {'path': str(directory)}}).execute()
    return notebook


def verify(book_output=None):
    validate_clean_sources()
    if book_output:
        book_output = Path(book_output).resolve()
        # Staging must not overwrite the real book or its ancestors/descendants.
        source_book = (ROOT / 'book').resolve()
        if book_output == source_book or book_output in source_book.parents or source_book in book_output.parents:
            raise ValueError('Choose a staging destination outside the source book directory.')
        if book_output.exists():
            raise FileExistsError(f'{book_output} exists; choose a fresh staging directory.')
    with tempfile.TemporaryDirectory(prefix='seven-hats-demo-') as temporary:
        directory = Path(temporary)
        for relative in SUPPORT_FILES:
            destination = directory / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(SOURCE / relative, destination)
        rich = json.loads((directory / 'examples' / 'global_health.json').read_text(encoding='utf-8'))
        # Default starts are a separate acceptance path: no demo is silently selected.
        for number in ('02', '03', '05', '06'):
            fresh = run(number, directory)
            text = ''.join(output.get('text', '') for cell in fresh.cells
                           if cell.cell_type == 'code' for output in cell.get('outputs', []))
            assert 'Action needed:' in text, f'{number}: missing first-run recovery guidance'
            assert not (directory / 'decision.json').exists(), f'{number}: unexpectedly wrote a decision'
            assert not (directory / 'exports').exists(), f'{number}: exported without a decision'
        completed = {'01': run('01', directory, demo=True)}
        demo_input = "CENTRAL_QUESTION = 'Practice the illustrative scenario'\nCONTEXT = 'Fictional learning example'\nGPT_RESPONSE = ''\nUSE_DEMO = True\nREPLACE_SAVED = False"
        completed['02'] = run('02', directory, demo_input, demo=True)
        expected_six = deepcopy(rich)
        expected_six.pop('purple')
        saved = directory / 'decision.json'
        assert json.loads(saved.read_text(encoding='utf-8')) == expected_six
        completed['03'] = run('03', directory, demo=True)
        before = saved.read_bytes()
        run('06', directory)  # Empty synthesis must preserve the captured six-hat decision.
        assert saved.read_bytes() == before
        purple_input = 'PURPLE_RESPONSE = ' + repr(json.dumps(rich['purple'], ensure_ascii=False))
        completed['06'] = run('06', directory, purple_input, demo=True)
        assert json.loads(saved.read_text(encoding='utf-8')) == rich
        completed['05'] = run('05', directory, demo=True)
        before = saved.read_bytes()
        completed['04'] = run('04', directory, demo=True)
        assert saved.read_bytes() == before
        demo_exports = list((directory / 'exports').glob('*/six-hats.json'))
        assert len(demo_exports) == 1
        demo_snapshot = demo_exports[0].parent
        assert json.loads(demo_exports[0].read_text(encoding='utf-8')) == rich
        for suffix in ('json', 'svg', 'md', 'html'):
            assert (demo_snapshot / f'six-hats.{suffix}').stat().st_size > 0
        demo_bytes = {path: path.read_bytes() for path in demo_snapshot.iterdir()}

        # An unrelated user decision must survive demo reruns and empty synthesis.
        custom = deepcopy(expected_six)
        custom['title'] = 'Preserve my unrelated café decision'
        custom['question'] = 'Which library workshop should we run?'
        custom['white']['items'].append('A user-only seventh-plus entry that must survive.')
        custom_json = json.dumps(custom, ensure_ascii=False)
        custom_input = "CENTRAL_QUESTION = 'Workshop'\nCONTEXT = 'Custom'\nGPT_RESPONSE = " + repr(custom_json) + "\nUSE_DEMO = False\nREPLACE_SAVED = True"
        run('02', directory, custom_input)
        before = saved.read_bytes()
        run('02', directory, demo_input)
        run('02', directory)  # Empty pasted response and default settings.
        run('03', directory)
        run('06', directory)
        run('04', directory)
        run('05', directory)
        assert saved.read_bytes() == before
        custom_exports = set((directory / 'exports').glob('*/six-hats.json')) - set(demo_exports)
        assert len(custom_exports) == 1
        assert json.loads(custom_exports.pop().read_text(encoding='utf-8')) == custom
        assert all(path.read_bytes() == contents for path, contents in demo_bytes.items())

        if book_output:
            shutil.copytree(ROOT / 'book', book_output,
                            ignore=shutil.ignore_patterns('_build', 'notebooks', '__pycache__', '.ipynb_checkpoints'))
            for relative in SUPPORT_FILES:
                destination = book_output / 'notebooks' / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(SOURCE / relative, destination)
            for number, notebook in completed.items():
                nbformat.write(notebook, book_output / 'notebooks' / NAMES[number])
    print('Verified all six notebooks in fresh kernels: capture, reopen, authored synthesis, exports, and preservation of unrelated data.')
    if book_output:
        print(f'Staged demonstration book: {book_output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--book-output', help='Fresh staging directory for a book with executed demo outputs')
    parser.add_argument('--check-sources-only', action='store_true', help='Check publishing inputs without executing notebooks')
    options = parser.parse_args()
    if options.check_sources_only:
        validate_clean_sources()
        print('Clean learner sources confirmed; no content changed.')
    else:
        verify(options.book_output)
