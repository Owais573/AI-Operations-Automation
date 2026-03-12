"""
Aggregation Agent -- Dynamic data grouping and metric calculation.

Responsibilities:
- Group data by configurable dimensions (product, region, time period)
- Calculate key business metrics (revenue, units, margins, growth)
- Compute period-over-period comparisons
- Prepare structured aggregates for the Analysis Agent
"""


import pandas as pd

from backend.agents.base_agent import BaseAgent
from backend.database.db import DatabaseClient


class AggregationAgent(BaseAgent):
    """
    Agent that aggregates cleaned data into business metrics.

    Input:
        records: list[dict] -- Cleaned data records
        group_by: list[str] (optional) -- Dimensions to group by (default: product, region)
        time_period: str (optional) -- Time grouping: 'daily', 'weekly', 'monthly' (default: monthly)

    Output:
        product_summary: list[dict] -- Per-product metrics
        region_summary: list[dict] -- Per-region metrics
        time_series: list[dict] -- Time-based metrics
        overall_metrics: dict -- High-level KPIs
        top_performers: dict -- Best-performing products and reps
    """

    def __init__(self, db: DatabaseClient):
        super().__init__(name="aggregation_agent", db=db)

    async def run(self, input_data: dict) -> dict:
        records: list[dict] = input_data["records"]
        group_by: list[str] = input_data.get("group_by", ["product", "region"])
        time_period: str = input_data.get("time_period", "monthly")

        df = pd.DataFrame(records)
        self.logger.info(f"Aggregating {len(df)} rows | group_by={group_by} | period={time_period}")

        # ── 0. Ensure numeric types ──
        numeric_cols = ["units_sold", "unit_price", "revenue", "cost"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")

        # ── 1. Overall KPIs ──
        overall_metrics = self._compute_overall_metrics(df)

        # ── 2. Product summary ──
        product_summary = self._aggregate_by_dimension(df, "product")

        # ── 3. Region summary ──
        region_summary = self._aggregate_by_dimension(df, "region")

        # ── 4. Time series ──
        time_series = self._aggregate_by_time(df, time_period)

        # ── 5. Top performers ──
        top_performers = self._get_top_performers(df)

        # ── 6. Cross-dimensional (product x region) ──
        cross_summary = self._aggregate_cross_dimensions(df, "product", "region")

        self.logger.info(
            f"Aggregation complete | products={len(product_summary)} | "
            f"regions={len(region_summary)} | time_periods={len(time_series)}"
        )

        return {
            "overall_metrics": overall_metrics,
            "product_summary": product_summary,
            "region_summary": region_summary,
            "time_series": time_series,
            "top_performers": top_performers,
            "cross_summary": cross_summary,
        }

    def _compute_overall_metrics(self, df: pd.DataFrame) -> dict:
        """Calculate high-level KPIs."""
        total_revenue = float(df["revenue"].sum()) if "revenue" in df.columns else 0
        total_cost = float(df["cost"].sum()) if "cost" in df.columns else 0
        total_units = float(df["units_sold"].sum()) if "units_sold" in df.columns else 0
        gross_profit = total_revenue - total_cost
        gross_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0

        metrics = {
            "total_revenue": round(total_revenue, 2),
            "total_cost": round(total_cost, 2),
            "gross_profit": round(gross_profit, 2),
            "gross_margin_pct": round(gross_margin, 2),
            "total_units_sold": round(total_units, 0),
            "total_transactions": len(df),
            "avg_order_value": round(total_revenue / len(df), 2) if len(df) > 0 else 0,
            "unique_products": int(df["product"].nunique()) if "product" in df.columns else 0,
            "unique_regions": int(df["region"].nunique()) if "region" in df.columns else 0,
        }

        if "date" in df.columns:
            valid_dates = df["date"].dropna()
            if len(valid_dates) > 0:
                metrics["date_range_start"] = str(valid_dates.min().date())
                metrics["date_range_end"] = str(valid_dates.max().date())

        return metrics

    def _aggregate_by_dimension(self, df: pd.DataFrame, dimension: str) -> list[dict]:
        """Aggregate metrics by a single dimension (e.g., product or region)."""
        if dimension not in df.columns:
            return []

        agg_df = df.groupby(dimension, dropna=False).agg(
            total_revenue=("revenue", "sum"),
            total_cost=("cost", "sum"),
            total_units=("units_sold", "sum"),
            transaction_count=("revenue", "count"),
            avg_unit_price=("unit_price", "mean"),
        ).reset_index()

        agg_df["gross_profit"] = agg_df["total_revenue"] - agg_df["total_cost"]
        agg_df["gross_margin_pct"] = (
            agg_df["gross_profit"] / agg_df["total_revenue"] * 100
        ).fillna(0)

        # Revenue share
        total_rev = agg_df["total_revenue"].sum()
        agg_df["revenue_share_pct"] = (agg_df["total_revenue"] / total_rev * 100).fillna(0)

        # Sort by revenue descending
        agg_df = agg_df.sort_values("total_revenue", ascending=False)

        # Round values
        for col in ["total_revenue", "total_cost", "gross_profit", "gross_margin_pct",
                     "avg_unit_price", "revenue_share_pct"]:
            agg_df[col] = agg_df[col].round(2)

        return agg_df.to_dict(orient="records")

    def _aggregate_by_time(self, df: pd.DataFrame, period: str) -> list[dict]:
        """Aggregate metrics by time period."""
        if "date" not in df.columns:
            return []

        df_time = df.dropna(subset=["date"]).copy()
        if len(df_time) == 0:
            return []

        # Set period grouper
        freq_map = {"daily": "D", "weekly": "W", "monthly": "MS"}
        freq = freq_map.get(period, "MS")

        df_time["period"] = df_time["date"].dt.to_period(
            {"D": "D", "W": "W", "MS": "M"}.get(freq, "M")
        )

        agg_df = df_time.groupby("period").agg(
            total_revenue=("revenue", "sum"),
            total_cost=("cost", "sum"),
            total_units=("units_sold", "sum"),
            transaction_count=("revenue", "count"),
        ).reset_index()

        agg_df["period"] = agg_df["period"].astype(str)
        agg_df["gross_profit"] = agg_df["total_revenue"] - agg_df["total_cost"]
        agg_df["gross_margin_pct"] = (
            agg_df["gross_profit"] / agg_df["total_revenue"] * 100
        ).fillna(0)

        # Period-over-period growth
        agg_df["revenue_growth_pct"] = agg_df["total_revenue"].pct_change() * 100
        agg_df = agg_df.fillna(0)

        # Round
        for col in ["total_revenue", "total_cost", "gross_profit", "gross_margin_pct", "revenue_growth_pct"]:
            agg_df[col] = agg_df[col].round(2)

        return agg_df.to_dict(orient="records")

    def _get_top_performers(self, df: pd.DataFrame) -> dict:
        """Identify top-performing products and sales reps."""
        result = {}

        # Top products by revenue
        if "product" in df.columns:
            top_products = (
                df.groupby("product")["revenue"]
                .sum()
                .sort_values(ascending=False)
                .head(5)
            )
            result["top_products_by_revenue"] = [
                {"product": name, "revenue": round(float(val), 2)}
                for name, val in top_products.items()
            ]

        # Top sales reps by revenue
        if "sales_rep" in df.columns:
            top_reps = (
                df.groupby("sales_rep")["revenue"]
                .sum()
                .sort_values(ascending=False)
                .head(5)
            )
            result["top_reps_by_revenue"] = [
                {"sales_rep": name, "revenue": round(float(val), 2)}
                for name, val in top_reps.items()
            ]

        # Top region by revenue
        if "region" in df.columns:
            top_regions = (
                df.groupby("region")["revenue"]
                .sum()
                .sort_values(ascending=False)
            )
            result["top_regions_by_revenue"] = [
                {"region": name, "revenue": round(float(val), 2)}
                for name, val in top_regions.items()
            ]

        return result

    def _aggregate_cross_dimensions(self, df: pd.DataFrame, dim1: str, dim2: str) -> list[dict]:
        """Cross-tabulate two dimensions."""
        if dim1 not in df.columns or dim2 not in df.columns:
            return []

        cross = df.groupby([dim1, dim2]).agg(
            total_revenue=("revenue", "sum"),
            total_units=("units_sold", "sum"),
        ).reset_index()

        cross["total_revenue"] = cross["total_revenue"].round(2)
        cross = cross.sort_values("total_revenue", ascending=False).head(20)

        return cross.to_dict(orient="records")
