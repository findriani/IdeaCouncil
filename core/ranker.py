"""
Ranking aggregation and consensus analysis.
Implements Borda count voting and consensus metrics.
"""

from typing import Dict, List, Any, Tuple
from collections import defaultdict
import statistics

class RankingAggregator:
    """
    Aggregate rankings from multiple council members.

    Uses Borda count method:
    - 1st place: n points (n = total number of ideas)
    - 2nd place: n-1 points
    - 3rd place: n-2 points
    - ...
    - nth place: 1 point
    """

    def borda_count(
        self,
        all_rankings: Dict[str, List[Dict[str, Any]]],
        num_ideas: int
    ) -> List[Tuple[int, float, Dict[str, Any]]]:
        """
        Aggregate rankings using Borda count method.

        Args:
            all_rankings: {member_id: [{idea_index, rank, reason}, ...], ...}
            num_ideas: Total number of ideas being ranked

        Returns:
            List of (idea_index, total_score, metadata) sorted by score (descending)
        """
        idea_scores = defaultdict(lambda: {
            "total": 0,
            "votes": [],
            "avg_rank": 0,
            "num_votes": 0
        })

        # Calculate Borda count
        for member_id, rankings in all_rankings.items():
            for ranking in rankings:
                idea_idx = ranking["idea_index"]
                rank = ranking["rank"]

                # Borda points: 1st = n, 2nd = n-1, ..., nth = 1
                points = num_ideas - rank + 1

                idea_scores[idea_idx]["total"] += points
                idea_scores[idea_idx]["num_votes"] += 1
                idea_scores[idea_idx]["votes"].append({
                    "member": member_id,
                    "rank": rank,
                    "points": points,
                    "reason": ranking.get("reason", "")
                })

        # Calculate average rank for each idea
        for idea_idx, data in idea_scores.items():
            ranks = [v["rank"] for v in data["votes"]]
            data["avg_rank"] = sum(ranks) / len(ranks) if ranks else 99

        # Sort by total score (descending)
        sorted_results = sorted(
            [(idx, data["total"], data) for idx, data in idea_scores.items()],
            key=lambda x: x[1],
            reverse=True
        )

        return sorted_results

    def calculate_consensus_score(
        self,
        all_rankings: Dict[str, List[Dict[str, Any]]]
    ) -> float:
        """
        Calculate consensus level among council members.

        Returns:
            Consensus score 0-1 (0 = total disagreement, 1 = perfect agreement)

        Method: Kendall's Tau correlation between all pairs of rankings
        """
        if len(all_rankings) < 2:
            return 1.0  # Perfect consensus with only 1 ranker

        try:
            from scipy.stats import kendalltau
        except ImportError:
            # Fallback: simple variance-based metric
            return self._calculate_consensus_fallback(all_rankings)

        # Extract rank orders from each member
        rank_orders = []

        for member_id, rankings in all_rankings.items():
            # Sort by rank to get ordered list of idea indices
            sorted_rankings = sorted(rankings, key=lambda x: x["rank"])
            order = [r["idea_index"] for r in sorted_rankings]
            rank_orders.append(order)

        # Calculate pairwise Kendall's Tau correlations
        correlations = []
        n = len(rank_orders)

        for i in range(n):
            for j in range(i + 1, n):
                try:
                    # Kendall's Tau: correlation between two rankings
                    tau, _ = kendalltau(rank_orders[i], rank_orders[j])
                    correlations.append(tau)
                except Exception:
                    # Handle edge cases (empty rankings, etc.)
                    pass

        if not correlations:
            return 0.0

        # Average correlation across all pairs
        avg_correlation = sum(correlations) / len(correlations)

        # Convert from [-1, 1] to [0, 1]
        # -1 = complete disagreement, 0 = random, 1 = perfect agreement
        consensus = (avg_correlation + 1) / 2

        return max(0.0, min(1.0, consensus))

    def _calculate_consensus_fallback(
        self,
        all_rankings: Dict[str, List[Dict[str, Any]]]
    ) -> float:
        """
        Fallback consensus calculation without scipy.

        Uses variance in ranks: lower variance = higher consensus
        """
        # Collect all ranks for each idea
        idea_ranks = defaultdict(list)

        for member_rankings in all_rankings.values():
            for ranking in member_rankings:
                idea_idx = ranking["idea_index"]
                rank = ranking["rank"]
                idea_ranks[idea_idx].append(rank)

        # Calculate average variance
        variances = []

        for ranks in idea_ranks.values():
            if len(ranks) > 1:
                var = statistics.variance(ranks)
                variances.append(var)

        if not variances:
            return 0.5

        avg_variance = sum(variances) / len(variances)

        # Normalize: high variance = low consensus
        # Assume max variance is ~5 (realistic for rankings)
        max_variance = 5.0
        consensus = 1.0 - min(avg_variance / max_variance, 1.0)

        return consensus

    def identify_controversial_ideas(
        self,
        all_rankings: Dict[str, List[Dict[str, Any]]],
        variance_threshold: float = 2.0
    ) -> List[int]:
        """
        Find ideas with high variance in rankings.

        These are polarizing ideas where council members strongly disagree.

        Args:
            all_rankings: All member rankings
            variance_threshold: Minimum variance to be considered controversial

        Returns:
            List of idea indices that are controversial
        """
        idea_ranks = defaultdict(list)

        # Collect ranks for each idea
        for member_rankings in all_rankings.values():
            for ranking in member_rankings:
                idea_idx = ranking["idea_index"]
                rank = ranking["rank"]
                idea_ranks[idea_idx].append(rank)

        controversial = []

        # Find high-variance ideas
        for idea_idx, ranks in idea_ranks.items():
            if len(ranks) > 1:
                var = statistics.variance(ranks)

                if var >= variance_threshold:
                    controversial.append(idea_idx)

        return controversial

    def get_unanimous_top_choices(
        self,
        all_rankings: Dict[str, List[Dict[str, Any]]],
        top_n: int = 3
    ) -> List[int]:
        """
        Find ideas that appear in everyone's top N.

        Args:
            all_rankings: All member rankings
            top_n: Size of "top" list to check

        Returns:
            List of idea indices that all members ranked in top N
        """
        if not all_rankings:
            return []

        # Get each member's top N ideas
        top_sets = []

        for member_rankings in all_rankings.values():
            sorted_rankings = sorted(member_rankings, key=lambda x: x["rank"])
            top_ideas = [r["idea_index"] for r in sorted_rankings[:top_n]]
            top_sets.append(set(top_ideas))

        # Find intersection
        if not top_sets:
            return []

        unanimous = set.intersection(*top_sets)

        return list(unanimous)

    def format_ranking_summary(
        self,
        ranked_ideas: List[Tuple[int, float, Dict[str, Any]]],
        all_ideas: List[Dict[str, Any]],
        top_n: int = 10
    ) -> str:
        """
        Format ranking results as readable text.

        Args:
            ranked_ideas: Output from borda_count()
            all_ideas: Original ideas list
            top_n: Number of top ideas to include

        Returns:
            Formatted summary string
        """
        lines = []
        lines.append("=" * 60)
        lines.append("COUNCIL RANKING (Borda Count)")
        lines.append("=" * 60)
        lines.append("")

        for rank, (idea_idx, total_score, metadata) in enumerate(ranked_ideas[:top_n], 1):
            if idea_idx >= len(all_ideas):
                continue

            idea = all_ideas[idea_idx]
            votes = metadata.get("votes", [])
            avg_rank = metadata.get("avg_rank", 0)

            lines.append(f"#{rank}: {idea.get('title', 'Untitled')}")
            lines.append(f"  Total Score: {total_score:.1f} points")
            lines.append(f"  Average Rank: {avg_rank:.1f}")
            lines.append(f"  Votes:")

            for vote in votes:
                lines.append(f"    - {vote['member']}: Rank {vote['rank']} ({vote['points']} pts)")
                if vote.get('reason'):
                    lines.append(f"      Reason: {vote['reason']}")

            lines.append("")

        return "\n".join(lines)
