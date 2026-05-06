"""
Criticize phase prompt templates.
Lower temperature (0.5) for balanced evaluation.
"""

from typing import Dict, Any, List

CRITICIZE_SYSTEM_PROMPT = """You are a rigorous research evaluator with expertise in assessing research proposals.
Your role is to provide constructive, critical feedback on research ideas, identifying strengths and weaknesses.

Be thorough, fair, and specific in your critiques. Focus on feasibility, impact, methodology, and value."""

NOVELTY_SYSTEM_PROMPT = """You are a specialist in research novelty assessment.
Your sole task is to evaluate how original each research idea is relative to existing and recent published work.
Do not assess feasibility or impact — focus exclusively on whether the core contribution is genuinely novel."""

REASONING_MODEL_SUFFIX = """
---
**FINAL OUTPUT REQUIREMENT (REASONING MODELS):**
You may reason internally as much as needed. However, your **final output** must consist ONLY of the structured critique blocks in the exact format above.
Do not include any preamble, summary of your thinking, or meta-commentary in the final output.
Start directly with `CRITIQUE OF IDEA 1:` and end after the last critique block.
"""

def build_criticize_prompt(
    ideas_to_review: List[Dict[str, Any]],
    user_profile: Dict[str, Any],
    dataset_context: str = "",
    literature_context: str = "",
    is_reasoning_model: bool = False,
    anonymized: bool = False,
) -> str:
    """
    Build criticize phase prompt for idea evaluation.

    Args:
        ideas_to_review: List of ideas to critique (excluding own ideas)
        user_profile: User research profile

    Returns:
        Formatted prompt string
    """
    prompt_parts = []

    # Context
    prompt_parts.append("**Task:** Critically evaluate the following research ideas.")
    prompt_parts.append(
        "For each idea, **first write a steelman** — the strongest possible argument "
        "*in favour* of the idea — before evaluating it. "
        "This prevents premature dismissal and ensures genuine merit is acknowledged."
    )
    prompt_parts.append("")

    if anonymized:
        prompt_parts.append(
            "⚠️ **ANONYMIZED REVIEW:** These ideas come from anonymous contributors. "
            "You do not know which model generated each one. "
            "Evaluate on merit only — ignore contributor labels entirely."
        )
        prompt_parts.append("")

    # Evaluation criteria (Novelty is assessed separately by the dedicated novelty critic)
    prompt_parts.append("**Evaluation Criteria:**")
    prompt_parts.append("1. **Feasibility:** How well-scoped and executable is this as a complete, bounded paper? Consider scope fit, concreteness of the method, and clarity of the evaluation path.")
    prompt_parts.append("2. **Impact:** If this idea succeeds, how significant is the advance — to the research community, to practitioners, or both?")
    prompt_parts.append("3. **Experimental Clarity:** Is the validation plan concrete and convincing?")
    prompt_parts.append("4. **Scope:** Is the scope appropriate for the expertise level?")
    prompt_parts.append("5. **Dependency Risk:** Does this rely on external tools, data, or approvals that may be unavailable?")
    prompt_parts.append("6. **Value:** Will this produce meaningful, reusable results?")
    prompt_parts.append("")

    # Dataset context (compact — key facts for feasibility assessment)
    if dataset_context:
        prompt_parts.append(f"**Dataset:** {dataset_context}")
        prompt_parts.append("")

    # Literature context (compact — calibrate impact significance against known work)
    if literature_context:
        prompt_parts.append(f"**Field Context (use to calibrate impact significance):** {literature_context}")
        prompt_parts.append("")

    # Researcher context
    constraints = user_profile.get("constraints", {})
    if constraints:
        prompt_parts.append("**Researcher Constraints (for context):**")
        if constraints.get("technical"):
            prompt_parts.append(f"- Technical: {', '.join(constraints['technical'][:2])}")
        if constraints.get("timeline"):
            prompt_parts.append(f"- Timeline: {', '.join(constraints['timeline'][:2])}")
        prompt_parts.append("")

    # Ideas to review
    prompt_parts.append("**Ideas to Evaluate:**")
    prompt_parts.append("")

    for i, idea in enumerate(ideas_to_review, 1):
        label = idea.get("contributor_id", f"Idea {i}") if anonymized else str(i)
        prompt_parts.append(f"### IDEA {i} ({label})" if anonymized else f"### IDEA {i}")
        if idea.get('contribution_type'):
            prompt_parts.append(f"**Contribution Type:** {idea.get('contribution_type')}")
        prompt_parts.append(f"**Title:** {idea.get('title', 'Untitled')}")
        prompt_parts.append(f"**Summary:** {idea.get('summary', '')}")
        # Use new structured fields; fall back to legacy methodology field
        if idea.get('gap'):
            prompt_parts.append(f"**Gap:** {idea.get('gap')}")
        if idea.get('novel_component'):
            prompt_parts.append(f"**Novel Component:** {idea.get('novel_component')}")
        if idea.get('pipeline'):
            prompt_parts.append(f"**Pipeline:** {idea.get('pipeline')}")
        elif idea.get('methodology'):
            prompt_parts.append(f"**Methodology:** {idea.get('methodology')}")
        if idea.get('feasibility'):
            prompt_parts.append(f"**Feasibility:** {idea.get('feasibility')}")
        prompt_parts.append("")

    # Output instructions
    prompt_parts.append("**Output Format:** For each idea, provide the fields below.")
    prompt_parts.append("**Strict word limits apply — do not exceed them. You are reviewing many ideas; brevity is required.**")
    prompt_parts.append("")
    prompt_parts.append("```")
    prompt_parts.append("CRITIQUE OF IDEA [number]:")
    prompt_parts.append("Steelman: [max 40 words — the strongest argument a proponent would make]")
    prompt_parts.append("Overall Assessment: [Strong/Moderate/Weak] [max 20 words reasoning]")
    prompt_parts.append("Strengths: [2 bullets, max 15 words each]")
    prompt_parts.append("Weaknesses: [2 bullets, max 15 words each]")
    prompt_parts.append("Feasibility Score: [1-5] — how well-scoped and executable is this as a complete, bounded paper?")
    prompt_parts.append("Impact Score: [1-5] — if this idea succeeds, how significant is the advance to the field or practitioners?")
    prompt_parts.append("Recommendation: [Highly Recommend / Recommend / Consider / Not Recommended]")
    prompt_parts.append("Improvement: [max 30 words — one specific, actionable suggestion]")
    prompt_parts.append("```")
    prompt_parts.append("")
    prompt_parts.append("Be precise and direct. Complete all ideas — do not truncate the list.")

    if is_reasoning_model:
        prompt_parts.append(REASONING_MODEL_SUFFIX)

    return "\n".join(prompt_parts)


NOVELTY_REASONING_MODEL_SUFFIX = """
---
**FINAL OUTPUT REQUIREMENT (REASONING MODELS):**
You may reason internally as much as needed. However, your **final output** must consist ONLY of the structured novelty assessment blocks in the exact format above.
Do not include any preamble, summary of your thinking, or meta-commentary in the final output.
Start directly with `NOVELTY ASSESSMENT OF IDEA 1:` and end after the last assessment block.
"""


def build_novelty_critique_prompt(
    ideas_to_review: List[Dict[str, Any]],
    literature_context: str = "",
    literature_check_report: str = "",
    is_reasoning_model: bool = False,
) -> str:
    """
    Build the prompt for the dedicated Novelty critic (Kimi K2.6).

    This critic reviews ALL ideas (including its own) and scores only Novelty.
    It has access to the full uploaded literature context and the live
    literature check report generated from SemanticScholar + OpenAlex.

    Args:
        ideas_to_review:        All post-dedup ideas (anonymized)
        literature_context:     Full 7000-char uploaded literature context
        literature_check_report: ~700-word report from live literature search
        is_reasoning_model:     Append structured-output instruction if True

    Returns:
        Formatted prompt string
    """
    prompt_parts = []

    prompt_parts.append("**Task:** Assess the novelty of each research idea below against known prior work and recent literature.")
    prompt_parts.append("Score ONLY Novelty — do not assess feasibility or impact.")
    prompt_parts.append("")

    prompt_parts.append(
        "⚠️ **ANONYMIZED REVIEW:** These ideas come from anonymous contributors. "
        "Evaluate on merit only — ignore contributor labels entirely."
    )
    prompt_parts.append("")

    # Full uploaded literature context
    if literature_context:
        prompt_parts.append("**Known Prior Work (uploaded by researcher):**")
        prompt_parts.append(literature_context)
        prompt_parts.append("")

    # Live literature check report
    if literature_check_report:
        prompt_parts.append("**Live Literature Check — Papers Published in the Last 5 Years:**")
        prompt_parts.append(literature_check_report)
        prompt_parts.append("")

    # Ideas to assess (title + gap + novel_component only — novelty-relevant fields)
    prompt_parts.append("**Ideas to Assess:**")
    prompt_parts.append("")

    for i, idea in enumerate(ideas_to_review, 1):
        label = idea.get("contributor_id", f"Idea {i}")
        prompt_parts.append(f"### IDEA {i} ({label})")
        if idea.get("contribution_type"):
            prompt_parts.append(f"**Contribution Type:** {idea.get('contribution_type')}")
        prompt_parts.append(f"**Title:** {idea.get('title', 'Untitled')}")
        if idea.get("gap"):
            prompt_parts.append(f"**Gap:** {idea.get('gap')}")
        if idea.get("novel_component"):
            prompt_parts.append(f"**Novel Component:** {idea.get('novel_component')}")
        prompt_parts.append("")

    # Output format
    prompt_parts.append("**Output Format:** For each idea, provide the fields below.")
    prompt_parts.append("**Strict word limits apply — do not exceed them.**")
    prompt_parts.append("")
    prompt_parts.append("```")
    prompt_parts.append("NOVELTY ASSESSMENT OF IDEA [number]:")
    prompt_parts.append("Closest Prior Work: [most similar existing paper or approach, ≤20 words]")
    prompt_parts.append("Novelty Justification: [why this is or isn't original vs. known work, ≤30 words]")
    prompt_parts.append("Novelty Score: [1-5]")
    prompt_parts.append("```")
    prompt_parts.append("")
    prompt_parts.append("Complete all ideas. Be specific — cite paper titles or methods by name where possible.")

    if is_reasoning_model:
        prompt_parts.append(NOVELTY_REASONING_MODEL_SUFFIX)

    return "\n".join(prompt_parts)
