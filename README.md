# Six Thinking Hats + JupyterLite

Carry one decision from a structured conversation to editable JSON, a complete connected SVG map, a human-reviewed synthesis, and downloadable files—all in your browser.

Edward de Bono developed **Six Thinking Hats**. This project adds an optional **Purple Hat — Orchestrator** for synthesis; Purple is not one of de Bono's original six hats.

## Start in your browser

- [Launch JupyterLite](https://jltobias.github.io/JupyterLite-Custom-GPT-Six-Thinking-Hats/lite/lab/index.html)
- [Read the Jupyter Book](https://jltobias.github.io/JupyterLite-Custom-GPT-Six-Thinking-Hats/book/index.html)
- [Project landing page](https://jltobias.github.io/JupyterLite-Custom-GPT-Six-Thinking-Hats/)

No local Python installation or credentials are needed for the notebooks. Open a notebook in JupyterLite, select **Python (Pyodide)** if asked, wait for the kernel, and run cells with **Shift+Enter**. Keep the notebooks, helper modules, and `examples` folder together.

Follow **01 → 02 → 03 → optional 06 → 05** for your own decision. Start [Notebook **04** — Build the supplied graphic](book/notebooks/04_global_health_example.ipynb) for an independent build-along: inspect the local original, add each perspective, compare Purple's role with authored reasoning, edit an item, and export your practice.

| Notebook | What you do |
|---|---|
| 01 — Method and schema | Frame one question and understand the original six hats. |
| 02 — Prompt and capture | Generate a prompt, paste or author JSON, validate it, and save `decision.json`. |
| 03 — Render | Reopen that same file as a complete SVG map and readable HTML. |
| 06 — Purple synthesis, optional | Author or paste a reviewed synthesis and save it into the same decision. |
| 05 — Export | Download JSON, SVG, Markdown, and standalone accessible HTML. |
| 04 — Build the supplied graphic | Reconstruct the original panels step by step, edit and export practice, and compare the separate fictional adaptation. |

For a first practice run, set `USE_DEMO = True` in Notebook 02, execute that input cell, then execute the save cell. The demo starts with six hats; Notebook 06 explains how to use the example's authored Purple object. The demo never replaces an existing `decision.json`. For your own question, keep that flag false and paste only JSON into `GPT_RESPONSE`. After every edit, execute the input cell before generating the prompt or saving. Do the same after editing `PURPLE_RESPONSE` in Notebook 06. For JSON containing three consecutive apostrophes, use the documented UTF-8 file upload/read alternative in the [workflow guide](book/workflow.md#upload-a-json-response-instead).

## Use the plugin or the generic prompt

[Six-Thinking-Hats-GPT](https://chatgpt.com/plugins/plugin_217cb0693754819196cd4d8af8c42973) can help generate the structured response. Access depends on your account and workspace permissions; access for another colleague is not assumed. If it is unavailable, use the same prompt from Notebook 02 in another assistant or author the JSON yourself.

The workflow uses deliberate copy and paste. It makes no live model calls and does not embed credentials. Validation checks structure and text, **not factual accuracy**. Review claims, assumptions, source context, and privacy before sharing.

Purple is authored reasoning, not item counting. It connects statements across the six hats, including feelings and values, then records a recommendation, uncertainties, and decision pivots. An empty synthesis input leaves the saved record unchanged. A newly submitted synthesis requires author/review-status provenance. If the saved decision changed since the synthesis prompt was generated, saving is refused until you regenerate the prompt and review the response.

## Preserve and resume your work

Each notebook opens `decision.json` from the same folder, even when it has a fresh kernel. A malformed response fails with a field-level message before it can replace saved data. Replacing an existing record from Notebook 02 requires explicitly setting `REPLACE_SAVED = True`; the separate worked example never replaces it.

JupyterLite work belongs to the current browser profile and site origin. Clearing site data, private browsing, another profile or device, or storage limits can remove or isolate it. **Download your files**, including JSON, using Notebook 05's links or the file browser's **Download** action. Each export creates a separate snapshot folder under `exports/`; the cell prints its name. Open that folder to find the four files. Earlier snapshots remain unchanged even if a later export fails. To resume, upload your JSON as `decision.json` beside the notebooks. Back up or rename an existing decision before replacing it.

SVG keeps all content and grows with long text; display dimensions scale the full drawing. HTML provides a responsive reading order with headings and lists, plus an expandable map. JSON preserves the exact record for editing. See the [workflow and schema](book/workflow.md).

## Build the supplied graphic

Use the supplied graphic as a teaching object in [Read, question, and improve a seven-hat map](book/graphic-lesson.md). The 25–35 minute reading lesson includes a full-size image, text companion, close-reading tasks, and a five-point decision-brief rubric. The accompanying 35–50 minute [Notebook 04 build-along](book/notebooks/04_global_health_example.ipynb) starts with the question, adds six perspectives, then Purple's role and possible outcomes. Expand intermediate maps as needed, compare an explicitly authored synthesis, and change an item before exporting.

The [source reconstruction](book/notebooks/examples/graphic_source.json) faithfully transcribes the meaningful panels: the exact question, seven items and four questions per original hat, Purple's role and six desired outputs, and six outcomes. It derives from [the full normalized transcription](book/graphic-text.md). Purple's role is stored in `focus` and its desired outputs in `items`; it is not a completed synthesis. The bundled [PNG copy](book/notebooks/examples/plugin-output-example.png) is byte-identical to the original image. SVG cards rebuild content and connections rather than the globe/hat artwork. Surrounding decorative callouts remain in the PNG and full transcription.

Notebook 04 keeps source text, teaching interpretation, authored synthesis, and editable practice clearly labeled. It runs with no `decision.json`, never reads or writes that personal file, and saves practice into unique `graphic-exports/` snapshot folders. Its independently runnable adapted-example export continues to save the unchanged fictional record to `example-exports/`.

The [global-health record](book/notebooks/examples/global_health.json) draws themes from the supplied image: GIS, GeoAI, health equity, open science, professional learning, ethics, and collaboration. It is not an assessment of a person, a verified research finding, or a recommendation for a real health deployment.

The [reference image](book/images/plugin-output-example.png) remains a separate illustration. The new renderer prioritizes complete editable text and explicit source limitations. [Candidate data sources](book/data-sources.md) are starting points for investigation, not verified evidence.

## Develop and verify

The learner runtime uses only Python's standard library and IPython display. Build and development packages are installed separately:

```bash
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python scripts/verify_notebooks.py --book-output _build-input/book
jupyter-book build _build-input/book
jupyter lite build --contents book/notebooks --output-dir _site/lite
```

Build only from clean learner sources. The verifier refuses saved outputs, execution state, edited response or file-read inputs, enabled demo/replacement flags, and private question/context inputs; it never clears them automatically. Back up your work and use a separate clean checkout for publishing. JupyterLite bundles only the explicit six notebooks, two helpers, two example JSON files, and original PNG copy; `decision.json`, response files, and all export folders are excluded. Always run the verifier before a local build; `python scripts/verify_notebooks.py --check-sources-only` provides the source guard without executing notebooks.

The notebook verifier runs all six notebooks in separate native Python kernels with one shared temporary directory. It checks the learning path, complete exports, empty-input preservation, and unrelated-user-data preservation. It stages a **clearly labeled demonstration book** without reading or modifying any learner's saved decision. Choose a fresh `--book-output` directory for another run. A plain `jupyter-book build book` also builds the source guide, but has no generated demonstration outputs.

CI runs deterministic unit tests, executes notebooks, and builds both static sites on pull requests. Deployment has a separate main-branch gate and requires those checks. Published JupyterLite uses the original unexecuted notebooks, so demonstration build outputs never become a learner's saved decision.

If setting up a new deployment, select **GitHub Actions** in repository **Settings → Pages**. The workflow assembles the landing page, book, and JupyterLite under one static Pages site.

## Attribution

de Bono, E. (1985). *Six Thinking Hats*. Little, Brown. [WorldCat catalog record](https://search.worldcat.org/title/six-thinking-hats-the-power-of-focused-thinking/oclc/21864205).

Cite de Bono for the method and this repository separately for the notebooks, schema, renderer, and Purple extension. Six Thinking Hats is a thinking aid; subject-matter expertise, representative evidence, governance, and human judgment remain necessary.
