"""
Generate a standalone prompt for use in any external LLM (web chat, API, etc.).
The user copies this prompt and pastes it — along with any context — into their LLM of choice.
"""

from typing import Any, Dict, List, Optional
from prompts.diverge_prompts import DEFAULT_CONTRIBUTION_TYPES


_HEADER = """\
================================================================================
  IDEACOUNCIL — EXTERNAL IDEA GENERATION PROMPT
  Copy this prompt and paste it into your preferred LLM.
  Attach or paste your dataset description and literature context alongside it.
  Fill in your research request in the section marked below.
================================================================================

INSTRUCTIONS
------------
You are acting as an external contributor for a research brainstorming session.
Generate structured research ideas based on the researcher profile and request
in this prompt, as well as any dataset or literature context provided.

OUTPUT RULES (strict):
- Output ONLY the structured idea blocks shown in the Output Format section.
- Start directly with "IDEA 1:" — no preamble, no commentary, no summary.
- End immediately after the last idea block.
- Follow the field names and order exactly as specified.
"""

_SECTION = lambda title: f"\n{'=' * 80}\n  {title}\n{'=' * 80}\n"


def build_external_prompt(
    user_profile: Dict[str, Any],
    ideas_per_member: int = 3,
    research_request: str = "",
) -> str:
    """
    Build a self-contained prompt .txt for external use in Claude.ai.

    Args:
        user_profile:      Researcher profile dict (from user_profile.yaml).
        ideas_per_member:  How many ideas to request (matches app setting).
        research_request:  Optional pre-filled research request. If empty, a
                           placeholder is inserted for the user to fill in.

    Returns:
        Full prompt text, ready to save as .txt and upload to Claude.ai.
    """
    parts = [_HEADER]

    # ── Researcher profile ────────────────────────────────────────────────────
    parts.append(_SECTION("RESEARCHER PROFILE"))

    interests = user_profile.get("research_interests", {})
    resources = user_profile.get("resources", {})
    constraints = user_profile.get("constraints", {})
    goals = user_profile.get("goals", {})

    if interests.get("primary_fields"):
        parts.append(f"Primary fields: {', '.join(interests['primary_fields'])}")
    if interests.get("specific_topics"):
        parts.append(f"Specific topics: {', '.join(interests['specific_topics'])}")
    if interests.get("avoid_topics"):
        parts.append(f"Topics to AVOID: {', '.join(interests['avoid_topics'])}")

    parts.append("")

    if constraints.get("expertise"):
        parts.append("Expertise / Background:")
        for c in constraints["expertise"]:
            parts.append(f"  - {c}")
    if constraints.get("technical"):
        parts.append("Technical constraints:")
        for c in constraints["technical"]:
            parts.append(f"  - {c}")
    if constraints.get("timeline"):
        parts.append("Timeline:")
        for c in constraints["timeline"]:
            parts.append(f"  - {c}")

    parts.append("")

    if resources.get("computational"):
        parts.append(f"Compute: {', '.join(resources['computational'])}")
    if resources.get("datasets"):
        parts.append(f"Data sources: {', '.join(resources['datasets'])}")
    if resources.get("budget"):
        parts.append(f"Budget: {resources['budget'].get('api_costs', 'Limited')}")

    parts.append("")

    if goals.get("primary"):
        parts.append(f"Primary goal: {goals['primary']}")
    if goals.get("secondary"):
        parts.append("Secondary goals:")
        for g in goals["secondary"]:
            parts.append(f"  - {g}")

    # ── Research request ──────────────────────────────────────────────────────
    parts.append(_SECTION("RESEARCH REQUEST  ← FILL THIS IN BEFORE UPLOADING"))

    if research_request.strip():
        parts.append(research_request.strip())
    else:
        parts.append(
            "[PASTE YOUR RESEARCH REQUEST HERE]\n\n"
            "Example: 'I need ML research ideas for Alzheimer's detection using the\n"
            "MRI dataset described in the uploaded context files. Undergraduate level,\n"
            "6-month thesis, Google Colab only.'"
        )

    # ── Dataset / literature note ─────────────────────────────────────────────
    parts.append(_SECTION("CONTEXT (provided alongside this prompt)"))
    parts.append(
        "The user will also provide additional context:\n"
        "  - Dataset description  (describes the data you will work with)\n"
        "  - Literature context   (related work and known approaches)\n\n"
        "Use that context to ensure ideas are grounded in the actual dataset and\n"
        "go beyond approaches already covered in the literature."
    )

    # ── Contribution types ────────────────────────────────────────────────────
    raw_types = user_profile.get("contribution_types", [])
    if raw_types:
        contribution_types = [(t, "") for t in raw_types]
    else:
        contribution_types = DEFAULT_CONTRIBUTION_TYPES

    parts.append(_SECTION("TASK"))
    parts.append(
        f"Generate {ideas_per_member} distinct research ideas, each assigned to a "
        f"DIFFERENT contribution type.\nNo two ideas may share the same type.\n"
    )
    parts.append("Available contribution types (pick one per idea):")
    for name, description in contribution_types:
        line = f"  - {name}"
        if description:
            line += f" — {description}"
        parts.append(line)

    parts.append("")
    parts.append("Each idea must also:")
    parts.append("  1. Address the research request above")
    parts.append("  2. Be feasible within the stated constraints")
    parts.append("  3. Be novel relative to the literature context")
    parts.append("  4. Fit within the stated timeline")

    # ── Output format ─────────────────────────────────────────────────────────
    parts.append(_SECTION("OUTPUT FORMAT  ← FOLLOW EXACTLY"))
    parts.append(
        "Repeat the block below for each idea. "
        f"You must produce exactly {ideas_per_member} blocks.\n"
        "Do NOT add any text before IDEA 1: or after the last block.\n"
    )

    for n in range(1, ideas_per_member + 1):
        parts.append(f"IDEA {n}:")
        parts.append("Contribution Type: [Type from the list above]")
        parts.append("Title: [Clear, descriptive title]")
        parts.append("Summary: [2-3 sentence overview]")
        parts.append("Gap: [The research gap or open problem this idea addresses]")
        parts.append("Novel Component: [The key novelty of the proposed approach]")
        parts.append("Pipeline: [Step-by-step methodology — data prep, model, experiments, evaluation]")
        parts.append("Feasibility: [Why this is doable with the given resources]")
        parts.append("Expected Outcomes: [What results to expect]")
        parts.append("")

    parts.append("=" * 80)

    return "\n".join(parts)
