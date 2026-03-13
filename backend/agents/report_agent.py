"""
Report Generation Agent -- Creates formatted Markdown business reports.

Responsibilities:
- Generate professional Markdown report from analysis insights
- Include data tables, summaries, and recommendations
- Produce a structured report suitable for stakeholders
- Optionally convert to PDF (via WeasyPrint)
"""

import json
from datetime import datetime, timezone

from openai import AsyncOpenAI

from backend.agents.base_agent import BaseAgent
from backend.config import get_settings
from backend.database.db import DatabaseClient


REPORT_SYSTEM_PROMPT = """You are a professional business report writer. Generate a comprehensive, well-structured
Markdown report from the provided analysis data.

The report should be formatted in Markdown and include:
1. A professional title with the date
2. Executive Summary section
3. Key Metrics overview (use a Markdown table)
4. Detailed Findings section with each finding clearly explained
5. Trend Analysis section
6. Anomalies & Alerts section (if any)
7. Recommendations section with priority levels
8. Data Quality Notes (brief)

Formatting rules:
- Use proper Markdown: headers (##, ###), tables, bold, bullet lists
- Include specific numbers and percentages -- never be vague
- Keep the executive summary to 3-4 sentences
- Use tables for numeric comparisons
- Mark high-priority items with bold or emoji indicators
- Write for a business executive audience -- clear, concise, actionable
- The entire report should be 400-800 words

Return ONLY the Markdown content. No JSON wrapper needed.
"""


class ReportAgent(BaseAgent):
    """
    LLM-powered agent that generates formatted business reports.

    Input:
        insights: dict -- Analysis insights from AnalysisAgent
        overall_metrics: dict -- KPIs from AggregationAgent
        product_summary: list[dict] -- Product metrics
        region_summary: list[dict] -- Region metrics
        time_series: list[dict] -- Time-based metrics
        top_performers: dict -- Top performers data

    Output:
        report_markdown: str -- The generated Markdown report
        report_title: str -- Report title
        report_metadata: dict -- Generation metadata
    """

    def __init__(self, db: DatabaseClient):
        super().__init__(name="report_agent", db=db)
        settings = get_settings()
        self.llm = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    async def run(self, input_data: dict) -> dict:
        self.logger.info("Generating business report")

        # ── 1. Build report context ──
        context = self._build_report_context(input_data)

        # ── 2. Generate report via LLM ──
        report_markdown = await self._generate_report(context)

        # ── 3. Build title and metadata ──
        now = datetime.now(timezone.utc)
        insights = input_data.get("insights", {})
        metrics = input_data.get("overall_metrics", {})

        date_start = metrics.get("date_range_start", "")
        date_end = metrics.get("date_range_end", "")
        if date_start and date_end:
            report_title = f"Sales Performance Report ({date_start} to {date_end})"
        else:
            report_title = "Sales Performance Report"

        report_metadata = {
            "generated_at": now.isoformat(),
            "model_used": self.model,
            "tokens_used": self.tokens_used,
            "confidence_score": insights.get("confidence_score", 0),
            "total_revenue_analyzed": metrics.get("total_revenue", 0),
            "total_transactions": metrics.get("total_transactions", 0),
        }

        self.logger.info(f"Report generated: {len(report_markdown)} characters")

        return {
            "report_markdown": report_markdown,
            "report_title": report_title,
            "report_metadata": report_metadata,
            "insights": insights,
        }

    def _build_report_context(self, input_data: dict) -> str:
        """Build context from all available data for report generation."""
        sections = []

        # Overall metrics
        metrics = input_data.get("overall_metrics", {})
        sections.append("=== OVERALL METRICS ===")
        sections.append(json.dumps(metrics, indent=2, default=str))

        # Insights
        insights = input_data.get("insights", {})
        sections.append("\n=== ANALYSIS INSIGHTS ===")
        sections.append(json.dumps(insights, indent=2, default=str))

        # Product summary (top 8)
        products = input_data.get("product_summary", [])
        if products:
            sections.append("\n=== PRODUCT PERFORMANCE ===")
            sections.append(json.dumps(products[:8], indent=2, default=str))

        # Region summary
        regions = input_data.get("region_summary", [])
        if regions:
            sections.append("\n=== REGIONAL PERFORMANCE ===")
            sections.append(json.dumps(regions, indent=2, default=str))

        # Time series
        time_series = input_data.get("time_series", [])
        if time_series:
            sections.append("\n=== MONTHLY TRENDS ===")
            sections.append(json.dumps(time_series, indent=2, default=str))

        # Top performers
        top = input_data.get("top_performers", {})
        if top:
            sections.append("\n=== TOP PERFORMERS ===")
            sections.append(json.dumps(top, indent=2, default=str))

        return "\n".join(sections)

    async def _generate_report(self, context: str) -> str:
        """Generate the Markdown report using LLM."""
        response = await self.llm.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": REPORT_SYSTEM_PROMPT},
                {"role": "user", "content": f"Generate a business report from this data:\n\n{context}"},
            ],
            temperature=0.3,
            max_tokens=3000,
        )

        if response.usage:
            self.tokens_used += response.usage.total_tokens

        report = response.choices[0].message.content.strip()

        # Strip any accidental code fences
        if report.startswith("```markdown"):
            report = report[len("```markdown"):].strip()
        elif report.startswith("```"):
            report = report[3:].strip()
        if report.endswith("```"):
            report = report[:-3].strip()

        return report

    async def generate_pdf(self, markdown_content: str, output_path: str) -> str:
        """
        Convert Markdown report to PDF using WeasyPrint.

        Args:
            markdown_content: The Markdown report text
            output_path: Path to save the PDF file

        Returns:
            Path to the generated PDF file
        """
        import markdown
        from xhtml2pdf import pisa

        # Convert Markdown to HTML
        html_body = markdown.markdown(
            markdown_content,
            extensions=["tables", "fenced_code"],
        )

        # Wrap in a styled HTML document
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                @page {{
                    margin: 1.5cm;
                }}
                body {{
                    font-family: Helvetica, Arial, sans-serif;
                    font-size: 12pt;
                    color: #333333;
                    line-height: 1.5;
                }}
                h1 {{ color: #1a1a2e; border-bottom: 2px solid #16213e; padding-bottom: 4pt; font-size: 20pt; margin: 0 0 12pt 0; }}
                h2 {{ color: #16213e; font-size: 16pt; margin: 16pt 0 8pt 0; }}
                h3 {{ color: #0f3460; font-size: 14pt; margin: 12pt 0 6pt 0; }}
                p {{ margin: 0 0 8pt 0; }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 12pt 0;
                }}
                th, td {{
                    border: 1px solid #cccccc;
                    padding: 6pt 8pt;
                    text-align: left;
                    font-size: 11pt;
                }}
                th {{ background-color: #16213e; color: #ffffff; font-weight: bold; }}
                tr:nth-child(even) {{ background-color: #f8f9fa; }}
                strong {{ color: #e94560; font-weight: bold; }}
                code {{ background-color: #f4f4f4; padding: 2pt 4pt; border-radius: 2pt; font-size: 11pt; }}
                ul {{ margin: 6pt 0 12pt 0; padding-left: 24pt; }}
                li {{ margin: 0 0 4pt 0; }}
                li p {{ margin: 0; }}
            </style>
        </head>
        <body>
            {html_body}
        </body>
        </html>
        """

        import os
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w+b") as result_file:
            pisa_status = pisa.CreatePDF(full_html, dest=result_file)

        if pisa_status.err:
            raise Exception("PDF generation failed with xhtml2pdf")

        self.logger.info(f"PDF generated: {output_path}")

        return output_path
