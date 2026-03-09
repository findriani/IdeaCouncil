"""
Phase workflow management.
"""

from enum import Enum
from typing import Optional

class Phase(Enum):
    """Workflow phases."""
    DIVERGE = "diverge"
    CRITICIZE = "criticize"
    CONVERGE = "converge"

class PhaseManager:
    """Manages phase transitions and state."""

    def __init__(self, max_iterations: int = 3):
        """
        Initialize phase manager.

        Args:
            max_iterations: Maximum number of iterations allowed
        """
        self.max_iterations = max_iterations
        self.current_iteration = 0
        self.current_phase: Optional[Phase] = None

    def start_iteration(self) -> None:
        """Start a new iteration."""
        if self.current_iteration >= self.max_iterations:
            raise ValueError(f"Maximum {self.max_iterations} iterations reached")

        self.current_iteration += 1
        self.current_phase = Phase.DIVERGE

    def advance_phase(self) -> Phase:
        """
        Advance to next phase.

        Returns:
            Next phase

        Raises:
            ValueError: If invalid phase transition
        """
        if self.current_phase is None:
            raise ValueError("No active iteration")

        if self.current_phase == Phase.DIVERGE:
            self.current_phase = Phase.CRITICIZE
        elif self.current_phase == Phase.CRITICIZE:
            self.current_phase = Phase.CONVERGE
        elif self.current_phase == Phase.CONVERGE:
            # Iteration complete
            self.current_phase = None
        else:
            raise ValueError(f"Invalid phase: {self.current_phase}")

        return self.current_phase

    def get_current_phase(self) -> Optional[Phase]:
        """Get current phase."""
        return self.current_phase

    def get_current_iteration(self) -> int:
        """Get current iteration number."""
        return self.current_iteration

    def can_iterate(self) -> bool:
        """Check if another iteration is allowed."""
        return self.current_iteration < self.max_iterations

    def is_iteration_complete(self) -> bool:
        """Check if current iteration is complete."""
        return self.current_phase is None and self.current_iteration > 0

    def reset(self) -> None:
        """Reset to initial state."""
        self.current_iteration = 0
        self.current_phase = None
