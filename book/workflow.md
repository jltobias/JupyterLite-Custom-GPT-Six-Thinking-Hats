# Workflow

## 1. Frame a decision or problem

Write one central question that is specific enough for each hat to examine from a different perspective.

## 2. Ask Six-Thinking-Hats-GPT for structured output

Notebook 02 generates a prompt that asks the custom GPT for JSON with one object per hat. The meanings follow Edward de Bono's method: white (information), red (feelings), black (caution), yellow (benefits), green (creativity), and blue (process/control).

## 3. Copy the JSON into JupyterLite

This repository intentionally uses copy/paste instead of embedding ChatGPT credentials in browser code. Treat any AI response as draft material that needs review.

## 4. Validate, render, and inspect

Notebook 03 validates the schema and uses `six_hats_mindmap.py` to render an SVG. The renderer is pure Python so it works in the Pyodide kernel used by JupyterLite.

## 5. Add orchestration only when useful

Notebook 06 demonstrates a **Purple Hat — Orchestrator** that synthesizes themes, tensions, blind spots, and next actions. This is a repository-specific extension, clearly separated from de Bono's original method.

## 6. Export reproducible artifacts

Save both the visual artifact and the source JSON. Keeping the source structure makes the reasoning traceable and easier to revise later.
