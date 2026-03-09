"""
Track iterations and user feedback.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime

class IterationTracker:
    """Tracks iteration history and user feedback."""

    def __init__(self):
        """Initialize iteration tracker."""
        self.iterations: List[Dict[str, Any]] = []
        self.start_time: Optional[datetime] = None

    def start_session(self) -> None:
        """Start a new session."""
        self.start_time = datetime.now()
        self.iterations = []

    def add_iteration(
        self,
        iteration_number: int,
        diverge_results: Dict[str, Any],
        criticize_results: Dict[str, Any],
        converge_results: Dict[str, Any],
        user_feedback: str = ""
    ) -> None:
        """
        Add a completed iteration.

        Args:
            iteration_number: Iteration number
            diverge_results: Results from diverge phase
            criticize_results: Results from criticize phase
            converge_results: Results from converge phase
            user_feedback: User feedback for next iteration
        """
        iteration_data = {
            "iteration": iteration_number,
            "timestamp": datetime.now().isoformat(),
            "diverge": diverge_results,
            "criticize": criticize_results,
            "converge": converge_results,
            "user_feedback": user_feedback
        }

        self.iterations.append(iteration_data)

    def get_all_iterations(self) -> List[Dict[str, Any]]:
        """Get all iteration data."""
        return self.iterations

    def get_latest_iteration(self) -> Optional[Dict[str, Any]]:
        """Get most recent iteration."""
        return self.iterations[-1] if self.iterations else None

    def get_previous_feedback(self) -> str:
        """Get feedback from previous iteration."""
        if len(self.iterations) > 0:
            return self.iterations[-1].get("user_feedback", "")
        return ""

    def get_all_ideas(self) -> List[Dict[str, Any]]:
        """Get all ideas from all iterations."""
        all_ideas = []

        for iteration in self.iterations:
            diverge_data = iteration.get("diverge", {})
            for member_id, member_data in diverge_data.items():
                ideas = member_data.get("ideas", [])
                all_ideas.extend(ideas)

        return all_ideas

    def get_session_duration(self) -> Optional[float]:
        """Get session duration in seconds."""
        if self.start_time:
            return (datetime.now() - self.start_time).total_seconds()
        return None

    def get_context_for_next_iteration(self) -> Dict[str, Any]:
        """
        Get context needed for next iteration.

        Returns:
            Dictionary with previous results and feedback
        """
        latest = self.get_latest_iteration()

        if not latest:
            return {
                "has_previous": False,
                "previous_feedback": "",
                "previous_ideas": [],
                "previous_synthesis": ""
            }

        # Extract top ideas from converge phase
        converge_data = latest.get("converge", {})
        top_ideas = converge_data.get("top_ideas", [])

        return {
            "has_previous": True,
            "previous_feedback": latest.get("user_feedback", ""),
            "previous_ideas": top_ideas,
            "previous_synthesis": converge_data.get("synthesis", ""),
            "iteration_number": latest.get("iteration", 0)
        }

    def reset(self) -> None:
        """Clear all tracked data."""
        self.iterations = []
        self.start_time = None
