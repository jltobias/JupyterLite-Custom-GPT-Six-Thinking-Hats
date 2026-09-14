# JupyterLite + Custom GPT: Six Thinking Hats

A browser-first learning repository that pairs a custom **Six-Thinking-Hats-GPT** with **JupyterLite** notebooks and a **Jupyter Book**. The notebooks demonstrate a reproducible workflow for moving from a structured Six Thinking Hats conversation to JSON, synthesis, and exportable SVG mind maps—without requiring a local Python installation.

> **Method attribution.** The Six Thinking Hats method was developed by **Edward de Bono**. This repository cites and adapts the method for educational demonstrations. The optional **Purple Hat — Orchestrator** used here is a project-specific extension for synthesis and is **not** one of de Bono's original six hats.

## Live sites

Once GitHub Pages is enabled with **GitHub Actions** as the source, the workflow in this repository publishes:

- **Project landing page:** <https://jltobias.github.io/JupyterLite-Custom-GPT-Six-Thinking-Hats/>
- **JupyterLite (JupyterLab):** <https://jltobias.github.io/JupyterLite-Custom-GPT-Six-Thinking-Hats/lite/lab/index.html>
- **Jupyter Book:** <https://jltobias.github.io/JupyterLite-Custom-GPT-Six-Thinking-Hats/book/index.html>
- **GitHub repository:** <https://github.com/jltobias/JupyterLite-Custom-GPT-Six-Thinking-Hats>

If the Pages links return 404 after the first commit, open **Settings → Pages**, choose **GitHub Actions** as the source, and re-run the Pages workflow.

## Notebooks

| Notebook | Purpose |
|---|---|
| `01_six_thinking_hats_method.ipynb` | Introduces the six hats, attribution, and a machine-readable schema. |
| `02_prompt_and_capture.ipynb` | Creates a reusable prompt for Six-Thinking-Hats-GPT and validates pasted JSON output. |
| `03_render_mind_map.ipynb` | Renders structured hat output as a dependency-free SVG mind map in the browser. |
| `04_global_health_example.ipynb` | Recreates the attached global-health/GeoAI scenario as a worked example with public data-source links. |
| `05_export_and_share.ipynb` | Exports JSON, SVG, and standalone HTML artifacts. |
| `06_purple_hat_orchestrator.ipynb` | Adds an optional synthesis layer for themes, tensions, blind spots, and next steps. |

The helper `book/notebooks/six_hats_mindmap.py` keeps the visualization logic reusable and JupyterLite-friendly.

## Recommended workflow with Six-Thinking-Hats-GPT

1. Open your **Six-Thinking-Hats-GPT** in ChatGPT.
2. Use the prompt template generated in Notebook 02 and ask the GPT to return the six perspectives as JSON.
3. Copy the JSON response into the notebook. This avoids placing API keys or private ChatGPT credentials in a public browser-executed notebook.
4. Validate and normalize the response.
5. Render it in Notebook 03 or the worked example in Notebook 04.
6. Optionally use Notebook 06 for the project-specific Purple Hat synthesis.
7. Export the map and source JSON with Notebook 05.

**Important:** a custom GPT in ChatGPT is not treated here as a public API endpoint. If you later add an API-backed service, keep secrets server-side rather than embedding them in JupyterLite.

## Local build

```bash
python -m pip install -r requirements.txt
jupyter-book build book
jupyter lite build --contents book/notebooks --output-dir _site/lite
```

## Public data sources for examples

These are useful starting points for global-health and GeoAI exercises. Always inspect licensing, update cadence, geographic coverage, and methodology before analysis.

| Source | Live link | Example use |
|---|---|---|
| WHO Global Health Observatory (GHO) | <https://www.who.int/data/gho> | Health indicators, country profiles, mortality, disease burden, health systems, equity. |
| WHO GHO OData API | <https://www.who.int/data/gho/info/gho-odata-api> | Programmatic access to GHO indicators. |
| World Bank Open Data | <https://data.worldbank.org/> | Population, development, health-system, environment, and socioeconomic indicators. |
| NASA Earthdata | <https://www.earthdata.nasa.gov/> | Earth observation, climate, land, atmosphere, hydrology, and other geospatial data. |
| NOAA Climate Data Online | <https://www.ncei.noaa.gov/cdo-web/> | Weather and climate observations for environmental-health analyses. |
| Copernicus Climate Data Store | <https://cds.climate.copernicus.eu/> | Climate reanalysis and derived climate products. |
| Humanitarian Data Exchange (HDX) | <https://data.humdata.org/> | Humanitarian, population, health, boundary, and crisis-response datasets. |
| UNAIDS resources | <https://www.unaids.org/en/resources/documents> | HIV/AIDS reports and downloadable resources; verify the current data product for your use case. |

## Citation and attribution

The conceptual foundation is Edward de Bono's Six Thinking Hats method:

> de Bono, E. (1985). *Six Thinking Hats*. Little, Brown. Goodreads record: <https://www.goodreads.com/book/show/97030.Six_Thinking_Hats>.

A library catalog record for the first U.S. edition is available via WorldCat: <https://search.worldcat.org/title/six-thinking-hats-the-power-of-focused-thinking/oclc/21864205>.

When using this repository in teaching or publications, cite de Bono for the Six Thinking Hats method and cite this repository separately for the JupyterLite/Jupyter Book implementation, mind-map renderer, and Purple Hat extension.

## Responsible use

Six Thinking Hats is a thinking aid, not a substitute for subject-matter expertise, representative data, validation, peer review, or governance. For health and geospatial applications, pay particular attention to privacy, re-identification risk, spatial bias, data gaps, model uncertainty, and the possibility that maps or AI-generated summaries may create false precision.
