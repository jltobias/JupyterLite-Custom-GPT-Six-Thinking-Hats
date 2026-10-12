(graphic-lesson)=
# Read, question, and improve a seven-hat map

This lesson uses the supplied **Six-Thinking-Hats-GPT output graphic** as its primary teaching object. Start with what the graphic actually says, examine what is missing, and turn the perspectives into a defensible next step. You can complete the reading and discussion without an assistant, an account, or Python.

**Suggested time:** 25–35 minutes, individually or in a small group. **Your product:** a short, annotated decision brief with a conditional Purple Hat recommendation.

By the end, you should be able to identify the six thinking modes and the Purple extension; distinguish evidence from a proposed benefit, feeling, or question; connect conflicting perspectives; and explain what would change a recommendation.

**For a 30-minute session:** inspect the graphic or transcript (3 minutes); scan all seven panel explanations and complete **two** “Try it” prompts of your choice (5 minutes); discuss the worked response (5 minutes); compare one image/JSON example (5 minutes); then write and assess the brief (12 minutes). Completing every prompt and executing the notebooks are optional extensions for a longer session.

```{admonition} Terms used in the graphic
:class: dropdown

- **GIS:** geographic information systems; tools for organizing and analyzing information about places.
- **GeoAI:** applying artificial intelligence to geographic information. **LLM:** a large language model, a type of AI used to generate and interpret text.
- **EO / remote sensing:** Earth observation, including measurements collected from satellites or other remote instruments. **Spatial epidemiology:** studying geographic patterns in health and disease.
- **Geoprivacy / re-identification:** protecting location information; re-identification means connecting supposedly anonymous information back to a person.
- **Spatial bias / false precision:** geographic data or methods can systematically misrepresent places or people; false precision makes results look more exact than the evidence warrants.
- **JupyterLite / Jupyter Book:** a browser environment for running notebooks, and a way to publish explanatory material alongside notebooks. You are reading the book; its notebook environment is a separate workspace.
```

## 1. Inspect the teaching object

```{figure} images/plugin-output-example.png
:name: fig-seven-hat-teaching-object
:alt: A globe-centered map about a global-health GIS professional in the age of AI. White, Red and Black panels appear on the left; Yellow, Green and Blue on the right. Purple spans the top and possible outcomes sit below the globe. Each original hat contains topics and key questions. The text companion below describes the panels and their relationships.
:width: 100%

Supplied example output from Six-Thinking-Hats-GPT, reproduced unchanged. The graphic is the object we are studying; the questions and worked response below are teaching additions.
```

Select the graphic to open the full-size image and zoom into its small text, or [download the original PNG](images/plugin-output-example.png) for inspection beside the lesson. A [complete text transcription](graphic-text.md) includes every panel's items, key questions, and surrounding callouts. Use it alongside the interpretive reading guide below; no color recognition or image reading is required.

The globe names the subject: **Global Health GIS Professional in the Age of AI**. The central question, placed inside the Purple panel, asks how a global-health GIS professional can evolve with AI and data science while advancing responsible, equitable, and ethical GeoAI use. Colored lines connect the subject to the hat panels. The bottom panel names possible outcomes; those are aspirations, not measured results.

The elephant callout illustrates partial perspectives: each hat notices something while missing something else. Bringing perspectives together helps reveal connections, but the graphic does not establish that every relevant perspective or fact has been included.

```{note}
Edward de Bono developed the original **six** hats. **Purple Hat — Orchestrator** is this project's added synthesis perspective. Treat the image as an example to investigate, not as a verified assessment of a person or evidence that a health intervention works.
```

## 2. Read each panel with a purpose

The quoted phrases in this section come from the graphic. The explanations and tasks are lesson commentary. Read the central question first, then follow the six modes, and return to Purple after examining the others.

### White — what would count as evidence?

The panel lists skills and experience; available Earth observation, climate, health, and mobility data; technology trends; evidence of impact; information gaps; infrastructure; and organizational context. Its question **“What do we know? What don't we know?”** is a useful starting point. Listing “Evidence of impact” does not itself supply evidence.

**Try it:** choose one proposed benefit elsewhere in the graphic. Write one observation or source that could support it, one limitation to examine, and what remains unknown. Do not supply a citation you have not checked.

### Red — whose feelings and values are represented?

The panel includes excitement about GeoAI, concern about geoprivacy, frustration with slow adoption, a wish to learn and share, and values such as ethics, inclusion, open science, and real-world impact. **“What feels aligned with my values?”** invites reflection, not a factual test.

**Try it:** record one feeling as a first-person statement. Then identify a stakeholder whose feelings are absent. A learner's enthusiasm cannot stand in for a community's priorities or consent.

### Black — what could go wrong?

The panel raises automation of GIS work, spatial bias, false precision, model misuse, re-identification, incomplete data, technical limits, governance, and sustainability. **“How might my assumptions be wrong?”** asks you to examine a failure mode.

**Try it:** turn one risk into a concrete scenario: what action might cause harm, to whom, and what observation would tell you to stop or change it? Notice that concern about privacy can appear in both Red and Black: Red expresses a feeling; Black analyzes a possible failure.

### Yellow — what benefit is worth investigating?

The panel proposes greater impact through AI and GeoAI; integration of environmental, health, and mobility data; earlier warning and better targeting; demand for geospatial intelligence; lower barriers through open-source tools; education; and responsible AI. **“Why could this work?”** is an invitation to give reasons.

**Try it:** recast “AI and GeoAI can amplify global health impact” as a testable possibility. Name who might benefit, a relevant comparison, and an observation that would count as improvement. The statement is a benefit hypothesis until supported.

### Green — what alternatives could we explore?

The panel suggests JupyterLite prototypes, interactive notebooks, analysis assistants, climate–health mapping, privacy demonstrations, hat-based agents, and new professional roles. **“What experiments could I build in a Jupyter notebook?”** points toward something small enough to try.

**Try it:** propose two ways to address the same need, including one that does not require AI. Explain what each alternative could teach you.

### Blue — how would we organize the work?

The panel proposes goals, scope, success measures, a 12-month learning roadmap, a Jupyter Book/JupyterLite structure, collaborators, and regular review. **“What should I do first?”** turns a broad ambition into a next action.

**Try it:** specify an owner, a review date, and one observable result for a small experiment. A completed notebook is an output; improved understanding or a better decision is a possible outcome that needs its own measure.

### Purple — what follows from these perspectives together?

The top panel describes coordination, connections, blind spots, tradeoffs, an integrated roadmap, and next steps. **“Integrate • Synthesize • See the Bigger Picture”** describes its role. The graphic does not yet state which specific alternative to choose, on what evidence, or under what conditions to change course.

**Try it:** connect actual statements from the six hats into a conditional recommendation. Include a tension, a missing perspective, and evidence that would change your choice. Repeating the seven panel titles is not synthesis.

### Possible outcomes — how would we recognize success?

The graphic names professional growth, GeoAI prototypes, a Jupyter Book/JupyterLite learning ecosystem, stronger collaborations, health-equity impact, and a responsible and sustainable future. These operate at different scales and timescales. A prototype alone does not demonstrate health-equity impact.

**Try it:** choose one near-term learning outcome and one longer-term aspiration. Explain which you could reasonably assess during a small learning exercise.

## 3. Work through one example

For this teaching exercise, narrow the broad career question to: **What should we learn from a first GeoAI teaching prototype?** This is a lesson-defined decision, not a quotation from the graphic.

| Trace back to the graphic | What it contributes to this decision |
|---|---|
| Yellow: opportunity to educate and build capacity; Green: JupyterLite experimentation | A small teaching notebook is one plausible option. |
| Red: desire to learn and share; ethics and inclusion | Judge usefulness with intended learners, not only by the author's enthusiasm. |
| White: evidence of impact and information gaps | Establish what learners need and how to assess learning before claiming success. |
| Black: bias, false precision, re-identification and technical constraints | Limit the demonstration and examine its assumptions and failure modes. |
| Blue: goals, metrics, collaborators and regular review | Assign responsibility and make a review point explicit. |

```{admonition} Worked Purple response — teaching interpretation
:class: tip

Start with a two-week teaching trial for GIS learners. Use a map of fictional district-level counts to practise identifying a misleading claim about health risk. Compare an AI-assisted explanation with a simple non-AI explanation of the same map. This connects the opportunity to teach (Yellow) and experiment (Green) with the wish to share responsibly (Red). First ask intended learners what they need (White). Explain that synthetic counts do not establish real disease risk, and examine misleading precision and interpretation (Black).

The lesson author owns the trial; the author and a peer reviewer review it on **day 14 after the agreed start date**, entered on the group's calendar at planning time (Blue). Use the same four-item exit ticket after each version: identify one unsupported claim, one evidence gap, one limitation, and one condition that would change a recommendation. Record how many of the four each learner explains correctly, along with any new misconceptions. These are proposed teaching criteria, not validated evaluation results.

The tension is between moving quickly and demonstrating useful, responsible learning. A missing perspective is that of the intended learners and affected communities. It is still unknown whether AI improves understanding. Continue investigating the AI version only if it improves the exit-ticket results without introducing new misconceptions; otherwise revise it or retain the simpler approach. This is a proposed learning experiment, not a validated recommendation for a real health deployment.
```

**Notice the added reasoning:** the original graphic supplies themes; the worked response supplies a limited choice, comparison, review responsibility, uncertainty, and conditions for changing course. Synthetic data limits exposure of real records; it does not establish fairness, usefulness, or readiness for deployment.

## 4. Compare the graphic with the editable example

Open [Notebook 04 — global-health worked example](notebooks/04_global_health_example.ipynb) in the book to inspect its demonstrated output. For execution, [launch JupyterLite](https://jltobias.github.io/JupyterLite-Custom-GPT-Six-Thinking-Hats/lite/lab/index.html), open `04_global_health_example.ipynb`, and run its cells. It reads the bundled example and exports to a separate example folder; it does not replace your saved decision.

Keep these three objects distinct:

| Object | What to inspect |
|---|---|
| Supplied PNG above | The original visual teaching object, including its framing, questions, omissions, and outcome claims. |
| [Illustrative JSON](notebooks/examples/global_health.json) | A separately authored adaptation inspired by the graphic, not an exact transcription or evidence that the image's claims are true. It adds structured evidence notes and a substantive Purple section. |
| Notebook-generated SVG and HTML | Views of that JSON. Compare their content and reading order with the original image; they do not reproduce its artwork. |

Find one idea carried over from the image, one statement rewritten in the adaptation, and one decision field added in the JSON. Inspect `purple.recommendation`, `purple.uncertainties`, and `purple.decision_pivots`. Explain how the additions help someone revisit a decision.

```{admonition} Check your comparison
:class: dropdown

One carried-over idea is JupyterLite experimentation. The broad White Hat category of current skills becomes an explicit task in the JSON: inventory demonstrated skills before selecting a learning goal. A newly explicit field is `purple.decision_pivots`: it records conditions that would change the proposed course. Other answers are valid when you identify both the image passage and the corresponding JSON content. Do not treat the adaptation as proof of a real person's skills or feelings.
```

## 5. Make and assess your own decision brief

Choose either the teaching-prototype question above or a decision you can discuss using public or fictional information. Work on paper or in a separate document first. Produce these five parts:

1. **Frame:** one decision question, the people affected, and a time horizon.
2. **Six perspectives:** one specific contribution from each original hat. Mark evidence as verified, assumed, or unknown; keep feelings identifiable as feelings.
3. **Connections:** one tension between hats and one missing stakeholder perspective. Point to the statements you connected.
4. **Purple recommendation:** one conditional choice, its reasoning, an uncertainty, and an observation that would change your choice.
5. **Next step:** an owner, a review date, and a measure of learning or decision quality. State what the result would not yet establish.

Use this quick peer or self-review rubric. Give one point only when the feature is explicit; revise any missing feature before sharing.

| Criterion | One-point evidence in the brief |
|---|---|
| Framing | A bounded decision, affected people, and a time horizon. |
| Six distinct modes | All six hats contribute, with facts, unknowns, and feelings distinguishable. |
| Integration | A tension and a missing perspective connected to specific statements. |
| Revisable recommendation | A conditional choice, uncertainty, and a concrete reason to change course. |
| Reviewable next step | An owner, date, observable measure, and a limit on what success would prove. |

The five-point score checks whether the reasoning is explicit. It does not certify factual accuracy or the quality of a real-world decision.

For the optional notebook extension, keep your written brief and follow **02 → 03 → 06 → 05** in the [capture-to-export workflow](workflow.md). **Include Notebook 06 for this lesson** so your Purple recommendation reaches the exported record; it is optional only in the general six-hat workflow.

In Notebook 02, put the decision question in `CENTRAL_QUESTION` and your framing and six-hat notes in `CONTEXT`, then generate the prompt. Review the returned JSON against your brief before saving: preserve each hat's contribution and your evidence limitations. Notebook 03 lets you inspect that saved record. In Notebook 06, use your brief's connections and recommendation to author or review the Purple response: put the tension in `tensions`, missing perspectives in `blind_spots`, the choice in `recommendation`, uncertainty in `uncertainties`, the change condition in `decision_pivots`, and the owner, review date, and measure in `next_steps`. Add an `author` and review status. Inspect the saved synthesis before exporting in Notebook 05. The notebooks provide prompts and validation; they do not automatically import the written brief.

Keep the supplied graphic available as a comparison object throughout: **what did it help you notice, and what did you need to add?**
