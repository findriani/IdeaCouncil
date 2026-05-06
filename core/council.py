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
from core.ranker import RankingAggregator
from utils.deduplicator import deduplicate
from utils.logger import logger
from core.literature_checker import LiteratureChecker
import re

class Council:
    """Orchestrates multiple LLM members through brainstorming workflow."""

    # Claude Sonnet is always the coordinator/converger
    COORDINATOR_MODEL_KEY = "claude_sonnet_latest"

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
        self.model_configs = model_configs  # retained for pricing lookups (e.g. literature check)
        self.ideas_per_member = ideas_per_member
        self.top_ideas_count = top_ideas_count

        # Initialize members — inject model_key into config so _run_criticize can filter
        self.members: List[CouncilMember] = []
        for i, model_key in enumerate(selected_model_keys):
            if model_key in model_configs:
                config = {**model_configs[model_key], "model_key": model_key}
                member = CouncilMember(
                    member_id=f"{model_key}_{i}",
                    model_config=config,
                    api_client=api_client
                )
                self.members.append(member)

        if not self.members:
            raise ValueError("No valid models selected for council")

        # Coordinator/Converger: always Claude Sonnet, independent of member selection
        coordinator_config = model_configs.get(self.COORDINATOR_MODEL_KEY)
        if coordinator_config:
            coordinator_config = {**coordinator_config, "model_key": self.COORDINATOR_MODEL_KEY}
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

        # Build fixed critic roster — always the same 4 models regardless of generator selection.
        # If a critic model was also selected as a generator, reuse that member instance
        # (so own-idea exclusion still works). Otherwise instantiate a critic-only instance.
        self.critic_members: List[CouncilMember] = []
        critic_keys = self.phase_settings.get("criticize", {}).get("critic_models", None)
        if critic_keys:
            for model_key in critic_keys:
                if model_key == self.COORDINATOR_MODEL_KEY:
                    # Coordinator is always available; add it directly
                    if self.coordinator:
                        self.critic_members.append(self.coordinator)
                    continue
                # Reuse existing generator member if present
                existing = next(
                    (m for m in self.members if m.model_config.get("model_key") == model_key),
                    None
                )
                if existing:
                    self.critic_members.append(existing)
                elif model_key in model_configs:
                    # Critic-only instance (no generated ideas → reviews everything)
                    config = {**model_configs[model_key], "model_key": model_key}
                    self.critic_members.append(CouncilMember(
                        member_id=f"{model_key}_critic",
                        model_config=config,
                        api_client=api_client
                    ))
                else:
                    logger.warning(f"Critic model key '{model_key}' not found in model_configs — skipping")
        else:
            # No restriction — all generator members critique
            self.critic_members = list(self.members)

        logger.info(
            f"Council initialized with {len(self.members)} generator(s), "
            f"{len(self.critic_members)} critic(s) | "
            f"Coordinator: {self.coordinator.model_config.get('display_name', 'unknown')}"
        )

    async def run_iteration(
        self,
        user_prompt: str,
        user_feedback: str = "",
        progress_callback: Optional[Callable[[str, str], None]] = None,
        manual_ideas: Optional[List[Dict[str, Any]]] = None,
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

        # Inject manual ideas from an external LLM session as a virtual council member
        if manual_ideas:
            for i, idea in enumerate(manual_ideas):
                idea["idea_id"] = f"external_llm__{i}"
                idea.setdefault("member_id", "external_llm")
            diverge_results["external_llm"] = {
                "member_id": "external_llm",
                "model": "External LLM (Manual)",
                "ideas": manual_ideas,
                "raw_response": "",
                "usage": {"input_tokens": 0, "output_tokens": 0},
            }
            logger.info(f"Injected {len(manual_ideas)} manual idea(s) from external LLM")

        # Deduplicate ideas before criticize to avoid wasting critique tokens
        all_ideas_flat = []
        for result in diverge_results.values():
            all_ideas_flat.extend(result.get("ideas", []))

        kept_ideas, dedup_report = deduplicate(all_ideas_flat, threshold=0.75)

        if dedup_report:
            logger.info(
                f"Deduplication removed {len(dedup_report)} near-duplicate idea(s) "
                f"before criticize phase"
            )

        kept_idea_ids = {idea["idea_id"] for idea in kept_ideas if idea.get("idea_id")}
        filtered_diverge_results = {
            member_id: {**result, "ideas": [
                idea for idea in result.get("ideas", [])
                if idea.get("idea_id") in kept_idea_ids
            ]}
            for member_id, result in diverge_results.items()
        }

        # Run literature check (between dedup and criticize)
        if progress_callback:
            progress_callback("phase", "Literature Check - Searching recent papers")

        literature_check_result = await self._run_literature_check(kept_ideas)

        # Run criticize phase (operates on deduplicated ideas only)
        if progress_callback:
            progress_callback("phase", "Criticize - Evaluating ideas")

        criticize_results = await self._run_criticize(
            filtered_diverge_results,
            literature_check_result=literature_check_result,
        )

        self.phase_manager.advance_phase()

        # Compute score variance / controversy across reviewers
        all_critiques_by_member = {
            member_id: result.get("critiques", [])
            for member_id, result in criticize_results.items()
        }
        controversy = RankingAggregator().compute_controversy(all_critiques_by_member)

        # Run converge phase
        if progress_callback:
            progress_callback("phase", "Converge - Synthesizing recommendations")

        converge_results = await self._run_converge(filtered_diverge_results, criticize_results)

        self.phase_manager.advance_phase()

        # Store iteration
        self.iteration_tracker.add_iteration(
            iteration_number=iteration_num,
            diverge_results=diverge_results,
            criticize_results=criticize_results,
            converge_results=converge_results,
            user_feedback=user_feedback,
            dedup_report=dedup_report,
            controversy=controversy,
        )

        if progress_callback:
            progress_callback("complete", f"Iteration {iteration_num} complete")

        return {
            "iteration": iteration_num,
            "diverge": diverge_results,
            "criticize": criticize_results,
            "converge": converge_results,
            "dedup_report": dedup_report,
            "controversy": controversy,
            "literature_check": literature_check_result,
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

        # Build prompt per member - reasoning models get a structured-output instruction
        tasks = []
        for member in self.members:
            is_reasoning = member.model_config.get("is_reasoning_model", False)
            member_max_tokens = member.model_config.get("diverge_max_tokens", max_tokens)
            messages = self.prompt_builder.build_diverge_messages(
                user_prompt=user_prompt,
                ideas_per_member=self.ideas_per_member,
                previous_feedback=user_feedback,
                is_reasoning_model=is_reasoning
            )
            task = member.generate_ideas(
                messages=messages,
                temperature=temperature,
                max_tokens=member_max_tokens
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

    async def _run_literature_check(
        self,
        all_ideas: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Run the Literature Check phase between dedup and criticize.

        Generates targeted search queries from all ideas, fetches papers from
        SemanticScholar and OpenAlex, and summarises them into a ~700-word
        report for the dedicated Novelty critic.

        Returns the literature_check_result dict (skipped=True on failure).
        """
        lit_settings = self.phase_settings.get("literature_check", {})
        if not lit_settings.get("enabled", True):
            logger.info("Literature check disabled in config — skipping")
            return {"queries": [], "papers": [], "report": "", "skipped": True, "error": "disabled"}

        summarizer_model = lit_settings.get(
            "summarizer_model", "google/gemini-3.1-flash-lite-preview"
        )
        year_range       = lit_settings.get("year_range", 5)
        papers_per_query = lit_settings.get("papers_per_query", 5)
        num_queries      = lit_settings.get("num_queries", 6)

        logger.info(
            f"Running literature check: {num_queries} queries, "
            f"±{papers_per_query} papers each, last {year_range} years"
        )

        checker = LiteratureChecker(
            api_client=self.api_client,
            summarizer_model_id=summarizer_model,
        )
        result = await checker.run(
            all_ideas=all_ideas,
            year_range=year_range,
            papers_per_query=papers_per_query,
            num_queries=num_queries,
        )

        if result.get("skipped"):
            logger.warning(
                f"Literature check skipped: {result.get('error', 'unknown reason')}"
            )
        else:
            logger.info(
                f"Literature check complete: {len(result.get('queries', []))} queries, "
                f"{len(result.get('papers', []))} papers found"
            )

        # Log LLM costs regardless of skipped status — query generation may have spent
        # tokens even when no papers were found (the two early-return paths now carry usage).
        # Pricing comes from the literature_check section in models.yaml.
        usage = result.get("usage", {})
        if usage.get("input_tokens") or usage.get("output_tokens"):
            pricing = lit_settings.get("pricing", {})
            self.cost_tracker.log_request(
                model=summarizer_model,
                phase="literature_check",
                member_id="literature_checker",
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0),
                input_cost_per_1m=pricing.get("input_per_1m", 0),
                output_cost_per_1m=pricing.get("output_per_1m", 0),
            )

        return result

    async def _run_criticize(
        self,
        diverge_results: Dict[str, Any],
        literature_check_result: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Run criticize phase - all members critique others' ideas in parallel.

        Args:
            diverge_results:          Results from diverge phase
            literature_check_result:  Output from _run_literature_check (may be None)

        Returns:
            Dictionary of critiques by member, plus "kimi_novelty" for the novelty pass
        """
        logger.info("Running criticize phase")

        criticize_settings = self.phase_settings.get("criticize", {})
        temperature  = criticize_settings.get("temperature", 0.5)
        max_tokens   = criticize_settings.get("max_tokens", 1500)

        # Identify the dedicated novelty critic model key
        novelty_critic_key    = criticize_settings.get("novelty_critic", "kimi")
        novelty_max_tokens    = criticize_settings.get("novelty_max_tokens", 20000)

        # Collect all ideas (with stable idea_id) indexed by member
        all_ideas_by_member: Dict[str, List] = {}
        for member_id, result in diverge_results.items():
            if "ideas" in result:
                all_ideas_by_member[member_id] = result["ideas"]

        # Anonymize all ideas to prevent brand bias during peer review
        anonymizer = IdeaAnonymizer(shuffle=True)
        all_anonymized, reverse_map = anonymizer.anonymize_ideas(all_ideas_by_member)
        logger.info(f"Anonymized {len(all_anonymized)} ideas for blind peer review")

        # ── Track A: General critics (Impact + Feasibility, exclude own ideas) ───
        member_tasks = []  # list of (member, coroutine_or_none, review_ids)
        for member in self.critic_members:
            ideas_to_review = anonymizer.get_ideas_for_member(
                member.member_id, all_anonymized, reverse_map
            )
            review_ids = [idea.get("idea_id", "") for idea in ideas_to_review]

            if not ideas_to_review:
                logger.warning(f"No ideas to review for {member.member_id}")
                member_tasks.append((member, None, review_ids))
                continue

            is_reasoning      = member.model_config.get("is_reasoning_model", False)
            member_max_tokens = member.model_config.get("criticize_max_tokens", max_tokens)
            messages = self.prompt_builder.build_criticize_messages(
                ideas_to_review=ideas_to_review,
                is_reasoning_model=is_reasoning,
                anonymized=True,
            )
            coro = member.critique_ideas(
                messages=messages,
                temperature=temperature,
                max_tokens=member_max_tokens,
            )
            member_tasks.append((member, coro, review_ids))

        # ── Track B: Novelty critic (Novelty only, ALL ideas including own) ────
        novelty_member = next(
            (m for m in self.critic_members
             if m.model_config.get("model_key") == novelty_critic_key),
            None
        )
        novelty_review_ids = [idea.get("idea_id", "") for idea in all_anonymized]
        novelty_coro = None
        if novelty_member:
            lit_report = (literature_check_result or {}).get("report", "")
            is_reasoning = novelty_member.model_config.get("is_reasoning_model", False)
            novelty_messages = self.prompt_builder.build_novelty_critique_messages(
                all_ideas=all_anonymized,
                literature_check_report=lit_report,
                is_reasoning_model=is_reasoning,
            )
            novelty_coro = novelty_member.assess_novelty(
                messages=novelty_messages,
                temperature=temperature,
                max_tokens=novelty_max_tokens,
            )
            logger.info(
                f"Novelty critic: {novelty_member.member_id} reviewing "
                f"{len(all_anonymized)} ideas (including own)"
            )
        elif novelty_critic_key in self.model_configs:
            # Novelty critic not in critic_members (e.g. gemini3flash) — instantiate on-the-fly
            config = {**self.model_configs[novelty_critic_key], "model_key": novelty_critic_key}
            novelty_member = CouncilMember(
                member_id=f"{novelty_critic_key}_novelty",
                model_config=config,
                api_client=self.api_client,
            )
            lit_report = (literature_check_result or {}).get("report", "")
            is_reasoning = novelty_member.model_config.get("is_reasoning_model", False)
            novelty_messages = self.prompt_builder.build_novelty_critique_messages(
                all_ideas=all_anonymized,
                literature_check_report=lit_report,
                is_reasoning_model=is_reasoning,
            )
            novelty_coro = novelty_member.assess_novelty(
                messages=novelty_messages,
                temperature=temperature,
                max_tokens=novelty_max_tokens,
            )
            logger.info(
                f"Novelty critic: {novelty_member.member_id} (on-the-fly) reviewing "
                f"{len(all_anonymized)} ideas"
            )
        else:
            logger.warning(
                f"Novelty critic model key '{novelty_critic_key}' not found in critic_members or model_configs — "
                "novelty pass skipped"
            )

        # ── Run both tracks concurrently ─────────────────────────────────────
        active_general = [(i, coro) for i, (_, coro, _) in enumerate(member_tasks) if coro is not None]
        all_coros = [coro for _, coro in active_general]
        if novelty_coro:
            all_coros.append(novelty_coro)

        gathered = await asyncio.gather(*all_coros, return_exceptions=True) if all_coros else []

        # Split results: first len(active_general) belong to Track A, last to Track B
        general_raw  = {idx: gathered[pos] for pos, (idx, _) in enumerate(active_general)}
        novelty_raw  = gathered[len(active_general)] if novelty_coro and gathered else None

        # ── Collect Track A results ───────────────────────────────────────────
        criticize_data: Dict[str, Any] = {}
        for i, (member, coro, review_ids) in enumerate(member_tasks):
            if coro is None:
                criticize_data[member.member_id] = {"critiques": [], "message": "No ideas to review"}
                continue

            result = general_raw[i]
            if isinstance(result, Exception):
                logger.error(f"Criticize failed for {member.member_id}: {result}")
                criticize_data[member.member_id] = {"critiques": [], "error": str(result)}
                continue

            for critique in result.get("critiques", []):
                local_idx = critique.get("idea_index", 0)
                critique["idea_id"] = review_ids[local_idx] if local_idx < len(review_ids) else None

            criticize_data[member.member_id] = result

            usage      = result.get("usage", {})
            model_config = member.model_config
            pricing    = model_config.get("pricing", {})
            self.cost_tracker.log_request(
                model=model_config["display_name"],
                phase="criticize",
                member_id=member.member_id,
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0),
                input_cost_per_1m=pricing.get("input_per_1m", 0),
                output_cost_per_1m=pricing.get("output_per_1m", 0),
            )

        # ── Collect Track B result ────────────────────────────────────────────
        if novelty_raw is not None and not isinstance(novelty_raw, Exception):
            for assessment in novelty_raw.get("assessments", []):
                local_idx = assessment.get("idea_index", 0)
                assessment["idea_id"] = (
                    novelty_review_ids[local_idx]
                    if local_idx < len(novelty_review_ids)
                    else None
                )
            criticize_data["kimi_novelty"] = novelty_raw
            usage      = novelty_raw.get("usage", {})
            model_config = novelty_member.model_config
            pricing    = model_config.get("pricing", {})
            self.cost_tracker.log_request(
                model=model_config["display_name"],
                phase="criticize_novelty",
                member_id=novelty_member.member_id,
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0),
                input_cost_per_1m=pricing.get("input_per_1m", 0),
                output_cost_per_1m=pricing.get("output_per_1m", 0),
            )
        elif isinstance(novelty_raw, Exception):
            logger.error(f"Novelty critic failed: {novelty_raw}")
            criticize_data["kimi_novelty"] = {"assessments": [], "error": str(novelty_raw)}

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

        # Collect all critiques (exclude kimi_novelty — it has assessments, not critiques)
        all_critiques = {}
        for member_id, result in criticize_results.items():
            if member_id == "kimi_novelty":
                continue
            if "critiques" in result:
                all_critiques[member_id] = result["critiques"]

        # Extract novelty scores from the dedicated novelty critic pass
        novelty_assessments: Dict[str, int] = {}
        kimi_novelty = criticize_results.get("kimi_novelty", {})
        for assessment in kimi_novelty.get("assessments", []):
            idea_id = assessment.get("idea_id")
            score   = assessment.get("novelty_score")
            if idea_id and score is not None:
                novelty_assessments[idea_id] = score

        # Always use the coordinator (Claude Sonnet) for synthesis
        synthesis_member = self.coordinator

        # Build converge prompt
        messages = self.prompt_builder.build_converge_messages(
            all_ideas=all_ideas,
            all_critiques=all_critiques,
            top_n=self.top_ideas_count,
            novelty_assessments=novelty_assessments,
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

        # Match both old format (RANK N:) and new format (## Rank N:)
        rank_pattern = r'(?:##\s+)?Rank\s+(\d+):\s*(.+?)(?=(?:##\s+)?Rank\s+\d+:|(?:##\s+)?Honorable|$)'
        rank_matches = re.finditer(rank_pattern, content, re.IGNORECASE | re.DOTALL)

        # Known field prefixes — covers both old and new prompt templates
        KNOWN_FIELDS = {
            "original idea", "why this ranks", "feasibility",
            "expected timeline", "next steps", "potential challenges",
            "rationale", "summary", "methodology sketch", "methodology",
            "key risk", "timeline"
        }

        for match in rank_matches:
            rank = int(match.group(1))
            idea_text = match.group(2).strip()

            idea = {"rank": rank, "raw_text": idea_text}

            # Title = first non-empty line (strip markdown bold markers)
            lines = idea_text.splitlines()
            title_line = next((l.strip() for l in lines if l.strip()), "")
            idea['title'] = title_line.strip('*# ').strip()

            # Parse known single-line fields (skip title line)
            for line in lines[1:]:
                if ':' not in line:
                    continue
                raw_key, value = line.split(':', 1)
                clean_key = raw_key.strip().lower().lstrip('*# ').rstrip('*# ')
                if any(clean_key.startswith(f) for f in KNOWN_FIELDS):
                    dict_key = clean_key.replace(' ', '_').replace('#', '')
                    idea[dict_key] = value.strip()

            synthesis["top_ideas"].append(idea)

        # Extract themes — handle both old (COMMON THEMES:) and new (## Common Themes) formats
        themes_match = re.search(
            r'(?:##\s+)?Common\s+Themes[:\s]*\n(.+?)(?=\n(?:##\s+|-{3,}|Rank\s+\d+)|\Z)',
            content, re.IGNORECASE | re.DOTALL
        )
        if themes_match:
            themes_text = themes_match.group(1).strip()
            themes = [line.strip('- *').strip() for line in themes_text.split('\n') if line.strip().startswith('-')]
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

