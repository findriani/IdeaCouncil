# Literature Summarization Prompt

Use this prompt to condense a long literature review into a compact briefing
before pasting it into LLMCouncil's "Related Literature" context field.

---

## Prompt

```
You are preparing a research landscape briefing for a creative brainstorming session.
Given the following literature, produce a compact briefing that covers:

1. **The Established Territory** (what is well-covered — avoid re-proposing these)
   - Dominant methods and their typical results
   - Standard datasets and evaluation protocols

2. **Why Current Work Falls Short** (not gaps to fill — context for why novelty matters)
   - Core assumptions most papers share that could be questioned
   - Evaluation or methodology weaknesses that make results hard to trust

3. **Open Terrain** (stated as observations, not prescriptions)
   - Conditions, populations, or problem framings rarely studied
   - Combinations of ideas that have not appeared together

Rules:
- Write as background context, NOT as a list of suggested research directions
- Do not use language like "future work should..." or "a promising direction is..."
- Target length: ~1000 words / ~7000 characters
- A creative reader should finish this and feel informed, not instructed

Literature to summarize:
[PASTE YOUR LITERATURE HERE]
```

---

## Usage

1. Run this prompt in any capable LLM (Claude, GPT, Gemini)
2. Paste the output into LLMCouncil's **Related Literature** field
3. The briefing will be injected into the Diverge and Criticize phases

## Why this framing

The goal is to give council members *awareness* of the landscape, not a to-do list
of gaps. Models told "here are the gaps" will fill them incrementally. Models told
"here is what exists and why it falls short" can go sideways — proposing genuinely
novel framings rather than obvious extensions.
