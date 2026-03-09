"""
Council member representing an individual LLM model.
"""

from typing import Dict, List, Any, Optional
from api.openrouter_client import OpenRouterClient
from utils.logger import logger
import json
import re

class CouncilMember:
    """Represents a single council member powered by an LLM."""

    def __init__(
        self,
        member_id: str,
        model_config: Dict[str, Any],
        api_client: OpenRouterClient
    ):
        """
        Initialize council member.

        Args:
            member_id: Unique identifier for this member
            model_config: Model configuration from settings
            api_client: OpenRouter API client
        """
        self.member_id = member_id
        self.model_config = model_config
        self.api_client = api_client
        self.conversation_history: List[Dict[str, str]] = []
        self.token_usage: Dict[str, int] = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0
        }

    async def generate_ideas(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """
        Generate research ideas (diverge phase).

        Args:
            messages: Prompt messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Dictionary with ideas and metadata
        """
        try:
            response = await self.api_client.chat_completion(
                model=self.model_config["openrouter_id"],
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            # Extract content and usage
            content = self.api_client.extract_content(response)
            usage = self.api_client.extract_usage(response)

            # Update token usage
            self._update_token_usage(usage)

            # Parse ideas from content
            ideas = self._parse_ideas(content)

            return {
                "member_id": self.member_id,
                "model": self.model_config["display_name"],
                "ideas": ideas,
                "raw_response": content,
                "usage": usage
            }

        except Exception as e:
            logger.error(f"Error generating ideas for {self.member_id}: {e}")
            return {
                "member_id": self.member_id,
                "model": self.model_config["display_name"],
                "ideas": [],
                "error": str(e),
                "usage": {"input_tokens": 0, "output_tokens": 0}
            }

    async def critique_ideas(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """
        Critique research ideas (criticize phase).

        Args:
            messages: Prompt messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Dictionary with critiques and metadata
        """
        try:
            response = await self.api_client.chat_completion(
                model=self.model_config["openrouter_id"],
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            # Extract content and usage
            content = self.api_client.extract_content(response)
            usage = self.api_client.extract_usage(response)

            # Update token usage
            self._update_token_usage(usage)

            # Parse critiques from content
            critiques = self._parse_critiques(content)

            return {
                "member_id": self.member_id,
                "model": self.model_config["display_name"],
                "critiques": critiques,
                "raw_response": content,
                "usage": usage
            }

        except Exception as e:
            logger.error(f"Error critiquing ideas for {self.member_id}: {e}")
            return {
                "member_id": self.member_id,
                "model": self.model_config["display_name"],
                "critiques": [],
                "error": str(e),
                "usage": {"input_tokens": 0, "output_tokens": 0}
            }

    def _parse_ideas(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse ideas from LLM response.

        Args:
            content: Raw response content

        Returns:
            List of parsed ideas
        """
        ideas = []

        # Split by "IDEA" markers
        idea_sections = re.split(r'IDEA\s+\d+:', content, flags=re.IGNORECASE)

        for section in idea_sections[1:]:  # Skip first empty section
            idea = {}

            # Extract fields using regex
            title_match = re.search(r'Title:\s*(.+)', section, re.IGNORECASE)
            if title_match:
                idea['title'] = title_match.group(1).strip()

            summary_match = re.search(r'Summary:\s*(.+?)(?=\n[A-Z]|\Z)', section, re.IGNORECASE | re.DOTALL)
            if summary_match:
                idea['summary'] = summary_match.group(1).strip()

            methodology_match = re.search(r'Methodology:\s*(.+?)(?=\n[A-Z]|\Z)', section, re.IGNORECASE | re.DOTALL)
            if methodology_match:
                idea['methodology'] = methodology_match.group(1).strip()

            feasibility_match = re.search(r'Feasibility:\s*(.+?)(?=\n[A-Z]|\Z)', section, re.IGNORECASE | re.DOTALL)
            if feasibility_match:
                idea['feasibility'] = feasibility_match.group(1).strip()

            timeline_match = re.search(r'Timeline:\s*(.+?)(?=\n[A-Z]|\Z)', section, re.IGNORECASE | re.DOTALL)
            if timeline_match:
                idea['timeline'] = timeline_match.group(1).strip()

            outcomes_match = re.search(r'Expected Outcomes:\s*(.+?)(?=\n[A-Z]|\Z)', section, re.IGNORECASE | re.DOTALL)
            if outcomes_match:
                idea['expected_outcomes'] = outcomes_match.group(1).strip()

            idea['member_id'] = self.member_id
            idea['full_description'] = section.strip()

            if idea.get('title'):  # Only add if we got at least a title
                ideas.append(idea)

        return ideas

    def _parse_critiques(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse critiques from LLM response.

        Args:
            content: Raw response content

        Returns:
            List of parsed critiques
        """
        critiques = []

        # Split by "CRITIQUE OF IDEA" markers
        critique_sections = re.split(r'CRITIQUE OF IDEA\s+\d+:', content, flags=re.IGNORECASE)

        for i, section in enumerate(critique_sections[1:]):  # Skip first empty section
            critique = {"idea_index": i}

            # Extract fields
            assessment_match = re.search(r'Overall Assessment:\s*(.+)', section, re.IGNORECASE)
            if assessment_match:
                critique['overall_assessment'] = assessment_match.group(1).strip()

            strengths_match = re.search(r'Strengths:\s*(.+?)(?=Weaknesses:|Feasibility Score:|\Z)', section, re.IGNORECASE | re.DOTALL)
            if strengths_match:
                critique['strengths'] = strengths_match.group(1).strip()

            weaknesses_match = re.search(r'Weaknesses:\s*(.+?)(?=Feasibility Score:|\Z)', section, re.IGNORECASE | re.DOTALL)
            if weaknesses_match:
                critique['weaknesses'] = weaknesses_match.group(1).strip()

            feasibility_match = re.search(r'Feasibility Score:\s*(\d+)', section, re.IGNORECASE)
            if feasibility_match:
                critique['feasibility_score'] = int(feasibility_match.group(1))

            novelty_match = re.search(r'Novelty Score:\s*(\d+)', section, re.IGNORECASE)
            if novelty_match:
                critique['novelty_score'] = int(novelty_match.group(1))

            publishability_match = re.search(r'Publishability Score:\s*(\d+)', section, re.IGNORECASE)
            if publishability_match:
                critique['publishability_score'] = int(publishability_match.group(1))

            recommendation_match = re.search(r'Recommendation:\s*(.+)', section, re.IGNORECASE)
            if recommendation_match:
                critique['recommendation'] = recommendation_match.group(1).strip()

            suggestions_match = re.search(r'Suggestions for Improvement:\s*(.+?)(?=\Z)', section, re.IGNORECASE | re.DOTALL)
            if suggestions_match:
                critique['suggestions'] = suggestions_match.group(1).strip()

            critique['member_id'] = self.member_id

            critiques.append(critique)

        return critiques

    def _update_token_usage(self, usage: Dict[str, int]) -> None:
        """Update cumulative token usage."""
        self.token_usage["input_tokens"] += usage.get("input_tokens", 0)
        self.token_usage["output_tokens"] += usage.get("output_tokens", 0)
        self.token_usage["total_tokens"] += usage.get("total_tokens", 0)

    def get_token_usage(self) -> Dict[str, int]:
        """Get total token usage for this member."""
        return self.token_usage.copy()

    def reset_usage(self) -> None:
        """Reset token usage counters."""
        self.token_usage = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0
        }
