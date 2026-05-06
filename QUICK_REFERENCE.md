# IdeaCouncil — Quick Reference

## Start the App

```bash
streamlit run app.py
```

---

## Key Files

| File | Purpose |
|------|---------|
| `app.py` | Main Streamlit application |
| `.env` | Your OpenRouter API key |
| `config/user_profile.yaml` | Your research profile (copy from `user_profile.example.yaml`) |
| `config/models.yaml` | Model registry, pricing, phase settings, critic roster |
| `README.md` | Full documentation |
| `QUICKSTART.md` | 5-minute setup guide |

---

## Workflow

```
Research prompt + optional context
        ↓
DIVERGE          — all selected models generate 4 ideas each (parallel, temp 0.9)
        ↓  near-duplicates removed
LITERATURE CHECK — 4-6 queries generated from ideas → SemanticScholar + OpenAlex
                   → ~700-word report (last 5 years, ~$0.01, graceful fallback)
        ↓
CRITICIZE        — split into two parallel tracks (temp 0.5)
  Track A: 4 general critics → Feasibility + Impact only
  Track B: Kimi K2.6 (novelty pass) → Novelty only, full lit context + live report
        ↓
CONVERGE         — Claude Sonnet synthesizes top 6, weights novelty most heavily (temp 0.3)
        ↓
Full report + optional next iteration (up to 3 total)
```

---

## Designated Critics

Regardless of which generator models you select, these 4 always critique:

- **Claude Sonnet** (also the converge coordinator) — Feasibility + Impact
- **GPT-5.4** — Feasibility + Impact
- **Kimi K2.6** — Feasibility + Impact (general pass) **+ Novelty only** (dedicated pass)
- **DeepSeek V4 Pro** — Feasibility + Impact

Kimi makes two calls per run: one as a general critic (excluding own ideas), and one as the dedicated Novelty critic (all ideas, full literature context + live search report).

To change the roster, edit `critic_models` in `config/models.yaml` → `phase_settings.criticize`.
To change the novelty critic, edit `novelty_critic` in the same section.

---

## Critique Scores

Scoring is split across two tracks:

| Score | Scored by | What it measures |
|-------|-----------|-----------------|
| **Novelty** | Kimi K2.6 (dedicated pass) — full lit context + live search report | Is this idea original vs. existing and recent work? |
| **Feasibility** | 4 general critics | How well-scoped and executable is this as a complete, bounded paper? |
| **Impact** | 4 general critics | If it works, how significant is the advance? |

Converge ranks ideas with **Novelty weighted most heavily**, then Impact, then Feasibility.

---

## Idea Fields

Each generated idea contains:

`Contribution Type` · `Title` · `Summary` · `Gap` · `Novel Component` · `Pipeline` · `Feasibility` · `Expected Outcomes`

The **Gap → Novel Component → Pipeline** structure separates the problem from the solution — useful for evaluating how publishable the core novelty is.

---

## Contribution Types (default)

| Type | Core novelty lives in... |
|------|--------------------------|
| Novel Pipeline Component | A new mechanism for a specific processing step |
| Inductive Bias / Architecture | Model structure assumptions |
| Training Paradigm | How the model learns (contrastive, self-supervised, etc.) |
| Lightweight Baseline | Simplicity that reveals something about the problem |
| Evaluation / Analysis Paper | A new benchmark, metric, or robustness study |
| New Problem Formulation | A new task structure where the challenge itself is novel |

Each council member must use a **different type per idea** — enforcing structural diversity across the idea pool.

---

## Cost Estimates

| Configuration | Est. cost/iteration |
|--------------|-------------------|
| Default (7 generators, 4 critics + Kimi novelty pass) | $0.55–$0.90 |
| Fewer generators (3–4 models) | $0.35–$0.60 |
| Literature Check (all configs) | +~$0.01 |

Critics are the main cost driver (~55–65% of total). Kimi now makes 2 calls per run (general + novelty pass). The literature check adds ~$0.01 via two Gemini Flash Lite calls — SemanticScholar and OpenAlex are free. Reduce overall cost by selecting fewer generator models.

---

## Common Commands

```bash
# Install
pip install -r requirements.txt

# Verify
python verify_installation.py

# Run
streamlit run app.py

# Tests
pytest tests/ -v
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `API key cannot be empty` | Add key to `.env` or enter in sidebar |
| `Insufficient credits` | Add credits at openrouter.ai/credits |
| `Module not found` | `pip install -r requirements.txt` |
| App won't start | Try `python -m streamlit run app.py` (Python 3.8+ required) |
| Stuck at Criticize phase | A model is timing out — others will still complete; check terminal log |
| Prompt cleared after profile edit | Fixed in current version — profile editor now preserves main page inputs |

---

## Example Prompts

**Specific (recommended):**
```
ML research ideas for multimodal spoilage detection using RGB, thermal IR,
and gas sensor data. Undergraduate thesis, 6 months, Google Colab T4 available,
targeting Q2/Q3 Scopus journal.
```

**Broad:**
```
Novel NLP ideas for low-resource Indonesian language processing, master's level,
no GPU, 4 months.
```

---

## Environment Variables

```bash
# .env
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

Get your key: https://openrouter.ai/keys

---

**Run:** `streamlit run app.py`
