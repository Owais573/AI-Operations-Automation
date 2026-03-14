# AI Operations Automation MVP

**Agentic Workflow System for Business Reporting Automation**

An AI-powered operational automation platform that converts manual ERP reporting workflows into autonomous AI agent pipelines with human-in-the-loop approval checkpoints.

---

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [MVP Scope](#2-mvp-scope)
3. [System Architecture](#3-system-architecture)
4. [Tech Stack](#4-tech-stack)
5. [Project Structure](#5-project-structure)
6. [Database Schema](#6-database-schema)
7. [Mock Data Strategy](#7-mock-data-strategy)
8. [Agent Design](#8-agent-design)
9. [LangGraph Orchestration](#9-langgraph-orchestration)
10. [Human-in-the-Loop Approval](#10-human-in-the-loop-approval)
11. [API Endpoints](#11-api-endpoints)
12. [Delivery Integrations](#12-delivery-integrations)
13. [Scheduling Automation](#13-scheduling-automation)
14. [Dashboard](#14-dashboard)
15. [Implementation Phases](#15-implementation-phases)
16. [Deliverables](#16-deliverables)
17. [Future Roadmap](#17-future-roadmap)

---

## 1. Problem Statement

Enterprise companies routinely perform these **manual operational workflows**:

- Pull operational data from ERP systems and spreadsheets
- Clean and structure the raw data
- Generate business reports (inventory, sales, financial metrics)
- Perform analysis and summarize insights
- Deliver reports to leadership

These workflows are repetitive, error-prone, and consume significant employee time.

**This system automates the entire pipeline using AI agents** — from data ingestion to report delivery — while maintaining appropriate human approval checkpoints.

---

## 2. MVP Scope

The MVP focuses on automating the **Sales Reporting Pipeline** end-to-end:

```
CSV / Mock ERP Data
        ↓
┌─────────────────────────┐
│   Ingestion Agent       │  → Load & validate raw data
├─────────────────────────┤
│   Cleaning Agent (LLM)  │  → Inspect data quality, clean intelligently
├─────────────────────────┤
│   Aggregation Agent     │  → Group, summarize, calculate metrics
├─────────────────────────┤
│   Aggregation Agent     │  → Dynamic grouping based on report type
├─────────────────────────┤
│   Analysis Agent (LLM)  │  → Generalized insights across domains
├─────────────────────────┤
│   ▸ Human Approval Gate │  → Pause for human review before final report
├─────────────────────────┤
│   Report Agent          │  → Context-aware Markdown + PDF report
├─────────────────────────┤
│   Delivery Agent        │  → Multi-channel dispatch (Slack/Email)
└─────────────────────────┘
```

**Key MVP differentiators:**
- **Dynamic Report Support**: Single pipeline handles diverse business operational data.
- **LLM-powered reasoning**: Agents adapt to data schemas without hardcoding.
- **Human-in-the-loop**: Integrated approval checkpoints.
- **Full Observability**: Detailed agent execution logs and duration tracking.

---

## 3. System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js)                         │
│  Dashboard │ Run History │ Report Viewer │ Approval Queue     │
└────────────────────────┬─────────────────────────────────────┘
                         │ REST API / WebSocket
┌────────────────────────▼─────────────────────────────────────┐
│                  BACKEND (FastAPI + Python)                    │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐   │
│  │            LangGraph Orchestration Engine              │   │
│  │                                                        │   │
│  │  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │   │
│  │  │ Ingest  │→ │  Clean   │→ │Aggregate │→ │Analyze │ │   │
│  │  │ Agent   │  │  Agent   │  │  Agent   │  │ Agent  │ │   │
│  │  └─────────┘  └──────────┘  └──────────┘  └────┬───┘ │   │
│  │                                                  │      │   │
│  │                              ┌───────────────────▼────┐ │   │
│  │                              │ Human Approval Gate    │ │   │
│  │                              └───────────┬────────────┘ │   │
│  │                                          │              │   │
│  │                              ┌───────────▼────────────┐ │   │
│  │                              │ Report Generation Agent│ │   │
│  │                              └───────────┬────────────┘ │   │
│  │                                          │              │   │
│  │                              ┌───────────▼────────────┐ │   │
│  │                              │  Delivery Agent        │ │   │
│  │                              └────────────────────────┘ │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                               │
│  Scheduling (APScheduler) │ State Store │ Error Handler       │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│                DATABASE (Supabase / PostgreSQL)                │
│  workflow_runs │ agent_logs │ reports │ approvals │ configs   │
└──────────────────────────────────────────────────────────────┘
```

---

## 4. Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Backend** | Python 3.12 + FastAPI | Async-native, ideal for AI workloads |
| **Agent Framework** | LangGraph + LangChain | State machine orchestration with human-in-the-loop support |
| **LLM** | OpenAI GPT-4o-mini | Cost-effective for data analysis tasks |
| **Data Processing** | Pandas | Industry standard for tabular data manipulation |
| **Database** | Supabase (PostgreSQL) | Auth, Realtime subscriptions, Storage built-in |
| **Frontend** | Next.js + Tailwind CSS + ShadCN UI + Recharts | Modern React dashboard with charts |
| **Delivery — Slack** | Slack Incoming Webhooks | Report delivery to team channels |
| **Delivery — Email** | Python `smtplib` + `email` (built-in) | Free, zero-dependency email via Gmail/Outlook SMTP |
| **Scheduling** | APScheduler (in-process) | Simple periodic job scheduling for MVP |
| **Report Format** | Markdown → PDF (xhtml2pdf) | Professional, downloadable report output |

---

## 5. Project Structure

```
ai-operations-automation/
│
├── backend/
│   ├── main.py                          # FastAPI application entry point
│   ├── config.py                        # Environment configuration (Pydantic Settings)
│   ├── requirements.txt
│   │
│   ├── agents/                          # LLM-powered agents
│   │   ├── __init__.py
│   │   ├── base_agent.py               # Base class: logging, error handling, retries
│   │   ├── ingestion_agent.py           # CSV/Excel loader with schema validation
│   │   ├── cleaning_agent.py            # LLM-guided data quality & cleaning
│   │   ├── aggregation_agent.py         # Dynamic grouping & metric calculation
│   │   ├── analysis_agent.py            # AI-powered trend detection & insights
│   │   ├── report_agent.py              # Markdown + PDF report generation
│   │   └── delivery_agent.py            # Slack & Email dispatch
│   │
│   ├── orchestration/                   # LangGraph workflow engine
│   │   ├── __init__.py
│   │   ├── workflow_graph.py            # Main state machine definition
│   │   ├── state.py                     # WorkflowState TypedDict schema
│   │   └── nodes.py                     # Graph node wrapper functions
│   │
│   ├── services/                        # External service integrations
│   │   ├── __init__.py
│   │   ├── slack_service.py             # Slack webhook sender
│   │   ├── email_service.py             # SMTP email sender
│   │   └── storage_service.py           # Supabase Storage for PDF reports
│   │
│   ├── api/                             # FastAPI route handlers
│   │   ├── __init__.py
│   │   ├── workflows.py                 # Trigger & manage workflow runs
│   │   ├── reports.py                   # View & download generated reports
│   │   ├── approvals.py                 # Human approval endpoints
│   │   └── dashboard.py                 # Dashboard stats & activity feed
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py                    # Database models
│   │   └── migrations/                  # Schema migration files
│   │
│   ├── scheduler/
│   │   ├── __init__.py
│   │   └── jobs.py                      # APScheduler periodic job definitions
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logger.py                    # Structured logging setup
│       └── error_handler.py             # Global error handling middleware
│
├── frontend/                            # Next.js dashboard application
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx                 # Dashboard home
│   │   │   ├── runs/page.tsx            # Workflow run history
│   │   │   ├── reports/page.tsx         # Report viewer & downloader
│   │   │   ├── approvals/page.tsx       # Approval queue
│   │   ├── components/
│   │   │   ├── ui/                      # ShadCN UI components
│   │   │   ├── dashboard/              # Dashboard-specific components
│   │   │   └── workflow/               # Workflow visualization components
│   │   └── lib/
│   │       ├── api.ts                   # API client helper
│   │       └── types.ts                 # Shared TypeScript types
│   └── package.json
│
├── data/                                # Mock datasets
│   ├── mock_sales_data.csv
│   ├── mock_inventory_data.csv
│   └── mock_financial_data.csv
│
├── docs/                                # Project documentation
│   ├── architecture.md                  # System architecture deep-dive
│   ├── workflow-analysis.md             # Original manual workflow documentation
│   └── agent-design.md                  # Agent design decisions & rationale
│
├── .env.example                         # Environment variable template
├── docker-compose.yml                   # Local development environment
└── README.md                            # Setup & usage instructions
```

---

## 6. Database Schema

### `workflow_runs` — Tracks each pipeline execution

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Unique run identifier |
| `workflow_type` | TEXT | Type of workflow (`sales_report`, `inventory_report`) |
| `status` | TEXT | `pending` → `running` → `awaiting_approval` → `completed` / `failed` |
| `input_config` | JSONB | Input parameters for this run |
| `started_at` | TIMESTAMPTZ | When execution began |
| `completed_at` | TIMESTAMPTZ | When execution finished |
| `error_message` | TEXT | Error details if failed |
| `created_at` | TIMESTAMPTZ | Record creation timestamp |

### `agent_logs` — Logs for each agent within a run

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Unique log identifier |
| `run_id` | UUID (FK → workflow_runs) | Parent workflow run |
| `agent_name` | TEXT | Agent identifier (`cleaning_agent`, `analysis_agent`, etc.) |
| `status` | TEXT | `started` / `completed` / `failed` |
| `input_summary` | JSONB | Summary of agent input data |
| `output_summary` | JSONB | Summary of agent output data |
| `duration_ms` | INTEGER | Execution time in milliseconds |
| `tokens_used` | INTEGER | LLM tokens consumed |
| `error_message` | TEXT | Error details if agent failed |
| `created_at` | TIMESTAMPTZ | Record creation timestamp |

### `reports` — Generated business reports

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Unique report identifier |
| `run_id` | UUID (FK → workflow_runs) | Parent workflow run |
| `title` | TEXT | Report title |
| `content_markdown` | TEXT | Full report in Markdown |
| `content_pdf_url` | TEXT | Supabase Storage URL for PDF |
| `insights` | JSONB | Structured insights data |
| `created_at` | TIMESTAMPTZ | Record creation timestamp |

### `approvals` — Human approval checkpoints

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Unique approval identifier |
| `run_id` | UUID (FK → workflow_runs) | Parent workflow run |
| `checkpoint_name` | TEXT | Checkpoint identifier (`pre_report_review`) |
| `status` | TEXT | `pending` / `approved` / `rejected` |
| `data_snapshot` | JSONB | Data at checkpoint for human review |
| `reviewer_notes` | TEXT | Human reviewer's notes |
| `decided_at` | TIMESTAMPTZ | When decision was made |
| `created_at` | TIMESTAMPTZ | Record creation timestamp |

### SQL Migration

```sql
-- Workflow run tracking
CREATE TABLE workflow_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    input_config JSONB,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Individual agent execution logs
CREATE TABLE agent_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES workflow_runs(id) ON DELETE CASCADE,
    agent_name TEXT NOT NULL,
    status TEXT NOT NULL,
    input_summary JSONB,
    output_summary JSONB,
    duration_ms INTEGER,
    tokens_used INTEGER,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Generated reports
CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES workflow_runs(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    content_markdown TEXT,
    content_pdf_url TEXT,
    insights JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Human approval checkpoints
CREATE TABLE approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES workflow_runs(id) ON DELETE CASCADE,
    checkpoint_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    data_snapshot JSONB,
    reviewer_notes TEXT,
    decided_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX idx_workflow_runs_status ON workflow_runs(status);
CREATE INDEX idx_agent_logs_run_id ON agent_logs(run_id);
CREATE INDEX idx_reports_run_id ON reports(run_id);
CREATE INDEX idx_approvals_status ON approvals(status);
```

---

## 7. Mock Data Strategy

Since real ERP systems are unavailable, we generate realistic mock datasets using Python's `Faker` library with custom business logic.

### Datasets

| File | Content | Columns | Rows |
|------|---------|---------|------|
| `mock_sales_data.csv` | Sales transactions | `date`, `product`, `region`, `units_sold`, `revenue`, `cost`, `sales_rep` | 500+ |
| `mock_inventory_data.csv` | Inventory levels | `date`, `sku`, `product_name`, `warehouse`, `stock_level`, `reorder_point` | 300+ |
| `mock_financial_data.csv` | Financial metrics | `date`, `category`, `amount`, `type`, `department` | 200+ |

### Sample: `mock_sales_data.csv`

| date | product | region | units_sold | revenue | cost |
|------|---------|--------|-----------|---------|------|
| 2026-01-01 | Laptop Pro 15 | North America | 120 | 143,880 | 89,400 |
| 2026-01-01 | 27" Monitor | North America | 80 | 39,920 | 23,200 |
| 2026-01-02 | Laptop Pro 15 | Europe | 95 | 113,810 | 70,775 |
| 2026-01-02 | Wireless Keyboard | Asia Pacific | 200 | 11,980 | 5,800 |
| 2026-01-03 | Laptop Pro 15 | North America | 45 | 53,955 | 33,525 |

Mock data will include **intentional anomalies** (e.g., sudden revenue spikes, missing values, duplicate rows) for the AI to detect and handle.

---

## 8. Agent Design

All agents follow a **Base Agent** pattern providing:
- **LLM reasoning** — uses GPT-4o-mini to decide *how* to process data
- **Structured output** — returns typed results via Pydantic models
- **Execution logging** — every action is logged to the `agent_logs` table
- **Error recovery** — handles failures gracefully with configurable retries

### 8.1 Base Agent Class

```python
from abc import ABC, abstractmethod
from datetime import datetime
import logging

class BaseAgent(ABC):
    """Base class for all workflow agents."""

    def __init__(self, name: str, db_client):
        self.name = name
        self.db = db_client
        self.logger = logging.getLogger(f"agent.{name}")

    async def execute(self, run_id: str, input_data: dict) -> dict:
        """Execute agent with logging and error handling."""
        start_time = datetime.now()
        log_id = await self._log_start(run_id, input_data)

        try:
            result = await self.run(input_data)
            duration = (datetime.now() - start_time).total_seconds() * 1000
            await self._log_complete(log_id, result, duration)
            return result
        except Exception as e:
            await self._log_failure(log_id, str(e))
            raise

    @abstractmethod
    async def run(self, input_data: dict) -> dict:
        """Override in each agent subclass."""
        pass

    async def _log_start(self, run_id, input_data):
        # Insert agent_logs record with status='started'
        ...

    async def _log_complete(self, log_id, result, duration):
        # Update agent_logs record with status='completed'
        ...

    async def _log_failure(self, log_id, error):
        # Update agent_logs record with status='failed'
        ...
```

### 8.2 Ingestion Agent

**Purpose:** Load and validate raw data files.

| Responsibility | Detail |
|---------------|--------|
| Load files | Supports CSV and Excel formats |
| Schema validation | Checks expected columns exist and have correct data types |
| Metadata extraction | Returns row count, column list, date range |
| Error reporting | Clear errors if file is missing, corrupted, or wrong schema |

```python
class IngestionAgent(BaseAgent):
    async def run(self, input_data: dict) -> dict:
        file_path = input_data["file_path"]
        df = pd.read_csv(file_path)

        # Validate schema
        required_columns = input_data.get("required_columns", [])
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        return {
            "data": df.to_dict(orient="records"),
            "metadata": {
                "rows": len(df),
                "columns": list(df.columns),
                "date_range": [str(df["date"].min()), str(df["date"].max())]
            }
        }
```

### 8.3 Cleaning Agent (LLM-Powered)

**Purpose:** Intelligently inspect and clean data quality issues.

Unlike a simple `df.drop_duplicates()`, this agent uses the LLM to:
1. **Inspect** the data for quality issues (the LLM reviews a sample & statistics)
2. **Generate a cleaning plan** based on what it finds
3. **Execute** the cleaning operations
4. **Report** what was cleaned and why

```python
class CleaningAgent(BaseAgent):
    async def run(self, input_data: dict) -> dict:
        df = pd.DataFrame(input_data["data"])

        # Build data profile for LLM inspection
        profile = {
            "shape": df.shape,
            "dtypes": df.dtypes.to_dict(),
            "null_counts": df.isnull().sum().to_dict(),
            "duplicate_rows": int(df.duplicated().sum()),
            "sample": df.head(5).to_string()
        }

        # LLM generates cleaning plan
        cleaning_plan = await self.llm.invoke(
            f"""Analyze this dataset profile and return a JSON cleaning plan.
            Profile: {profile}

            Return JSON with keys:
            - "drop_duplicates": bool
            - "fill_strategy": dict mapping column -> strategy ("mean", "median", "zero", "forward_fill")
            - "type_fixes": dict mapping column -> target type
            - "issues_found": list of string descriptions
            """
        )

        # Execute cleaning based on LLM plan
        if cleaning_plan["drop_duplicates"]:
            df = df.drop_duplicates()

        for col, strategy in cleaning_plan["fill_strategy"].items():
            if strategy == "mean":
                df[col] = df[col].fillna(df[col].mean())
            elif strategy == "zero":
                df[col] = df[col].fillna(0)
            # ... more strategies

        return {
            "data": df.to_dict(orient="records"),
            "cleaning_report": {
                "issues_found": cleaning_plan["issues_found"],
                "rows_before": len(input_data["data"]),
                "rows_after": len(df),
                "actions_taken": cleaning_plan
            }
        }
```

### 8.4 Aggregation Agent

**Purpose:** Dynamically group and summarize data based on the identified report type (Sales, Inventory, or Financial).

| Report Type | Dimensions | Key Measures |
|-------------|------------|--------------|
| **Sales** | Product, Region, Time | Revenue, Cost, Units Sold, Margin |
| **Inventory** | SKU, Warehouse, Category | Stock Level, Reorder Point, Value |
| **Financial** | Department, Category, Type | Amount, Budget Variance |

```python
class AggregationAgent(BaseAgent):
    async def run(self, input_data: dict) -> dict:
        df = pd.DataFrame(input_data["data"])

        # Product-level aggregation
        by_product = df.groupby("product").agg({
            "units_sold": "sum",
            "revenue": "sum",
            "cost": "sum"
        }).reset_index()
        by_product["profit_margin"] = (
            (by_product["revenue"] - by_product["cost"]) / by_product["revenue"] * 100
        ).round(2)

        # Region-level aggregation
        by_region = df.groupby("region").agg({
            "units_sold": "sum",
            "revenue": "sum"
        }).reset_index()

        # Time-series aggregation (weekly)
        df["date"] = pd.to_datetime(df["date"])
        by_week = df.resample("W", on="date").agg({
            "units_sold": "sum",
            "revenue": "sum"
        }).reset_index()

        return {
            "by_product": by_product.to_dict(orient="records"),
            "by_region": by_region.to_dict(orient="records"),
            "by_week": by_week.to_dict(orient="records"),
            "totals": {
                "total_revenue": float(df["revenue"].sum()),
                "total_units": int(df["units_sold"].sum()),
                "total_cost": float(df["cost"].sum()),
                "overall_margin": round((df["revenue"].sum() - df["cost"].sum()) / df["revenue"].sum() * 100, 2)
            }
        }
```

### 8.5 Analysis Agent (Core LLM Agent)

**Purpose:** The most "agentic" component — uses chain-of-thought reasoning to generate structured business insights.

| Insight Type | Description |
|-------------|-------------|
| **Trends** | Revenue and unit growth patterns |
| **Anomalies** | Unusual spikes, drops, or data patterns |
| **Recommendations** | Actionable business suggestions |
| **Key Metrics** | Highlighted numbers for executive summary |

```python
from pydantic import BaseModel

class AnalysisInsight(BaseModel):
    category: str          # "trend", "anomaly", "recommendation"
    title: str             # Short headline
    description: str       # Detailed explanation
    severity: str          # "info", "warning", "critical"
    metric_value: str      # Relevant number

class AnalysisResult(BaseModel):
    executive_summary: str
    insights: list[AnalysisInsight]
    key_metrics: dict[str, str]

class AnalysisAgent(BaseAgent):
    async def run(self, input_data: dict) -> dict:
        prompt = f"""You are a senior business analyst. Analyze this operational data
        and provide structured business insights.

        Product Summary:
        {json.dumps(input_data["by_product"], indent=2)}

        Regional Summary:
        {json.dumps(input_data["by_region"], indent=2)}

        Weekly Trend:
        {json.dumps(input_data["by_week"], indent=2)}

        Totals:
        {json.dumps(input_data["totals"], indent=2)}

        Provide your analysis as structured JSON matching this schema:
        - executive_summary: 2-3 sentence overview
        - insights: array of {{ category, title, description, severity, metric_value }}
        - key_metrics: dict of metric_name -> formatted_value
        """

        response = await self.llm.invoke(prompt, response_format=AnalysisResult)
        return response.model_dump()
```

### 8.6 Report Generation Agent

**Purpose:** Convert AI analysis into professional business reports.

Outputs:
- **Markdown** — for Slack messages and web display
- **PDF** — for email attachments and downloads (via WeasyPrint)

```python
class ReportAgent(BaseAgent):
    async def run(self, input_data: dict) -> dict:
        analysis = input_data["analysis"]

        # Generate Markdown report using LLM for natural language formatting
        markdown = await self.llm.invoke(
            f"""Convert this analysis into a professional weekly business report
            in Markdown format. Include:
            - Executive Summary section
            - Key Metrics table
            - Detailed Insights (with severity indicators)
            - Recommendations section
            - Footer with generation timestamp

            Analysis Data: {json.dumps(analysis, indent=2)}
            """
        )

        # Convert Markdown to PDF using WeasyPrint
        pdf_bytes = self._markdown_to_pdf(markdown)
        pdf_url = await self.storage.upload(f"reports/{run_id}.pdf", pdf_bytes)

        return {
            "title": f"Weekly Sales Report — {datetime.now().strftime('%B %d, %Y')}",
            "content_markdown": markdown,
            "content_pdf_url": pdf_url,
            "insights": analysis
        }
```

### 8.7 Delivery Agent

**Purpose:** Dispatch reports through configured channels.

| Channel | Method | Content |
|---------|--------|---------|
| **Slack** | Incoming Webhook | Executive summary + key metrics + link to full report |
| **Email** | SMTP (`smtplib`) | Full report in body + PDF as attachment |

```python
class DeliveryAgent(BaseAgent):
    async def run(self, input_data: dict) -> dict:
        report = input_data["report"]
        channels = input_data.get("delivery_channels", ["slack"])
        results = {}

        if "slack" in channels:
            results["slack"] = await self.slack_service.send(
                message=report["content_markdown"],
                channel=input_data.get("slack_channel", "#reports")
            )

        if "email" in channels:
            results["email"] = await self.email_service.send(
                to=input_data.get("email_recipients", []),
                subject=report["title"],
                body=report["content_markdown"],
                pdf_url=report["content_pdf_url"]
            )

        return {"delivery_results": results}
```

---

## 9. LangGraph Orchestration

The workflow is orchestrated as a **state machine** using LangGraph, enabling:
- **Sequential agent execution** with data passing between nodes
- **Conditional routing** (e.g., skip delivery if human rejects)
- **Persistent state** via checkpointer (survives restarts)
- **Human-in-the-loop** pause and resume

### Workflow State Definition

```python
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

class WorkflowState(TypedDict):
    run_id: str
    file_path: str
    raw_data: Optional[dict]
    cleaned_data: Optional[dict]
    cleaning_report: Optional[dict]
    aggregated_data: Optional[dict]
    analysis: Optional[dict]
    report: Optional[dict]
    delivery_results: Optional[dict]
    status: str
    error: Optional[str]
    approval_status: Optional[str]   # "pending", "approved", "rejected"
```

### Graph Definition

```python
def build_workflow() -> StateGraph:
    workflow = StateGraph(WorkflowState)

    # Add agent nodes
    workflow.add_node("ingest", ingest_node)
    workflow.add_node("clean", clean_node)
    workflow.add_node("aggregate", aggregate_node)
    workflow.add_node("analyze", analyze_node)
    workflow.add_node("human_review", human_review_node)
    workflow.add_node("generate_report", report_node)
    workflow.add_node("deliver", deliver_node)

    # Sequential edges
    workflow.set_entry_point("ingest")
    workflow.add_edge("ingest", "clean")
    workflow.add_edge("clean", "aggregate")
    workflow.add_edge("aggregate", "analyze")
    workflow.add_edge("analyze", "human_review")

    # Conditional: only proceed if approved
    workflow.add_conditional_edges(
        "human_review",
        route_after_review,   # Returns "generate_report", "end", or stays in "human_review"
    )
    workflow.add_edge("generate_report", "deliver")
    workflow.add_edge("deliver", END)

    # Compile with persistence
    return workflow.compile(checkpointer=MemorySaver())


def route_after_review(state: WorkflowState) -> str:
    """Route based on human approval status."""
    if state["approval_status"] == "approved":
        return "generate_report"
    elif state["approval_status"] == "rejected":
        return END
    else:
        return "human_review"  # Still pending, wait
```

---

## 10. Human-in-the-Loop Approval

This is a **key differentiator** — the workflow pauses after AI analysis and requires human approval before generating the final report.

### Approval Flow

```
Analysis Agent completes
        ↓
Create approval record (status: "pending")
Save workflow state via LangGraph checkpointer
        ↓
Dashboard shows pending approval in Approval Queue
Human reviews: AI executive summary + insights + key metrics
        ↓
Human clicks "Approve" or "Reject" (with optional notes)
        ↓
API updates approval record → resumes LangGraph workflow
        ↓
If Approved  → Report Generation → Delivery
If Rejected  → Workflow ends (logged as "rejected")
```

### Approval API

```python
@router.post("/api/approvals/{approval_id}/approve")
async def approve_checkpoint(approval_id: str, notes: str = ""):
    # Update approval record
    await db.update("approvals", approval_id, {
        "status": "approved",
        "reviewer_notes": notes,
        "decided_at": datetime.now()
    })

    # Resume the paused LangGraph workflow
    approval = await db.get("approvals", approval_id)
    run_id = approval["run_id"]

    # Update workflow state and continue execution
    await workflow_app.aupdate_state(
        config={"configurable": {"thread_id": run_id}},
        values={"approval_status": "approved"}
    )
    await workflow_app.ainvoke(None, config={"configurable": {"thread_id": run_id}})

    return {"status": "approved", "message": "Workflow resumed"}
```

---

## 11. API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| **Workflows** | | |
| `POST` | `/api/workflows/run` | Trigger a new workflow run |
| `GET` | `/api/workflows/runs` | List all workflow runs with pagination |
| `GET` | `/api/workflows/runs/{id}` | Get run details + agent execution logs |
| **Reports** | | |
| `GET` | `/api/reports` | List all generated reports |
| `GET` | `/api/reports/{id}` | Get specific report content |
| `GET` | `/api/reports/{id}/download` | Download report as PDF |
| **Approvals** | | |
| `GET` | `/api/approvals/pending` | List pending approval requests |
| `POST` | `/api/approvals/{id}/approve` | Approve a checkpoint (resumes workflow) |
| `POST` | `/api/approvals/{id}/reject` | Reject a checkpoint (ends workflow) |
| **Dashboard** | | |
| `GET` | `/api/dashboard/stats` | Summary statistics (total runs, success rate, etc.) |
| `GET` | `/api/dashboard/activity` | Recent activity feed |

### Example: Triggering a Workflow

```bash
# Trigger a sales report workflow
curl -X POST http://localhost:8000/api/workflows/run \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_type": "sales_report",
    "config": {
      "file_path": "data/mock_sales_data.csv",
      "delivery_channels": ["slack", "email"],
      "email_recipients": ["leadership@company.com"]
    }
  }'
```

**Response:**
```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "message": "Workflow started successfully"
}
```

---

## 12. Delivery Integrations

### 12.1 Slack Integration

Reports are delivered to Slack channels via Incoming Webhooks.

```python
import requests

class SlackService:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def send(self, message: str, channel: str = "#reports"):
        payload = {
            "channel": channel,
            "blocks": [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": "📊 Weekly Sales Report"}
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": message[:3000]}
                }
            ]
        }
        response = requests.post(self.webhook_url, json=payload)
        return {"status": response.status_code, "channel": channel}
```

**Example Slack Message:**
```
📊 Weekly Sales Report — March 10, 2026

Revenue: $345,000 (+12% vs last week)
Units Sold: 1,240
Profit Margin: 38.5%

Top Products:
• Laptop Pro 15 — $143,880
• 27" Monitor — $39,920
• Wireless Keyboard — $11,980

⚠️ Anomaly: Asia Pacific units dropped 22% — investigate supply chain
✅ Recommendation: Increase Laptop Pro inventory in North America
```

### 12.2 Email Integration (Free — Using Python smtplib)

Email delivery uses Python's **built-in `smtplib` and `email` modules** — completely free with no external service required. Works with Gmail, Outlook, or any SMTP server.

```python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

class EmailService:
    def __init__(self, smtp_host: str, smtp_port: int, username: str, password: str):
        self.smtp_host = smtp_host       # e.g., "smtp.gmail.com"
        self.smtp_port = smtp_port       # e.g., 587
        self.username = username
        self.password = password         # App password for Gmail

    async def send(self, to: list[str], subject: str, body: str, pdf_url: str = None):
        msg = MIMEMultipart()
        msg["From"] = self.username
        msg["To"] = ", ".join(to)
        msg["Subject"] = subject

        # HTML body from markdown
        msg.attach(MIMEText(self._md_to_html(body), "html"))

        # Attach PDF if available
        if pdf_url:
            pdf_bytes = await self._download_pdf(pdf_url)
            attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
            attachment.add_header("Content-Disposition", "attachment", filename="report.pdf")
            msg.attach(attachment)

        # Send via SMTP
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            server.login(self.username, self.password)
            server.sendmail(self.username, to, msg.as_string())

        return {"status": "sent", "recipients": to}
```

**SMTP Configuration (`.env`):**
```env
# For Gmail (use App Password, not your regular password)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password

# For Outlook
# SMTP_HOST=smtp.office365.com
# SMTP_PORT=587
```

---

## 13. Scheduling Automation

Workflows can run on a schedule using **APScheduler** (in-process Python scheduler).

### Configuration

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = AsyncIOScheduler()

# Weekly sales report: Every Monday at 8:00 AM
scheduler.add_job(
    trigger_workflow,
    CronTrigger(day_of_week="mon", hour=8, minute=0),
    args=["sales_report", "data/mock_sales_data.csv"],
    id="weekly_sales_report",
    name="Weekly Sales Report"
)

# Monthly financial report: 1st of every month at 9:00 AM
scheduler.add_job(
    trigger_workflow,
    CronTrigger(day=1, hour=9, minute=0),
    args=["financial_report", "data/mock_financial_data.csv"],
    id="monthly_financial_report",
    name="Monthly Financial Report"
)

scheduler.start()
```

### Schedule Summary

| Report | Schedule | Cron Expression |
|--------|----------|----------------|
| Weekly Sales Report | Every Monday, 8:00 AM | `0 8 * * MON` |
| Monthly Financial Report | 1st of month, 9:00 AM | `0 9 1 * *` |
| Inventory Check | Daily, 7:00 AM | `0 7 * * *` |

---

## 14. Dashboard

The Next.js dashboard provides full visibility into the automation system.

### Pages

| Page | Features |
|------|----------|
| **Dashboard Home** | Total runs count, success rate, average duration, pending approvals badge, recent activity feed, quick-run button |
| **Run History** | Sortable/filterable table of all workflow runs with status badges (`running`, `completed`, `failed`, `awaiting_approval`) |
| **Run Detail** | Visual timeline of agent execution, per-agent logs with duration/tokens, input/output data viewer, error details |
| **Reports** | List of generated reports with preview, read in-browser, download as PDF |
| **Approval Queue** | Pending approvals showing AI insights summary, approve/reject buttons with notes field |

### Dashboard Home Metrics (Example)

```
╔═══════════════╗  ╔═══════════════╗  ╔═══════════════╗  ╔═══════════════╗
║ Total Runs    ║  ║ Success Rate  ║  ║ Avg Duration  ║  ║ Pending       ║
║     47        ║  ║    95.7%      ║  ║   2m 34s      ║  ║  2 approvals  ║
╚═══════════════╝  ╚═══════════════╝  ╚═══════════════╝  ╚═══════════════╝
```

---

## 15. Implementation Phases

### Phase 1: Foundation (Days 1–3)
- Project setup — Python virtualenv, FastAPI skeleton, Supabase project
- Database schema migration (all 4 tables)
- Mock data generation scripts (500+ row sales dataset)
- Base agent class with logging and error handling
- Config management (`.env` + Pydantic Settings)

### Phase 2: Core Agents (Days 4–7)
- Ingestion Agent — CSV loader with schema validation
- Cleaning Agent — LLM-powered data inspection and cleaning
- Aggregation Agent — dynamic grouping with multi-level metrics
- Analysis Agent — structured insights with GPT-4o-mini
- Report Generation Agent — Markdown + PDF output
- Unit tests for each agent

### Phase 3: Orchestration (Days 8–10)
- LangGraph state machine setup
- Workflow state persistence with checkpointer
- Human-in-the-loop approval gate
- Error handling and retry logic
- Workflow run tracking (database logging)

### Phase 4: API Layer (Days 11–12)
- FastAPI endpoints for workflow management
- Report endpoints (list, view, download)
- Approval endpoints (list pending, approve, reject)
- Dashboard data endpoints (stats, activity)
- WebSocket for real-time run status updates

### Phase 5: Delivery & Scheduling (Days 13–14)
- Slack webhook integration
- Email delivery (Python `smtplib` + Gmail/Outlook SMTP — completely free)
- APScheduler setup for periodic workflow runs
- Supabase Storage for PDF report files

### Phase 6: Frontend Dashboard (Done)
- Next.js project setup with ShadCN UI
- Dashboard home page with summary statistics
- Run history page with filtering and sorting
- Run detail page with agent execution timeline
- Report viewer with in-browser preview and PDF download
- Approval queue page with approve/reject actions
- Real-time status updates via polling

### Phase 7: Multi-Report & Final Polish (Done)
- Refactored agents to support dynamic schemas (Sales, Inventory, Finance)
- Implemented report type selector on Dashboard
- Fixed dynamic report titles in UI
- Added cascading deletion and storage cleanup for workflow runs
- Final documentation and GitHub push

### Phase 15: Slack Sharing Formatting & Responsive UI (Done)
- Refactored DeliveryAgent's `_send_slack` method to natively parse full markdown block kit elements.
- Adjusted Report API's slack_share endpoint to conditionally fetch raw insights and route to DeliveryAgent.
- Replaced frontend `alert` calls with `sonner` toast notifications on the Reports page.
- Adjusted the Reports page grid layout to wrap action buttons (`Share to Slack`, `View`, `Delete`) securely on mobile screens using `flex-wrap` and `sm:flex-grow-0`.
- Implemented a responsive bottom-dock navigation for mobile devices, hiding the sidebar layout on small screens via `md:ml-64` utilities.

---

## 16. Deliverables

This MVP produces all deliverables that a client would expect:

| Deliverable | Output |
|---|---|
| **Workflow analysis document** | `docs/workflow-analysis.md` — documents the original manual workflow being automated |
| **Agent architecture design** | `docs/architecture.md` — system architecture + `docs/agent-design.md` — agent design rationale |
| **Working agentic workflow** | Fully functional LangGraph pipeline with 6 LLM-powered agents |
| **Report generation** | Automated Markdown + PDF reports with AI-generated insights |
| **Documentation** | Complete `docs/` folder + README with setup instructions |

---

## 17. Future Roadmap

Once the MVP is complete, the system can evolve into a full **AI Operations Platform**:

| Enhancement | Description |
|---|---|
| **Real ERP Connectors** | SAP, NetSuite, QuickBooks API integrations |
| **Additional Workflows** | Inventory forecasting, vendor scoring, financial reconciliation |
| **CRM Integrations** | HubSpot, Salesforce data import |
| **Multi-Tenant SaaS** | Role-based access, organization management |
| **RAG Knowledge Base** | Vector DB for historical report search (pgvector) |
| **Advanced Scheduling** | Apache Airflow or Prefect for complex DAG workflows |
| **Monitoring** | Prometheus + Grafana for system health tracking |
| **Enterprise Auth** | SSO with SAML/OAuth for corporate clients |

---

**Potential Product Names:**
- **OpsPilot AI** — AI-powered operations copilot
- **AgentOps AI** — Agentic operations automation
- **AutoOps AI** — Autonomous operations platform