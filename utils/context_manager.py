"""
Context manager for additional user-provided research context.

Supports two independent optional slots:
  - dataset:    data description, features, size, format, etc.
  - literature: related work, key papers, known approaches, etc.

Phase-aware character limits per slot:

  Dataset:
    Diverge   → 2500 chars  (models need full context to generate relevant ideas)
    Criticize → 500 chars   (key facts for feasibility assessment)
    Converge  → 100 chars   (dataset name/label only — ideas already embed full context)

  Literature:
    Diverge   → 7000 chars  (full briefing — models need as much landscape context as possible)
    Criticize → 1000 chars  (enough to assess novelty against known work)
    Converge  → none        (synthesis works from ideas/critiques, not raw papers)
"""

# Terms that signal high-salience lines in literature context
_LITERATURE_KEYWORDS = frozenset([
    "gap", "limitation", "baseline", "accuracy", "challenge", "dataset",
    "future", "problem", "weakness", "state-of-the-art", "sota",
    "outperform", "missing", "lack", "however", "but", "no existing",
    "not been", "benchmark", "evaluation", "open problem",
])


class _Slot:
    """Single context slot with phase-aware truncation."""

    def __init__(self, raw: str = "", kind: str = "dataset"):
        self._raw = raw.strip()
        self._kind = kind  # "dataset" or "literature"

    @property
    def is_empty(self) -> bool:
        return not self._raw

    def full(self) -> str:
        return self._raw

    def truncate(self, char_limit: int) -> str:
        """
        Truncate to char_limit characters.
        For literature slots, salient lines (containing research-relevant keywords)
        are prioritised before falling back to first-N-lines order.
        """
        if not self._raw:
            return ""
        lines = self._raw.splitlines()
        if self._kind == "literature":
            salient = [l for l in lines if any(kw in l.lower() for kw in _LITERATURE_KEYWORDS)]
            rest    = [l for l in lines if l not in salient]
            lines   = salient + rest
        result_lines, total = [], 0
        for line in lines:
            line_len = len(line) + 1  # +1 for newline
            if total + line_len > char_limit:
                break
            result_lines.append(line)
            total += line_len
        text = "\n".join(result_lines).strip()
        if len(result_lines) < len(lines):
            text += " ..."
        return text

    def token_estimate(self) -> dict:
        """Rough token estimates per phase for this slot."""
        def est(t):
            return max(1, len(t) // 4)
        if self._kind == "dataset":
            return {
                "diverge":   est(self.truncate(2500)),
                "criticize": est(self.truncate(500)),
                "converge":  est(self.truncate(100)),
            }
        else:  # literature
            return {
                "diverge":   est(self.truncate(7000)),
                "criticize": est(self.truncate(1000)),
                "converge":  0,
            }


class ContextManager:
    """Manages dataset and literature context slots with phase-aware compression."""

    def __init__(self, dataset: str = "", literature: str = ""):
        self.dataset    = _Slot(dataset,    kind="dataset")
        self.literature = _Slot(literature, kind="literature")

    @property
    def is_empty(self) -> bool:
        return self.dataset.is_empty and self.literature.is_empty

    # ── Per-phase helpers ───────────────────────────────────────────────────

    def for_diverge(self) -> dict:
        """Dataset: 2500 chars. Literature: 7000 chars (salience-ordered)."""
        return {
            "dataset":    self.dataset.truncate(2500),
            "literature": self.literature.truncate(7000),
        }

    def for_criticize(self) -> dict:
        """Dataset: 500 chars. Literature: 1000 chars (salience-ordered)."""
        return {
            "dataset":    self.dataset.truncate(500),
            "literature": self.literature.truncate(1000),
        }

    def for_novelty_critique(self) -> dict:
        """Full literature context for the dedicated novelty critic (up to 7000 chars)."""
        return {
            "literature": self.literature.truncate(7000),
        }

    def for_converge(self) -> dict:
        """Dataset: 100 chars (name/label only). Literature: dropped."""
        return {
            "dataset":    self.dataset.truncate(100),
            "literature": "",
        }

    def token_estimate(self) -> dict:
        """Rough per-phase token estimates for both slots combined."""
        def total(phase_dict):
            return sum(max(1, len(v) // 4) for v in phase_dict.values() if v)
        return {
            "diverge":   total(self.for_diverge()),
            "criticize": total(self.for_criticize()),
            "converge":  total(self.for_converge()),
        }

    @staticmethod
    def _read_file(uploaded_file) -> str:
        uploaded_file.seek(0)
        return uploaded_file.read().decode("utf-8", errors="replace")
