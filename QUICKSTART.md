# Quick Start Guide

Get IdeaCouncil running in 5 minutes.

---

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Set Up API Key

1. Get your OpenRouter API key at [openrouter.ai/keys](https://openrouter.ai/keys)
2. Create a `.env` file in the project root:

```
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
```

## Step 3: Set Up Your Profile

```bash
cp config/user_profile.example.yaml config/user_profile.yaml
```

Edit `user_profile.yaml` with your research field, compute constraints, and goals — or use the sidebar editor in the app.

## Step 4: Run

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`.

---

## Step 5: Start Brainstorming

1. **Sidebar:** Enter your API key (if not using `.env`) and select the Default preset
2. **Main area:** Enter your research prompt
3. **Optional:** Expand "Additional Context" to paste a dataset description and related literature — this significantly improves idea quality
4. **Click "Start Brainstorming"**

**Expected runtime:** 3–10 minutes depending on model selection. Reasoning models (Kimi, GLM) take longer but produce more structured outputs.

---

## What to Expect

With the Default preset (7 generator models, 4 ideas each):

- **28 ideas generated** in diverge (near-duplicates removed automatically)
- **4 designated critics** (Claude, GPT, Kimi, DeepSeek) each evaluate all ideas with Novelty / Publishability / Impact scores
- **Top 6 ideas ranked** in converge, each with a full methodology sketch

**Typical cost per iteration:** $0.50–$0.85 with the Default preset.

---

## Tips

- **Be specific in your prompt** — "ML ideas for a 6-month undergrad thesis on multimodal spoilage detection using RGB + IR + gas sensors" beats "ML research ideas"
- **Fill in the context slots** — dataset description and literature context are the biggest quality multipliers
- **Use the profile editor** — the sidebar profile editor preserves your main page inputs (prompt, dataset, literature) when you open and close it
- **Iterate** — after the first run, provide feedback and run a second iteration to refine the direction
- **Check the Critiques tab** — scroll through individual critic scores to see which ideas were controversial (high score variance) vs. unanimously rated

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `API key cannot be empty` | Check your `.env` file exists and the key is correct |
| `Insufficient credits` | Add credits at [openrouter.ai/credits](https://openrouter.ai/credits) |
| `Module not found` | Run `pip install -r requirements.txt` in the project directory |
| App won't start | Check Python 3.8+: `python --version` — then try `python -m streamlit run app.py` |
| Stuck at Criticize for 10+ min | A model is timing out — check the terminal log; the others will still complete |

---

## Changing the Critics

The default critic roster is Claude, GPT, Kimi, and DeepSeek. To change it, edit `config/models.yaml`:

```yaml
phase_settings:
  criticize:
    critic_models: ["claude_sonnet_latest", "kimi", "deepseek", "chatgpt"]
```

Use any model key listed under `available_models`. If a critic model was not selected as a generator, it will be instantiated as a critic-only participant and will review all ideas.

---

**Full documentation:** [README.md](README.md)
