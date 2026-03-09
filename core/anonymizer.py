"""
Idea anonymization for unbiased peer review.
Inspired by Karpathy's LLM Council implementation.
"""

import random
from typing import Dict, List, Any, Tuple

class IdeaAnonymizer:
    """
    Anonymize ideas to prevent brand bias during peer review.

    Models may exhibit favoritism toward prestigious brands (e.g., preferring
    ideas from "Claude" or "GPT-4"). By anonymizing, we ensure evaluation
    based purely on merit.
    """

    def __init__(self, shuffle: bool = True):
        """
        Initialize anonymizer.

        Args:
            shuffle: Whether to randomize order (prevents position bias)
        """
        self.shuffle = shuffle

    def anonymize_ideas(
        self,
        ideas_by_member: Dict[str, List[Dict[str, Any]]]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        """
        Anonymize all ideas with random contributor IDs.

        Args:
            ideas_by_member: {member_id: [idea1, idea2, ...], ...}

        Returns:
            Tuple of:
            - anonymized_ideas: List of ideas with contributor_id instead of member_id
            - reverse_map: {contributor_id: member_id} for de-anonymization
        """
        anonymized = []
        reverse_map = {}

        # Flatten all ideas with their source
        all_ideas = []
        for member_id, ideas in ideas_by_member.items():
            for idea in ideas:
                all_ideas.append((member_id, idea))

        # Shuffle to prevent order-based attribution
        if self.shuffle:
            random.shuffle(all_ideas)

        # Assign anonymous IDs
        for idx, (member_id, idea) in enumerate(all_ideas):
            anonymous_id = f"Contributor_{idx + 1}"

            # Create clean copy without member attribution
            anon_idea = {k: v for k, v in idea.items() if k != "member_id"}
            anon_idea["contributor_id"] = anonymous_id

            anonymized.append(anon_idea)
            reverse_map[anonymous_id] = member_id

        return anonymized, reverse_map

    def get_ideas_for_member(
        self,
        member_id: str,
        all_anonymized: List[Dict[str, Any]],
        reverse_map: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Get anonymized ideas excluding a specific member's own ideas.

        Args:
            member_id: ID of the member who will review
            all_anonymized: All anonymized ideas
            reverse_map: Mapping from contributor_id to member_id

        Returns:
            List of ideas for this member to review (excluding their own)
        """
        return [
            idea for idea in all_anonymized
            if reverse_map.get(idea["contributor_id"]) != member_id
        ]

    def de_anonymize_results(
        self,
        anonymized_results: Dict[str, Any],
        reverse_map: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        De-anonymize results after critique phase.

        Args:
            anonymized_results: Results with contributor_id references
            reverse_map: Mapping from contributor_id to member_id

        Returns:
            Results with member_id restored
        """
        de_anon = anonymized_results.copy()

        # Replace contributor_id references with member_id
        if "critiques" in de_anon:
            for critique in de_anon["critiques"]:
                if "contributor_id" in critique:
                    contributor_id = critique["contributor_id"]
                    critique["original_member_id"] = reverse_map.get(contributor_id, "Unknown")

        return de_anon

    @staticmethod
    def create_anonymization_notice() -> str:
        """
        Create notice to include in critique prompts.

        Returns:
            Text explaining anonymization
        """
        return """
⚠️ **IMPORTANT - ANONYMIZED REVIEW:**
- These ideas come from ANONYMOUS contributors
- You do NOT know which AI model generated each idea
- Contributor labels (e.g., "Contributor_1") are randomized
- Evaluate ideas purely on merit, not based on presumed source
- Avoid assumptions about quality based on contributor identity
"""
