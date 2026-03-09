"""
Diverge phase prompt templates.
High temperature (0.9) for creative idea generation.
"""

from typing import Dict, Any

DIVERGE_SYSTEM_PROMPT = """You are a creative research advisor helping to brainstorm novel research ideas.
Your goal is to generate innovative, feasible research ideas that align with the user's constraints and interests.

Be creative and diverse in your suggestions while remaining practical and grounded in reality."""

REASONING_MODEL_SUFFIX = """
---
**FINAL OUTPUT REQUIREMENT (REASONING MODELS):**
You may reason internally as much as needed. However, your **final output** must consist ONLY of the structured idea blocks in the exact format above.
Do not include any preamble, summary of your thinking, or meta-commentary in the final output.
Start directly with `IDEA 1:` and end after the last idea block.
"""

def build_diverge_prompt(
    user_prompt: str,
    user_profile: Dict[str, Any],
    ideas_per_member: int = 3,
    previous_feedback: str = "",
    dataset_context: str = "",
    literature_context: str = "",
    is_reasoning_model: bool = False
) -> str:
    """
    Build diverge phase prompt for idea generation.

    Args:
        user_prompt: User's research request
        user_profile: User research profile
        ideas_per_member: Number of ideas to generate
        previous_feedback: Feedback from previous iteration

    Returns:
        Formatted prompt string
    """
    # Extract profile information
    interests = user_profile.get("research_interests", {})
    resources = user_profile.get("resources", {})
    constraints = user_profile.get("constraints", {})
    goals = user_profile.get("goals", {})

    prompt_parts = []

    # User request
    prompt_parts.append(f"**Research Request:**\n{user_prompt}\n")

    # Dataset context (full — models need all details)
    if dataset_context:
        prompt_parts.append("**Dataset Description:**")
        prompt_parts.append(dataset_context)
        prompt_parts.append("")

    # Literature context (compact — avoid re-inventing known approaches)
    if literature_context:
        prompt_parts.append("**Related Work / Known Approaches (generate ideas that go beyond these):**")
        prompt_parts.append(literature_context)
        prompt_parts.append("")

    # User profile context
    prompt_parts.append("**Researcher Profile:**")

    if interests.get("primary_fields"):
        fields = ", ".join(interests["primary_fields"])
        prompt_parts.append(f"- Primary fields: {fields}")

    if interests.get("specific_topics"):
        topics = ", ".join(interests["specific_topics"])
        prompt_parts.append(f"- Specific interests: {topics}")

    if interests.get("avoid_topics"):
        avoid = ", ".join(interests["avoid_topics"])
        prompt_parts.append(f"- Topics to avoid: {avoid}")

    prompt_parts.append("")

    # Resources
    prompt_parts.append("**Available Resources:**")

    if resources.get("computational"):
        comp = ", ".join(resources["computational"])
        prompt_parts.append(f"- Computational: {comp}")

    if resources.get("datasets"):
        data = ", ".join(resources["datasets"])
        prompt_parts.append(f"- Data sources: {data}")

    if resources.get("budget"):
        prompt_parts.append(f"- Budget: {resources['budget'].get('api_costs', 'Limited')}")

    prompt_parts.append("")

    # Constraints
    prompt_parts.append("**Constraints:**")

    if constraints.get("technical"):
        for constraint in constraints["technical"]:
            prompt_parts.append(f"- {constraint}")

    if constraints.get("timeline"):
        for constraint in constraints["timeline"]:
            prompt_parts.append(f"- {constraint}")

    if constraints.get("expertise"):
        for constraint in constraints["expertise"]:
            prompt_parts.append(f"- {constraint}")

    prompt_parts.append("")

    # Goals
    if goals.get("primary"):
        prompt_parts.append(f"**Primary Goal:** {goals['primary']}\n")

    # Previous feedback (if iterating)
    if previous_feedback:
        prompt_parts.append("**Feedback from Previous Iteration:**")
        prompt_parts.append(previous_feedback)
        prompt_parts.append("")

    # Task instructions with orthogonality requirement
    prompt_parts.append(f"**Task:** Generate {ideas_per_member} distinct research ideas, each from a **different contribution type**.")
    prompt_parts.append("Assign one contribution type per idea — no two ideas may share the same type:")
    prompt_parts.append("- **New Problem Formulation** — Define a novel task, metric, or evaluation framework")
    prompt_parts.append("- **Feature Engineering** — Propose a new signal extraction or representation approach")
    prompt_parts.append("- **Lightweight Baseline** — Simple, interpretable method that establishes a strong baseline")
    prompt_parts.append("- **Data-Centric Study** — Analyze dataset quality, bias, distribution, or preprocessing impact")
    prompt_parts.append("- **Evaluation / Analysis Paper** — Comparative study, robustness analysis, or benchmark")
    prompt_parts.append("- **Methodology Improvement** — Adapt or extend an existing method in a novel way")
    prompt_parts.append("")
    prompt_parts.append("Each idea must also:")
    prompt_parts.append("1. Address the research request")
    prompt_parts.append("2. Be feasible within the given constraints")
    prompt_parts.append("3. Align with the researcher's interests and goals")
    prompt_parts.append("4. Be novel relative to any related work provided above")
    prompt_parts.append("5. Fit within the specified timeline")
    prompt_parts.append("")

    # Output format
    prompt_parts.append("**Output Format:** For each idea, provide:")
    prompt_parts.append("")
    prompt_parts.append("```")
    prompt_parts.append("IDEA [number]:")
    prompt_parts.append("Title: [Clear, descriptive title]")
    prompt_parts.append("Summary: [2-3 sentence overview]")
    prompt_parts.append("Methodology: [Specific approach and methods]")
    prompt_parts.append("Feasibility: [Why this is doable with given resources]")
    prompt_parts.append("Timeline: [Estimated duration and key milestones]")
    prompt_parts.append("Expected Outcomes: [What results to expect]")
    prompt_parts.append("```")
    prompt_parts.append("")
    prompt_parts.append("Generate creative, diverse ideas. Think outside the box while staying practical.")

    if is_reasoning_model:
        prompt_parts.append(REASONING_MODEL_SUFFIX)

    return "\n".join(prompt_parts)
