# AI Operations Automation

**Agentic Workflow System for Business Reporting**

An AI-powered operational automation platform that converts manual ERP reporting workflows into autonomous AI agent pipelines with human-in-the-loop approval checkpoints.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12 + FastAPI |
| Agent Framework | LangGraph + LangChain |
| LLM | OpenAI GPT-4o-mini |
| Data Processing | Pandas |
| Database | Supabase (PostgreSQL) |
| Frontend | Next.js + Tailwind CSS + ShadCN UI + Recharts |
| Email | Python smtplib (free, built-in) |
| Scheduling | APScheduler |
| PDF Generation | xhtml2pdf |

---

## Quick Start

### Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Node.js 22+ (for frontend)
- OpenAI API key
- Supabase project (already configured)

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/Owais573/AI-Operations-Automation.git
cd AI-Operations-Automation

# 2. Install Python dependencies
uv sync

# 3. Configure environment
cp .env.example .env
# Edit .env with your keys (SUPABASE_SERVICE_ROLE_KEY, OPENAI_API_KEY)

# 4. Generate mock data
uv run python -c "from backend.data_generator import generate_all; generate_all('data')"

# 5. Start the backend server
uv run uvicorn backend.main:app --reload --port 8000

# 6. Visit API docs
# http://localhost:8000/docs
```

---

## Project Structure

```
ai-operations-automation/
├── backend/
│   ├── main.py                    # FastAPI entry point + health check
│   ├── config.py                  # Pydantic Settings (env var management)
│   ├── data_generator.py          # Mock ERP data generator (Faker)
│   ├── agents/                    # LLM-powered workflow agents
│   │   ├── base_agent.py          # Abstract base with lifecycle logging
│   │   ├── ingestion_agent.py     # CSV/Excel loader + schema validation
│   │   ├── cleaning_agent.py      # LLM-powered data cleaning
│   │   ├── aggregation_agent.py   # Multi-dimensional grouping + KPIs
│   │   ├── analysis_agent.py      # LLM chain-of-thought insights
│   │   ├── report_agent.py        # LLM Markdown report + PDF generation
│   │   └── delivery_agent.py      # Slack webhook + SMTP email
│   ├── orchestration/             # LangGraph state machine (Phase 3)
│   ├── api/                       # FastAPI route handlers (Phase 4)
│   ├── services/                  # External service integrations
│   ├── database/
│   │   └── db.py                  # Supabase client with CRUD helpers
│   ├── scheduler/                 # APScheduler jobs (Phase 5)
│   └── utils/
│       ├── logger.py              # Structured colored logging
│       └── error_handler.py       # Custom exceptions + FastAPI handlers
├── data/                          # Generated mock CSV datasets
│   ├── mock_sales_data.csv        # 620 rows with intentional anomalies
│   ├── mock_inventory_data.csv    # 344 rows with stock levels
│   └── mock_financial_data.csv    # 250 rows financial metrics
├── .env.example                   # Environment variable template
├── pyproject.toml                 # Python dependencies (uv)
└── README.md
```

---

## Architecture

### System Overview

```
+--------------------------------------------------------------+
|                    FRONTEND (Next.js)                         |
|  Dashboard | Run History | Report Viewer | Approval Queue     |
+-----------------------------+--------------------------------+
                              | REST API / WebSocket
+-----------------------------v--------------------------------+
|                  BACKEND (FastAPI + Python)                    |
|                                                               |
|  +-----------------------------------------------------------+
|  |            LangGraph Orchestration Engine                  |
|  |                                                            |
|  |  +---------+  +----------+  +----------+  +--------+      |
|  |  | Ingest  |->|  Clean   |->|Aggregate |->|Analyze |      |
|  |  | Agent   |  |  Agent   |  |  Agent   |  | Agent  |      |
|  |  +---------+  +----------+  +----------+  +----+---+      |
|  |                                                 |          |
|  |                              +------------------v-------+  |
|  |                              | Human Approval Gate      |  |
|  |                              +------------------+-------+  |
|  |                                                 |          |
|  |                              +------------------v-------+  |
|  |                              | Report Generation Agent  |  |
|  |                              +------------------+-------+  |
|  |                                                 |          |
|  |                              +------------------v-------+  |
|  |                              |  Delivery Agent          |  |
|  |                              +--------------------------+  |
+-----------------------------------------------------------+
|                                                               |
|  Scheduling (APScheduler) | State Store | Error Handler       |
+-----------------------------+--------------------------------+
                              |
+-----------------------------v--------------------------------+
|               DATABASE (Supabase / PostgreSQL)                |
|  workflow_runs | agent_logs | reports | approvals             |
+--------------------------------------------------------------+
```

### Workflow Pipeline

```
CSV / Mock ERP Data
        |
        v
+-------------------------+
|   Ingestion Agent       |  --> Load & validate raw data
+-------------------------+
|   Cleaning Agent (LLM)  |  --> Inspect data quality, clean intelligently
+-------------------------+
|   Aggregation Agent     |  --> Group, summarize, calculate metrics
+-------------------------+
|   Analysis Agent (LLM)  |  --> Generate insights, detect trends & anomalies
+-------------------------+
|   Human Approval Gate   |  --> Pause for human review before final report
+-------------------------+
|   Report Agent          |  --> Generate Markdown + PDF report
+-------------------------+
|   Delivery Agent        |  --> Send via Slack / Email
+-------------------------+
```

---

## Agents (Phase 2 -- Implemented)

| Agent | Type | Key Capabilities |
|-------|------|-----------------|
| **Ingestion** | Data | Load CSV/Excel files, validate schema against expected columns, extract metadata (row count, date range, column types), detect duplicates and missing values |
| **Cleaning** | LLM-powered | Sends data summary to GPT-4o-mini for a structured cleaning plan, then executes: deduplication, null filling (median/mode), type conversion, outlier flagging (3x IQR), text standardization |
| **Aggregation** | Data (Pandas) | Multi-dimensional grouping (product, region, time), overall KPIs (revenue, margin, AOV), month-over-month growth, top performers by revenue, cross-dimensional analysis |
| **Analysis** | LLM-powered | Chain-of-thought business insights: executive summary, key findings with impact levels, trend analysis + growth assessment, anomaly detection, prioritized recommendations, confidence scoring |
| **Report** | LLM + xhtml2pdf | Generates professional Markdown reports via GPT-4o-mini, includes tables and structured sections, converts to styled PDF with professional CSS |
| **Delivery** | Integration | Slack delivery via Block Kit formatted webhooks, Email via smtplib (SMTP/TLS) with HTML body + optional PDF attachment, graceful handling of unconfigured channels |

### Base Agent Features

All agents inherit from `BaseAgent` which provides:
- **Lifecycle logging** -- automatic start/complete/fail logging to `agent_logs` table
- **Duration tracking** -- millisecond-precision execution timing
- **Token counting** -- tracks LLM token usage per agent
- **Error handling** -- structured `AgentExecutionError` with original error chain

---

## Database Schema

| Table | Columns | Purpose |
|-------|---------|---------|
| `workflow_runs` | id, workflow_type, status, input_config, started_at, completed_at, error_message | Tracks each pipeline execution lifecycle |
| `agent_logs` | id, run_id (FK), agent_name, status, input/output_summary, duration_ms, tokens_used | Per-agent execution logs with performance metrics |
| `reports` | id, run_id (FK), title, content_markdown, content_pdf_url, insights | Generated business reports with structured insights |
| `approvals` | id, run_id (FK), checkpoint_name, status, data_snapshot, reviewer_notes, decided_at | Human approval checkpoints with review workflow |

---

## Mock Data

The project includes a mock data generator (`backend/data_generator.py`) that creates realistic ERP datasets with:

- **Sales data** (620 rows): 8 products, 4 regions, 12 sales reps, date range Oct 2025 - Feb 2026
  - Includes intentional anomalies: 5 duplicate rows, 8 missing values, revenue spike day
- **Inventory data** (344 rows): Stock level snapshots across 4 warehouses with reorder points
- **Financial data** (250 rows): Revenue, COGS, Marketing, Payroll, Operations, R&D by department

All mock data uses a fixed seed (`Faker.seed(42)`) for reproducibility.

---

## Key Features

- **Truly Agentic** -- Agents use LLM reasoning to make decisions, not hardcoded logic
- **Human-in-the-Loop** -- Workflow pauses for human approval before report generation
- **Full Observability** -- Every agent execution logged with duration, tokens, and I/O summaries
- **Multi-format Reports** -- Markdown for web/Slack, PDF for email/download
- **Scheduled Automation** -- Configurable periodic runs via APScheduler
- **Free Email Delivery** -- Uses Python's built-in smtplib (no paid services)

---

## Implementation Progress

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1: Foundation | Done | Project setup, Supabase DB, mock data, base agent, config, FastAPI |
| Phase 2: Core Agents | Done | All 6 agents (Ingestion, Cleaning, Aggregation, Analysis, Report, Delivery) |
| Phase 3: Orchestration | Done | LangGraph state machine, workflow persistence, approval gate |
| Phase 4: API Layer | Done | REST endpoints for workflows, reports, approvals |
| Phase 5: Delivery & Scheduling | Done | Slack/Email integration, APScheduler, Supabase Storage |
| Phase 6: Frontend Dashboard | Done | Next.js dashboard with ShadCN UI |
| Phase 7: Documentation | Done | Architecture docs, demo, final polish |

---

## License

Private -- All rights reserved.
