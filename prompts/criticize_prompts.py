"""
Criticize phase prompt templates.
Lower temperature (0.5) for balanced evaluation.
"""

from typing import Dict, Any, List

CRITICIZE_SYSTEM_PROMPT = """You are a rigorous research evaluator with expertise in assessing research proposals.
Your role is to provide constructive, critical feedback on research ideas, identifying strengths and weaknesses.

Be thorough, fair, and specific in your critiques. Focus on feasibility, novelty, methodology, and value."""

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
    prompt_parts.append("")

    if anonymized:
        prompt_parts.append(
            "⚠️ **ANONYMIZED REVIEW:** These ideas come from anonymous contributors. "
            "You do not know which model generated each one. "
            "Evaluate on merit only — ignore contributor labels entirely."
        )
        prompt_parts.append("")

    # Evaluation criteria
    prompt_parts.append("**Evaluation Criteria:**")
    prompt_parts.append("1. **Feasibility:** Can this be completed with available resources and constraints?")
    prompt_parts.append("2. **Novelty:** Is this idea original relative to existing work?")
    prompt_parts.append("3. **Publishability:** Would this make a clear, defensible contribution to a research venue?")
    prompt_parts.append("4. **Experimental Clarity:** Is the validation plan concrete and convincing?")
    prompt_parts.append("5. **Scope:** Is the scope appropriate for the timeline and expertise level?")
    prompt_parts.append("6. **Dependency Risk:** Does this rely on external tools, data, or approvals that may be unavailable?")
    prompt_parts.append("7. **Value:** Will this produce meaningful, reusable results?")
    prompt_parts.append("")

    # Dataset context (compact — key facts for feasibility assessment)
    if dataset_context:
        prompt_parts.append(f"**Dataset:** {dataset_context}")
        prompt_parts.append("")

    # Literature context (compact — assess novelty against known work)
    if literature_context:
        prompt_parts.append(f"**Known Related Work (use to assess novelty):** {literature_context}")
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
        prompt_parts.append(f"**Title:** {idea.get('title', 'Untitled')}")
        prompt_parts.append(f"**Summary:** {idea.get('summary', '')}")
        prompt_parts.append(f"**Methodology:** {idea.get('methodology', '')}")
        prompt_parts.append(f"**Feasibility:** {idea.get('feasibility', '')}")
        prompt_parts.append(f"**Timeline:** {idea.get('timeline', '')}")
        prompt_parts.append("")

    # Output instructions
    prompt_parts.append("**Output Format:** For each idea, provide:")
    prompt_parts.append("")
    prompt_parts.append("```")
    prompt_parts.append("CRITIQUE OF IDEA [number]:")
    prompt_parts.append("Overall Assessment: [Strong/Moderate/Weak with brief reasoning]")
    prompt_parts.append("Strengths:")
    prompt_parts.append("- [List 2-3 key strengths]")
    prompt_parts.append("Weaknesses:")
    prompt_parts.append("- [List 2-3 key concerns, including dependency risks if any]")
    prompt_parts.append("Feasibility Score: [1-5, where 5 is highly feasible]")
    prompt_parts.append("Novelty Score: [1-5, where 5 is highly novel]")
    prompt_parts.append("Publishability Score: [1-5, where 5 is clearly publishable at a research venue]")
    prompt_parts.append("Recommendation: [Highly Recommend/Recommend/Consider/Not Recommended]")
    prompt_parts.append("Suggestions for Improvement: [Specific actionable suggestions]")
    prompt_parts.append("```")
    prompt_parts.append("")
    prompt_parts.append("Be honest and constructive. Identify both strengths and areas for improvement.")

    if is_reasoning_model:
        prompt_parts.append(REASONING_MODEL_SUFFIX)

    return "\n".join(prompt_parts)
