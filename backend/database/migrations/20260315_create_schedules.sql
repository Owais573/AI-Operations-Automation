-- Create schedules table for persistent workflow automation
CREATE TABLE IF NOT EXISTS public.schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id TEXT UNIQUE NOT NULL,
    workflow_type TEXT NOT NULL,
    file_path TEXT NOT NULL,
    trigger_type TEXT NOT NULL, -- 'interval' or 'cron'
    trigger_value TEXT NOT NULL, -- hours for interval, cron expression for cron
    expected_columns JSONB DEFAULT '[]'::jsonb,
    email_recipients JSONB DEFAULT '[]'::jsonb,
    slack_channel TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS (disabled for now as per previous tables, but good practice to mention)
ALTER TABLE public.schedules ENABLE ROW LEVEL SECURITY;

-- Allow all for now (matching existing tables)
CREATE POLICY "Allow all for now" ON public.schedules FOR ALL USING (true);
