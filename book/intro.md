# Six Thinking Hats + JupyterLite

Carry one decision through capture, review, synthesis, visualization, and download. The notebooks run in your browser, while this book explains the path and shows labeled demonstration outputs.

```{admonition} Attribution
Edward de Bono developed **Six Thinking Hats**. The optional **Purple Hat — Orchestrator** is this project's synthesis extension, not part of his original six-hat method.
```

## Start here

[Launch JupyterLite](https://jltobias.github.io/JupyterLite-Custom-GPT-Six-Thinking-Hats/lite/lab/index.html), open Notebook 01, and run cells with **Shift+Enter**. Select the **Python (Pyodide)** kernel if asked and allow it to finish loading. No local Python installation or credentials are required.

Read the [workflow](workflow.md), then follow **01 → 02 → 03 → optional 06 → 05**. Each notebook reopens the same `decision.json`. Notebook 04 is a separate fictional global-health example and never changes your decision.

For a no-account practice run, explicitly set `USE_DEMO = True` in Notebook 02, execute the edited input cell, then execute its save cell. For your own decision, execute the input cell to generate a prompt, paste or author the response JSON, execute the edited input cell again, and save. The [Six-Thinking-Hats-GPT plugin](https://chatgpt.com/plugins/plugin_217cb0693754819196cd4d8af8c42973) requires suitable account/workspace access; the same generic prompt also works in another assistant or as a writing template.

The published demonstration outputs are generated from the fictional example in an isolated build directory. Your live JupyterLite notebooks begin with empty response inputs. Download your JSON and exports to preserve work outside browser storage.

[View the repository](https://github.com/jltobias/JupyterLite-Custom-GPT-Six-Thinking-Hats).
