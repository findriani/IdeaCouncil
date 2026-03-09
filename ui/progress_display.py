"""
Progress display components.
"""

import streamlit as st
from typing import Optional

class ProgressDisplay:
    """Display progress updates during council execution."""

    def __init__(self, verbosity: str = "Progress"):
        """
        Initialize progress display.

        Args:
            verbosity: Display level (Minimal/Progress/Full)
        """
        self.verbosity = verbosity
        self.progress_bar = None
        self.status_text = None
        self.phase_container = None

    def start(self):
        """Start progress display."""
        if self.verbosity == "Minimal":
            self.status_text = st.empty()
            self.status_text.info("🔄 Processing...")

        elif self.verbosity == "Progress":
            self.progress_bar = st.progress(0)
            self.status_text = st.empty()
            self.phase_container = st.container()

        else:  # Full
            self.progress_bar = st.progress(0)
            self.status_text = st.empty()
            self.phase_container = st.container()

    def update(self, update_type: str, message: str):
        """
        Update progress display.

        Args:
            update_type: Type of update (iteration/phase/complete)
            message: Update message
        """
        if update_type == "iteration":
            if self.verbosity in ["Progress", "Full"]:
                self.status_text.info(f"🔄 {message}")

        elif update_type == "phase":
            if self.verbosity == "Progress":
                # Update progress bar based on phase
                if "Diverge" in message:
                    self.progress_bar.progress(0.2)
                elif "Criticize" in message:
                    self.progress_bar.progress(0.5)
                elif "Converge" in message:
                    self.progress_bar.progress(0.8)

                self.status_text.info(f"⚙️ {message}")

            elif self.verbosity == "Full":
                if "Diverge" in message:
                    self.progress_bar.progress(0.2)
                elif "Criticize" in message:
                    self.progress_bar.progress(0.5)
                elif "Converge" in message:
                    self.progress_bar.progress(0.8)

                with self.phase_container:
                    st.write(f"**{message}**")

        elif update_type == "complete":
            if self.progress_bar:
                self.progress_bar.progress(1.0)

            if self.status_text:
                self.status_text.success(f"✅ {message}")

    def finish(self):
        """Complete progress display."""
        if self.progress_bar:
            self.progress_bar.progress(1.0)

        if self.status_text:
            self.status_text.success("✅ Complete!")

    def error(self, message: str):
        """Display error message."""
        if self.status_text:
            self.status_text.error(f"❌ {message}")
        else:
            st.error(f"❌ {message}")


def display_phase_results(phase_name: str, results: dict, verbosity: str = "Progress"):
    """
    Display results from a phase.

    Args:
        phase_name: Name of the phase
        results: Phase results
        verbosity: Display verbosity
    """
    if verbosity == "Minimal":
        return

    with st.expander(f"📋 {phase_name} Results", expanded=(verbosity == "Full")):
        if phase_name == "Diverge":
            for member_id, data in results.items():
                st.write(f"**{member_id}**")
                ideas = data.get("ideas", [])
                for i, idea in enumerate(ideas, 1):
                    st.write(f"{i}. **{idea.get('title', 'Untitled')}**")
                    if verbosity == "Full":
                        st.write(f"   {idea.get('summary', '')}")

        elif phase_name == "Criticize":
            for member_id, data in results.items():
                if verbosity == "Full":
                    st.write(f"**{member_id}**")
                    critiques = data.get("critiques", [])
                    st.write(f"   Evaluated {len(critiques)} ideas")

        elif phase_name == "Converge":
            synthesis = results.get("synthesis", "")
            if synthesis:
                st.markdown(synthesis[:500] + "..." if len(synthesis) > 500 else synthesis)
