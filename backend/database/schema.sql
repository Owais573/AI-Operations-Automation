-- Supabase Database Schema
-- AI Operations Automation Platform

-- Step 1: Enable Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA "extensions";
CREATE EXTENSION IF NOT EXISTS "vector" WITH SCHEMA "public";
CREATE EXTENSION IF NOT EXISTS "pgcrypto" WITH SCHEMA "extensions";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements" WITH SCHEMA "extensions";

-- Step 2: Create Tables

-- 1. workflow_runs (Master Workflow tracking)
CREATE TABLE IF NOT EXISTS public.workflow_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    input_config JSONB,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 2. agent_logs (Detailed observability for each agent)
CREATE TABLE IF NOT EXISTS public.agent_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES public.workflow_runs(id) ON DELETE CASCADE,
    agent_name TEXT NOT NULL,
    status TEXT NOT NULL,
    input_summary JSONB,
    output_summary JSONB,
    duration_ms INTEGER,
    tokens_used INTEGER,
    error_message TEXT,
    started_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 3. reports (Final business reports)
CREATE TABLE IF NOT EXISTS public.reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES public.workflow_runs(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    content_markdown TEXT,
    pdf_public_url TEXT,
    pdf_storage_path TEXT,
    pdf_size INTEGER,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 4. approvals (Human-in-the-loop checkpoints)
CREATE TABLE IF NOT EXISTS public.approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES public.workflow_runs(id) ON DELETE CASCADE,
    checkpoint_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    data_snapshot JSONB,
    reviewer_notes TEXT,
    decided_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 5. report_embeddings (Vector storage for RAG search)
CREATE TABLE IF NOT EXISTS public.report_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID UNIQUE REFERENCES public.reports(id) ON DELETE CASCADE,
    embedding public.vector(1536), 
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 6. schedules (Periodic automation jobs)
CREATE TABLE IF NOT EXISTS public.schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id TEXT UNIQUE NOT NULL,
    workflow_type TEXT NOT NULL,
    file_path TEXT NOT NULL,
    trigger_type TEXT NOT NULL,
    trigger_value TEXT NOT NULL,
    expected_columns JSONB DEFAULT '[]'::jsonb,
    email_recipients JSONB DEFAULT '[]'::jsonb,
    slack_channel TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Step 3: Enable Security Policies
ALTER TABLE public.schedules ENABLE ROW LEVEL SECURITY;

-- Basic Placeholder Policy for Schedules
CREATE POLICY "Allow public read-only access for schedules" 
ON public.schedules FOR SELECT 
TO authenticated, anon 
USING (true);

-- Step 4: Storage Buckets (Manual Step Reminder)
-- Ensure 'reports' bucket exists in Supabase Storage and is set to 'Public' or has appropriate policies.
