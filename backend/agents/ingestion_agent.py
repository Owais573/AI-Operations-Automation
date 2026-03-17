"""
Ingestion Agent -- Loads and validates raw data files.

Responsibilities:
- Load CSV/Excel files from disk or URL
- Validate schema (expected columns present)
- Extract metadata (row count, date range, column types)
- Detect file format issues before downstream agents process data
- Smart multi-sheet Excel handling: automatically select the most
  relevant worksheet based on report type keyword matching.
"""

import os
from typing import Optional

import pandas as pd

from backend.agents.base_agent import BaseAgent
from backend.database.db import DatabaseClient


# ── Keyword map: report_type → column signals ──────────────────────────────
# Each keyword is checked as a SUBSTRING of a lowercased column name.
# More specific keywords listed first (higher signal value).
SHEET_KEYWORD_MAP: dict[str, list[str]] = {
    "sales_report": [
        "revenue", "units_sold", "sales_rep", "margin", "discount",
        "sales", "product", "region", "cost",
    ],
    "inventory_report": [
        "stock_level", "reorder_point", "sku", "warehouse",
        "inventory", "stock", "quantity", "location",
    ],
    "financial_report": [
        "payroll", "cogs", "expense", "income", "budget",
        "amount", "department", "category", "financial",
    ],
}


class IngestionAgent(BaseAgent):
    """
    Agent that ingests raw data files and performs initial validation.

    Input:
        file_path: str -- Path to the CSV/Excel file to ingest
        workflow_type: str -- Report type (used for smart sheet selection)
        expected_columns: list[str] (optional) -- Columns that must be present

    Output:
        records: list[dict] -- Parsed data as list of row dictionaries
        metadata: dict -- File statistics, schema info, and sheet selection details
        validation: dict -- Validation results (warnings/errors)
    """

    def __init__(self, db: DatabaseClient):
        super().__init__(name="ingestion_agent", db=db)

    # ── Private: Smart Sheet Selector ─────────────────────────────────────
    def _select_best_sheet(
        self, excel_file: pd.ExcelFile, workflow_type: str
    ) -> tuple[str, int, str, Optional[str]]:
        """
        Score each worksheet against the keyword map for the given report type.

        Returns:
            (sheet_name, score, selection_method, warning_message | None)
        """
        sheet_names = excel_file.sheet_names

        # Single-sheet file — skip scoring entirely
        if len(sheet_names) == 1:
            return sheet_names[0], -1, "single_sheet", None

        keywords = SHEET_KEYWORD_MAP.get(workflow_type, [])
        best_sheet = sheet_names[0]  # default fallback
        best_score = 0

        for sheet in sheet_names:
            # Parse columns ONLY (nrows=0) — fast, no data loaded
            try:
                cols = excel_file.parse(sheet, nrows=0).columns.tolist()
            except Exception:
                self.logger.warning(f"Could not read columns from sheet: {sheet}")
                continue

            cols_lower = " ".join(str(c).lower() for c in cols)
            score = sum(1 for kw in keywords if kw in cols_lower)

            self.logger.info(
                f"Sheet '{sheet}' — columns: {cols} — keyword score: {score}"
            )

            if score > best_score:
                best_score = score
                best_sheet = sheet

        if best_score >= 1:
            return best_sheet, best_score, "keyword_match", None

        # Fallback — no sheet matched
        warning = (
            f"⚠️ No sheets in this file appear to match the selected report type "
            f"({workflow_type.replace('_', ' ').title()}). "
            f"Loaded first sheet '{best_sheet}'. Results may be unexpected."
        )
        self.logger.warning(warning)
        return best_sheet, 0, "fallback_first_sheet", warning

    # ── Main run ──────────────────────────────────────────────────────────
    async def run(self, input_data: dict) -> dict:
        file_path: str = input_data["file_path"]
        workflow_type: str = input_data.get("workflow_type", "sales_report")
        expected_columns: list[str] = input_data.get("expected_columns", [])

        self.logger.info(f"Loading file: {file_path}  (report type: {workflow_type})")

        # ── 1. Validate file exists ──
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Data file not found: {file_path}")

        # ── 2. Load data based on file extension ──
        ext = os.path.splitext(file_path)[1].lower()
        sheet_meta: dict = {}

        if ext == ".csv":
            df = pd.read_csv(file_path)
            sheet_meta = {
                "available_sheets": None,
                "sheet_name": None,
                "sheet_score": None,
                "sheet_selection_method": "csv_file",
                "sheet_warning": None,
            }

        elif ext in (".xlsx", ".xls"):
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names

            selected_sheet, score, method, warning = self._select_best_sheet(
                excel_file, workflow_type
            )

            self.logger.info(
                f"Selected sheet: '{selected_sheet}'  "
                f"(method={method}, score={score})"
            )

            df = excel_file.parse(selected_sheet)

            sheet_meta = {
                "available_sheets": sheet_names,
                "sheet_name": selected_sheet,
                "sheet_score": score,
                "sheet_selection_method": method,
                "sheet_warning": warning,
            }
        else:
            raise ValueError(f"Unsupported file format: {ext}. Use .csv, .xlsx or .xls")

        self.logger.info(f"Loaded {len(df)} rows x {len(df.columns)} columns")

        # ── 3. Schema validation ──
        warnings: list[str] = []
        errors: list[str] = []

        # Surface sheet warning into pipeline validation warnings
        if sheet_meta.get("sheet_warning"):
            warnings.append(sheet_meta["sheet_warning"])

        if expected_columns:
            missing = set(expected_columns) - set(df.columns)
            extra = set(df.columns) - set(expected_columns)
            if missing:
                errors.append(f"Missing expected columns: {sorted(missing)}")
            if extra:
                warnings.append(f"Extra columns found (will be kept): {sorted(extra)}")

        # ── 4. Data quality quick scan ──
        null_counts = df.isnull().sum()
        columns_with_nulls = {col: int(count) for col, count in null_counts.items() if count > 0}
        if columns_with_nulls:
            warnings.append(f"Columns with missing values: {columns_with_nulls}")

        duplicate_count = int(df.duplicated().sum())
        if duplicate_count > 0:
            warnings.append(f"Found {duplicate_count} duplicate rows")

        # ── 5. Extract metadata ──
        date_columns = [col for col in df.columns if "date" in col.lower()]
        date_range = {}
        for col in date_columns:
            try:
                dates = pd.to_datetime(df[col], errors="coerce")
                date_range[col] = {
                    "min": str(dates.min()),
                    "max": str(dates.max()),
                }
            except Exception:
                pass

        column_info = {}
        for col in df.columns:
            column_info[col] = {
                "dtype": str(df[col].dtype),
                "non_null_count": int(df[col].count()),
                "null_count": int(df[col].isnull().sum()),
                "unique_count": int(df[col].nunique()),
            }

        metadata = {
            "file_name": os.path.basename(file_path),
            "file_size_bytes": os.path.getsize(file_path),
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "column_info": column_info,
            "date_range": date_range,
            "duplicate_count": duplicate_count,
            **sheet_meta,  # merge sheet selection details
        }

        validation = {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

        self.logger.info(
            f"Validation: valid={validation['is_valid']} | "
            f"warnings={len(warnings)} | errors={len(errors)}"
        )

        # ── 6. Convert DataFrame to list of dicts for pipeline ──
        # Replace NaN with None for JSON serialization
        records = df.astype(object).where(pd.notnull(df), None).to_dict(orient="records")

        return {
            "records": records,
            "metadata": metadata,
            "validation": validation,
        }
