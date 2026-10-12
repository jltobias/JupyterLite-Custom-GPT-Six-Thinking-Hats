"""Adaptive, connected SVG maps using only the Python standard library."""
from html import escape
import math
import re
import unicodedata
import uuid

from decision_workflow import record_sections, validate_record, ValidationError

HAT_META = {
    "white": ("White Hat — Facts & Evidence", "#f7f7f7", "#596570"),
    "red": ("Red Hat — Feelings & Intuition", "#ffe9ed", "#ad1938"),
    "black": ("Black Hat — Risks & Challenges", "#eeeeee", "#222222"),
    "yellow": ("Yellow Hat — Benefits & Opportunities", "#fff4bf", "#775700"),
    "green": ("Green Hat — Creativity & Alternatives", "#e7f8ea", "#17652f"),
    "blue": ("Blue Hat — Process & Next Steps", "#e4f1ff", "#125e9e"),
    "purple": ("Purple Hat — Orchestrator (project extension)", "#efe4ff", "#6f2dbd"),
    "evidence": ("Evidence and source context", "#f5f7fa", "#526075"),
    "outcomes": ("Possible outcomes", "#edf3ff", "#375d91"),
    "decision": ("Decision", "#f1f6ff", "#254b7d"),
}


def _units(text):
    return sum(0 if unicodedata.combining(char) else 2 if unicodedata.east_asian_width(char) in "WF" else 1 for char in text)


def _wrap(text, limit):
    """Wrap every character, including long URLs and wide Unicode, without a slice limit."""
    lines = []
    for paragraph in text.expandtabs(4).splitlines() or [""]:
        line = ""
        for token in re.findall(r"\S+\s*", paragraph):
            if line and _units(line + token.rstrip()) > limit:
                lines.append(line.rstrip())
                line = ""
            for char in token:
                if _units(line + char) > limit:
                    lines.append(line.rstrip())
                    line = ""
                line += char
        lines.append(line.rstrip())
    return lines


def _measure(title, blocks, width):
    entries = []
    cursor = 30

    def add(text, size=14, bold=False, bullet=False):
        nonlocal cursor
        indent = 16 if bullet else 0
        limit = max(8, int((width - 48 - indent) / (size * .66)))
        lines = _wrap(text, limit)
        step = math.ceil(size * 1.45)
        entries.append((cursor, text, lines, size, bold, indent, step))
        cursor += len(lines) * step + 8

    add(title, 20, True)
    for label, values in blocks:
        add(label, 15, True)
        for value in values or ["No entries recorded."]:
            add(value, bullet=True)
        cursor += 6
    return cursor + 12, entries


def _card(hat, title, blocks, x, y, width):
    height, entries = _measure(title, blocks, width)
    _, fill, stroke = HAT_META[hat]
    out = [f'<g role="group" aria-label="{escape(title, quote=True)}">',
           f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="18" fill="{fill}" stroke="{stroke}" stroke-width="2"/>']
    for offset, original, lines, size, bold, indent, step in entries:
        tx, ty = x + 24 + indent, y + offset
        if indent:
            out.append(f'<circle cx="{x+27}" cy="{ty-5}" r="2.5" fill="{stroke}"/>')
        out.append(f'<text x="{tx}" y="{ty}" font-size="{size}" font-weight="{"bold" if bold else "normal"}" aria-label="{escape(original, quote=True)}">')
        for index, line in enumerate(lines):
            out.append(f'<tspan x="{tx}" dy="{0 if index == 0 else step}">{escape(line)}</tspan>')
        out.append('</text>')
    out.append('</g>')
    return height, "".join(out)


def _dimension(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise ValidationError(f"{name}: expected a finite positive number of pixels.")


def render_mind_map(data, width=1400, height=None, include_purple=True, *, visible_sections=None):
    """Render complete records, optionally showing selected panels for a teaching stage.

    The decision card is always visible. ``visible_sections`` is a list/tuple of
    distinct section names present in the record; [] shows only the decision.
    Selection never relaxes record validation or changes canonical panel order.
    Display dimensions scale a stable content-sized viewBox.
    """
    validate_record(data)
    _dimension(width, "width")
    if height is not None:
        _dimension(height, "height")
    if not isinstance(include_purple, bool):
        raise ValidationError("include_purple: expected True or False.")
    sections = {hat: (title, blocks) for hat, title, blocks in record_sections(data)}
    available = list(sections)
    if visible_sections is not None:
        if not isinstance(visible_sections, (list, tuple)) or any(not isinstance(hat, str) for hat in visible_sections):
            raise ValidationError("visible_sections: expected a list or tuple of section names.")
        if len(set(visible_sections)) != len(visible_sections):
            raise ValidationError("visible_sections: section names must be distinct.")
        for hat in visible_sections:
            if hat not in sections:
                raise ValidationError(f"visible_sections: {hat!r} is not a section in this record; choose from {', '.join(available)}.")
        if not include_purple and "purple" in visible_sections:
            raise ValidationError("visible_sections: purple conflicts with include_purple=False.")
        sections = {hat: value for hat, value in sections.items() if hat in visible_sections}
    if not include_purple:
        sections.pop("purple", None)
    omitted = [hat for hat in available if hat not in sections]
    description = ("Partial decision map. Shown: decision question" +
                   (", " + ", ".join(sections) if sections else " only") +
                   ". Omitted panels: " + ", ".join(omitted) + ".") if omitted else "Complete decision map."
    layout_width, margin, card_width = 1440, 48, 624
    root_blocks = [("Decision question", [data["question"]])]
    for key in ("subtitle", "context", "demo_notice"):
        if data.get(key):
            root_blocks.append((key.replace("_", " ").capitalize(), [data[key]]))
    if omitted:
        root_blocks.append(("Teaching stage" if visible_sections is not None else "Selected view", [description]))
    root_height, root = _card("decision", data["title"], root_blocks, margin, margin, layout_width - 2 * margin)
    cards = [root]
    connectors = []
    y = margin + root_height + 48
    last_y = margin + root_height
    for left, right in (("white", "yellow"), ("red", "green"), ("black", "blue")):
        row_height = 0
        for hat, x in ((left, margin), (right, 768)):
            if hat not in sections:
                continue
            title, blocks = sections.pop(hat)
            if "label" not in data[hat]:
                title = HAT_META[hat][0]
            card_height, card = _card(hat, title, blocks, x, y, card_width)
            cards.append(card)
            row_height = max(row_height, card_height)
            midpoint = y + card_height / 2
            edge = x + card_width if hat == left else x
            connectors.append(f'<path d="M 720 {last_y} V {midpoint} H {edge}" stroke="{HAT_META[hat][2]}"/>')
        if row_height:
            last_y = y + row_height / 2
            y += row_height + 48
    for hat, (title, blocks) in sections.items():
        connectors.append(f'<path d="M 720 {last_y} V {y}" stroke="{HAT_META[hat][2]}"/>')
        card_height, card = _card(hat, title, blocks, margin, y, layout_width - 2 * margin)
        cards.append(card)
        last_y = y + card_height
        y += card_height + 48
    layout_height = y + 34
    display_height = height if height is not None else round(width * layout_height / layout_width, 2)
    accessible_id = "map-" + uuid.uuid4().hex
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{display_height}" '
            f'viewBox="0 0 {layout_width} {layout_height}" preserveAspectRatio="xMidYMin meet" role="img" aria-labelledby="{accessible_id}-title {accessible_id}-desc">'
            f'<title id="{accessible_id}-title">{escape(data["title"])}</title>'
            f'<desc id="{accessible_id}-desc">{escape(description)} Panels connect to the decision by a central spine. Six Thinking Hats by Edward de Bono. '
            'Purple is a project extension. A semantic HTML and Markdown version accompanies the SVG export.</desc>'
            '<rect width="100%" height="100%" fill="white"/>'
            '<g fill="none" stroke-width="3">' + "".join(connectors) + '</g>'
            '<g font-family="DejaVu Sans Mono, monospace" fill="#17243b">' + "".join(cards) + '</g>'
            f'<text x="48" y="{y+4}" font-size="15" font-family="sans-serif" fill="#17243b">Six Thinking Hats: Edward de Bono. Purple: project extension. Evidence requires human review.</text></svg>')
