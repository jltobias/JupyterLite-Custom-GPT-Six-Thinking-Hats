# One decision, from question to download

Use the path **01 → 02 → 03 → optional 06 → 05**. Treat **04** as an independent example. Keep the notebooks, both Python helper files, and the `examples` folder together in JupyterLite.

## First run and recovery

For an immediate worked example, open **04** and choose **Run → Run All Cells**. To practice the connected workflow, open **02**, change `USE_DEMO = False` to `USE_DEMO = True`, and run all its cells. Wait for **ILLUSTRATIVE DEMO saved** or **Reopened existing decision** before opening **03**, **06**, or **05**. Running 02 with its unchanged defaults prepares a prompt but does not save a decision.

**Action needed** means a prerequisite or input needs attention; the cell has not completed its requested result. Follow the message, correct the input, and rerun the affected cell. Invalid JSON still needs correction, and a saved decision still needs explicit permission before replacement. View and export cells reopen their files independently after a kernel restart. Capture cells need their input cell first; saving a non-empty Purple response also needs a successfully generated prompt in the current kernel.

If you see an older traceback after this update, JupyterLite may be opening your browser's previously saved notebook copy. Download your notebooks and `decision.json` before replacing any file. Obtain the updated notebook from the repository and upload it into the same folder as the helper files. A private window can check the published defaults separately; it will not contain your saved decision. Do not clear site storage to update notebooks, because that can erase your work.

## 1. Frame the question in Notebook 01

Choose one decision, identify who it affects, and state the time horizon, constraints, and evidence available. White examines information; red records feelings and values; black considers caution; yellow explores benefits; green generates alternatives; blue organizes the process. No hat establishes truth by itself.

## 2. Capture and save in Notebook 02

Edit `CENTRAL_QUESTION` and `CONTEXT`, **execute the edited input cell**, then run the prompt cell. Copy the prompt into [Six-Thinking-Hats-GPT](https://chatgpt.com/plugins/plugin_217cb0693754819196cd4d8af8c42973) if your account and workspace permit access. Colleague access has not been verified. Another assistant or manual authorship can use the same generic prompt.

Paste only the response JSON into `GPT_RESPONSE`, **execute that input cell again**, then run the save cell. Editing a cell changes its text; executing it updates its Python variables. There are no live model calls or embedded credentials. To practice without an assistant, explicitly select `USE_DEMO = True`, execute the input cell, and then execute the save cell; it starts the fictional global-health record with six hats and never replaces an existing decision.

The cell writes `decision.json` only after validation. A blank input reopens existing work or explains that no decision has been saved. To deliberately replace a saved record with your reviewed pasted JSON, set `REPLACE_SAVED = True` and execute the input cell before the save cell. Back up the previous record first.

### Upload a JSON response instead

Valid JSON can contain three consecutive apostrophes (`'''`), which cannot be pasted inside the notebook's default raw triple-apostrophe Python literal. Save the response as UTF-8 `response.json` and upload it beside the notebook. Replace the entire `GPT_RESPONSE` assignment in the input cell, including its closing quotes, with:

```python
from pathlib import Path
GPT_RESPONSE = None  # Clear an older response before attempting the read.
try:
    GPT_RESPONSE = Path("response.json").read_text(encoding="utf-8")
except (OSError, UnicodeError) as error:
    print("Action needed: could not read response.json.", error)
```

Keep the other input settings, using unquoted `True` or `False` for both switches. Execute the edited input cell and resolve any file-read message before executing the save cell. A failed upload read clears the previous response; it cannot be saved accidentally. Notebook 06 supports the same alternative with `PURPLE_RESPONSE` and `purple-response.json`.

## 3. Reopen and inspect in Notebook 03

Notebook 03 loads the saved file even in a fresh kernel. The SVG expands with headings and text, retains every item and question, and includes evidence, Purple synthesis, and possible outcomes when present. Width and height affect display scaling, not the drawing's content.

The semantic HTML view offers a readable small-screen alternative with headings and lists. Check whether factual claims are supported, feelings remain identifiable as feelings, questions expose real uncertainties, and alternative views are represented.

## 4. Author optional synthesis in Notebook 06

Purple is a project extension. Its role is to connect the actual content of the six hats, not count entries. The generated prompt includes the full saved decision. Write a synthesis yourself or paste a reviewed response from an assistant.

A useful Purple object explains:

- Themes that connect multiple perspectives.
- Tensions between benefits, risks, evidence, and values.
- Blind spots, including whose views are missing.
- A conditional recommendation.
- Uncertainties and decision pivots: evidence or conditions that would change the recommendation.
- Concrete next steps and review responsibility.

After pasting or reading `PURPLE_RESPONSE`, **execute the edited input cell**, then execute the save cell. A new synthesis requires a non-empty `author` identifying authorship and review status, a recommendation, uncertainties, and decision pivots. The prompt cell retains its source snapshot. At save time, the notebook compares that snapshot with the current saved record and refuses a changed decision; regenerate the prompt and review a new synthesis before saving. A blank response changes nothing. Rerunning the same already-saved synthesis is also a no-op; it does not require regenerating the prompt. Return to 03 to view the updated map or continue to 05.

## 5. Export and resume in Notebook 05

The export cell reopens and validates `decision.json`, then prepares UTF-8 JSON, SVG, Markdown, and standalone HTML. It writes all four formats into a newly named snapshot subfolder of `exports/`, prints that folder, and displays download links only after the snapshot is complete. Rerunning creates another snapshot and leaves earlier snapshots untouched. A failed write removes only the incomplete new snapshot.

If files were saved but link preparation failed, the completed snapshot remains available at the printed folder path.

Click each download link. If embedded downloads are restricted, use the JupyterLite file browser: open `exports`, open the snapshot folder printed by the cell, right-click a file, and select **Download**. Review sensitive content, claims, and source limitations before sharing.

Browser storage is tied to this site's origin and browser profile. Clearing site data, private browsing, switching devices or profiles, and storage limits can remove or isolate work. To resume, upload a downloaded JSON into the notebook folder and name it `decision.json`. Back up or rename any existing decision first.

## Schema reference

Records use UTF-8 JSON. All text must contain valid XML characters so the same content can be safely exported as SVG. JSON objects may not repeat keys. Unknown fields are rejected with an explanation instead of being discarded.

| Field | Required? | Type and meaning |
|---|---|---|
| `title`, `question` | Yes | Non-empty strings identifying the decision. |
| `white`, `red`, `black`, `yellow`, `green`, `blue` | Yes | Hat objects as described below. |
| `subtitle`, `context`, `demo_notice` | No | Strings for context or a demonstration label. |
| `evidence` | No | List of objects with non-empty `claim`, `source`, `status`, and optional `notes` strings. |
| `outcomes` | No | List of non-empty strings describing possible outcomes. |
| `purple` | No | Hat object with optional synthesis fields below. |

Every hat object requires `items`, a list of non-empty strings. It can also contain non-empty `label` and `focus` strings and a `questions` list of non-empty strings. Lists may be empty when no entries have been recorded. There is no item-count limit.

Purple supports these additional fields: non-empty `author` and `recommendation` strings; and `themes`, `tensions`, `blind_spots`, `uncertainties`, `decision_pivots`, and `next_steps` lists of non-empty strings. Existing minimal Purple records with only items can be read; Notebook 06 requires `author`, `recommendation`, `uncertainties`, and `decision_pivots` for a newly saved synthesis.

An evidence entry could be:

```json
{
  "claim": "A public indicator might help assess the question.",
  "source": "Dataset or source URL to inspect",
  "status": "Candidate source; not yet verified",
  "notes": "Check version, retrieval date, coverage, denominators, missingness, license, and uncertainty."
}
```

Validation runs at capture, load, rendering, synthesis, and export boundaries. It checks types, required fields, duplicate keys, and characters. It does **not** verify facts, links, source credibility, ethical acceptability, or whether a recommendation follows logically. Those require human review.

## Troubleshooting

| What you see | What to do |
|---|---|
| “No saved decision” | Run Notebook 02, paste JSON or select its demo, and execute the save cell. |
| JSON line/column error | Remove Markdown fences and correct JSON punctuation; quote all keys and strings. |
| A named field has the wrong type | Use the schema above. For example, `white.items` must be a list of strings, not one string. |
| An existing-file message | Reopen the file, choose another filename in the helper call, or deliberately enable replacement after review. |
| A missing Python helper module | Keep the notebook and supplied `.py` files in the same folder. |
| The map is tall or text is small | Use the HTML reading view or download and zoom the SVG; nothing was truncated. |
| Work is missing in another browser | Upload your downloaded JSON; browser storage is not a cross-device account. |

(illustrative-reference)=
## Illustrative reference

Study the supplied graphic in [Read, question, and improve a seven-hat map](graphic-lesson.md). That lesson places the unchanged image at the center of a guided activity, with a full-size view, a text companion, questions for each hat, a worked Purple synthesis, and a decision-brief rubric.

Notebook 04 uses a separate [illustrative JSON adaptation](notebooks/examples/global_health.json). The lesson asks you to compare the original graphic with this editable example and identify what was retained, rewritten, and added. Neither establishes personal facts or verified health outcomes. Use the comparison to improve your own reasoning before export.
