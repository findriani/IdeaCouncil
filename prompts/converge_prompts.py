"""
Converge phase prompt templates.
Low temperature (0.3) for focused synthesis.
"""

from typing import Dict, Any, List

CONVERGE_SYSTEM_PROMPT = """You are a senior research advisor synthesizing multiple perspectives and ideas.
Your role is to identify the best research ideas based on collective feedback and rank them clearly.

Provide actionable recommendations with clear reasoning."""

def build_converge_prompt(
    all_ideas: List[Dict[str, Any]],
    all_critiques: Dict[str, List[Dict[str, Any]]],
    user_profile: Dict[str, Any],
    top_n: int = 5,
    additional_context: str = "",
    novelty_assessments: Dict[str, int] = None,
) -> str:
    """
    Build converge phase prompt for synthesis.

    Args:
        all_ideas: All generated ideas from diverge phase
        all_critiques: All critiques organized by member
        user_profile: User research profile
        top_n: Number of top ideas to recommend
    novelty_assessments: {idea_id: novelty_score} from the dedicated novelty critic

    Returns:
        Formatted prompt string
    """
    if novelty_assessments is None:
        novelty_assessments = {}
    prompt_parts = []

    # Task
    prompt_parts.append(f"**Task:** Synthesize all research ideas and critiques to identify the top {top_n} recommendations.")
    prompt_parts.append("")

    # Context
    goals = user_profile.get("goals", {})
    if goals.get("primary"):
        prompt_parts.append(f"**Research Goal:** {goals['primary']}")
        prompt_parts.append("")

    # Minimal context (dataset name / topic only)
    if additional_context:
        prompt_parts.append(f"**Dataset/Topic:** {additional_context}")
        prompt_parts.append("")

    # All ideas summary
    prompt_parts.append(f"**All Generated Ideas ({len(all_ideas)} total):**")
    prompt_parts.append("")

    for i, idea in enumerate(all_ideas, 1):
        prompt_parts.append(f"{i}. **{idea.get('title', 'Untitled')}**")
        prompt_parts.append(f"   Summary: {idea.get('summary', '')[:150]}")
        # Include methodological fields so coordinator can assess novelty
        if idea.get('gap'):
            prompt_parts.append(f"   Gap: {idea.get('gap', '')[:120]}")
        if idea.get('novel_component'):
            prompt_parts.append(f"   Novel Component: {idea.get('novel_component', '')[:120]}")
        elif idea.get('methodology'):
            prompt_parts.append(f"   Methodology: {idea.get('methodology', '')[:120]}")
        prompt_parts.append("")

    # Critique summary — grouped by stable idea_id (assigned after diverge)
    prompt_parts.append("**Collective Critiques:**")
    prompt_parts.append("")

    idea_critiques: Dict[str, List[str]] = {}
    for member_id, critiques in all_critiques.items():
        for critique in critiques:
            idea_id = critique.get("idea_id")
            if not idea_id:
                continue
            if idea_id not in idea_critiques:
                idea_critiques[idea_id] = []

            assessment = critique.get("overall_assessment", "")
            recommendation = critique.get("recommendation", "")
            # Novelty comes from the dedicated novelty critic (kimi_novelty), not general critics
            novelty = novelty_assessments.get(idea_id, "N/A")
            feasibility = critique.get("feasibility_score", "N/A")
            impact = critique.get("impact_score", "N/A")

            summary = (
                f"{member_id}: {assessment} | "
                f"Novelty: {novelty}/5 | Feasibility: {feasibility}/5 | "
                f"Impact: {impact}/5 | {recommendation}"
            )
            idea_critiques[idea_id].append(summary)

    for i, idea in enumerate(all_ideas, 1):
        idea_id = idea.get("idea_id", "")
        if idea_id in idea_critiques:
            prompt_parts.append(f"**Idea {i}: {idea.get('title', 'Untitled')}**")
            for critique_summary in idea_critiques[idea_id]:
                prompt_parts.append(f"  - {critique_summary}")
            prompt_parts.append("")

    # Synthesis instructions
    prompt_parts.append("**Synthesis Task:**")
    prompt_parts.append("")
    prompt_parts.append(f"1. Analyze all ideas and their critiques")
    prompt_parts.append(f"2. Identify the top {top_n} most promising ideas based on:")
    prompt_parts.append("   - Collective feedback (novelty, feasibility, and impact scores)")
    prompt_parts.append("   - Alignment with research goals")
    prompt_parts.append("   - Practical viability")
    prompt_parts.append("   - Potential for meaningful outcomes")
    prompt_parts.append(f"3. Rank them from best to {top_n}th best")
    prompt_parts.append("   **Ranking priority:** Weight novelty most heavily — it is the hardest publishability bar to clear.")
    prompt_parts.append("   Then weight impact, then feasibility. Use qualitative judgment informed by all critique text, not just the numbers.")
    prompt_parts.append("4. Provide clear rationale for each recommendation")
    prompt_parts.append("5. Identify common themes across ideas")
    prompt_parts.append("")

    # Output format
    prompt_parts.append("**Output Format:** Use plain markdown only — ## headers and --- dividers.")
    prompt_parts.append("Do NOT use ASCII art separators (═══, ───, ===) anywhere in the output.")
    prompt_parts.append("")
    prompt_parts.append("```")
    prompt_parts.append("## Executive Summary")
    prompt_parts.append("[2-3 sentences on the strongest directions and what makes them stand out]")
    prompt_parts.append("")
    prompt_parts.append("## Common Themes")
    prompt_parts.append("- [Theme 1]")
    prompt_parts.append("- [Theme 2]")
    prompt_parts.append("- [Theme 3]")
    prompt_parts.append("")
    prompt_parts.append("---")
    prompt_parts.append("")
    prompt_parts.append("## Rank 1: [Idea title]")
    prompt_parts.append("")
    prompt_parts.append("**Why this ranks #1:** [Reasoning grounded in collective scores and critiques]")
    prompt_parts.append("")
    prompt_parts.append("**Methodology sketch:**")
    prompt_parts.append("- Dataset / data preparation: [what subset, splits, label choices]")
    prompt_parts.append("- Novel component: [what the core method does and why it addresses the gap]")
    prompt_parts.append("- Experiments: [what to run — e.g. model A vs. baseline B vs. ablation C — and on which metric]")
    prompt_parts.append("- Evaluation: [primary metric, secondary metrics, any qualitative analysis]")
    prompt_parts.append("")
    prompt_parts.append("**Feasibility:** [High / Medium / Low — one sentence justification]")
    prompt_parts.append("")
    prompt_parts.append("**Key risk:** [The single most important challenge to address early]")
    prompt_parts.append("")
    prompt_parts.append("---")
    prompt_parts.append("")
    prompt_parts.append("[Repeat ## Rank N block for each remaining rank]")
    prompt_parts.append("")
    prompt_parts.append("## Honorable Mentions")
    prompt_parts.append("[Ideas that scored well but overlap with higher-ranked ones — one line each with a note on what makes them distinct or how they could be merged]")
    prompt_parts.append("```")
    prompt_parts.append("")
    prompt_parts.append("Keep each rank block focused. The methodology sketch is the most important field — make it specific enough that the researcher can start working from it directly.")

    return "\n".join(prompt_parts)
