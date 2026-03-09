"""
Cost tracking for API requests.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json

class CostTracker:
    """Track API costs across requests."""

    def __init__(self):
        """Initialize cost tracker."""
        self.requests: List[Dict[str, Any]] = []

    def log_request(
        self,
        model: str,
        phase: str,
        member_id: str,
        input_tokens: int,
        output_tokens: int,
        input_cost_per_1m: float,
        output_cost_per_1m: float,
        timestamp: Optional[datetime] = None
    ) -> float:
        """
        Log an API request and calculate its cost.

        Args:
            model: Model identifier
            phase: Phase name (diverge/criticize/converge)
            member_id: Council member identifier
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            input_cost_per_1m: Input cost per 1M tokens
            output_cost_per_1m: Output cost per 1M tokens
            timestamp: Request timestamp (defaults to now)

        Returns:
            Cost of this request in USD
        """
        if timestamp is None:
            timestamp = datetime.now()

        # Calculate cost
        input_cost = (input_tokens / 1_000_000) * input_cost_per_1m
        output_cost = (output_tokens / 1_000_000) * output_cost_per_1m
        total_cost = input_cost + output_cost

        # Log request
        self.requests.append({
            "timestamp": timestamp.isoformat(),
            "model": model,
            "phase": phase,
            "member_id": member_id,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost
        })

        return total_cost

    def get_total_cost(self) -> float:
        """Get total cost across all requests."""
        return sum(req["total_cost"] for req in self.requests)

    def get_cost_by_phase(self) -> Dict[str, float]:
        """Get cost breakdown by phase."""
        phase_costs: Dict[str, float] = {}

        for req in self.requests:
            phase = req["phase"]
            cost = req["total_cost"]
            phase_costs[phase] = phase_costs.get(phase, 0.0) + cost

        return phase_costs

    def get_cost_by_model(self) -> Dict[str, float]:
        """Get cost breakdown by model."""
        model_costs: Dict[str, float] = {}

        for req in self.requests:
            model = req["model"]
            cost = req["total_cost"]
            model_costs[model] = model_costs.get(model, 0.0) + cost

        return model_costs

    def get_token_usage(self) -> Dict[str, int]:
        """Get total token usage."""
        total_input = sum(req["input_tokens"] for req in self.requests)
        total_output = sum(req["output_tokens"] for req in self.requests)

        return {
            "input_tokens": total_input,
            "output_tokens": total_output,
            "total_tokens": total_input + total_output
        }

    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive cost summary."""
        return {
            "total_cost": self.get_total_cost(),
            "by_phase": self.get_cost_by_phase(),
            "by_model": self.get_cost_by_model(),
            "token_usage": self.get_token_usage(),
            "request_count": len(self.requests)
        }

    def export_to_json(self) -> str:
        """Export all request data to JSON."""
        return json.dumps({
            "summary": self.get_summary(),
            "requests": self.requests
        }, indent=2)

    def reset(self) -> None:
        """Clear all tracked requests."""
        self.requests.clear()
