# IdeaCouncil

IdeaCouncil is a Streamlit app for generating and evaluating research ideas with a small council of LLMs. It is designed for researchers, students, and practitioners who want more than one model's perspective when exploring possible research directions.

Instead of asking one model for ideas, IdeaCouncil runs a structured workflow:

1. Multiple models generate diverse research ideas.
2. Near-duplicate ideas are filtered before review.
3. A live literature search checks what has already been published recently.
4. A fixed set of critic models reviews those ideas anonymously.
5. A dedicated novelty critic checks ideas against your literature context and recent academic search results.
6. A coordinator model synthesizes the strongest directions into ranked recommendations.

The goal is not to replace research judgment. The goal is to give you a richer, more critical starting point.

## Inspiration

IdeaCouncil is inspired by [Andrej Karpathy's LLM Council](https://github.com/karpathy/llm-council), which demonstrated using multiple LLMs to evaluate each other's answers through blind peer review.

IdeaCouncil adapts that idea for research brainstorming: instead of answering a single question, the council generates, critiques, and synthesizes novel research directions — personalized to your constraints, expertise, and goals.

## Features

- Multi-model brainstorming through OpenRouter
- Structured idea generation with contribution types, gaps, novel components, and pipelines
- Near-duplicate filtering to avoid wasting review tokens on similar ideas
- Blind peer review so critics do not know which model generated each idea
- Fixed critic roster for more consistent evaluation across runs
- Dedicated novelty assessment using uploaded literature context plus live literature search
- Dataset and literature context slots to ground ideas in your actual research setting
- Optional external LLM idea import for ideas generated outside the app
- Iterative refinement with user feedback
- Session restore through saved URLs
- Markdown reports for full results and top recommendations
- Cost tracking by phase and model

## How IdeaCouncil Works

```
Your research prompt
+ dataset context
+ literature context
         │
         ▼
  ┌─────────────────────────────────────────────┐
  │  DIVERGE                                    │
  │  7 models × 4 ideas each, in parallel       │
  │  each idea: Gap → Novel Component →         │
  │             Pipeline                        │
  └─────────────────────────────────────────────┘
         │  near-duplicates removed
         ▼
  ┌─────────────────────────────────────────────┐
  │  LITERATURE CHECK                           │
  │  4–6 queries → Semantic Scholar + OpenAlex  │
  │  last 5 years → ~700-word landscape report  │
  └─────────────────────────────────────────────┘
         │
         ▼
  ┌─────────────────────────────────────────────┐
  │  CRITICIZE                                  │
  │                                             │
  │  Track A  Qwen · GPT · Kimi · DeepSeek       │
  │           → Feasibility + Impact            │
  │                                             │
  │  Track B  Gemini 3 Flash (dedicated pass)    │
  │           → Novelty · full lit context      │
  └─────────────────────────────────────────────┘
         │
         ▼
  ┌─────────────────────────────────────────────┐
  │  CONVERGE  (Claude Sonnet)                  │
  │  synthesizes all results                    │
  │  novelty weighted most heavily              │
  │  → top 6 ranked recommendations             │
  └─────────────────────────────────────────────┘
         │
         ▼
  Full report + optional next iteration
```

IdeaCouncil runs a four-step pipeline: generate ideas, filter and search literature, critique, then synthesize.

### 1. Diverge: Generate Ideas

With the default preset, seven models generate ideas in parallel — each independently, without seeing what the others are producing. Each model is asked for four ideas, so up to 28 ideas enter the pool before any filtering.

Every idea must follow a structured eight-field format:

| Field | Purpose |
|---|---|
| Contribution Type | Categorizes the structural nature of the idea |
| Title | Short descriptive name |
| Summary | 2–3 sentence overview |
| Gap | The specific open problem this idea addresses |
| Novel Component | The core novelty — what makes this different from existing work |
| Pipeline | Step-by-step methodology: data prep, model, experiments, evaluation |
| Feasibility | Why this is achievable within the stated constraints |
| Expected Outcomes | What a successful result looks like |

The Gap → Novel Component → Pipeline structure is deliberate. It separates the problem from the proposed solution and the execution plan, which makes it easier to judge how publishable the core contribution actually is.

Each model must also assign a *different contribution type* to each of its ideas — types like Novel Pipeline Component, Training Paradigm, Lightweight Baseline, or Evaluation Paper. This forces structural diversity across the pool and prevents ideas from clustering around the same approach.

### 2. Deduplicate and Search Literature

Before review, IdeaCouncil filters out near-duplicate ideas using cosine similarity on the idea text. Ideas that are more than 75% similar to another idea in the pool are removed. Filtered ideas are still shown in the All Ideas tab under a "Near-Duplicates" section — nothing is silently discarded.

The live literature check then runs. A small, fast model (Gemini Flash Lite) reads the full idea pool and generates 4–6 targeted search queries based on the gaps and novel components across all ideas. Those queries are sent in parallel to Semantic Scholar and OpenAlex, filtered to the last five years. The top results from each query are collected, deduplicated by title, and summarized into a ~700-word literature landscape report organized by theme.

This report is passed directly to the novelty critic in the next step. Semantic Scholar and OpenAlex are free APIs; the only cost is the two summarization calls, which typically adds about $0.01.

### 3. Criticize: Blind Review

All ideas are anonymized and shuffled before critique. Critics see the proposal, not the model that wrote it.

Four models always serve as general critics, regardless of which generators you selected: **Qwen3.6 Plus**, **GPT-5.4**, **Kimi K2.6**, and **DeepSeek V4 Pro**. Each scores every idea it reviews on **Feasibility** and **Impact** (1–5 each), plus a written steelman, assessment, and suggestions. All four critics run in parallel.

**Gemini 3 Flash** makes a second separate pass as the dedicated novelty critic. In this pass it receives all ideas (including those from Kimi, if Kimi is a generator), the full uploaded literature context (up to 7,000 characters), and the live literature search report. It scores each idea on **Novelty only** (1–5), identifying the closest prior work and justifying whether the idea is genuinely original. Gemini 3 Flash is used here because it is fast and inexpensive — novelty scoring needs breadth across all ideas, not deep reasoning.

After all scores are in, IdeaCouncil computes score variance across the four general critics. Ideas where critics strongly disagree on Feasibility or Impact are flagged as **controversial** in the Critiques tab. A controversial flag means the idea's merits are genuinely debatable — worth reading the individual assessments rather than just the averages.

### 4. Converge: Rank Recommendations

Claude Sonnet always acts as the coordinator, regardless of which models you selected. It receives every idea, all written critiques, and the novelty scores from Gemini 3 Flash, then produces a ranked list of the top six recommendations.

Novelty is weighted most heavily in the ranking because originality is the hardest bar to clear for publication. Impact comes second, feasibility third. The coordinator uses qualitative judgment across all critique text, not just the numerical scores.

Each recommendation in the final output includes:

- **Why it ranks where it does**, grounded in specific scores and critique comments
- **A methodology sketch** with enough detail to start from: dataset setup, what to implement, which experiments to run, and which metrics to use
- **Feasibility** — one-line judgment
- **Key risk** — the single most important challenge to address early

The report closes with an executive summary and a list of common themes across the idea pool.

## Requirements

- Python 3.11 or newer
- An OpenRouter API key (see below)

## Installation

```bash
git clone https://github.com/findriani/IdeaCouncil.git
cd IdeaCouncil
pip install -r requirements.txt
```

## API Key

IdeaCouncil routes all model calls through [OpenRouter](https://openrouter.ai), a gateway that gives you access to models from Anthropic, Google, OpenAI, and others through a single API key and billing account.

Create a `.env` file in the project root:

```bash
OPENROUTER_API_KEY=your_key_here
```

You can also paste the key directly into the app sidebar. It will not be stored anywhere.

Get an API key at [openrouter.ai/keys](https://openrouter.ai/keys). You will need to add credits to your account before making requests.

## Cost

IdeaCouncil makes API calls on your behalf. Typical costs with the default model preset:

| Configuration | Per iteration |
|---|---|
| Default (7 generators, 4 critics + novelty pass) | $0.55 – $0.90 |
| Fewer generators (3–4 models) | $0.35 – $0.60 |
| Literature search (all configurations) | +~$0.01 |

The literature search uses Semantic Scholar and OpenAlex, which are free. The small cost is for the two summarization calls.

You can see a full cost breakdown by phase and model in the Cost tab after each run.

## User Profile

Copy the example profile:

```bash
cp config/user_profile.example.yaml config/user_profile.yaml
```

Edit `config/user_profile.yaml` to describe your research interests, constraints, resources, and goals. You can also edit the profile from the app sidebar.

The profile helps the council avoid ideas that are unrealistic for your timeline, compute, skill level, or target publication venue.

## Run the App

```bash
streamlit run app.py
```

Then open `http://localhost:8501` in your browser.

## Using the App

1. Enter your OpenRouter API key in the sidebar, or load it from `.env`.
2. Choose a model preset or custom model selection.
3. Enter your research prompt.
4. Optionally add dataset and literature context.
5. Start brainstorming.
6. Review the ranked recommendations, all ideas, critiques, literature check, and cost breakdown.
7. Optionally provide feedback and run another iteration (up to 3 per session).

After a run completes, the app URL updates with a session token. You can bookmark or share that URL to restore the full session later, including all ideas, critiques, and the final report.

## Context Inputs

Dataset context should describe what data you actually have:

- Dataset name and source
- Number of samples
- Features, signals, labels, or modalities
- File format
- Known limitations

Literature context should summarize relevant prior work:

- Common methods
- Important papers
- Known limitations
- Existing benchmarks and datasets
- What has already been tried

The better this context is, the less likely the council is to propose generic or already-solved ideas.

## External LLM Ideas

You can generate ideas in another LLM interface, such as a web chat, then paste the output into IdeaCouncil.

Those ideas are injected as an additional virtual council member before critique and convergence. This is useful if you want to include a model that is not available through OpenRouter, or if you want to manually seed the idea pool.

Use the **Generate External Prompt** button in the app to get a pre-formatted prompt you can paste into any LLM.

## Outputs

IdeaCouncil provides:

- Top recommendations report
- Full markdown report
- All generated ideas
- Critiques and scores
- Novelty assessments
- Literature search queries and retrieved papers
- Cost breakdown by phase and model

Reports can be downloaded as Markdown files.

## Project Structure

```text
app.py                          Streamlit app entry point
config/models.yaml              Model registry and phase settings
config/user_profile.example.yaml
api/openrouter_client.py        OpenRouter client
api/literature_search_client.py Semantic Scholar and OpenAlex clients
core/council.py                 Main workflow orchestration
core/member.py                  Model wrapper and response parsers
core/literature_checker.py      Live literature check pipeline
core/ranker.py                  Score variance and controversy analysis
prompts/                        Phase prompts
ui/                             Streamlit UI components
utils/                          Context, reports, sessions, validation
tests/                          Regression tests
```

## Notes and Limitations

- LLM-generated ideas still need human verification.
- Literature search is a helpful signal, not a full systematic review.
- Model availability and pricing depend on OpenRouter.
- Costs vary with selected models, prompt length, number of ideas, and output length.
- Very long or noisy literature context can reduce idea quality; summarize it before use when possible.

## License

MIT
