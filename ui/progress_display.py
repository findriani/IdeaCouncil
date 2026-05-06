"""
Progress display components.
"""

import streamlit as st


# Progress bar positions for each phase
_PHASE_PROGRESS = {
    "Diverge":           0.20,
    "Literature Check":  0.40,
    "Criticize":         0.65,
    "Converge":          0.85,
}


class ProgressDisplay:
    """Display progress updates during council execution."""

    def __init__(self, verbosity: str = "Full"):
        # verbosity parameter kept for backwards compat but no longer used
        self.progress_bar = None
        self.status_text = None
        self.phase_container = None

    def start(self):
        """Start progress display."""
        self.progress_bar = st.progress(0)
        self.status_text = st.empty()
        self.phase_container = st.container()

    def update(self, update_type: str, message: str):
        """Update progress display."""
        if update_type == "iteration":
            self.status_text.info(f"🔄 {message}")

        elif update_type == "phase":
            # Find matching phase key and advance progress bar
            for key, pct in _PHASE_PROGRESS.items():
                if key in message:
                    self.progress_bar.progress(pct)
                    break

            self.status_text.info(f"⚙️ {message}")
            with self.phase_container:
                st.write(f"**{message}**")

        elif update_type == "complete":
            self.progress_bar.progress(1.0)
            self.status_text.success(f"✅ {message}")

    def finish(self):
        """Complete progress display."""
        self.progress_bar.progress(1.0)
        self.status_text.success("✅ Complete!")

    def error(self, message: str):
        """Display error message."""
        if self.status_text:
            self.status_text.error(f"❌ {message}")
        else:
            st.error(f"❌ {message}")


def display_phase_results(phase_name: str, results: dict, verbosity: str = "Full"):
    """
    Display results from a phase as an expanded expander.

    Args:
        phase_name: Name of the phase
        results:    Phase results dict
        verbosity:  Kept for backwards compat — always expands
    """
    with st.expander(f"📋 {phase_name} Results", expanded=True):
        if phase_name == "Diverge":
            for member_id, data in results.items():
                st.write(f"**{member_id}**")
                ideas = data.get("ideas", [])
                for i, idea in enumerate(ideas, 1):
                    st.write(f"{i}. **{idea.get('title', 'Untitled')}**")
                    st.write(f"   {idea.get('summary', '')}")

        elif phase_name == "Criticize":
            for member_id, data in results.items():
                if member_id == "kimi_novelty":
                    assessments = data.get("assessments", [])
                    st.write(f"**Kimi K2.6 (novelty pass)** — {len(assessments)} idea(s) assessed")
                else:
                    critiques = data.get("critiques", [])
                    st.write(f"**{member_id}** — evaluated {len(critiques)} idea(s)")

        elif phase_name == "Converge":
            synthesis = results.get("synthesis", "")
            if synthesis:
                st.markdown(synthesis[:500] + "..." if len(synthesis) > 500 else synthesis)
