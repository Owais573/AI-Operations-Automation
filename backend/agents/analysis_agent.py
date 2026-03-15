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
Analyze the provided business data and metrics to generate strategic insights.

### AUTONOMOUS SCHEMA DISCOVERY
You have the ability to notice "Extra Columns" or "Hidden Dimensions" in the data quality reports. 
Even if a metric wasn't explicitly aggregated, if you see high-cardinality flags or unusual column names (e.g., 'DiscountCode', 'ReturnReason', 'MarketingChannel'), incorporate them into your findings as potential drivers of the observed performance.

The data could be about SALES, INVENTORY, FINANCE, or other operational areas. 
Adapt your reasoning based on the metrics provided.

You MUST respond with ONLY valid JSON. No markdown, no code blocks, no extra text.

Respond with this exact JSON structure:
{
    "executive_summary": "2-3 sentence high-level summary of the operational performance",
    "key_findings": [
        {
            "finding": "Brief description of the finding",
            "category": "trend" | "anomaly" | "opportunity" | "risk" | "discovery",
            "impact": "high" | "medium" | "low",
            "details": "Detailed explanation with specific numbers and metrics. Include any discovered columns here.",
            "recommendation": "Actionable recommendation"
        }
    ],
    "trend_analysis": {
        "primary_trend": "description of the primary metric trend over time",
        "growth_assessment": "improving" | "stable" | "declining",
        "observations": "any notable patterns observed in the time series"
    },
    "anomalies_detected": [
        {
            "description": "What was unusual about the data",
            "severity": "critical" | "warning" | "info",
            "affected_metric": "which metric(s) were affected",
            "possible_cause": "likely explanation based on the data"
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
    "data_quality_notes": "Include notes on any unexpected schema columns discoverd."
}

Analysis Rules:
- Use specific numbers and percentages provided in the data.
- Compare metrics across time periods if available.
- Identify correlations between different dimensions (e.g., regions/departments/warehouses).
- Provide actionable, business-oriented recommendations.
- Focus on performance, efficiency, and risk highlights.
- Actively highlight any columns in the 'Extra/Unexpected' section that seem significant.
"""


class AnalysisAgent(BaseAgent):
    """
    LLM-powered agent that generates business insights from aggregated data.
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
        report_type = input_data.get("report_type", "General Business")
        lines = [f"=== {report_type.upper()} ANALYSIS CONTEXT ===", ""]

        # Overall metrics
        metrics = input_data.get("overall_metrics", {})
        lines.append("--- OVERALL KPIs & METRICS ---")
        for key, value in metrics.items():
            lines.append(f"  {key}: {value}")
        lines.append("")

        # Schema Discovery (The "Extra" Columns)
        metadata = input_data.get("metadata", {})
        if metadata:
            all_cols = metadata.get("columns", [])
            lines.append("--- SCHEMA DISCOVERY (ALL COLUMNS) ---")
            lines.append(f"  Available Dimensions/Measures: {', '.join(all_cols)}")
            
            # Highlight non-standard columns
            std_cols = ["date", "product", "region", "revenue", "cost", "quantity", "category", "department", "sku", "price"]
            extra = [c for c in all_cols if not any(s in c.toLowerCase() for s in std_cols)]
            if extra:
                lines.append(f"  Unexpected/Custom Columns Found: {', '.join(extra)}")
            lines.append("")

        # Time series
        time_series = input_data.get("time_series", [])
        if time_series:
            lines.append("--- PERFORMANCE OVER TIME ---")
            for period in time_series:
                p_text = f"  {period.get('period', '?')}: "
                # Dynamically include any 'total_*' or 'growth_*' columns
                measure_parts = []
                for k, v in period.items():
                    if k != "period":
                        if isinstance(v, float):
                            measure_parts.append(f"{k}={v:.2f}")
                        else:
                            measure_parts.append(f"{k}={v}")
                lines.append(p_text + " | ".join(measure_parts))
            lines.append("")

        # Dimension Summaries (Generic)
        for key in ["product_summary", "region_summary", "department_summary", "category_summary"]:
            data = input_data.get(key, [])
            if data:
                lines.append(f"--- {key.replace('_', ' ').upper()} (Top 10) ---")
                for item in data[:10]:
                    parts = [f"{k}: {v}" for k, v in item.items()]
                    lines.append("  " + " | ".join(parts))
                lines.append("")

        # Cleaning report context
        cleaning = input_data.get("cleaning_report", {})
        if cleaning:
            lines.append("--- DATA QUALITY & RELIABILITY ---")
            lines.append(f"  Original rows: {cleaning.get('original_row_count', '?')}")
            lines.append(f"  After cleaning: {cleaning.get('final_row_count', '?')}")
            lines.append(f"  Risk level: {cleaning.get('risk_level', '?')}")
            lines.append(f"  LLM assessment: {cleaning.get('llm_assessment', '?')}")

        return "\n".join(lines)

    async def _analyze_with_llm(self, context: str) -> dict:
        """Send data to LLM for analysis and parse structured response."""
        response = await self.llm.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
                {"role": "user", "content": f"Analyze the following operational data and provide structured insights:\n\n{context}"},
            ],
            temperature=0.2,
            max_tokens=2000,
        )

        if response.usage:
            self.tokens_used += response.usage.total_tokens

        raw = response.choices[0].message.content.strip()

        # Strip markdown code fences
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            self.logger.warning("Failed to parse LLM analysis response")
            # Fallback structure
            return {
                "executive_summary": "Analysis completed but parsing failed.",
                "key_findings": [],
                "trend_analysis": {"primary_trend": "Unknown", "growth_assessment": "stable", "observations": "N/A"},
                "anomalies_detected": [],
                "recommendations": [],
                "confidence_score": 0.5,
                "data_quality_notes": "JSON parsing error.",
            }
