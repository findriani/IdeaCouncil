# Dataset Description Prompt

Use this prompt to produce a compact, structured dataset briefing before pasting
it into LLMCouncil's "Dataset Description" context field.

---

## Prompt

```
You are preparing a dataset briefing for a research brainstorming session.
Given the following dataset documentation, produce a structured description
that covers everything a researcher needs to generate relevant ideas.

Use this exact structure:

**Dataset Name & Source:**
[Full name, authors/institution, publication year, DOI or URL if available]

**Purpose & Domain:**
[What the dataset was designed for; the clinical, scientific, or engineering domain]

**Subjects / Samples:**
[Number of subjects or samples, demographics if relevant, sampling strategy]

**Signals / Features:**
[List each signal or feature column, its type, units, and sampling rate if applicable]

**Labels & Ground Truth:**
[What labels are available, how they were collected, any labeling gaps or caveats]

**Data Format & Structure:**
[File format, folder structure, row/column layout, any preprocessing applied]

**Key Constraints & Caveats:**
[Missing data, collection conditions, known quality issues, ethical or access restrictions]

**Unique Strengths:**
[What makes this dataset unusual or particularly valuable for research]

Rules:
- Be specific: name exact column labels, signal types, sample counts
- Do not speculate about what research could be done — only describe what exists
- Flag any ambiguities or limitations explicitly
- Target length: ~400 words / ~2500 characters
```

---

## Usage

1. Run this prompt in any capable LLM (Claude, GPT, Gemini), providing the
   full dataset documentation (README, paper, data dictionary) as input
2. Paste the output into LLMCouncil's **Dataset Description** field
3. The description is injected at:
   - **Diverge** — full 2500 chars, so models generate ideas grounded in what the data can support
   - **Criticize** — first 500 chars (name, purpose, key constraints), for feasibility scoring
   - **Converge** — full 2500 chars, so the coordinator can anchor recommendations to the dataset

## Why structured over prose

A structured description ensures the most decision-relevant facts (labels,
constraints, format) survive the Criticize truncation to 500 chars. If the
description starts with name, purpose, and key constraints, critics can assess
feasibility accurately even with limited context.
