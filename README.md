# AI Operations Automation

**Agentic Workflow System for Business Reporting**

An AI-powered operational automation platform that converts manual ERP reporting workflows into autonomous AI agent pipelines with human-in-the-loop approval checkpoints.

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

## Quick Start

### Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Node.js 22+ (for frontend)
- OpenAI API key
- Supabase project (already configured)

### Setup

```bash
# 1. Clone the repository
git clone <repo-url>
cd ai-operations-automation

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

### Project Structure

```
├── backend/
│   ├── main.py                 # FastAPI entry point
│   ├── config.py               # Environment configuration
│   ├── data_generator.py       # Mock ERP data generator
│   ├── agents/                 # LLM-powered agents
│   │   ├── base_agent.py       # Base agent class
│   │   ├── ingestion_agent.py
│   │   ├── cleaning_agent.py
│   │   ├── aggregation_agent.py
│   │   ├── analysis_agent.py
│   │   ├── report_agent.py
│   │   └── delivery_agent.py
│   ├── orchestration/          # LangGraph workflows
│   ├── api/                    # FastAPI routes
│   ├── services/               # Slack, Email, Storage
│   ├── database/               # Supabase client
│   ├── scheduler/              # APScheduler jobs
│   └── utils/                  # Logger, error handling
├── frontend/                   # Next.js dashboard
├── data/                       # Mock CSV datasets
├── docs/                       # Architecture docs
└── pyproject.toml
```

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
|  +-----------------------------------------------------------+
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

### Agents

| Agent | Type | Purpose |
|-------|------|---------|
| **Ingestion** | Data | Load CSV/Excel, validate schema, extract metadata |
| **Cleaning** | LLM-powered | Inspect data quality issues, generate & execute cleaning plan |
| **Aggregation** | Data | Dynamic grouping by product/region/time, calculate metrics |
| **Analysis** | LLM-powered | Chain-of-thought reasoning for trends, anomalies, recommendations |
| **Report** | LLM-powered | Generate formatted Markdown + PDF business reports |
| **Delivery** | Integration | Dispatch reports via Slack webhooks and Email (SMTP) |

### Database Schema

| Table | Purpose |
|-------|---------|
| `workflow_runs` | Tracks each pipeline execution with status lifecycle |
| `agent_logs` | Per-agent execution logs with duration and token usage |
| `reports` | Generated business reports (Markdown + PDF URL) |
| `approvals` | Human approval checkpoints with review notes |

### Key Features

- **Truly Agentic** -- Agents use LLM reasoning, not hardcoded functions
- **Human-in-the-Loop** -- Workflow pauses for human approval before report generation
- **Full Observability** -- Every agent execution is logged with duration and token tracking
- **Multi-format Reports** -- Markdown for web/Slack, PDF for email/download
- **Scheduled Automation** -- Configurable periodic runs via APScheduler

## License

Private -- All rights reserved.
