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

# 4. Start the backend server
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
│   ├── agents/                    # LLM-powered workflow agents
│   │   ├── base_agent.py          # Abstract base with lifecycle logging
│   │   ├── ingestion_agent.py     # CSV/Excel loader + schema validation
│   │   ├── cleaning_agent.py      # LLM-powered data cleaning
│   │   ├── aggregation_agent.py   # Multi-dimensional grouping + KPIs
│   │   ├── analysis_agent.py      # LLM chain-of-thought insights
│   │   ├── report_agent.py        # LLM Markdown report + PDF generation
│   │   └── delivery_agent.py      # Slack webhook + SMTP email
│   ├── orchestration/             # LangGraph state machine
│   ├── api/                       # FastAPI route handlers
│   ├── services/                  # External service integrations
│   ├── database/
│   │   └── db.py                  # Supabase client with CRUD helpers
│   ├── scheduler/                 # APScheduler jobs
│   └── utils/
│       ├── logger.py              # Structured colored logging
│       └── error_handler.py       # Custom exceptions + FastAPI handlers
├── data/                          # Operational data storage
│   └── uploads/                   # User-uploaded ERP datasets (CSV/Excel)
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
| **Ingestion** | Data | Load CSV/Excel files, dynamic schema detection, extract metadata (row count, date range), detect duplicates and missing values |
| **Cleaning** | LLM-powered | Generates a structured cleaning plan via GPT-4o-mini: deduplication, null filling, type conversion, outlier flagging, text standardization |
| **Aggregation** | Data (Pandas) | **Multi-Report Support**: Dynamic grouping by dimensions (product, region, department) and measures (revenue, stock_level, amount) based on report type |
| **Analysis** | LLM-powered | **Generalized Insights**: Chain-of-thought analysis for Sales, Inventory, and Finance domains. Trend detection, anomaly alerting, and prioritized recommendations |
| **Report** | LLM + xhtml2pdf | Generates contextual Markdown reports with dynamic titles and date ranges, converted to high-quality PDF with professional CSS |
| **Delivery** | Integration | Slack Block Kit notifications, SMTP Email with HTML body + PDF attachment, multi-channel support |

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

The project is designed to handle diverse ERP and business datasets. Users can upload their own CSV/Excel files directly through the Dashboard, which triggers the autonomous agentic pipeline.

---

## Key Features

- **Multi-Report Support** -- Dynamic pipelines for Sales, Inventory, and Financial datasets
- **Truly Agentic** -- Agents use LLM reasoning to make decisions, not hardcoded logic
- **Human-in-the-Loop** -- Workflow pauses for human approval before report generation
- **Advanced Conversational BI (Chat with your Data)** -- Ask strategic questions and get data-driven growth advice directly from reports using AI. Features full Markdown formatting and comprehensive report context.
- **Report Search & Archiving (RAG)** -- Semantic vector search across all historical reports using pgvector.
- **Visual Workflow Scheduler UI** -- Manage, create, and monitor periodic workflow runs from the dashboard.
- **Documentation Center** -- Integrated, LangChain-inspired documentation hub with sticky navigation and premium UX.
- **Enhanced UX & Interface** -- Premium semantic Tailwind styling, perfect dark mode compatibility, and responsive layout with a bottom-dock mobile navigation.
- **Full Observability** -- Every agent execution logged with duration, tokens, and I/O summaries.
- **Dynamic Slack Delivery** -- Full parsing of Markdown into Slack Block Kit natively.
- **Anomaly Detection Highlighting** -- AI autonomously flags and highlights critical anomalies in your data with proactive executive summaries.
- **Scheduled Automation** -- Configurable periodic runs via APScheduler.

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
| Phase 7: Polish & Documentation | Done | Multi-report pipeline support, dynamic UI titles, initial documentation |
| Phase 8: Manual Delivery Updates | Done | Native Slack block extraction and responsive mobile navigation |
| Phase 9: Enterprise Upgrades | Done | Conversational BI, Visual Workflow Scheduler UI, Report RAG Search, Anomaly Highlighting, and fully Enhanced UX with semantic theming |
| Phase 10: UX Refinement | Done | Optimized Chat reasoning, formatted markdown output, and Documentation Center implementation |
| Phase 11: Final Polish | Done | Workspace cleanup, preservation of user uploads, and documentation finalized |

---

## License

Private -- All rights reserved.
