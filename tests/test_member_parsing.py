"""Regression tests for parsing council member outputs."""

from core.member import CouncilMember


def make_member() -> CouncilMember:
    """Create a minimal member instance for parser-only tests."""
    return CouncilMember(
        member_id="kimi_1",
        model_config={"display_name": "Kimi K2.5"},
        api_client=None,
    )


def test_parse_ideas_skips_placeholder_title_and_keeps_details():
    """Kimi-style reasoning preambles should not overwrite the real idea block."""
    member = make_member()
    content = """
Structure check:
```
IDEA [number]:
Title: [Clear, descriptive title]
Summary: [2-3 sentence overview]
Gap: [The research gap being addressed]
Novel Component: [The key novelty of the approach]
Pipeline: [Step-by-step methodology]
Feasibility: [Why this is doable with given resources]
Expected Outcomes: [What results to expect]
```

Drafting:

**Algorithmic Disagreement Signatures as Proxy for Movement Complexity in Free-Living Populations**

Title: Algorithmic Disagreement Signatures as Proxy for Movement Complexity in Free-Living Populations
Summary: Instead of treating discrepancies between step-counting algorithms as noise, this study extracts features from minute-level disagreement to predict health indicators.
Gap: No prior work has mined inter-algorithm disagreement as a proxy for movement complexity.
Novel Component: A disagreement feature extractor that quantifies per-minute variance and entropy.
Pipeline: Calculate per-minute variance and entropy across the six step algorithms.
Use Random Forest and XGBoost on the engineered features.
Feasibility: Purely CPU-based feature engineering and classical ML.
Expected Outcomes: A lightweight biomarker and a publishable methods-focused baseline.
"""

    ideas = member._parse_ideas(content)

    assert len(ideas) == 1
    assert ideas[0]["title"] == (
        "Algorithmic Disagreement Signatures as Proxy for Movement Complexity "
        "in Free-Living Populations"
    )
    assert ideas[0]["summary"].startswith("Instead of treating discrepancies")
    assert "Use Random Forest and XGBoost" in ideas[0]["pipeline"]
    assert ideas[0]["feasibility"] == "Purely CPU-based feature engineering and classical ML."
    assert ideas[0]["expected_outcomes"].startswith("A lightweight biomarker")


def test_parse_ideas_handles_markdown_labels_and_multiline_fields():
    """Markdown-formatted labels should still parse into structured fields."""
    member = make_member()
    content = """
IDEA 1:
**Title:** Temporal Activity Fragmentation Index
**Summary:** Develop and validate novel metrics quantifying how fragmented physical activity is.
This should remain attached to the summary field.
**Gap:** No validated fragmentation metric exists for free-living accelerometer data.
**Novel Component:** A set of bout-based features capturing fragmentation patterns.
**Pipeline:** Engineer bout-based features.
1. Count activity bouts.
2. Compute Gini coefficient of bout lengths.
**Feasibility:** No GPU required.
**Expected Outcomes:** A compact and interpretable activity-quality metric.
"""

    ideas = member._parse_ideas(content)

    assert len(ideas) == 1
    assert ideas[0]["title"] == "Temporal Activity Fragmentation Index"
    assert "remain attached to the summary field" in ideas[0]["summary"]
    assert "Compute Gini coefficient" in ideas[0]["pipeline"]
