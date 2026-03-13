const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `API Error ${res.status}`);
  }
  return res.json();
}

// ── Dashboard ──
export function fetchDashboardStats() {
  return apiFetch<DashboardStats>("/api/dashboard/stats");
}

export function fetchDashboardActivity() {
  return apiFetch<ActivityItem[]>("/api/dashboard/activity");
}

// ── Workflows ──
export function fetchWorkflowRuns(limit = 50) {
  return apiFetch<WorkflowRun[]>(`/api/workflows/runs?limit=${limit}`);
}

export function fetchWorkflowRun(runId: string) {
  return apiFetch<WorkflowRunDetail>(`/api/workflows/runs/${runId}`);
}

export function triggerWorkflow(body: TriggerWorkflowRequest) {
  return apiFetch<{ message: string; run_id: string }>("/api/workflows/run", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function deleteWorkflowRun(runId: string) {
  return apiFetch<{ message: string }>(`/api/workflows/runs/${runId}`, {
    method: "DELETE",
  });
}

// ── Reports ──
export function fetchReports() {
  return apiFetch<Report[]>("/api/reports");
}

export function fetchReport(reportId: string) {
  return apiFetch<Report>(`/api/reports/${reportId}`);
}

// ── Approvals ──
export function fetchPendingApprovals() {
  return apiFetch<Approval[]>("/api/approvals/pending");
}

export function approveWorkflow(approvalId: string, notes = "") {
  return apiFetch<{ message: string; run_id: string }>(`/api/approvals/${approvalId}/approve`, {
    method: "POST",
    body: JSON.stringify({ reviewer_notes: notes }),
  });
}

export function rejectWorkflow(approvalId: string, notes = "") {
  return apiFetch<{ message: string }>(`/api/approvals/${approvalId}/reject`, {
    method: "POST",
    body: JSON.stringify({ reviewer_notes: notes }),
  });
}

// ── Schedules ──
export function fetchSchedules() {
  return apiFetch<Schedule[]>("/api/schedules");
}

// ── Types ──
export interface DashboardStats {
  total_runs: number;
  successful_runs: number;
  failed_runs: number;
  success_rate_percentage: number;
  total_reports_generated: number;
  pending_human_approvals: number;
}

export interface ActivityItem {
  id: string;
  workflow_type: string;
  status: string;
  created_at: string;
}

export interface WorkflowRun {
  id: string;
  workflow_type: string;
  status: string;
  input_config: Record<string, unknown>;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  created_at: string;
}

export interface WorkflowRunDetail {
  run: WorkflowRun;
  logs: AgentLog[];
}

export interface AgentLog {
  id: string;
  run_id: string;
  agent_name: string;
  status: string;
  input_data: Record<string, unknown>;
  output_data: Record<string, unknown>;
  started_at: string;
  completed_at: string;
  error_message: string | null;
}

export interface Report {
  id: string;
  run_id: string;
  title: string;
  content_markdown: string;
  pdf_storage_path: string | null;
  pdf_public_url: string | null;
  created_at: string;
}

export interface Approval {
  id: string;
  run_id: string;
  checkpoint_name: string;
  status: string;
  data_snapshot: Record<string, unknown>;
  reviewer_notes: string | null;
  decided_at: string | null;
  created_at: string;
  workflow_runs?: { status: string; workflow_type: string };
}

export interface Schedule {
  job_id: string;
  next_run: string | null;
  trigger: string;
  kwargs: Record<string, unknown>;
}

export interface TriggerWorkflowRequest {
  workflow_type: string;
  file_path?: string;
  expected_columns?: string[];
  email_recipients?: string[];
  slack_channel?: string;
}
