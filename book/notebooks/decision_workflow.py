"""Validated, portable decision records. Runtime: Python standard library only."""
from base64 import b64encode
from copy import deepcopy
from html import escape
import json
from pathlib import Path
import shutil
import tempfile
import uuid

HATS = ("white", "red", "black", "yellow", "green", "blue")
FOCUS = {
    "white": "Facts, evidence, knowns and unknowns",
    "red": "Feelings, intuition and values",
    "black": "Risks, constraints and failure modes",
    "yellow": "Benefits, value and opportunities",
    "green": "Creative alternatives and experiments",
    "blue": "Process, decisions and next steps",
    "purple": "Integrate perspectives into an authored synthesis (project extension)",
}
PURPLE_LISTS = ("themes", "tensions", "blind_spots", "uncertainties", "decision_pivots", "next_steps")
DEFAULT_RECORD = Path("decision.json")


class ValidationError(ValueError):
    """An actionable error in a decision or synthesis field."""


def _object(value, path, allowed, required=()):
    if not isinstance(value, dict):
        raise ValidationError(f"{path}: expected an object, got {type(value).__name__}.")
    missing = set(required) - value.keys()
    if missing:
        raise ValidationError(f"{path}: missing required field(s): {', '.join(sorted(missing))}.")
    unknown = value.keys() - set(allowed)
    if unknown:
        raise ValidationError(f"{path}: unrecognized field(s): {', '.join(map(str, unknown))}. See the schema; no content has been discarded.")


def _string(value, path, nonempty=False):
    if not isinstance(value, str):
        raise ValidationError(f"{path}: expected a string, got {type(value).__name__}.")
    if nonempty and not value.strip():
        raise ValidationError(f"{path}: enter non-empty text.")
    for char in value:
        number = ord(char)
        if not (number in (9, 10, 13) or 0x20 <= number <= 0xD7FF or
                0xE000 <= number <= 0xFFFD or 0x10000 <= number <= 0x10FFFF):
            raise ValidationError(f"{path}: contains an invalid XML character U+{number:04X}; remove it before saving.")


def _strings(value, path):
    if not isinstance(value, list):
        raise ValidationError(f"{path}: expected a list of strings.")
    for index, item in enumerate(value):
        _string(item, f"{path}[{index}]", nonempty=True)


def _section(section, path, purple=False):
    allowed = {"label", "focus", "items", "questions"}
    if purple:
        allowed.update(PURPLE_LISTS + ("recommendation", "author"))
    _object(section, path, allowed, ("items",))
    for key, value in section.items():
        if key in ("items", "questions") + PURPLE_LISTS:
            _strings(value, f"{path}.{key}")
        else:
            _string(value, f"{path}.{key}", nonempty=True)


def validate_record(data):
    """Validate without normalizing, truncating or mutating the caller's data."""
    required = ("title", "question") + HATS
    optional = ("subtitle", "context", "demo_notice", "evidence", "purple", "outcomes")
    _object(data, "record", required + optional, required)
    for key in ("title", "question", "subtitle", "context", "demo_notice"):
        if key in data:
            _string(data[key], key, nonempty=key in ("title", "question"))
    for hat in HATS:
        _section(data[hat], hat)
    if "purple" in data:
        _section(data["purple"], "purple", purple=True)
    if "outcomes" in data:
        _strings(data["outcomes"], "outcomes")
    if "evidence" in data:
        if not isinstance(data["evidence"], list):
            raise ValidationError("evidence: expected a list of evidence objects.")
        for index, entry in enumerate(data["evidence"]):
            path = f"evidence[{index}]"
            _object(entry, path, ("claim", "source", "status", "notes"), ("claim", "source", "status"))
            for key, value in entry.items():
                _string(value, f"{path}.{key}", nonempty=True)
    return data


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError(f"JSON: duplicate field {key!r}; keep one value so nothing is silently overwritten.")
        result[key] = value
    return result


def parse_json(text):
    if not isinstance(text, str):
        raise ValidationError("response: expected JSON text.")
    try:
        return json.loads(text, object_pairs_hook=_unique_pairs)
    except json.JSONDecodeError as exc:
        raise ValidationError(f"JSON line {exc.lineno}, column {exc.colno}: {exc.msg}. Paste only JSON, without Markdown fences.") from exc


def parse_record(text):
    return validate_record(parse_json(text))


def _atomic_write(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        temporary.write_text(content, encoding="utf-8")
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def save_record(data, path=DEFAULT_RECORD, *, overwrite=False):
    validate_record(data)
    path = Path(path)
    content = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if overwrite:
        _atomic_write(path, content)
    else:
        try:
            _exclusive_write(path, content)
        except FileExistsError as exc:
            raise FileExistsError(f"{path} already exists. Reopen it, choose another filename, or set overwrite=True after reviewing your changes.") from exc
    return path


def _exclusive_write(path, content):
    """The filesystem decides which initial writer wins; never replace an existing file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("x", encoding="utf-8")
    try:
        with handle:
            handle.write(content)
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def load_record(path=DEFAULT_RECORD):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"No saved decision at {path}. Run Notebook 02, paste your JSON (or explicitly choose its demo), and save first.")
    try:
        return parse_record(path.read_text(encoding="utf-8"))
    except UnicodeError as exc:
        raise ValidationError(f"{path}: expected a UTF-8 JSON file.") from exc


def capture_response(response, path=DEFAULT_RECORD, *, overwrite=False):
    """A blank input is a no-op; saving a replacement requires explicit opt-in."""
    if not isinstance(response, str):
        raise ValidationError("response: expected JSON text.")
    if not response.strip():
        return None
    data = parse_record(response)
    save_record(data, path, overwrite=overwrite)
    return data


def new_record(title, question, context=""):
    record = {"title": title, "question": question, "context": context}
    record.update({hat: {"label": f"{hat.title()} Hat", "focus": FOCUS[hat], "items": [], "questions": []} for hat in HATS})
    return validate_record(record)


def capture_prompt(question, context=""):
    schema = new_record("Replace with a concise decision title", question, context)
    return ("Use Edward de Bono's original Six Thinking Hats to examine this decision. "
            "Return only valid JSON using the shape below. Preserve the question and context. "
            "Fill each hat's items and questions with substantive text; there is no six-item limit. "
            "Separate facts, assumptions and unknowns. Do not invent evidence or citations. "
            "Optional evidence is a list of objects with claim, source, status and optional notes strings. "
            "Record source context and verification limits; source links alone are not evidence. "
            "Optional outcomes is a list of strings. Do not add other fields.\n\n" +
            json.dumps(schema, ensure_ascii=False, indent=2))


def synthesis_prompt(data):
    validate_record(data)
    template = {"label": "Purple Hat — Orchestrator (project extension)", "author": "Identify the learner or model and review status",
                "items": ["Integrated conclusion supported by named perspectives"],
                "questions": ["Unresolved decision question"],
                "recommendation": "A conditional recommendation grounded in this record"}
    template.update({key: ["Replace with a substantive statement"] for key in PURPLE_LISTS})
    return ("Author a Purple Hat synthesis, a project extension to de Bono's six hats. "
            "Return ONLY the Purple object using the template. Connect actual statements across the hats; "
            "include red-hat values and feelings. Explain tensions, blind spots, uncertainties, a conditional "
            "recommendation, decision pivots (what evidence would change it), and actionable next steps. "
            "Do not count items as a substitute for synthesis or invent facts.\n\nTemplate:\n" +
            json.dumps(template, ensure_ascii=False, indent=2) + "\n\nDecision:\n" +
            json.dumps(data, ensure_ascii=False, indent=2))


def apply_synthesis(data, response):
    """Return a new record only for an authored/pasted Purple object; blank is no-op."""
    validate_record(data)
    if not isinstance(response, str):
        raise ValidationError("purple response: expected JSON text.")
    if not response.strip():
        return None
    purple = parse_json(response)
    _section(purple, "purple", purple=True)
    for field in ("author", "recommendation", "uncertainties", "decision_pivots"):
        if not purple.get(field):
            raise ValidationError(f"purple.{field}: include a substantive value before saving a synthesis.")
    result = deepcopy(data)
    result["purple"] = purple
    return validate_record(result)


def record_sections(data, *, include_purple=True):
    """One content inventory shared by text, HTML and SVG outputs."""
    validate_record(data)
    sections = []
    for hat in HATS + (("purple",) if include_purple and "purple" in data else ()):
        section = data[hat]
        blocks = []
        if section.get("focus"):
            blocks.append(("Focus", [section["focus"]]))
        blocks.append(("Items", section["items"]))
        if "questions" in section:
            blocks.append(("Key questions", section["questions"]))
        if hat == "purple":
            for key in ("author", "recommendation") + PURPLE_LISTS:
                if key in section:
                    value = section[key]
                    blocks.append((key.replace("_", " ").capitalize(), [value] if isinstance(value, str) else value))
        sections.append((hat, section.get("label", f"{hat.title()} Hat"), blocks))
    if data.get("evidence"):
        blocks = []
        for index, entry in enumerate(data["evidence"], 1):
            blocks.append((f"Evidence {index}", [f"{key.capitalize()}: {value}" for key, value in entry.items()]))
        sections.append(("evidence", "Evidence and source context", blocks))
    if "outcomes" in data:
        sections.append(("outcomes", "Possible outcomes", [("Outcomes", data["outcomes"])]))
    return sections


def _md(value):
    # Keep arbitrary learner text literal in Markdown viewers, including raw HTML.
    text = escape(value.replace("\r\n", "\n").replace("\r", "\n"), quote=False)
    for character in "\\`*_{}[]()#+-.!|":
        text = text.replace(character, "\\" + character)
    return text.replace("\n", "  \n")


def to_markdown(data):
    validate_record(data)
    lines = [f"# {_md(data['title'])}", "", f"**Decision question:** {_md(data['question'])}", ""]
    for key in ("subtitle", "context", "demo_notice"):
        if data.get(key):
            lines.extend([f"**{key.replace('_', ' ').capitalize()}:** {_md(data[key])}", ""])
    for _, title, blocks in record_sections(data):
        lines.extend([f"## {_md(title)}", ""])
        for label, values in blocks:
            lines.extend([f"### {label}", ""])
            lines.extend(["- " + _md(value).replace("\n", "\n  ") for value in values] or ["No entries recorded."])
            lines.append("")
    lines.extend(["Six Thinking Hats: Edward de Bono. Purple Hat: project extension. Evidence is not automatically verified.", ""])
    return "\n".join(lines)


def to_html(data):
    validate_record(data)
    from six_hats_mindmap import render_mind_map
    body = [f"<h1>{escape(data['title'])}</h1>", f"<p><strong>Decision question:</strong> {escape(data['question'])}</p>"]
    for key in ("subtitle", "context", "demo_notice"):
        if data.get(key):
            body.append(f"<p><strong>{key.replace('_', ' ').capitalize()}:</strong> {escape(data[key])}</p>")
    for hat, title, blocks in record_sections(data):
        body.append(f'<section aria-labelledby="{hat}-heading"><h2 id="{hat}-heading">{escape(title)}</h2>')
        for label, values in blocks:
            body.append(f"<h3>{escape(label)}</h3>")
            body.append("<ul>" + "".join(f"<li>{escape(value)}</li>" for value in values) + "</ul>" if values else "<p>No entries recorded.</p>")
        body.append("</section>")
    body.append("<details><summary>Open scalable mind map</summary>" + render_mind_map(data) + "</details>")
    body.append("<footer>Six Thinking Hats: Edward de Bono. Purple Hat: project extension. Evidence is not automatically verified.</footer>")
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            f"<title>{escape(data['title'])}</title><style>"
            ".decision-record{font-family:system-ui,sans-serif;line-height:1.65;color:#17243b;background:white;max-width:70rem;margin:2rem auto;padding:0 1rem}"
            ".decision-record section{border-top:2px solid #ccd5e2;margin-top:2rem}"
            ".decision-record :is(h1,h2,h3,p,li){white-space:pre-wrap;overflow-wrap:anywhere}"
            ".decision-record svg{max-width:100%;height:auto}.decision-record summary{cursor:pointer}.decision-record footer{margin-top:2rem}"
            '</style></head><body><main class="decision-record">' + "".join(body) + "</main></body></html>")


def export_record(data, directory="exports", *, stem="six-hats"):
    validate_record(data)
    if not isinstance(stem, str) or not stem or Path(stem).name != stem or any(char in stem for char in '\\/:*?"<>|') or stem in (".", ".."):
        raise ValidationError("stem: use a filename without path separators or reserved filename characters.")
    from six_hats_mindmap import render_mind_map
    # Prepare and validate every representation before touching the destination.
    contents = {"json": json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                "svg": render_mind_map(data), "md": to_markdown(data), "html": to_html(data)}
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    # Exclusive directory creation isolates this attempt from every earlier snapshot.
    snapshot = Path(tempfile.mkdtemp(prefix=f"{stem}-", dir=directory))
    paths = {}
    try:
        for suffix, content in contents.items():
            path = snapshot / f"{stem}.{suffix}"
            _atomic_write(path, content)
            paths[suffix] = path
    except BaseException:
        # Only this newly created snapshot is eligible for cleanup.
        if snapshot.resolve().parent == directory:
            shutil.rmtree(snapshot)
        raise
    return paths


def download_links(paths):
    """Embedded downloads work in JupyterLite and in pre-rendered teaching outputs."""
    types = {"json": "application/json", "svg": "image/svg+xml", "md": "text/markdown", "html": "text/html"}
    links = []
    for suffix, path in paths.items():
        path = Path(path)
        payload = b64encode(path.read_bytes()).decode("ascii")
        links.append(f'<li><a download="{escape(path.name)}" href="data:{types[suffix]};charset=utf-8;base64,{payload}">Download {escape(path.name)}</a></li>')
    return '<nav aria-label="Download decision files"><ul>' + "".join(links) + "</ul></nav>"
