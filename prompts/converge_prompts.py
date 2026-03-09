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
    additional_context: str = ""
) -> str:
    """
    Build converge phase prompt for synthesis.

    Args:
        all_ideas: All generated ideas from diverge phase
        all_critiques: All critiques organized by member
        user_profile: User research profile
        top_n: Number of top ideas to recommend

    Returns:
        Formatted prompt string
    """
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
        prompt_parts.append(f"   Summary: {idea.get('summary', '')[:150]}...")
        prompt_parts.append(f"   Source: {idea.get('member_id', 'Unknown')}")
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
            feasibility = critique.get("feasibility_score", "N/A")
            novelty = critique.get("novelty_score", "N/A")
            publishability = critique.get("publishability_score", "N/A")

            summary = (
                f"{member_id}: {assessment} | "
                f"Feasibility: {feasibility}/5 | Novelty: {novelty}/5 | "
                f"Publishability: {publishability}/5 | {recommendation}"
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
    prompt_parts.append("   - Collective feedback (feasibility, novelty scores)")
    prompt_parts.append("   - Alignment with research goals")
    prompt_parts.append("   - Practical viability")
    prompt_parts.append("   - Potential for meaningful outcomes")
    prompt_parts.append(f"3. Rank them from best to {top_n}th best")
    prompt_parts.append("4. Provide clear rationale for each recommendation")
    prompt_parts.append("5. Identify common themes across ideas")
    prompt_parts.append("")

    # Output format
    prompt_parts.append("**Output Format:**")
    prompt_parts.append("")
    prompt_parts.append("```")
    prompt_parts.append("EXECUTIVE SUMMARY:")
    prompt_parts.append("[2-3 sentences summarizing the overall findings]")
    prompt_parts.append("")
    prompt_parts.append("COMMON THEMES:")
    prompt_parts.append("- [List 2-3 recurring themes across ideas]")
    prompt_parts.append("")
    prompt_parts.append("TOP RECOMMENDATIONS:")
    prompt_parts.append("")
    prompt_parts.append("RANK 1: [Idea title]")
    prompt_parts.append("Original Idea: [Brief summary]")
    prompt_parts.append("Why This Ranks #1: [Clear reasoning based on critiques]")
    prompt_parts.append("Feasibility: [High/Medium/Low with justification]")
    prompt_parts.append("Expected Timeline: [Estimated duration]")
    prompt_parts.append("Next Steps: [3-4 concrete first actions]")
    prompt_parts.append("Potential Challenges: [Key risks to address]")
    prompt_parts.append("")
    prompt_parts.append("[Repeat for ranks 2-5]")
    prompt_parts.append("")
    prompt_parts.append("HONORABLE MENTIONS:")
    prompt_parts.append("[Any other ideas worth considering, with brief notes]")
    prompt_parts.append("```")
    prompt_parts.append("")
    prompt_parts.append("Provide clear, actionable recommendations that synthesize the council's collective wisdom.")

    return "\n".join(prompt_parts)
