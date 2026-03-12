"""
Cleaning Agent -- LLM-powered intelligent data cleaning.

Responsibilities:
- Analyze data quality issues using LLM reasoning
- Generate a structured cleaning plan
- Execute cleaning operations (dedup, fill nulls, fix types, remove outliers)
- Report what was changed and why
"""


import pandas as pd
from openai import AsyncOpenAI

from backend.agents.base_agent import BaseAgent
from backend.config import get_settings
from backend.database.db import DatabaseClient


CLEANING_SYSTEM_PROMPT = """You are a data quality analyst for business operations data.
Given a dataset summary with quality issues, create a structured cleaning plan.

You MUST respond with ONLY valid JSON. No markdown, no code blocks, no extra text.

Respond with this exact JSON structure:
{
    "assessment": "Brief summary of the data quality state",
    "actions": [
        {
            "action": "remove_duplicates" | "fill_missing" | "convert_types" | "remove_outliers" | "standardize_values",
            "target_column": "column_name or null for row-level ops",
            "strategy": "description of how to handle it",
            "priority": 1-5
        }
    ],
    "risk_level": "low" | "medium" | "high"
}

Rules:
- Prioritize data integrity over completeness
- For missing numeric values, prefer median over mean (more robust to outliers)
- Flag but don't auto-remove statistical outliers -- just mark them
- Always remove exact duplicate rows
- Convert date strings to consistent ISO format
"""


class CleaningAgent(BaseAgent):
    """
    LLM-powered agent that intelligently cleans data.

    Input:
        records: list[dict] -- Raw data records from ingestion
        metadata: dict -- Dataset metadata from ingestion

    Output:
        records: list[dict] -- Cleaned data records
        cleaning_report: dict -- What was changed and why
    """

    def __init__(self, db: DatabaseClient):
        super().__init__(name="cleaning_agent", db=db)
        settings = get_settings()
        self.llm = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    async def run(self, input_data: dict) -> dict:
        records: list[dict] = input_data["records"]
        metadata: dict = input_data["metadata"]

        df = pd.DataFrame(records)
        original_row_count = len(df)
        self.logger.info(f"Cleaning {original_row_count} rows x {len(df.columns)} columns")

        # ── 1. Build data summary for LLM ──
        summary = self._build_data_summary(df, metadata)

        # ── 2. Get LLM cleaning plan ──
        cleaning_plan = await self._get_cleaning_plan(summary)
        self.logger.info(f"LLM cleaning plan: {cleaning_plan.get('assessment', 'N/A')}")

        # ── 3. Execute cleaning actions ──
        actions_taken: list[dict] = []

        for action in sorted(cleaning_plan.get("actions", []), key=lambda a: a.get("priority", 5)):
            action_type = action.get("action", "")
            target = action.get("target_column")

            before_count = len(df)

            if action_type == "remove_duplicates":
                df = df.drop_duplicates()
                removed = before_count - len(df)
                actions_taken.append({
                    "action": "remove_duplicates",
                    "rows_affected": removed,
                    "detail": f"Removed {removed} duplicate rows",
                })

            elif action_type == "fill_missing" and target and target in df.columns:
                null_count = int(df[target].isnull().sum())
                if null_count > 0:
                    if df[target].dtype in ("float64", "int64", "float32", "int32"):
                        median_val = df[target].median()
                        df[target] = df[target].fillna(median_val)
                        actions_taken.append({
                            "action": "fill_missing",
                            "column": target,
                            "rows_affected": null_count,
                            "detail": f"Filled {null_count} nulls with median ({median_val})",
                        })
                    else:
                        mode_val = df[target].mode()
                        if len(mode_val) > 0:
                            df[target] = df[target].fillna(mode_val.iloc[0])
                            actions_taken.append({
                                "action": "fill_missing",
                                "column": target,
                                "rows_affected": null_count,
                                "detail": f"Filled {null_count} nulls with mode ({mode_val.iloc[0]})",
                            })

            elif action_type == "convert_types" and target and target in df.columns:
                if "date" in target.lower():
                    try:
                        df[target] = pd.to_datetime(df[target], errors="coerce").dt.strftime("%Y-%m-%d")
                        actions_taken.append({
                            "action": "convert_types",
                            "column": target,
                            "detail": f"Converted {target} to ISO date format",
                        })
                    except Exception:
                        pass
                elif "price" in target.lower() or "cost" in target.lower() or "revenue" in target.lower():
                    try:
                        df[target] = pd.to_numeric(df[target], errors="coerce")
                        actions_taken.append({
                            "action": "convert_types",
                            "column": target,
                            "detail": f"Converted {target} to numeric",
                        })
                    except Exception:
                        pass

            elif action_type == "remove_outliers" and target and target in df.columns:
                if df[target].dtype in ("float64", "int64", "float32", "int32"):
                    q1 = df[target].quantile(0.25)
                    q3 = df[target].quantile(0.75)
                    iqr = q3 - q1
                    lower = q1 - 3.0 * iqr  # Use 3x IQR (generous) to avoid false positives
                    upper = q3 + 3.0 * iqr
                    outlier_mask = (df[target] < lower) | (df[target] > upper)
                    outlier_count = int(outlier_mask.sum())
                    if outlier_count > 0:
                        # Mark outliers instead of removing
                        df[f"{target}_is_outlier"] = outlier_mask
                        actions_taken.append({
                            "action": "flag_outliers",
                            "column": target,
                            "rows_affected": outlier_count,
                            "detail": f"Flagged {outlier_count} outliers (3x IQR: {lower:.2f} - {upper:.2f})",
                        })

            elif action_type == "standardize_values" and target and target in df.columns:
                if df[target].dtype == "object":
                    df[target] = df[target].str.strip().str.title()
                    actions_taken.append({
                        "action": "standardize_values",
                        "column": target,
                        "detail": f"Standardized text values in {target} (strip + title case)",
                    })

        # ── 4. Final null cleanup for numeric columns ──
        numeric_cols = df.select_dtypes(include=["float64", "int64"]).columns
        for col in numeric_cols:
            remaining_nulls = int(df[col].isnull().sum())
            if remaining_nulls > 0:
                median_val = df[col].median()
                df[col] = df[col].fillna(median_val)
                actions_taken.append({
                    "action": "fill_missing_final",
                    "column": col,
                    "rows_affected": remaining_nulls,
                    "detail": f"Final cleanup: filled {remaining_nulls} remaining nulls with median ({median_val})",
                })

        # ── 5. Build cleaning report ──
        cleaning_report = {
            "original_row_count": original_row_count,
            "final_row_count": len(df),
            "rows_removed": original_row_count - len(df),
            "llm_assessment": cleaning_plan.get("assessment", ""),
            "risk_level": cleaning_plan.get("risk_level", "unknown"),
            "actions_taken": actions_taken,
            "remaining_nulls": int(df.isnull().sum().sum()),
        }

        self.logger.info(
            f"Cleaning complete: {original_row_count} -> {len(df)} rows | "
            f"{len(actions_taken)} actions taken"
        )

        # Convert back to records
        cleaned_records = df.where(df.notnull(), None).to_dict(orient="records")

        return {
            "records": cleaned_records,
            "cleaning_report": cleaning_report,
        }

    def _build_data_summary(self, df: pd.DataFrame, metadata: dict) -> str:
        """Build a concise text summary of the dataset for the LLM."""
        lines = [
            f"Dataset: {metadata.get('file_name', 'unknown')}",
            f"Shape: {len(df)} rows x {len(df.columns)} columns",
            f"Columns: {list(df.columns)}",
            "",
            "Column Details:",
        ]

        for col in df.columns:
            dtype = str(df[col].dtype)
            nulls = int(df[col].isnull().sum())
            uniques = int(df[col].nunique())
            line = f"  - {col}: type={dtype}, nulls={nulls}, unique={uniques}"
            if dtype in ("float64", "int64"):
                line += f", min={df[col].min()}, max={df[col].max()}, mean={df[col].mean():.2f}"
            elif dtype == "object":
                top_vals = df[col].value_counts().head(3).to_dict()
                line += f", top_values={top_vals}"
            lines.append(line)

        dupes = int(df.duplicated().sum())
        lines.append(f"\nDuplicate rows: {dupes}")

        return "\n".join(lines)

    async def _get_cleaning_plan(self, summary: str) -> dict:
        """Ask LLM to analyze data and return a cleaning plan."""
        import json

        response = await self.llm.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": CLEANING_SYSTEM_PROMPT},
                {"role": "user", "content": f"Analyze this dataset and create a cleaning plan:\n\n{summary}"},
            ],
            temperature=0.1,
            max_tokens=1000,
        )

        # Track token usage
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
            self.logger.warning("Failed to parse LLM cleaning plan, using defaults")
            return {
                "assessment": "Failed to parse LLM response, applying default cleaning",
                "actions": [
                    {"action": "remove_duplicates", "target_column": None, "strategy": "Remove exact duplicates", "priority": 1},
                ],
                "risk_level": "low",
            }
