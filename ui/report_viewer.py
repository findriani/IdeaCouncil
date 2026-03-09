"""
Report viewer and export components.
"""

import streamlit as st
from typing import Dict, Any, List
from pathlib import Path

def display_report(
    report_content: str,
    recommendations_content: str,
    cost_summary: Dict[str, Any],
    iterations_data: List[Dict[str, Any]]
):
    """
    Display final report with tabs.

    Args:
        report_content: Full markdown report content (download only)
        recommendations_content: Short top-recommendations report (shown on screen)
        cost_summary: Cost breakdown
        iterations_data: All iteration data
    """
    tabs = st.tabs(["🏆 Top Recommendations", "💡 All Ideas", "💬 Critiques", "💰 Cost Breakdown"])

    # Top Recommendations Tab
    with tabs[0]:
        # Download buttons at the top
        col_dl1, col_dl2, col_spacer = st.columns([2, 2, 3])
        with col_dl1:
            st.download_button(
                label="⬇️ Top Recommendations (.md)",
                data=recommendations_content,
                file_name="llm_council_recommendations.md",
                mime="text/markdown",
                type="primary",
                use_container_width=True
            )
        with col_dl2:
            st.download_button(
                label="⬇️ Full Report (.md)",
                data=report_content,
                file_name="llm_council_full_report.md",
                mime="text/markdown",
                use_container_width=True
            )

        st.divider()
        st.markdown(recommendations_content)

    # All Ideas Tab
    with tabs[1]:
        st.subheader("All Generated Ideas")

        for i, iteration in enumerate(iterations_data, 1):
            st.write(f"### Iteration {i}")

            diverge_data = iteration.get("diverge", {})

            for member_id, data in diverge_data.items():
                with st.expander(f"**{member_id}** ({data.get('model', 'Unknown')})", expanded=False):
                    ideas = data.get("ideas", [])

                    if ideas:
                        for j, idea in enumerate(ideas, 1):
                            st.write(f"**Idea {j}: {idea.get('title', 'Untitled')}**")
                            if idea.get('summary'):
                                st.write(f"*Summary:* {idea.get('summary')}")
                            if idea.get('methodology'):
                                st.write(f"*Methodology:* {idea.get('methodology')}")
                            if idea.get('feasibility'):
                                st.write(f"*Feasibility:* {idea.get('feasibility')}")
                            if idea.get('timeline'):
                                st.write(f"*Timeline:* {idea.get('timeline')}")
                            st.divider()
                    else:
                        # Parsing failed — show raw response as fallback
                        raw = data.get("raw_response", "")
                        if raw:
                            st.markdown(raw)
                        else:
                            st.write("No ideas available.")

    # Critiques Tab
    with tabs[2]:
        st.subheader("Critical Evaluations")

        for i, iteration in enumerate(iterations_data, 1):
            st.write(f"### Iteration {i}")

            criticize_data = iteration.get("criticize", {})

            for member_id, data in criticize_data.items():
                with st.expander(f"**{member_id}** Critiques", expanded=False):
                    raw_response = data.get("raw_response", "")
                    if raw_response:
                        st.markdown(raw_response)
                    else:
                        st.write("No critiques available")

    # Cost Breakdown Tab
    with tabs[3]:
        st.subheader("Cost Analysis")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Total Cost", f"${cost_summary.get('total_cost', 0):.4f}")
            st.metric("Total Requests", cost_summary.get('request_count', 0))

        with col2:
            token_usage = cost_summary.get('token_usage', {})
            st.metric("Input Tokens", f"{token_usage.get('input_tokens', 0):,}")
            st.metric("Output Tokens", f"{token_usage.get('output_tokens', 0):,}")

        # Cost by phase
        st.write("**Cost by Phase**")
        by_phase = cost_summary.get('by_phase', {})

        if by_phase:
            phase_data = {
                "Phase": list(by_phase.keys()),
                "Cost": [f"${v:.4f}" for v in by_phase.values()]
            }
            st.table(phase_data)

        # Cost by model
        st.write("**Cost by Model**")
        by_model = cost_summary.get('by_model', {})

        if by_model:
            model_data = {
                "Model": list(by_model.keys()),
                "Cost": [f"${v:.4f}" for v in by_model.values()]
            }
            st.table(model_data)


def display_quick_summary(iterations_data: List[Dict[str, Any]]):
    """
    Display quick summary of results.

    Args:
        iterations_data: Iteration data
    """
    if not iterations_data:
        st.info("No results yet. Start brainstorming to see recommendations.")
        return

    st.success(f"✅ Completed {len(iterations_data)} iteration(s)")

    final_iteration = iterations_data[-1]

    if "converge" in final_iteration:
        top_ideas = final_iteration["converge"].get("top_ideas", [])

        if top_ideas:
            st.write("**Top Recommendations:**")

            for i, idea in enumerate(top_ideas[:3], 1):
                title = idea.get("title", "Untitled")
                st.write(f"{i}. {title}")

        # Show executive summary if available
        synthesis = final_iteration["converge"].get("synthesis", "")
        if "EXECUTIVE SUMMARY:" in synthesis:
            summary_start = synthesis.find("EXECUTIVE SUMMARY:") + len("EXECUTIVE SUMMARY:")
            summary_end = synthesis.find("\n\n", summary_start)
            if summary_end > summary_start:
                executive_summary = synthesis[summary_start:summary_end].strip()
                st.info(executive_summary)


def display_refinement_section(
    can_iterate: bool,
    current_iteration: int,
    max_iterations: int
) -> str:
    """
    Display refinement/feedback section.

    Args:
        can_iterate: Whether another iteration is allowed
        current_iteration: Current iteration number
        max_iterations: Maximum iterations

    Returns:
        User feedback text
    """
    st.subheader("🔄 Refine Results")

    if not can_iterate:
        st.warning(f"Maximum {max_iterations} iterations reached. Start a new session to continue.")
        return ""

    st.write(f"Iteration {current_iteration} of {max_iterations}")

    feedback = st.text_area(
        "Provide feedback for refinement",
        placeholder="e.g., 'Focus more on educational applications' or 'Make ideas more practical for undergraduates'",
        help="Your feedback will guide the next iteration",
        key="refinement_feedback"
    )

    return feedback
