# Six Thinking Hats + JupyterLite

Carry one decision through capture, review, synthesis, visualization, and download. The notebooks run in your browser, while this book explains the path and shows labeled demonstration outputs.

```{admonition} Attribution
Edward de Bono developed **Six Thinking Hats**. The optional **Purple Hat — Orchestrator** is this project's synthesis extension, not part of his original six-hat method.
```

## Start here

Begin with [Read, question, and improve a seven-hat map](graphic-lesson.md): a guided lesson built around the supplied example graphic. Inspect each perspective, critique the difference between a proposed benefit and evidence, work through a conditional Purple recommendation, and create a short decision brief. No notebook execution is needed for the first part.

For a runnable build-along, open [Notebook 04 — Build the supplied graphic](notebooks/04_global_health_example.ipynb). Reconstruct the exact panels one hat at a time, compare Purple's role with an authored synthesis, change an item, and export your practice. The original image and source JSON are bundled locally; no assistant or saved decision is needed.

[Launch JupyterLite](https://jltobias.github.io/JupyterLite-Custom-GPT-Six-Thinking-Hats/lite/lab/index.html), open Notebook 01, and run cells with **Shift+Enter**. Select the **Python (Pyodide)** kernel if asked and allow it to finish loading. No local Python installation or credentials are required.

Read the [workflow](workflow.md), then follow **01 → 02 → 03 → optional 06 → 05**. Each notebook reopens the same `decision.json`. Notebook 04 is an independent graphic build-along with a separate fictional adaptation for comparison; it never reads or changes your decision.

For a no-account practice run, explicitly set `USE_DEMO = True` in Notebook 02, execute the edited input cell, then execute its save cell. For your own decision, execute the input cell to generate a prompt, paste or author the response JSON, execute the edited input cell again, and save. The [Six-Thinking-Hats-GPT plugin](https://chatgpt.com/plugins/plugin_217cb0693754819196cd4d8af8c42973) requires suitable account/workspace access; the same generic prompt also works in another assistant or as a writing template.

The published demonstration outputs are generated from the fictional example in an isolated build directory. Your live JupyterLite notebooks begin with empty response inputs. Download your JSON and exports to preserve work outside browser storage.

[View the repository](https://github.com/jltobias/JupyterLite-Custom-GPT-Six-Thinking-Hats).
