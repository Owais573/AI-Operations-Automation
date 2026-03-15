"""
Ingestion Agent -- Loads and validates raw data files.

Responsibilities:
- Load CSV/Excel files from disk or URL
- Validate schema (expected columns present)
- Extract metadata (row count, date range, column types)
- Detect file format issues before downstream agents process data
"""

import os

import pandas as pd

from backend.agents.base_agent import BaseAgent
from backend.database.db import DatabaseClient


class IngestionAgent(BaseAgent):
    """
    Agent that ingests raw data files and performs initial validation.

    Input:
        file_path: str -- Path to the CSV/Excel file to ingest
        expected_columns: list[str] (optional) -- Columns that must be present

    Output:
        records: list[dict] -- Parsed data as list of row dictionaries
        metadata: dict -- File statistics and schema info
        validation: dict -- Validation results (warnings/errors)
    """

    def __init__(self, db: DatabaseClient):
        super().__init__(name="ingestion_agent", db=db)

    async def run(self, input_data: dict) -> dict:
        file_path: str = input_data["file_path"]
        expected_columns: list[str] = input_data.get("expected_columns", [])

        self.logger.info(f"Loading file: {file_path}")

        # ── 1. Validate file exists ──
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Data file not found: {file_path}")

        # ── 2. Load data based on file extension ──
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".csv":
            df = pd.read_csv(file_path)
        elif ext in (".xlsx", ".xls"):
            df = pd.read_excel(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}. Use .csv or .xlsx")

        self.logger.info(f"Loaded {len(df)} rows x {len(df.columns)} columns")

        # ── 3. Schema validation ──
        warnings: list[str] = []
        errors: list[str] = []

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
        # Note: We cast to object type first to ensure None is preserved and not converted back to nan
        records = df.astype(object).where(pd.notnull(df), None).to_dict(orient="records")

        return {
            "records": records,
            "metadata": metadata,
            "validation": validation,
        }
