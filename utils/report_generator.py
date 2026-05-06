"""
Markdown report generation.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from utils.validator import Validator

import re as _re


class ReportGenerator:
    """Generate markdown reports from council results."""

    def __init__(self, output_dir: Path):
        """
        Initialize report generator.

        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    @staticmethod
    def _clean_synthesis(text: str) -> str:
        """
        Clean raw LLM synthesis text for markdown output:
        1. Strip ``` code-block fences the model sometimes wraps around its output.
        2. Join hard line-wrapped paragraphs (single \\n within a paragraph → space).
           Structural lines (headers, bullets, separators, blank lines) are preserved.
        """
        if not text:
            return text

        # 1. Remove leading/trailing ``` fences
        text = _re.sub(r'^```[^\n]*\n', '', text.strip())
        text = _re.sub(r'\n```\s*$', '', text)
        text = text.strip()

        # 2. Strip ASCII art separator lines (═══, ───, ━━━) that models sometimes generate.
        #    Replace them with a standard markdown --- divider.
        text = _re.sub(r'^[═━─]{4,}\s*$', '---', text, flags=_re.MULTILINE)

        # 3. Join hard-wrapped paragraph lines.
        #    A line is "structural" if it starts with a markdown marker or is blank.
        STRUCTURAL = _re.compile(
            r'^\s*($|#+\s|[-*+]\s|\d+\.\s|>{1}|-{3,}|\*{3,})'
        )

        lines = text.splitlines()
        out = []
        for line in lines:
            if not out:
                out.append(line)
                continue
            prev = out[-1]
            # If either current or previous line is structural, keep as-is
            if STRUCTURAL.match(line) or STRUCTURAL.match(prev) or not prev.strip():
                out.append(line)
            else:
                # Soft-wrap: join to previous line with a space
                out[-1] = prev.rstrip() + ' ' + line.lstrip()

        return '\n'.join(out)

    def generate_report(
        self,
        user_prompt: str,
        iterations_data: List[Dict[str, Any]],
        total_cost: float,
        cost_breakdown: Dict[str, Any],
        selected_models: List[str]
    ) -> str:
        """
        Generate comprehensive markdown report.

        Args:
            user_prompt: Original user research prompt
            iterations_data: List of iteration results
            total_cost: Total cost across all iterations
            cost_breakdown: Cost breakdown by phase and model
            selected_models: List of selected model keys

        Returns:
            Markdown report as string
        """
        report_lines = []

        # Header
        report_lines.append("# LLM Council Research Brainstorming Report")
        report_lines.append("")
        report_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"**Iterations:** {len(iterations_data)}")
        report_lines.append(f"**Total Cost:** ${total_cost:.4f}")
        report_lines.append(f"**Council Models:** {', '.join(selected_models)}")
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")

        # Original Prompt
        report_lines.append("## Original Research Prompt")
        report_lines.append("")
        report_lines.append(f"> {user_prompt}")
        report_lines.append("")

        # Results — show synthesis once, cleanly
        if iterations_data:
            final_iteration = iterations_data[-1]
            if "converge" in final_iteration:
                report_lines.append("## Results")
                report_lines.append("")
                report_lines.append(self._clean_synthesis(final_iteration["converge"].get("synthesis", "")))
                report_lines.append("")

        # Iteration History
        report_lines.append("## Iteration History")
        report_lines.append("")

        for i, iteration in enumerate(iterations_data, 1):
            report_lines.append(f"### Iteration {i}")
            report_lines.append("")

            if "user_feedback" in iteration and iteration["user_feedback"]:
                report_lines.append(f"**User Feedback:** {iteration['user_feedback']}")
                report_lines.append("")

            # Diverge phase
            if "diverge" in iteration:
                report_lines.append("#### Diverge Phase - Generated Ideas")
                report_lines.append("")

                for member_id, member_result in iteration["diverge"].items():
                    report_lines.append(f"**{member_id}:**")
                    report_lines.append("")
                    for idea in member_result.get("ideas", []):
                        report_lines.append(f"- **{idea.get('title', 'Untitled')}**: {idea.get('summary', '')}")
                    report_lines.append("")

            # Criticize phase
            if "criticize" in iteration:
                report_lines.append("#### Criticize Phase - Key Insights")
                report_lines.append("")

                # Extract common themes from critiques
                report_lines.append("*Critical evaluations were performed by all council members.*")
                report_lines.append("")

            # Converge phase — synthesis shown in Results section above
            if "converge" in iteration:
                report_lines.append("#### Converge Phase")
                report_lines.append("")
                report_lines.append("*Synthesis complete — see Results section above.*")
                report_lines.append("")

        # Cost Breakdown
        report_lines.append("## Cost Breakdown")
        report_lines.append("")
        report_lines.append(f"**Total Cost:** ${total_cost:.4f}")
        report_lines.append("")

        if "by_phase" in cost_breakdown:
            report_lines.append("### By Phase")
            report_lines.append("")
            for phase, cost in cost_breakdown["by_phase"].items():
                report_lines.append(f"- **{phase.capitalize()}:** ${cost:.4f}")
            report_lines.append("")

        if "by_model" in cost_breakdown:
            report_lines.append("### By Model")
            report_lines.append("")
            for model, cost in cost_breakdown["by_model"].items():
                report_lines.append(f"- **{model}:** ${cost:.4f}")
            report_lines.append("")

        # Appendices
        report_lines.append("## Appendices")
        report_lines.append("")
        report_lines.append("### All Generated Ideas")
        report_lines.append("")

        for i, iteration in enumerate(iterations_data, 1):
            if "diverge" in iteration:
                report_lines.append(f"#### Iteration {i}")
                report_lines.append("")

                for member_id, member_result in iteration["diverge"].items():
                    report_lines.append(f"**{member_id}:**")
                    report_lines.append("")
                    for idea in member_result.get("ideas", []):
                        report_lines.append(f"**{idea.get('title', 'Untitled')}**")
                        report_lines.append("")
                        report_lines.append(idea.get('full_description', idea.get('summary', '')))
                        report_lines.append("")

        # Footer
        report_lines.append("---")
        report_lines.append("")
        report_lines.append("*Generated by LLM Council Research Brainstorming Application*")

        return "\n".join(report_lines)

    def _format_top_ideas(self, top_ideas: list) -> list:
        """Format top ideas into markdown lines.
        Uses raw_text (the full block from the converge output) for complete content.
        """
        lines = []
        for i, idea in enumerate(top_ideas, 1):
            title = idea.get('title', 'Untitled')
            lines.append(f"### {i}. {title}")
            lines.append("")
            raw = idea.get('raw_text', '')
            if raw:
                # Strip the title line to avoid duplication, then clean line breaks
                raw_lines = raw.splitlines()
                body = "\n".join(raw_lines[1:]).strip() if len(raw_lines) > 1 else ""
                if body:
                    lines.append(self._clean_synthesis(body))
            lines.append("")
        return lines

    def generate_recommendations_report(
        self,
        user_prompt: str,
        iterations_data: List[Dict[str, Any]],
        total_cost: float,
        selected_models: List[str]
    ) -> str:
        """
        Generate a short Top Recommendations-only report for on-screen display and download.
        """
        lines = []
        lines.append("# LLM Council — Top Recommendations")
        lines.append("")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Iterations:** {len(iterations_data)}")
        lines.append(f"**Total Cost:** ${total_cost:.4f}")
        lines.append(f"**Council:** {', '.join(selected_models)}")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Research Prompt")
        lines.append("")
        lines.append(f"> {user_prompt}")
        lines.append("")

        if not iterations_data:
            return "\n".join(lines)

        final = iterations_data[-1]
        converge = final.get("converge", {})

        # Render the synthesis directly — it is already well-formatted markdown
        synthesis = self._clean_synthesis(converge.get("synthesis", ""))
        if synthesis:
            lines.append(synthesis)

        lines.append("---")
        lines.append("")
        lines.append("*Generated by LLM Council Research Brainstorming Application*")
        return "\n".join(lines)

    def save_report(
        self,
        report_content: str,
        filename: Optional[str] = None
    ) -> Path:
        """
        Save report to file.

        Args:
            report_content: Markdown report content
            filename: Optional custom filename

        Returns:
            Path to saved report
        """
        if filename is None:
            filename = f"council_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        else:
            filename = Validator.sanitize_filename(filename)
            if not filename.endswith('.md'):
                filename += '.md'

        filepath = self.output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_content)

        return filepath

    def generate_quick_summary(self, iterations_data: List[Dict[str, Any]]) -> str:
        """
        Generate a quick summary for display.

        Args:
            iterations_data: List of iteration results

        Returns:
            Brief summary text
        """
        if not iterations_data:
            return "No results yet."

        final_iteration = iterations_data[-1]

        summary_lines = []
        summary_lines.append(f"**Completed {len(iterations_data)} iteration(s)**")
        summary_lines.append("")

        if "converge" in final_iteration:
            top_ideas = final_iteration["converge"].get("top_ideas", [])
            if top_ideas:
                summary_lines.append("**Top Recommendations:**")
                for i, idea in enumerate(top_ideas[:3], 1):
                    summary_lines.append(f"{i}. {idea.get('title', 'Untitled')}")

        return "\n".join(summary_lines)
