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
- **Context slots** — paste dataset description and literature review; app summarizes if too long
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
