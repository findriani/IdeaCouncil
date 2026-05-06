"""
Semantic deduplication of research ideas using TF-IDF cosine similarity.
Falls back gracefully if scikit-learn is unavailable.
"""

from typing import Any, Dict, List, Tuple

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    _SKLEARN_AVAILABLE = True
except ImportError:
    _SKLEARN_AVAILABLE = False


def deduplicate(
    all_ideas: List[Dict[str, Any]],
    threshold: float = 0.75,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Remove near-duplicate ideas using greedy TF-IDF cosine similarity.

    Iterates through ideas in order. An idea is flagged as a duplicate when
    its cosine similarity to any already-kept idea exceeds `threshold`. The
    first occurrence of any near-duplicate group is always kept.

    Args:
        all_ideas:  Flat list of idea dicts, each with 'idea_id', 'title',
                    and optionally 'summary'.
        threshold:  Cosine similarity above which an idea is considered a
                    duplicate (default 0.75).

    Returns:
        kept_ideas   — ideas that survived deduplication (original order).
        dedup_report — list of {removed_title, duplicate_of_title,
                       similarity_score} for each removed idea.
    """
    if not all_ideas:
        return [], []

    if not _SKLEARN_AVAILABLE:
        return list(all_ideas), []

    texts = [
        f"{idea.get('title', '')}. {idea.get('summary', '')}".strip()
        for idea in all_ideas
    ]

    vectorizer = TfidfVectorizer(stop_words="english")
    try:
        tfidf_matrix = vectorizer.fit_transform(texts)
    except ValueError:
        # All texts empty or only stop words — keep everything
        return list(all_ideas), []

    kept_indices: List[int] = []
    dedup_report: List[Dict[str, Any]] = []

    for i, idea in enumerate(all_ideas):
        if not kept_indices:
            kept_indices.append(i)
            continue

        candidate_vec = tfidf_matrix[i]
        kept_matrix = tfidf_matrix[kept_indices]
        similarities = cosine_similarity(candidate_vec, kept_matrix)[0]

        max_sim_pos = int(similarities.argmax())
        max_sim = float(similarities[max_sim_pos])

        if max_sim > threshold:
            duplicate_of = all_ideas[kept_indices[max_sim_pos]]
            dedup_report.append({
                "removed_title": idea.get("title", "Untitled"),
                "duplicate_of_title": duplicate_of.get("title", "Untitled"),
                "similarity_score": round(max_sim, 4),
            })
        else:
            kept_indices.append(i)

    kept_ideas = [all_ideas[i] for i in kept_indices]
    return kept_ideas, dedup_report
