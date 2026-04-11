"""Manual checker for Kimi brainstorming parsing.

Usage:
  python tools/check_kimi_parser.py
  python tools/check_kimi_parser.py --file path\to\raw_kimi_output.txt
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.member import CouncilMember  # noqa: E402


SAMPLE_KIMI_OUTPUT = """
Structure check:
```
IDEA [number]:
Title: [Clear, descriptive title]
Summary: [2-3 sentence overview]
Methodology: [Specific approach and methods]
Feasibility: [Why this is doable with given resources]
Timeline: [Estimated duration and key milestones]
Expected Outcomes: [What results to expect]
```

Drafting:

**Algorithmic Disagreement Signatures as Proxy for Movement Complexity in Free-Living Populations**

Title: Algorithmic Disagreement Signatures as Proxy for Movement Complexity in Free-Living Populations
Summary: Instead of treating discrepancies between step-counting algorithms as noise, this study extracts features from minute-level disagreement to predict health indicators.
Methodology: Calculate per-minute variance and entropy across the six step algorithms.
Use Random Forest and XGBoost on the engineered features.
Feasibility: Purely CPU-based feature engineering and classical ML.
Timeline: Month 1-2 for preprocessing, Month 3-4 for modeling, Month 5-6 for writing.
Expected Outcomes: A lightweight biomarker and a publishable methods-focused baseline.
"""


def build_member() -> CouncilMember:
    return CouncilMember(
        member_id="kimi_manual",
        model_config={"display_name": "Kimi K2.5"},
        api_client=None,
    )


def print_ideas(ideas: list[dict]) -> None:
    print(f"Parsed ideas: {len(ideas)}")
    print("=" * 80)
    for index, idea in enumerate(ideas, 1):
        print(f"IDEA {index}")
        print(f"title: {idea.get('title', '')}")
        print(f"summary: {idea.get('summary', '')}")
        print(f"methodology: {idea.get('methodology', '')}")
        print(f"feasibility: {idea.get('feasibility', '')}")
        print(f"timeline: {idea.get('timeline', '')}")
        print(f"expected_outcomes: {idea.get('expected_outcomes', '')}")
        print("-" * 80)

    print("JSON:")
    print(json.dumps(ideas, indent=2, ensure_ascii=True))


def main() -> None:
    parser = argparse.ArgumentParser(description="Check Kimi brainstorming parsing.")
    parser.add_argument(
        "--file",
        type=Path,
        help="Optional path to a text file containing the raw Kimi response.",
    )
    args = parser.parse_args()

    if args.file:
        content = args.file.read_text(encoding="utf-8")
        print(f"Loaded raw response from: {args.file}")
    else:
        content = SAMPLE_KIMI_OUTPUT
        print("Using built-in Kimi-style sample response.")

    member = build_member()
    ideas = member._parse_ideas(content)
    print_ideas(ideas)


if __name__ == "__main__":
    main()
