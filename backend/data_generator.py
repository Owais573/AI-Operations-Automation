"""
Mock ERP Data Generator.

Generates realistic sales, inventory, and financial datasets
using Faker with intentional anomalies for AI detection testing.
"""

import csv
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)

# ── Constants ─────────────────────────────────────────────────

PRODUCTS = [
    {"name": "Laptop Pro 15", "base_price": 1199, "base_cost": 745},
    {"name": '27" Monitor', "base_price": 499, "base_cost": 290},
    {"name": "Wireless Keyboard", "base_price": 59.90, "base_cost": 29},
    {"name": "USB-C Hub", "base_price": 79.90, "base_cost": 35},
    {"name": "Ergonomic Mouse", "base_price": 69.90, "base_cost": 32},
    {"name": "Webcam HD", "base_price": 129, "base_cost": 58},
    {"name": "Noise-Cancel Headset", "base_price": 249, "base_cost": 115},
    {"name": "Desk Lamp LED", "base_price": 44.90, "base_cost": 18},
]

REGIONS = ["North America", "Europe", "Asia Pacific", "Latin America"]
SALES_REPS = [fake.name() for _ in range(12)]

WAREHOUSES = ["WH-East", "WH-West", "WH-Central", "WH-Europe"]
FINANCIAL_CATEGORIES = ["Revenue", "COGS", "Marketing", "Payroll", "Operations", "R&D"]
DEPARTMENTS = ["Sales", "Marketing", "Engineering", "Operations", "Finance"]


# ── Sales Data ────────────────────────────────────────────────

def generate_sales_data(
    output_path: str,
    start_date: str = "2025-10-01",
    end_date: str = "2026-02-28",
    rows: int = 600,
) -> str:
    """
    Generate mock sales transaction data.

    Features:
    - Realistic price variation (±10%)
    - Regional demand differences
    - Weekend dips in volume
    - Intentional anomalies: duplicates, missing values, a revenue spike
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    date_range = (end - start).days

    records = []
    for i in range(rows):
        day_offset = random.randint(0, date_range)
        date = start + timedelta(days=day_offset)
        product = random.choice(PRODUCTS)
        region = random.choice(REGIONS)
        sales_rep = random.choice(SALES_REPS)

        # Weekend dip
        weekend_factor = 0.4 if date.weekday() >= 5 else 1.0

        # Regional demand factor
        region_factors = {
            "North America": 1.2,
            "Europe": 1.0,
            "Asia Pacific": 0.8,
            "Latin America": 0.6,
        }
        demand = region_factors.get(region, 1.0) * weekend_factor

        units = max(1, int(random.gauss(50, 20) * demand))
        price_variation = random.uniform(0.90, 1.10)
        unit_price = round(product["base_price"] * price_variation, 2)
        unit_cost = round(product["base_cost"] * price_variation, 2)
        revenue = round(units * unit_price, 2)
        cost = round(units * unit_cost, 2)

        record = {
            "date": date.strftime("%Y-%m-%d"),
            "product": product["name"],
            "region": region,
            "sales_rep": sales_rep,
            "units_sold": units,
            "unit_price": unit_price,
            "revenue": revenue,
            "cost": cost,
        }
        records.append(record)

    # ── Inject anomalies ──
    # 1. Duplicate rows (5 random duplicates)
    for _ in range(5):
        records.append(random.choice(records).copy())

    # 2. Missing values (set 8 random fields to empty)
    for _ in range(8):
        idx = random.randint(0, len(records) - 1)
        field = random.choice(["units_sold", "revenue", "cost", "region"])
        records[idx][field] = ""

    # 3. Revenue spike anomaly (one day with 5× normal volume)
    spike_date = (start + timedelta(days=random.randint(30, date_range - 30))).strftime("%Y-%m-%d")
    for _ in range(15):
        product = PRODUCTS[0]  # Laptop spike
        records.append({
            "date": spike_date,
            "product": product["name"],
            "region": "North America",
            "sales_rep": random.choice(SALES_REPS),
            "units_sold": random.randint(200, 400),
            "unit_price": product["base_price"],
            "revenue": round(random.randint(200, 400) * product["base_price"], 2),
            "cost": round(random.randint(200, 400) * product["base_cost"], 2),
        })

    # Shuffle records
    random.shuffle(records)

    # Write CSV
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)

    print(f"[OK] Generated {len(records)} sales records -> {output_path}")
    return output_path


# ── Inventory Data ────────────────────────────────────────────

def generate_inventory_data(
    output_path: str,
    start_date: str = "2025-10-01",
    end_date: str = "2026-02-28",
    rows: int = 350,
) -> str:
    """
    Generate mock inventory level snapshots.

    Features:
    - Realistic stock depletion patterns
    - Reorder point thresholds
    - Some items below reorder point (for AI to flag)
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    date_range = (end - start).days

    records = []
    sku_counter = 1000

    for product in PRODUCTS:
        sku = f"SKU-{sku_counter}"
        sku_counter += 1
        reorder_point = random.randint(20, 60)

        for _ in range(rows // len(PRODUCTS)):
            day_offset = random.randint(0, date_range)
            date = start + timedelta(days=day_offset)
            warehouse = random.choice(WAREHOUSES)

            # Stock level with depletion trend
            base_stock = random.randint(10, 200)
            # Some items critically low
            if random.random() < 0.15:
                base_stock = random.randint(2, reorder_point - 5)

            records.append({
                "date": date.strftime("%Y-%m-%d"),
                "sku": sku,
                "product_name": product["name"],
                "warehouse": warehouse,
                "stock_level": base_stock,
                "reorder_point": reorder_point,
            })

    random.shuffle(records)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)

    print(f"[OK] Generated {len(records)} inventory records -> {output_path}")
    return output_path


# ── Financial Data ────────────────────────────────────────────

def generate_financial_data(
    output_path: str,
    start_date: str = "2025-10-01",
    end_date: str = "2026-02-28",
    rows: int = 250,
) -> str:
    """
    Generate mock financial metric data.

    Features:
    - Monthly aggregated financial entries
    - Category-based amounts with realistic ranges
    - Department attribution
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    date_range = (end - start).days

    category_ranges = {
        "Revenue": (50000, 200000),
        "COGS": (20000, 80000),
        "Marketing": (5000, 30000),
        "Payroll": (30000, 100000),
        "Operations": (10000, 40000),
        "R&D": (15000, 60000),
    }

    records = []
    for _ in range(rows):
        day_offset = random.randint(0, date_range)
        date = start + timedelta(days=day_offset)
        category = random.choice(FINANCIAL_CATEGORIES)
        lo, hi = category_ranges[category]
        amount = round(random.uniform(lo, hi), 2)
        entry_type = "income" if category == "Revenue" else "expense"
        department = random.choice(DEPARTMENTS)

        records.append({
            "date": date.strftime("%Y-%m-%d"),
            "category": category,
            "amount": amount,
            "type": entry_type,
            "department": department,
        })

    random.shuffle(records)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)

    print(f"[OK] Generated {len(records)} financial records -> {output_path}")
    return output_path


# ── Main ──────────────────────────────────────────────────────

def generate_all(data_dir: str = "data"):
    """Generate all mock datasets."""
    print("=" * 50)
    print("  Generating Mock ERP Datasets")
    print("=" * 50)

    generate_sales_data(os.path.join(data_dir, "mock_sales_data.csv"))
    generate_inventory_data(os.path.join(data_dir, "mock_inventory_data.csv"))
    generate_financial_data(os.path.join(data_dir, "mock_financial_data.csv"))

    print("=" * 50)
    print("  All datasets generated successfully!")
    print("=" * 50)


if __name__ == "__main__":
    # Run from project root: uv run python -m backend.data_generator
    project_root = Path(__file__).parent.parent
    generate_all(str(project_root / "data"))
