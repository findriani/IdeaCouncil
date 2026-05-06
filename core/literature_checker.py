"""
Literature Check phase orchestration.

Generates targeted search queries from the idea pool, fetches relevant papers
from SemanticScholar and OpenAlex (both free, no key required), deduplicates
results, and summarises them into a ~700-word report for the Novelty critic.

Pipeline:
  1. LLM call (Gemini Flash Lite) → 4-6 academic search queries
  2. Parallel API calls → top papers per query from both APIs
  3. Deduplicate by title
  4. LLM call (Gemini Flash Lite) → ~700-word structured report
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from api.literature_search_client import OpenAlexClient, SemanticScholarClient
from utils.logger import logger

_QUERY_GENERATION_PROMPT = """\
Below is a list of research ideas with their identified gap and proposed novel component.

{idea_list}

Generate {num_queries} precise academic search queries to find prior work directly relevant \
to these ideas. Focus on the core technical contributions — avoid generic queries.
Restrict your queries to target papers from {year_from} to {year_to}.

Return only the queries, one per line, with no numbering, bullets, or extra text.\
"""

_SUMMARIZE_PROMPT = """\
The following papers were retrieved from academic databases for research on: {topic_hint}

{paper_list}

Write a ~700-word literature landscape summary. Structure it by the search query themes above. \
For each theme:
- Describe what methods or approaches existing papers use
- Identify limitations or gaps that remain open
- Note how these findings relate to the novelty of the proposed ideas

Be specific: name papers by title and year. Focus on what is and isn't already solved. \
Do not suggest future research directions — only describe the existing landscape.\
"""


class LiteratureChecker:
    """
    Orchestrates the live literature check:
    query generation → API search → dedup → summarisation.
    """

    def __init__(self, api_client: Any, summarizer_model_id: str):
        """
        Args:
            api_client:          OpenRouterClient instance (for LLM calls)
            summarizer_model_id: OpenRouter model ID for query gen + summarisation
        """
        self.api_client = api_client
        self.summarizer_model_id = summarizer_model_id
        self._ss = SemanticScholarClient()
        self._oa = OpenAlexClient()

    async def run(
        self,
        all_ideas: List[Dict[str, Any]],
        year_range: int = 5,
        papers_per_query: int = 5,
        num_queries: int = 6,
    ) -> Dict[str, Any]:
        """
        Run the full literature check pipeline.

        Args:
            all_ideas:        Post-dedup idea list (each has title, gap, novel_component)
            year_range:       How many years back to search (default 5 → 2021-2026)
            papers_per_query: Max papers to fetch per query per API
            num_queries:      Number of search queries to generate

        Returns:
            {
                "queries":  List[str],   # generated search queries
                "papers":   List[Dict],  # deduplicated papers with query_label, source, etc.
                "report":   str,         # ~700-word summarised report
                "skipped":  bool,        # True when APIs or LLM calls failed
                "error":    str | None,
            }
        """
        current_year = datetime.now().year
        year_from = current_year - year_range
        year_to = current_year

        empty = {"queries": [], "papers": [], "report": "", "skipped": True, "error": None}

        usage_total: Dict[str, int] = {"input_tokens": 0, "output_tokens": 0}

        # ── Step 1: Generate search queries via LLM ──────────────────────────
        queries, query_usage = await self._generate_queries(all_ideas, year_from, year_to, num_queries)
        usage_total["input_tokens"] += query_usage.get("input_tokens", 0)
        usage_total["output_tokens"] += query_usage.get("output_tokens", 0)

        if not queries:
            logger.warning("Literature check: no queries generated — skipping")
            empty["error"] = "Query generation returned no results"
            empty["usage"] = usage_total
            empty["model"] = self.summarizer_model_id
            return empty

        # ── Step 2: Fetch papers in parallel (S2 + OA per query) ─────────────
        tasks: List = []
        task_query_labels: List[str] = []
        for query in queries:
            tasks.append(self._ss.search(query, year_from, year_to, limit=papers_per_query))
            tasks.append(self._oa.search(query, year_from, year_to, limit=papers_per_query))
            task_query_labels.extend([query, query])

        raw_results = await asyncio.gather(*tasks, return_exceptions=True)

        flat_papers: List[Dict[str, Any]] = []
        for result, query_label in zip(raw_results, task_query_labels):
            if isinstance(result, Exception):
                logger.warning(f"Literature search error: {result}")
                continue
            for paper in result:
                paper["query_label"] = query_label
                flat_papers.append(paper)

        if not flat_papers:
            logger.warning("Literature check: all API calls returned empty — skipping")
            empty["error"] = "All API calls returned empty results"
            empty["usage"] = usage_total
            empty["model"] = self.summarizer_model_id
            return empty

        # ── Step 3: Deduplicate by lowercased title ───────────────────────────
        papers = self._deduplicate(flat_papers)

        # ── Step 4: Summarise into ~700-word report ───────────────────────────
        report, summarise_usage = await self._summarise(papers, queries)
        usage_total["input_tokens"] += summarise_usage.get("input_tokens", 0)
        usage_total["output_tokens"] += summarise_usage.get("output_tokens", 0)

        return {
            "queries": queries,
            "papers": papers,
            "report": report,
            "skipped": False,
            "error": None,
            "usage": usage_total,
            "model": self.summarizer_model_id,
        }

    # ── Private helpers ───────────────────────────────────────────────────────

    async def _generate_queries(
        self,
        all_ideas: List[Dict[str, Any]],
        year_from: int,
        year_to: int,
        num_queries: int,
    ):
        """Call LLM to generate targeted search queries from the idea pool.

        Returns:
            Tuple of (queries: List[str], usage: Dict[str, int])
        """
        idea_lines: List[str] = []
        for i, idea in enumerate(all_ideas, 1):
            title = idea.get("title", "Untitled")
            gap = (idea.get("gap") or "")[:120]
            novel = (idea.get("novel_component") or "")[:120]
            idea_lines.append(
                f"Idea {i}: {title} — Gap: {gap} — Novel Component: {novel}"
            )

        prompt = _QUERY_GENERATION_PROMPT.format(
            idea_list="\n".join(idea_lines),
            num_queries=num_queries,
            year_from=year_from,
            year_to=year_to,
        )

        try:
            response = await self.api_client.chat_completion(
                model=self.summarizer_model_id,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=400,
            )
            content = self.api_client.extract_content(response)
            usage = self.api_client.extract_usage(response)
            queries = [
                line.strip().lstrip("-•*0123456789. ").strip()
                for line in content.splitlines()
                if line.strip() and len(line.strip()) > 10
            ]
            return queries[:num_queries], usage
        except Exception as e:
            logger.error(f"Literature query generation failed: {e}")
            return [], {}

    def _deduplicate(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove papers with duplicate titles (case-insensitive), keeping first."""
        seen: set = set()
        unique: List[Dict[str, Any]] = []
        for paper in papers:
            key = (paper.get("title") or "").lower().strip()
            if not key or key in seen:
                continue
            seen.add(key)
            unique.append(paper)
        return unique

    async def _summarise(
        self,
        papers: List[Dict[str, Any]],
        queries: List[str],
    ):
        """Call LLM to produce a ~700-word structured report from the paper list.

        Returns:
            Tuple of (report: str, usage: Dict[str, int])
        """
        # Group papers by the query that found them
        by_query: Dict[str, List[Dict[str, Any]]] = {}
        for paper in papers:
            q = paper.get("query_label", "Other")
            by_query.setdefault(q, []).append(paper)

        # Format paper list: S2 abstracts truncated to 200 chars; OA has none
        lines: List[str] = []
        for query in queries:
            query_papers = by_query.get(query, [])
            if not query_papers:
                continue
            lines.append(f"\nQuery: {query}")
            for paper in query_papers:
                title = paper.get("title") or "Unknown"
                year = paper.get("year", "?")
                citations = paper.get("citation_count", 0)
                source = paper.get("source", "")
                entry = f'  - "{title}" ({year}, {citations} citations, {source})'
                abstract = (paper.get("abstract") or "")[:200]
                if abstract:
                    entry += f"\n    Abstract: {abstract}..."
                lines.append(entry)

        paper_list = "\n".join(lines)
        topic_hint = ", ".join(queries[:3])

        prompt = _SUMMARIZE_PROMPT.format(
            topic_hint=topic_hint,
            paper_list=paper_list,
        )

        try:
            response = await self.api_client.chat_completion(
                model=self.summarizer_model_id,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1100,  # ~700 words
            )
            content = self.api_client.extract_content(response)
            usage = self.api_client.extract_usage(response)
            return content, usage
        except Exception as e:
            logger.error(f"Literature summarisation failed: {e}")
            # Graceful fallback: return the formatted paper list as-is
            return f"Literature search found {len(papers)} paper(s):\n{paper_list}", {}
