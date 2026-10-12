"""Execute the learning path in separate kernels and one isolated shared directory.

Optionally stage an entire book with clearly labeled demonstration outputs.
Learner notebooks and decision.json files in the source tree are never executed or changed.
"""
import argparse
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
from xml.etree import ElementTree as ET

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
SUPPORT_FILES = ('decision_workflow.py', 'six_hats_mindmap.py', 'examples/global_health.json',
                 'examples/graphic_source.json', 'examples/plugin-output-example.png')
INVENTORY = (*NAMES.values(), *SUPPORT_FILES)
INPUT_DEFAULTS = {
    '02': {'CENTRAL_QUESTION': 'What decision should we examine?',
           'CONTEXT': 'Describe the stakeholders, constraints, timescale, and evidence.',
           'GPT_RESPONSE': '', 'USE_DEMO': False, 'REPLACE_SAVED': False},
    '06': {'PURPLE_RESPONSE': ''},
}
GRAPHIC_PRACTICE_ITEM = 'Learner exercise: build a tiny JupyterLite comparison of AI and non-AI explanations using fictional district counts.'
GRAPHIC_PRACTICE_NOTICE = 'AUTHORED PRACTICE — copied from the current lesson, which may already include learner-authored edits. Further practice changes belong to the learner, not the original graphic. This is not a verified assessment or a completed synthesis.'


def normalize_ast(value):
    """Canonical AST data, independent of ast.dump's version-specific empty fields."""
    if isinstance(value, ast.AST):
        return {'node': type(value).__name__, 'fields': {
            name: normalize_ast(child) for name, child in ast.iter_fields(value)
            if child is not None and child != []}}
    if isinstance(value, list):
        return [normalize_ast(child) for child in value]
    if isinstance(value, bytes):
        return {'bytes': value.hex()}
    if isinstance(value, complex):
        return {'complex': [value.real, value.imag]}
    if value is Ellipsis:
        return {'ellipsis': True}
    return value


def code_fingerprint(source):
    """Ignore formatting/comments while preserving every executable literal and statement."""
    normalized = json.dumps(normalize_ast(ast.parse(source)), sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


# Approved clean Notebook 04 code, including all editable hat, Purple, outcome,
# synthesis and practice literals. Update intentionally when shipping new defaults;
# never regenerate these from learner files during verification or publishing.
GRAPHIC_CODE_DEFAULTS = {
    "graphic-original": "03e7f25a3e6dae530b729176ba5d9060297db873e9674285eadf6cb4b2e877f8",
    "graphic-source-view": "25424c80249b4cdb4560e3a1228f8cef90af84dc203c788d7064cd7738b4e89a",
    "graphic-setup": "5a7ddc2a838d655a876b817777b6b21b77faecb421e68d8e60bc68a08a6045fe",
    "graphic-white": "c70269530e0657a0f012a1ac05240dc8bc1a250a15b1fe669ed60bab149e02bb",
    "graphic-red": "c0f08035778f73050522c634ef2866635ea81858dd2af5f5a2f7755071e7a86b",
    "graphic-black": "d837e20813cc32a122a2ed0b3b8eadbc0446cd20d992f483812534c2ea30a6de",
    "graphic-yellow": "e89bd8b24152bd415b6bc652d3355c156d32d2b135e1d1b10376149628ca52f5",
    "graphic-green": "d06f0393da91d1297465644eba07a08707a3c68e018467226370d07938b6f5b1",
    "graphic-blue": "c3ffdbcdfee92068a8645665ad2ca24803498496ddb0f89d955aaee12748c653",
    "graphic-purple": "87e4f88d3086d4c886dc0af6324e20a6634ce25cc6e678c76bd46110c718240f",
    "graphic-outcomes": "efbf8afec2be12a91341b7df47612706830ffc537acff3b3e4b385e0d1ca6b30",
    "graphic-synthesis": "248c4e06efddfa119e26c7f15f635f90f1b84bb5ec8a2c5f7b3f4e8d59962f5d",
    "example-render": "9fbc11bc8bcf08bb0a388de36abed629e176051471684404019f6ee75c85219f",
    "graphic-practice-copy": "4582c1c026e7318013546065b93ae85bf017a19e0bfb8b15e1b608899d4974f7",
    "graphic-practice-edit": "db6238db0804ab0f2ae98c59537f151a539a04b0a2bd3866c90bec55b5478eee",
    "graphic-practice-render": "836e6f144a04d3081a6996207ce139d9cfe473c7fe126115de4bed7a6bb7c9c9",
    "graphic-export": "c065153e70cbee101f614b75e5f268ce5a539f30e83b14e63a451f28e2c331cf",
    "example-export": "afaecd34e0df35b90191388aa197e96e993f74f3730489586f63cb07f991b290"
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
        graphic_code = {}
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
            if number == '04':
                graphic_code[cell.id] = code_fingerprint(cell.source)
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
        if number == '04' and graphic_code != GRAPHIC_CODE_DEFAULTS:
            reject('contains nondefault graphic lesson code or editable inputs')
        nbformat.validate(notebook)


def run(number, directory, input_source=None, *, demo=False):
    notebook = nbformat.read(SOURCE / NAMES[number], as_version=4)
    if demo:
        notice = ('the supplied graphic reconstruction and explicitly labeled authored practice/adaptation'
                  if number == '04' else 'the fictional global-health example')
        notebook.cells.insert(1, nbformat.v4.new_markdown_cell(
            '**BUILD DEMONSTRATION:** Outputs below were generated from ' + notice +
            ' in an isolated temporary folder. Open JupyterLite to edit and run the notebook.',
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


def verify_graphic_outputs(notebook, directory):
    """Inspect executed outputs, not just successful execution, of the build-along."""
    cells = {cell.id: cell for cell in notebook.cells}
    source = json.loads((directory / 'examples/graphic_source.json').read_text(encoding='utf-8'))
    namespace = {'s': 'http://www.w3.org/2000/svg'}

    def output_text(ident, mime='text/html'):
        return ''.join(output.get('data', {}).get(mime, '') for output in cells[ident].get('outputs', []))

    assert 'data:image/png;base64,' in output_text('graphic-original'), '04: missing local original image'
    stages = ['graphic-setup', *['graphic-' + hat for hat in ('white', 'red', 'black', 'yellow', 'green', 'blue')],
              'graphic-purple', 'graphic-outcomes']
    for count, ident in enumerate(stages):
        html = output_text(ident)
        svg = re.search(r'<svg\b.*?</svg>', html, re.S)
        assert svg, f'04: {ident} did not demonstrate a map'
        root = ET.fromstring(svg.group())
        assert len(root.findall('.//s:g[@role="group"]', namespace)) == count + 1, ident
        assert len(root.findall('.//s:path', namespace)) == count, ident
        assert ('Partial' if count < 8 else 'Complete') in root.find('s:desc', namespace).text, ident
    labels = {node.get('aria-label') for node in root.iter() if node.get('aria-label')}
    for hat in ('white', 'red', 'black', 'yellow', 'green', 'blue', 'purple'):
        for value in source[hat].values():
            for text in value if isinstance(value, list) else [value]:
                assert text in labels, f'04: final reconstruction omitted {hat} content'
    assert source['question'] in labels
    assert all(outcome in labels for outcome in source['outcomes'])
    assert 'two-week' in output_text('graphic-synthesis'), '04: authored synthesis comparison missing'
    assert 'four-week' in output_text('example-render'), '04: fictional adaptation comparison missing'
    assert 'Learner exercise:' in output_text('graphic-practice-render'), '04: practice edit was not rendered'
    assert output_text('graphic-export').count(' download=') == 4, '04: lesson downloads missing'
    verify_graphic_exports(directory, source)


def verify_graphic_exports(directory, source):
    """A familiar prefix is insufficient: every field must match the approved practice."""
    expected = deepcopy(source)
    expected['demo_notice'] = GRAPHIC_PRACTICE_NOTICE
    expected['green']['items'][0] = GRAPHIC_PRACTICE_ITEM
    lesson_exports = list((directory / 'graphic-exports').glob('*/graphic-practice.json'))
    assert lesson_exports, '04: no lesson snapshot was created'
    for path in lesson_exports:
        practice = json.loads(path.read_text(encoding='utf-8'))
        assert practice == expected, '04: exported practice differs from the full clean default record'
        for suffix in ('json', 'svg', 'md', 'html'):
            assert path.with_suffix('.' + suffix).stat().st_size > 0


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
        support_bytes = {directory / relative: (directory / relative).read_bytes() for relative in SUPPORT_FILES}
        # Default starts are a separate acceptance path: no demo is silently selected.
        for number in ('02', '03', '05', '06'):
            fresh = run(number, directory)
            text = ''.join(output.get('text', '') for cell in fresh.cells
                           if cell.cell_type == 'code' for output in cell.get('outputs', []))
            assert 'Action needed:' in text, f'{number}: missing first-run recovery guidance'
            assert not (directory / 'decision.json').exists(), f'{number}: unexpectedly wrote a decision'
            assert not (directory / 'exports').exists(), f'{number}: exported without a decision'
        fresh_graphic = run('04', directory)
        verify_graphic_outputs(fresh_graphic, directory)
        assert not (directory / 'decision.json').exists(), '04: unexpectedly wrote a personal decision'
        graphic_bytes = {path: path.read_bytes() for path in directory.glob('graphic-exports/*/*')}
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
        verify_graphic_outputs(completed['04'], directory)
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
        assert all(path.read_bytes() == contents for path, contents in graphic_bytes.items())
        assert all(path.read_bytes() == contents for path, contents in support_bytes.items())

        if book_output:
            shutil.copytree(ROOT / 'book', book_output,
                            ignore=shutil.ignore_patterns('_build', 'notebooks', '__pycache__', '.ipynb_checkpoints'))
            for relative in SUPPORT_FILES:
                destination = book_output / 'notebooks' / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(SOURCE / relative, destination)
            for number, notebook in completed.items():
                nbformat.write(notebook, book_output / 'notebooks' / NAMES[number])
    print('Verified all six notebooks in fresh kernels: capture, reopen, authored synthesis, staged graphic reconstruction, edited lesson exports, and preservation of source fixtures, prior exports, and unrelated data.')
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
