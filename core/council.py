"""
Council orchestration - coordinates all members through three-phase workflow.
"""

import asyncio
from typing import Dict, List, Any, Optional, Callable
from core.member import CouncilMember
from core.phase_manager import PhaseManager, Phase
from core.iteration_tracker import IterationTracker
from api.openrouter_client import OpenRouterClient
from api.cost_tracker import CostTracker
from prompts.prompt_builder import PromptBuilder
from utils.context_manager import ContextManager
from core.anonymizer import IdeaAnonymizer
from utils.logger import logger
import re

class Council:
    """Orchestrates multiple LLM members through brainstorming workflow."""

    # Claude Sonnet is always the coordinator/converger
    COORDINATOR_MODEL_KEY = "claude_sonnet"

    def __init__(
        self,
        model_configs: Dict[str, Dict[str, Any]],
        selected_model_keys: List[str],
        api_client: OpenRouterClient,
        cost_tracker: CostTracker,
        user_profile: Dict[str, Any],
        max_iterations: int = 3,
        ideas_per_member: int = 3,
        top_ideas_count: int = 5,
        context_manager: Optional[ContextManager] = None,
        phase_settings: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize council.

        Args:
            model_configs: All available model configurations
            selected_model_keys: Keys of models to use
            api_client: OpenRouter API client
            cost_tracker: Cost tracker instance
            user_profile: User research profile
            max_iterations: Maximum iterations
            ideas_per_member: Ideas to generate per member
            top_ideas_count: Top ideas to recommend
        """
        self.api_client = api_client
        self.cost_tracker = cost_tracker
        self.user_profile = user_profile
        self.ideas_per_member = ideas_per_member
        self.top_ideas_count = top_ideas_count

        # Initialize members
        self.members: List[CouncilMember] = []
        for i, model_key in enumerate(selected_model_keys):
            if model_key in model_configs:
                member = CouncilMember(
                    member_id=f"{model_key}_{i}",
                    model_config=model_configs[model_key],
                    api_client=api_client
                )
                self.members.append(member)

        if not self.members:
            raise ValueError("No valid models selected for council")

        # Coordinator/Converger: always Claude Sonnet, independent of member selection
        coordinator_config = model_configs.get(self.COORDINATOR_MODEL_KEY)
        if coordinator_config:
            self.coordinator = CouncilMember(
                member_id="coordinator",
                model_config=coordinator_config,
                api_client=api_client
            )
        else:
            # Fallback: use first member if Claude Sonnet config is missing
            self.coordinator = self.members[0] if self.members else None
            logger.warning("Claude Sonnet config not found; falling back to first member as coordinator")

        # Phase management
        self.phase_manager = PhaseManager(max_iterations=max_iterations)
        self.iteration_tracker = IterationTracker()
        self.prompt_builder = PromptBuilder(
            user_profile=user_profile,
            context_manager=context_manager or ContextManager()
        )

        # Phase settings (temperatures, max_tokens per phase) — passed from settings
        self.phase_settings = phase_settings or {}

        logger.info(
            f"Council initialized with {len(self.members)} members | "
            f"Coordinator: {self.coordinator.model_config.get('display_name', 'unknown')}"
        )

    async def run_iteration(
        self,
        user_prompt: str,
        user_feedback: str = "",
        progress_callback: Optional[Callable[[str, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Run one complete iteration (diverge-criticize-converge).

        Args:
            user_prompt: User's research request
            user_feedback: Feedback from previous iteration
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary with all phase results
        """
        # Start iteration
        self.phase_manager.start_iteration()
        iteration_num = self.phase_manager.get_current_iteration()

        logger.info(f"Starting iteration {iteration_num}")

        if progress_callback:
            progress_callback("iteration", f"Starting iteration {iteration_num}")

        # Run diverge phase
        if progress_callback:
            progress_callback("phase", "Diverge - Generating ideas")

        diverge_results = await self._run_diverge(user_prompt, user_feedback)

        self.phase_manager.advance_phase()

        # Run criticize phase
        if progress_callback:
            progress_callback("phase", "Criticize - Evaluating ideas")

        criticize_results = await self._run_criticize(diverge_results)

        self.phase_manager.advance_phase()

        # Run converge phase
        if progress_callback:
            progress_callback("phase", "Converge - Synthesizing recommendations")

        converge_results = await self._run_converge(diverge_results, criticize_results)

        self.phase_manager.advance_phase()

        # Store iteration
        self.iteration_tracker.add_iteration(
            iteration_number=iteration_num,
            diverge_results=diverge_results,
            criticize_results=criticize_results,
            converge_results=converge_results,
            user_feedback=user_feedback
        )

        if progress_callback:
            progress_callback("complete", f"Iteration {iteration_num} complete")

        return {
            "iteration": iteration_num,
            "diverge": diverge_results,
            "criticize": criticize_results,
            "converge": converge_results
        }

    async def _run_diverge(
        self,
        user_prompt: str,
        user_feedback: str = ""
    ) -> Dict[str, Any]:
        """
        Run diverge phase - all members generate ideas in parallel.

        Args:
            user_prompt: User's research request
            user_feedback: Optional feedback from previous iteration

        Returns:
            Dictionary of results by member
        """
        logger.info("Running diverge phase")

        # Get phase settings
        diverge_settings = self.phase_settings.get("diverge", {})
        temperature = diverge_settings.get("temperature", 0.9)
        max_tokens = diverge_settings.get("max_tokens", 2000)

        # Build prompt per member — reasoning models get a structured-output instruction
        tasks = []
        for member in self.members:
            is_reasoning = member.model_config.get("is_reasoning_model", False)
            messages = self.prompt_builder.build_diverge_messages(
                user_prompt=user_prompt,
                ideas_per_member=self.ideas_per_member,
                previous_feedback=user_feedback,
                is_reasoning_model=is_reasoning
            )
            task = member.generate_ideas(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and track costs
        diverge_data = {}

        for member, result in zip(self.members, results):
            if isinstance(result, Exception):
                logger.error(f"Diverge failed for {member.member_id}: {result}")
                diverge_data[member.member_id] = {
                    "ideas": [],
                    "error": str(result)
                }
            else:
                # Assign stable global idea IDs immediately after diverge
                for local_idx, idea in enumerate(result.get("ideas", [])):
                    idea["idea_id"] = f"{member.member_id}__{local_idx}"

                diverge_data[member.member_id] = result

                # Track cost
                usage = result.get("usage", {})
                model_config = member.model_config
                pricing = model_config.get("pricing", {})

                self.cost_tracker.log_request(
                    model=model_config["display_name"],
                    phase="diverge",
                    member_id=member.member_id,
                    input_tokens=usage.get("input_tokens", 0),
                    output_tokens=usage.get("output_tokens", 0),
                    input_cost_per_1m=pricing.get("input_per_1m", 0),
                    output_cost_per_1m=pricing.get("output_per_1m", 0)
                )

        return diverge_data

    async def _run_criticize(
        self,
        diverge_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run criticize phase - all members critique others' ideas in parallel.

        Args:
            diverge_results: Results from diverge phase

        Returns:
            Dictionary of critiques by member
        """
        logger.info("Running criticize phase")

        # Get phase settings
        criticize_settings = self.phase_settings.get("criticize", {})
        temperature = criticize_settings.get("temperature", 0.5)
        max_tokens = criticize_settings.get("max_tokens", 1500)

        # Collect all ideas (with stable idea_id) indexed by member
        all_ideas_by_member = {}
        for member_id, result in diverge_results.items():
            if "ideas" in result:
                all_ideas_by_member[member_id] = result["ideas"]

        # Anonymize all ideas to prevent brand bias during peer review
        anonymizer = IdeaAnonymizer(shuffle=True)
        all_anonymized, reverse_map = anonymizer.anonymize_ideas(all_ideas_by_member)
        logger.info(f"Anonymized {len(all_anonymized)} ideas for blind peer review")

        # Build per-member task list and review-ID maps (parallel preparation)
        member_tasks = []  # list of (member, coroutine_or_none, review_ids)
        for member in self.members:
            # Each member reviews all ideas except their own (anonymized)
            ideas_to_review = anonymizer.get_ideas_for_member(
                member.member_id, all_anonymized, reverse_map
            )
            # review_ids[i] = the stable idea_id of ideas_to_review[i]
            review_ids = [idea.get("idea_id", "") for idea in ideas_to_review]

            if not ideas_to_review:
                logger.warning(f"No ideas to review for {member.member_id}")
                member_tasks.append((member, None, review_ids))
                continue

            is_reasoning = member.model_config.get("is_reasoning_model", False)
            messages = self.prompt_builder.build_criticize_messages(
                ideas_to_review=ideas_to_review,
                is_reasoning_model=is_reasoning,
                anonymized=True,
            )
            coro = member.critique_ideas(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            member_tasks.append((member, coro, review_ids))

        # Run all critique calls in parallel
        active = [(i, coro) for i, (_, coro, _) in enumerate(member_tasks) if coro is not None]
        if active:
            gathered = await asyncio.gather(*[coro for _, coro in active], return_exceptions=True)
            raw_results = {idx: r for (idx, _), r in zip(active, gathered)}
        else:
            raw_results = {}

        # Collect results, translate local idea_index → stable idea_id, track costs
        criticize_data = {}
        for i, (member, coro, review_ids) in enumerate(member_tasks):
            if coro is None:
                criticize_data[member.member_id] = {
                    "critiques": [],
                    "message": "No ideas to review"
                }
                continue

            result = raw_results[i]
            if isinstance(result, Exception):
                logger.error(f"Criticize failed for {member.member_id}: {result}")
                criticize_data[member.member_id] = {
                    "critiques": [],
                    "error": str(result)
                }
                continue

            # Translate each critique's local position index to the stable idea_id
            for critique in result.get("critiques", []):
                local_idx = critique.get("idea_index", 0)
                critique["idea_id"] = review_ids[local_idx] if local_idx < len(review_ids) else None

            criticize_data[member.member_id] = result

            # Track cost
            usage = result.get("usage", {})
            model_config = member.model_config
            pricing = model_config.get("pricing", {})
            self.cost_tracker.log_request(
                model=model_config["display_name"],
                phase="criticize",
                member_id=member.member_id,
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0),
                input_cost_per_1m=pricing.get("input_per_1m", 0),
                output_cost_per_1m=pricing.get("output_per_1m", 0)
            )

        return criticize_data

    async def _run_converge(
        self,
        diverge_results: Dict[str, Any],
        criticize_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run converge phase - synthesize best ideas.

        Args:
            diverge_results: Results from diverge phase
            criticize_results: Results from criticize phase

        Returns:
            Synthesis with top recommendations
        """
        logger.info("Running converge phase")

        # Get phase settings
        converge_settings = self.phase_settings.get("converge", {})
        temperature = converge_settings.get("temperature", 0.3)
        max_tokens = converge_settings.get("max_tokens", 6000)

        # Collect all ideas
        all_ideas = []
        for member_id, result in diverge_results.items():
            if "ideas" in result:
                all_ideas.extend(result["ideas"])

        # Collect all critiques
        all_critiques = {}
        for member_id, result in criticize_results.items():
            if "critiques" in result:
                all_critiques[member_id] = result["critiques"]

        # Always use the coordinator (Claude Sonnet) for synthesis
        synthesis_member = self.coordinator

        # Build converge prompt
        messages = self.prompt_builder.build_converge_messages(
            all_ideas=all_ideas,
            all_critiques=all_critiques,
            top_n=self.top_ideas_count
        )

        # Get synthesis
        response = await synthesis_member.api_client.chat_completion(
            model=synthesis_member.model_config["openrouter_id"],
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        content = synthesis_member.api_client.extract_content(response)
        usage = synthesis_member.api_client.extract_usage(response)

        # Parse synthesis
        synthesis_data = self._parse_synthesis(content)

        # Track cost
        model_config = synthesis_member.model_config
        pricing = model_config.get("pricing", {})

        self.cost_tracker.log_request(
            model=model_config["display_name"],
            phase="converge",
            member_id=synthesis_member.member_id,
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            input_cost_per_1m=pricing.get("input_per_1m", 0),
            output_cost_per_1m=pricing.get("output_per_1m", 0)
        )

        return {
            "synthesis": content,
            "top_ideas": synthesis_data.get("top_ideas", []),
            "themes": synthesis_data.get("themes", []),
            "raw_response": content,
            "usage": usage
        }

    def _parse_synthesis(self, content: str) -> Dict[str, Any]:
        """
        Parse synthesis from converge phase.

        Args:
            content: Raw synthesis content

        Returns:
            Parsed synthesis data
        """
        synthesis = {
            "top_ideas": [],
            "themes": []
        }

        # Extract top ideas
        rank_pattern = r'RANK\s+(\d+):\s*(.+?)(?=RANK\s+\d+:|HONORABLE MENTIONS:|$)'
        rank_matches = re.finditer(rank_pattern, content, re.IGNORECASE | re.DOTALL)

        # Known single-line field names from the converge prompt template
        KNOWN_FIELDS = {
            "original idea", "why this ranks", "feasibility",
            "expected timeline", "next steps", "potential challenges",
            "rationale", "summary", "methodology", "timeline"
        }

        for match in rank_matches:
            rank = int(match.group(1))
            idea_text = match.group(2).strip()

            idea = {"rank": rank, "raw_text": idea_text}

            # Title = first non-empty line
            lines = idea_text.splitlines()
            title_line = next((l.strip() for l in lines if l.strip()), "")
            idea['title'] = title_line

            # Parse known single-line fields only (skip title line)
            for line in lines[1:]:
                if ':' not in line:
                    continue
                raw_key, value = line.split(':', 1)
                clean_key = raw_key.strip().lower().lstrip('*# ').rstrip('*# ')
                # Only accept lines whose key starts with a known field name
                if any(clean_key.startswith(f) for f in KNOWN_FIELDS):
                    dict_key = clean_key.replace(' ', '_').replace('#', '')
                    idea[dict_key] = value.strip()

            synthesis["top_ideas"].append(idea)

        # Extract themes
        themes_match = re.search(r'COMMON THEMES:\s*(.+?)(?=TOP RECOMMENDATIONS:|$)', content, re.IGNORECASE | re.DOTALL)
        if themes_match:
            themes_text = themes_match.group(1).strip()
            themes = [line.strip('- ').strip() for line in themes_text.split('\n') if line.strip().startswith('-')]
            synthesis["themes"] = themes

        return synthesis

    def get_coordinator_name(self) -> str:
        """Return display name of the coordinator model."""
        if self.coordinator:
            return self.coordinator.model_config.get("display_name", "Unknown")
        return "Unknown"

    def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost summary."""
        return self.cost_tracker.get_summary()

    def get_all_iterations(self) -> List[Dict[str, Any]]:
        """Get all iteration data."""
        return self.iteration_tracker.get_all_iterations()

    def can_iterate(self) -> bool:
        """Check if another iteration is allowed."""
        return self.phase_manager.can_iterate()

    def reset(self) -> None:
        """Reset council state."""
        self.phase_manager.reset()
        self.iteration_tracker.reset()
        self.cost_tracker.reset()

        for member in self.members:
            member.reset_usage()
