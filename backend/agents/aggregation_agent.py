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
    Supports multiple report types with dynamic dimension/measure mapping.
    """

    # ── Report Configurations ──
    REPORT_CONFIGS = {
        "sales_report": {
            "dimensions": ["product", "region"],
            "measures": ["revenue", "cost", "units_sold"],
            "kpis": ["total_revenue", "total_cost", "total_units_sold"],
            "primary_dim": "product",
            "secondary_dim": "region",
        },
        "inventory_report": {
            "dimensions": ["product_name", "warehouse"],
            "measures": ["stock_level", "reorder_point"],
            "kpis": ["avg_stock_level", "low_stock_items"],
            "primary_dim": "product_name",
            "secondary_dim": "warehouse",
        },
        "financial_report": {
            "dimensions": ["category", "department"],
            "measures": ["amount"],
            "kpis": ["total_amount", "expense_ratio"],
            "primary_dim": "category",
            "secondary_dim": "department",
        }
    }

    def __init__(self, db: DatabaseClient):
        super().__init__(name="aggregation_agent", db=db)

    async def run(self, input_data: dict) -> dict:
        records: list[dict] = input_data["records"]
        report_type: str = input_data.get("report_type", "sales_report")
        time_period: str = input_data.get("time_period", "monthly")

        # Fallback for unknown report types
        config = self.REPORT_CONFIGS.get(report_type, self.REPORT_CONFIGS["sales_report"])
        
        df = pd.DataFrame(records)
        self.logger.info(f"Aggregating {len(df)} rows | type={report_type} | period={time_period}")

        if df.empty:
            return self._empty_result()

        # ── 0. Ensure numeric types for measures ──
        for col in config["measures"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")

        # ── 1. Overall KPIs ──
        overall_metrics = self._compute_overall_metrics(df, report_type, config)

        # ── 2. Primary dimension summary ──
        product_summary = self._aggregate_by_dimension(df, config["primary_dim"], config)

        # ── 3. Secondary dimension summary ──
        region_summary = self._aggregate_by_dimension(df, config["secondary_dim"], config)

        # ── 4. Time series ──
        time_series = self._aggregate_by_time(df, time_period, config)

        # ── 5. Top performers ──
        top_performers = self._get_top_performers(df, config)

        # ── 6. Cross-dimensional summary ──
        cross_summary = self._aggregate_cross_dimensions(df, config["primary_dim"], config["secondary_dim"], config)

        self.logger.info(
            f"Aggregation complete | {config['primary_dim']}s={len(product_summary)} | "
            f"{config['secondary_dim']}s={len(region_summary)} | time_periods={len(time_series)}"
        )

        return {
            "report_type": report_type,
            "overall_metrics": overall_metrics,
            "product_summary": product_summary,  # Keeping name for compatibility or aliasing internally
            "region_summary": region_summary,
            "time_series": time_series,
            "top_performers": top_performers,
            "cross_summary": cross_summary,
        }

    def _empty_result(self) -> dict:
        return {
            "overall_metrics": {},
            "product_summary": [],
            "region_summary": [],
            "time_series": [],
            "top_performers": {},
            "cross_summary": [],
        }

    def _compute_overall_metrics(self, df: pd.DataFrame, report_type: str, config: dict) -> dict:
        """Calculate high-level KPIs based on report type."""
        metrics = {
            "total_transactions": len(df),
            "report_type": report_type
        }

        if report_type == "sales_report":
            rev = float(df["revenue"].sum()) if "revenue" in df.columns else 0
            cost = float(df["cost"].sum()) if "cost" in df.columns else 0
            units = float(df["units_sold"].sum()) if "units_sold" in df.columns else 0
            profit = rev - cost
            metrics.update({
                "total_revenue": round(rev, 2),
                "total_cost": round(cost, 2),
                "gross_profit": round(profit, 2),
                "gross_margin_pct": round((profit / rev * 100) if rev > 0 else 0, 2),
                "total_units_sold": int(units)
            })
        elif report_type == "inventory_report":
            avg_stock = float(df["stock_level"].mean()) if "stock_level" in df.columns else 0
            low_stock = int((df["stock_level"] < df["reorder_point"]).sum()) if "stock_level" in df.columns and "reorder_point" in df.columns else 0
            metrics.update({
                "avg_stock_level": round(avg_stock, 1),
                "low_stock_items": low_stock,
                "out_of_stock_items": int((df["stock_level"] == 0).sum()) if "stock_level" in df.columns else 0
            })
        elif report_type == "financial_report":
            total_amt = float(df["amount"].sum()) if "amount" in df.columns else 0
            metrics.update({
                "total_amount": round(total_amt, 2),
                "avg_transaction_size": round(total_amt / len(df), 2) if len(df) > 0 else 0
            })

        if "date" in df.columns:
            valid_dates = df["date"].dropna()
            if not valid_dates.empty:
                metrics["date_range_start"] = str(valid_dates.min().date())
                metrics["date_range_end"] = str(valid_dates.max().date())

        return metrics

    def _aggregate_by_dimension(self, df: pd.DataFrame, dimension: str, config: dict) -> list[dict]:
        """Aggregate metrics by a single dimension."""
        if dimension not in df.columns:
            return []

        # Find the main measure to aggregate
        main_measure = config["measures"][0]
        
        agg_map = {main_measure: ["sum", "mean", "count"]}
        # If there are multiple measures, sum them all
        for m in config["measures"][1:]:
            agg_map[m] = ["sum"]

        agg_df = df.groupby(dimension, dropna=False).agg(agg_map).reset_index()
        
        # Flatten multi-index columns if they exist
        if isinstance(agg_df.columns, pd.MultiIndex):
            agg_df.columns = [
                f"{col}_{stat}" if stat else col 
                for col, stat in agg_df.columns
            ]

        # Rename for simplicity and clean up internal naming
        primary_col = f"{main_measure}_sum"
        if primary_col in agg_df.columns:
            agg_df = agg_df.sort_values(primary_col, ascending=False)

        # Round all numeric columns
        numeric_cols = agg_df.select_dtypes(include=['number']).columns
        agg_df[numeric_cols] = agg_df[numeric_cols].round(2)

        # Keep top 50 to prevent context overflow
        return agg_df.head(50).to_dict(orient="records")

    def _aggregate_by_time(self, df: pd.DataFrame, period: str, config: dict) -> list[dict]:
        """Aggregate metrics by time period."""
        if "date" not in df.columns:
            return []

        df_time = df.dropna(subset=["date"]).copy()
        if df_time.empty:
            return []

        freq_map = {"daily": "D", "weekly": "W", "monthly": "MS"}
        freq = freq_map.get(period, "MS")
        df_time["period"] = df_time["date"].dt.to_period(
            {"D": "D", "W": "W", "MS": "M"}.get(freq, "M")
        ).astype(str)

        main_measure = config["measures"][0]
        agg_df = df_time.groupby("period").agg({
            main_measure: "sum",
            "date": "count"
        }).rename(columns={main_measure: f"total_{main_measure}", "date": "transaction_count"}).reset_index()

        # Growth calculation
        val_col = f"total_{main_measure}"
        agg_df["growth_pct"] = agg_df[val_col].pct_change().fillna(0) * 100
        
        agg_df = agg_df.round(2)
        return agg_df.to_dict(orient="records")

    def _get_top_performers(self, df: pd.DataFrame, config: dict) -> dict:
        """Identify top performers in the relative dimensions."""
        result = {}
        measure = config["measures"][0]
        
        for dim in config["dimensions"]:
            if dim in df.columns:
                top = df.groupby(dim)[measure].sum().sort_values(ascending=False).head(5)
                result[f"top_{dim}_by_{measure}"] = [
                    {dim: name, measure: round(float(val), 2)}
                    for name, val in top.items()
                ]
        return result

    def _aggregate_cross_dimensions(self, df: pd.DataFrame, dim1: str, dim2: str, config: dict) -> list[dict]:
        """Cross-tabulate two dimensions."""
        if dim1 not in df.columns or dim2 not in df.columns:
            return []

        measure = config["measures"][0]
        cross = df.groupby([dim1, dim2]).agg({
            measure: "sum"
        }).reset_index()

        cross[measure] = cross[measure].round(2)
        return cross.sort_values(measure, ascending=False).head(20).to_dict(orient="records")

