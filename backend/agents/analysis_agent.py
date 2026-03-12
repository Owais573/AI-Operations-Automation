"""
Analysis Agent -- LLM-powered business insights generation.

Responsibilities:
- Analyze aggregated metrics using chain-of-thought reasoning
- Detect trends, anomalies, and performance patterns
- Generate structured business insights and recommendations
- Assess data confidence and highlight areas of concern
"""

import json

from openai import AsyncOpenAI

from backend.agents.base_agent import BaseAgent
from backend.config import get_settings
from backend.database.db import DatabaseClient


ANALYSIS_SYSTEM_PROMPT = """You are a senior business intelligence analyst for an enterprise operations team.
Given aggregated sales data and metrics, perform a thorough analysis.

You MUST respond with ONLY valid JSON. No markdown, no code blocks, no extra text.

Respond with this exact JSON structure:
{
    "executive_summary": "2-3 sentence high-level summary of business performance",
    "key_findings": [
        {
            "finding": "Brief description of the finding",
            "category": "trend" | "anomaly" | "opportunity" | "risk",
            "impact": "high" | "medium" | "low",
            "details": "Detailed explanation with specific numbers",
            "recommendation": "Actionable recommendation"
        }
    ],
    "trend_analysis": {
        "revenue_trend": "description of revenue trend over time",
        "growth_assessment": "growing" | "stable" | "declining",
        "seasonality_notes": "any seasonal patterns observed"
    },
    "anomalies_detected": [
        {
            "description": "What was unusual",
            "severity": "critical" | "warning" | "info",
            "affected_metric": "which metric(s) were affected",
            "possible_cause": "likely explanation"
        }
    ],
    "recommendations": [
        {
            "title": "Short recommendation title",
            "description": "What to do and why",
            "priority": "high" | "medium" | "low",
            "expected_impact": "What improvement is expected"
        }
    ],
    "confidence_score": 0.0-1.0,
    "data_quality_notes": "Any concerns about data reliability"
}

Analysis Rules:
- Use specific numbers and percentages, not vague language
- Compare month-over-month and identify trends
- Flag any metrics that deviate >20% from average as anomalies
- Provide at least 3 actionable recommendations
- Be honest about data limitations
- Focus on the most impactful findings first
"""


class AnalysisAgent(BaseAgent):
    """
    LLM-powered agent that generates business insights from aggregated data.

    Input:
        overall_metrics: dict -- High-level KPIs from aggregation
        product_summary: list[dict] -- Per-product metrics
        region_summary: list[dict] -- Per-region metrics
        time_series: list[dict] -- Time-based metrics
        top_performers: dict -- Best-performing products/reps
        cleaning_report: dict (optional) -- Data cleaning summary

    Output:
        insights: dict -- Structured analysis with findings, trends, anomalies, recommendations
    """

    def __init__(self, db: DatabaseClient):
        super().__init__(name="analysis_agent", db=db)
        settings = get_settings()
        self.llm = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    async def run(self, input_data: dict) -> dict:
        self.logger.info("Generating business insights with LLM analysis")

        # ── 1. Build analysis context ──
        context = self._build_analysis_context(input_data)

        # ── 2. Get LLM analysis ──
        insights = await self._analyze_with_llm(context)

        finding_count = len(insights.get("key_findings", []))
        anomaly_count = len(insights.get("anomalies_detected", []))
        rec_count = len(insights.get("recommendations", []))

        self.logger.info(
            f"Analysis complete: {finding_count} findings | "
            f"{anomaly_count} anomalies | {rec_count} recommendations"
        )

        return {"insights": insights}

    def _build_analysis_context(self, input_data: dict) -> str:
        """Build a comprehensive text summary for the LLM."""
        lines = ["=== BUSINESS DATA ANALYSIS CONTEXT ===", ""]

        # Overall metrics
        metrics = input_data.get("overall_metrics", {})
        lines.append("--- OVERALL METRICS ---")
        for key, value in metrics.items():
            lines.append(f"  {key}: {value}")
        lines.append("")

        # Time series
        time_series = input_data.get("time_series", [])
        if time_series:
            lines.append("--- MONTHLY PERFORMANCE ---")
            for period in time_series:
                lines.append(
                    f"  {period.get('period', '?')}: "
                    f"Revenue=${period.get('total_revenue', 0):,.2f} | "
                    f"Profit=${period.get('gross_profit', 0):,.2f} | "
                    f"Margin={period.get('gross_margin_pct', 0):.1f}% | "
                    f"Growth={period.get('revenue_growth_pct', 0):+.1f}%"
                )
            lines.append("")

        # Product summary
        products = input_data.get("product_summary", [])
        if products:
            lines.append("--- PRODUCT PERFORMANCE ---")
            for p in products[:10]:
                lines.append(
                    f"  {p.get('product', '?')}: "
                    f"Revenue=${p.get('total_revenue', 0):,.2f} | "
                    f"Units={p.get('total_units', 0):,.0f} | "
                    f"Margin={p.get('gross_margin_pct', 0):.1f}% | "
                    f"Share={p.get('revenue_share_pct', 0):.1f}%"
                )
            lines.append("")

        # Region summary
        regions = input_data.get("region_summary", [])
        if regions:
            lines.append("--- REGIONAL PERFORMANCE ---")
            for r in regions:
                lines.append(
                    f"  {r.get('region', '?')}: "
                    f"Revenue=${r.get('total_revenue', 0):,.2f} | "
                    f"Units={r.get('total_units', 0):,.0f} | "
                    f"Margin={r.get('gross_margin_pct', 0):.1f}% | "
                    f"Share={r.get('revenue_share_pct', 0):.1f}%"
                )
            lines.append("")

        # Top performers
        top = input_data.get("top_performers", {})
        if top:
            lines.append("--- TOP PERFORMERS ---")
            for category, items in top.items():
                lines.append(f"  {category}:")
                for item in items[:5]:
                    lines.append(f"    {item}")
            lines.append("")

        # Cleaning report context
        cleaning = input_data.get("cleaning_report", {})
        if cleaning:
            lines.append("--- DATA QUALITY NOTES ---")
            lines.append(f"  Original rows: {cleaning.get('original_row_count', '?')}")
            lines.append(f"  After cleaning: {cleaning.get('final_row_count', '?')}")
            lines.append(f"  Rows removed: {cleaning.get('rows_removed', 0)}")
            lines.append(f"  Risk level: {cleaning.get('risk_level', '?')}")
            lines.append(f"  LLM assessment: {cleaning.get('llm_assessment', '?')}")

        return "\n".join(lines)

    async def _analyze_with_llm(self, context: str) -> dict:
        """Send data to LLM for analysis and parse structured response."""
        response = await self.llm.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
                {"role": "user", "content": f"Analyze the following business data:\n\n{context}"},
            ],
            temperature=0.2,
            max_tokens=2000,
        )

        if response.usage:
            self.tokens_used += response.usage.total_tokens

        raw = response.choices[0].message.content.strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            self.logger.warning("Failed to parse LLM analysis response")
            return {
                "executive_summary": "Analysis completed but response parsing failed. Raw insights were generated.",
                "key_findings": [],
                "trend_analysis": {"revenue_trend": "Unable to parse", "growth_assessment": "unknown", "seasonality_notes": "N/A"},
                "anomalies_detected": [],
                "recommendations": [],
                "confidence_score": 0.3,
                "data_quality_notes": "LLM response could not be parsed as structured JSON.",
                "raw_response": raw[:1000],
            }
