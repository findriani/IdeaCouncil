# IdeaCouncil

> A multi-LLM council that brainstorms, critiques, and ranks research ideas — so you don't have to choose just one perspective.

Built with **Python + Streamlit**, powered by **OpenRouter API**.

---

## Inspiration

IdeaCouncil is inspired by [Andrej Karpathy's LLM Council](https://github.com/karpathy/llm-council), which demonstrated using multiple LLMs to evaluate each other's answers through blind peer review.

IdeaCouncil adapts this idea for **research brainstorming**: instead of answering a single question, the council generates, critiques, and synthesizes novel research directions — personalized to your constraints, expertise, and goals.

Key additions over Karpathy's approach:
- Research-specific **Diverge → Criticize → Converge** workflow
- **Anonymized peer review** during criticism (models don't know who wrote what)
- **Iterative refinement** with user feedback between rounds
- **User profile** (expertise, timeline, compute constraints) injected into all prompts
- **Dataset & literature context** slots to ground ideas in your actual data
- **Q&A panel** to ask follow-up questions about any generated idea
- Real-time **cost tracking** with live pricing from OpenRouter

---

## How It Works

```
Your research prompt
        ↓
  ┌─────────────────────────────────────────┐
  │  DIVERGE  — all models generate ideas   │  ← parallel, high temperature
  │             (4 ideas each)              │
  └─────────────────────────────────────────┘
        ↓
  ┌─────────────────────────────────────────┐
  │  CRITICIZE — blind peer review          │  ← parallel, anonymized
  │  Ideas shown as Contributor_1/2/3...    │
  │  No model knows who wrote what          │
  └─────────────────────────────────────────┘
        ↓
  ┌─────────────────────────────────────────┐
  │  CONVERGE — one model synthesizes       │  ← top 6 ranked recommendations
  │             top ideas + critiques       │
  └─────────────────────────────────────────┘
        ↓
  Full report + optional next iteration
```

---

## Features

- **Multi-model council** — Claude, GPT, Gemini, Kimi, Qwen, GLM and more via OpenRouter
- **Anonymized criticism** — models evaluate ideas without knowing the source (prevents brand bias)
- **Iterative refinement** — up to 3 rounds with feedback between each
- **User profile** — persistent YAML config for your field, constraints, timeline, resources
- **Dataset context** — describe your dataset so ideas are grounded in what your data can actually support
- **Literature context** — paste your related work so the council avoids re-proposing already-done ideas
- **Built-in summarizer** — one-click summarization of long context using Gemini Flash Lite (cheap, fast)
- **Q&A panel** — ask follow-up questions about any idea after the council runs
- **Live pricing** — model prices fetched from OpenRouter at startup, not hardcoded
- **Cost tracking** — real-time breakdown by phase and model
- **Downloadable reports** — full markdown report + concise top recommendations

---

## Quickstart

### 1. Clone and install

```bash
git clone https://github.com/findriani/IdeaCouncil.git
cd IdeaCouncil
pip install -r requirements.txt
```

### 2. Configure API key

```bash
# Option A: .env file (local)
echo "OPENROUTER_API_KEY=your_key_here" > .env

# Option B: Streamlit secrets (cloud)
# Add to .streamlit/secrets.toml:
# OPENROUTER_API_KEY = "your_key_here"
```

Get an API key at [openrouter.ai/keys](https://openrouter.ai/keys).

### 3. Set up your profile

```bash
cp config/user_profile.example.yaml config/user_profile.yaml
# Edit user_profile.yaml with your research field, constraints, and goals
```

### 4. Run

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`.

---

## User Profile

`config/user_profile.yaml` is injected into every prompt so the council generates ideas that fit your situation:

```yaml
research_interests:
  primary_fields: [Machine Learning, Computer Science]
  specific_topics: [feature engineering, data preprocessing]

constraints:
  expertise: [Undergraduate level, familiar with Python and basic ML]
  technical: [No GPU, prefer lightweight models]
  timeline: [Thesis duration: 6 months]

goals:
  primary: Publishable at a regional conference or journal

resources:
  computational: [Personal laptop 8GB RAM, Google Colab free tier]
  datasets: [Public datasets — Kaggle, UCI]
```

Edit via the sidebar editor in the app, or directly in the YAML file.

---

## Context Slots

Before running the council, you can optionally provide two pieces of context that significantly improve idea quality.

### Dataset Description

If you already have a specific dataset you want to work with, describe it here. The council uses this to generate ideas that are actually feasible with your data — avoiding suggestions that require signals, labels, or sample sizes you don't have.

**What to include:** dataset name, number of samples, features/signals, labels, format, and any known limitations.

**Target length:** ~400 words / ~2500 characters. A helper prompt for generating a well-structured description is provided in [`dataset_description_prompt.md`](dataset_description_prompt.md).

Context is injected at different verbosity levels per phase:
- **Diverge** — full description (2500 chars), so models generate ideas grounded in what the data can support
- **Criticize** — first 500 chars (name, purpose, key constraints), for feasibility scoring
- **Converge** — first 100 chars (dataset name only), to anchor the final synthesis

### Literature Context

Paste a summary of related work in your area. This tells the council what has already been done, so brainstormers can avoid re-proposing existing approaches and instead focus on genuine gaps.

**What to include:** dominant methods and their results, standard benchmarks, known limitations of current work, and under-explored conditions or problem framings.

**Framing tip:** describe the landscape as *background context*, not as a list of gaps to fill. Models told "here are the gaps" will fill them incrementally. Models told "here is what exists and why it falls short" tend to go sideways — proposing genuinely novel framings rather than obvious extensions.

**Target length:** ~1000 words / ~7000 characters. A helper prompt for condensing a long literature review is provided in [`literature_summarization_prompt.md`](literature_summarization_prompt.md).

Context is injected at:
- **Diverge** — full summary (7000 chars), so models know the landscape before generating ideas
- **Criticize** — first 1000 chars, to assess novelty against known work
- **Converge** — dropped (synthesis works from ideas and critiques, not raw papers)

### Built-in Summarizer

If your dataset description or literature dump is too long, the **✨ Summarize** button calls Gemini 3.1 Flash Lite to compress it to the target length automatically. The character count is shown next to the input so you know when to use it.

---

## Model Presets

| Preset | Models | Est. cost/iteration |
|--------|--------|-------------------|
| **Default** | Claude Sonnet, GPT-5.4, Gemini 3.1 Pro, Kimi K2.5, Qwen3.5, GLM-5 | ~$0.50 |
| **Budget** | Gemini 3.1 Flash Lite, GLM-4.7 Flash, Qwen3.5 Flash, GPT-5.3 Chat | ~$0.08 |
| **Premium** | Claude Opus, GPT-5.4, Gemini 3.1 Pro, Kimi, Qwen (x2), GLM | ~$1.80 |

Pricing is fetched live from OpenRouter at startup.

---

## Project Structure

```
IdeaCouncil/
├── app.py                         # Main Streamlit app
├── requirements.txt
├── config/
│   ├── models.yaml                # Model registry and phase settings
│   ├── settings.py                # Config loader
│   ├── user_profile.example.yaml  # Profile template
│   └── user_profile.yaml          # Your profile (gitignored)
├── core/
│   ├── council.py                 # Orchestrates all three phases
│   ├── member.py                  # Individual model wrapper
│   ├── anonymizer.py              # Blind peer review shuffler
│   ├── phase_manager.py
│   └── iteration_tracker.py
├── api/
│   ├── openrouter_client.py       # Async API client with retries
│   ├── rate_limiter.py
│   └── cost_tracker.py
├── prompts/
│   ├── diverge_prompts.py
│   ├── criticize_prompts.py
│   ├── converge_prompts.py
│   └── prompt_builder.py
├── ui/
│   ├── sidebar.py
│   ├── progress_display.py
│   └── report_viewer.py
└── utils/
    ├── context_manager.py         # Phase-aware context truncation
    ├── report_generator.py
    ├── validator.py
    └── logger.py
```

---

## Acknowledgements

- Inspired by [Andrej Karpathy's LLM Council](https://github.com/karpathy/llm-council)
- Built with [Streamlit](https://streamlit.io/)
- Powered by [OpenRouter API](https://openrouter.ai/)
- Models by Anthropic, OpenAI, Google, Moonshot AI, Alibaba, Zhipu AI

---

## License

MIT
