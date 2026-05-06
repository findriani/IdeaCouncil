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
    tabs = st.tabs(["🏆 Top Recommendations", "💡 All Ideas", "💬 Critiques", "🔬 Literature Check", "💰 Cost Breakdown"])

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
            dedup_report = iteration.get("dedup_report", [])

            for member_id, data in diverge_data.items():
                with st.expander(f"**{member_id}** ({data.get('model', 'Unknown')})", expanded=False):
                    ideas = data.get("ideas", [])

                    if ideas:
                        for j, idea in enumerate(ideas, 1):
                            ct = idea.get('contribution_type', '')
                            title_line = f"**Idea {j}: {idea.get('title', 'Untitled')}**"
                            if ct:
                                title_line += f"  `{ct}`"
                            st.write(title_line)
                            if idea.get('summary'):
                                st.write(f"*Summary:* {idea.get('summary')}")
                            if idea.get('gap'):
                                st.warning(f"**Gap:** {idea.get('gap')}")
                            if idea.get('novel_component'):
                                st.success(f"**Novel Component:** {idea.get('novel_component')}")
                            if idea.get('pipeline'):
                                st.write(f"*Pipeline:* {idea.get('pipeline')}")
                            # legacy field fallback
                            if idea.get('methodology') and not idea.get('pipeline'):
                                st.write(f"*Methodology:* {idea.get('methodology')}")
                            if idea.get('feasibility'):
                                st.write(f"*Feasibility:* {idea.get('feasibility')}")
                            st.divider()
                    else:
                        # Parsing failed — show raw response as fallback
                        raw = data.get("raw_response", "")
                        if raw:
                            st.markdown(raw)
                        else:
                            st.write("No ideas available.")

            if dedup_report:
                with st.expander(
                    f"Near-Duplicates Filtered Before Review — {len(dedup_report)} idea(s)",
                    expanded=False
                ):
                    st.caption(
                        "These ideas were removed before the criticize phase because they were "
                        "too similar to another idea already in the pool (cosine similarity > 0.75). "
                        "They are shown here for transparency."
                    )
                    for entry in dedup_report:
                        sim_pct = int(entry.get("similarity_score", 0) * 100)
                        st.write(
                            f"- **{entry.get('removed_title', 'Untitled')}** → similar to "
                            f"**{entry.get('duplicate_of_title', 'Untitled')}** "
                            f"({sim_pct}% similarity)"
                        )

    # Critiques Tab
    with tabs[2]:
        st.subheader("Critical Evaluations")

        for i, iteration in enumerate(iterations_data, 1):
            st.write(f"### Iteration {i}")

            controversy = iteration.get("controversy", {})
            criticize_data = iteration.get("criticize", {})

            # Novelty Assessment (separate dedicated pass — currently Gemini 3 Flash)
            kimi_novelty = criticize_data.get("kimi_novelty", {})
            if kimi_novelty:
                with st.expander("**Gemini 3 Flash — Novelty Assessments** (dedicated novelty critic)", expanded=False):
                    assessments = kimi_novelty.get("assessments", [])
                    if not assessments:
                        raw = kimi_novelty.get("raw_response", "")
                        if raw:
                            st.markdown(raw)
                        else:
                            st.write("No novelty assessments available.")
                    else:
                        for assessment in assessments:
                            st.markdown(f"**Idea {assessment.get('idea_index', 0) + 1}**")
                            col_n, col_blank = st.columns([1, 2])
                            with col_n:
                                st.metric("Novelty Score", assessment.get("novelty_score", "—"))
                            if assessment.get("closest_prior_work"):
                                st.write(f"**Closest Prior Work:** {assessment['closest_prior_work']}")
                            if assessment.get("novelty_justification"):
                                st.write(f"**Justification:** {assessment['novelty_justification']}")
                            st.divider()

            # General critics (Feasibility + Impact)
            for member_id, data in criticize_data.items():
                if member_id == "kimi_novelty":
                    continue  # already displayed above

                with st.expander(f"**{member_id}** Critiques", expanded=False):
                    critiques = data.get("critiques", [])

                    if not critiques:
                        raw_response = data.get("raw_response", "")
                        if raw_response:
                            st.markdown(raw_response)
                        else:
                            st.write("No critiques available")
                        continue

                    for critique in critiques:
                        idea_id = critique.get("idea_id", "")
                        idea_controversy = controversy.get(idea_id, {})
                        is_controversial = idea_controversy.get("is_controversial", False)

                        # Header with optional controversy badge
                        header = f"**Idea {critique.get('idea_index', 0) + 1}**"
                        if is_controversial:
                            header += "   🔥 Controversial"
                        st.markdown(header)

                        if is_controversial:
                            n_rev = idea_controversy.get("num_reviews", 0)
                            st.caption(
                                f"High score variance across {n_rev} reviewer(s) — "
                                f"Feasibility: {idea_controversy.get('mean_feasibility', 0):.1f}"
                                f"±{idea_controversy.get('std_feasibility', 0):.1f}  |  "
                                f"Impact: {idea_controversy.get('mean_impact', 0):.1f}"
                                f"±{idea_controversy.get('std_impact', 0):.1f}"
                            )

                        if critique.get("steelman"):
                            st.info(f"**Steelman:** {critique['steelman']}")

                        if critique.get("overall_assessment"):
                            st.write(f"**Assessment:** {critique['overall_assessment']}")

                        col_f, col_i = st.columns(2)
                        with col_f:
                            st.metric("Feasibility", critique.get("feasibility_score", "—"))
                        with col_i:
                            st.metric("Impact", critique.get("impact_score", "—"))

                        if critique.get("strengths"):
                            st.write(f"**Strengths:**\n{critique['strengths']}")
                        if critique.get("weaknesses"):
                            st.write(f"**Weaknesses:**\n{critique['weaknesses']}")
                        if critique.get("recommendation"):
                            st.write(f"**Recommendation:** {critique['recommendation']}")
                        if critique.get("suggestions"):
                            st.write(f"**Suggestions:** {critique['suggestions']}")

                        st.divider()

    # Literature Check Tab
    with tabs[3]:
        st.subheader("Literature Check")
        st.caption(
            "Targeted academic search run between the Diverge and Criticize phases. "
            "Results were used by the dedicated Novelty critic (Kimi K2.6) alongside "
            "your uploaded literature context."
        )

        for i, iteration in enumerate(iterations_data, 1):
            if len(iterations_data) > 1:
                st.write(f"### Iteration {i}")

            lit_check = iteration.get("literature_check", {})

            if not lit_check:
                st.info("No literature check data for this iteration.")
                continue

            if lit_check.get("skipped"):
                st.warning(
                    f"Literature check was skipped — {lit_check.get('error', 'APIs unreachable')}. "
                    "Novelty scoring used only the uploaded literature context."
                )
                continue

            # Search queries
            queries = lit_check.get("queries", [])
            if queries:
                with st.expander(f"Search Queries ({len(queries)} generated)", expanded=True):
                    for q in queries:
                        st.write(f"- {q}")

            # Papers found
            papers = lit_check.get("papers", [])
            if papers:
                with st.expander(f"Papers Found ({len(papers)} unique)", expanded=False):
                    # Group by query label for display
                    by_query: dict = {}
                    for paper in papers:
                        q_label = paper.get("query_label", "Other")
                        by_query.setdefault(q_label, []).append(paper)

                    for q_label, q_papers in by_query.items():
                        st.write(f"**Query:** {q_label}")
                        for paper in q_papers:
                            source = paper.get("source", "")
                            badge = "**[S2]**" if source == "SemanticScholar" else "**[OA]**"
                            year = paper.get("year", "?")
                            citations = paper.get("citation_count", 0)
                            title = paper.get("title", "Unknown")
                            st.write(f"  {badge} {title} ({year}, {citations:,} citations)")
                        st.write("")

            # Summarised report
            report = lit_check.get("report", "")
            if report:
                st.write("**Literature Landscape Report**")
                st.info(report)

    # Cost Breakdown Tab
    with tabs[4]:
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
