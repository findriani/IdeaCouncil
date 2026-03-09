"""
Dynamic prompt construction with user context injection.
"""

from typing import Dict, Any, List, Optional
from prompts.diverge_prompts import DIVERGE_SYSTEM_PROMPT, build_diverge_prompt
from prompts.criticize_prompts import CRITICIZE_SYSTEM_PROMPT, build_criticize_prompt
from prompts.converge_prompts import CONVERGE_SYSTEM_PROMPT, build_converge_prompt
from utils.context_manager import ContextManager


class PromptBuilder:
    """Build prompts for different phases with user context."""

    def __init__(self, user_profile: Dict[str, Any], context_manager: Optional[ContextManager] = None):
        """
        Initialize prompt builder.

        Args:
            user_profile: User research profile
            context_manager: Optional additional context (dataset description, etc.)
        """
        self.user_profile = user_profile
        self.context_manager = context_manager or ContextManager()

    def build_diverge_messages(
        self,
        user_prompt: str,
        ideas_per_member: int = 3,
        previous_feedback: str = "",
        is_reasoning_model: bool = False
    ) -> List[Dict[str, str]]:
        """
        Diverge phase: full dataset context + compact literature context.
        Reasoning models get a structured-output instruction appended.
        """
        ctx = self.context_manager.for_diverge()
        prompt = build_diverge_prompt(
            user_prompt=user_prompt,
            user_profile=self.user_profile,
            ideas_per_member=ideas_per_member,
            previous_feedback=previous_feedback,
            dataset_context=ctx["dataset"],
            literature_context=ctx["literature"],
            is_reasoning_model=is_reasoning_model
        )
        return [
            {"role": "system", "content": DIVERGE_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]

    def build_criticize_messages(
        self,
        ideas_to_review: List[Dict[str, Any]],
        is_reasoning_model: bool = False,
        anonymized: bool = False,
    ) -> List[Dict[str, str]]:
        """
        Criticize phase: compact dataset + compact literature context.
        Reasoning models get a structured-output instruction appended.
        When anonymized=True, contributor labels replace model names.
        """
        ctx = self.context_manager.for_criticize()
        prompt = build_criticize_prompt(
            ideas_to_review=ideas_to_review,
            user_profile=self.user_profile,
            dataset_context=ctx["dataset"],
            literature_context=ctx["literature"],
            is_reasoning_model=is_reasoning_model,
            anonymized=anonymized,
        )
        return [
            {"role": "system", "content": CRITICIZE_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]

    def build_converge_messages(
        self,
        all_ideas: List[Dict[str, Any]],
        all_critiques: Dict[str, List[Dict[str, Any]]],
        top_n: int = 5
    ) -> List[Dict[str, str]]:
        """
        Converge phase: minimal dataset context only (no literature needed).
        """
        ctx = self.context_manager.for_converge()
        prompt = build_converge_prompt(
            all_ideas=all_ideas,
            all_critiques=all_critiques,
            user_profile=self.user_profile,
            top_n=top_n,
            additional_context=ctx["dataset"]
        )
        return [
            {"role": "system", "content": CONVERGE_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]

    def update_user_profile(self, user_profile: Dict[str, Any]) -> None:
        """Update user profile for future prompts."""
        self.user_profile = user_profile

    def update_context(self, context_manager: ContextManager) -> None:
        """Update additional context."""
        self.context_manager = context_manager
