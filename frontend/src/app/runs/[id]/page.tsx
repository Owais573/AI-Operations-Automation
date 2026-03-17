"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { fetchWorkflowRun, deleteWorkflowRun, type WorkflowRunDetail, type AgentLog } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import {
  ArrowLeft,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Clock,
  Trash2,
  ChevronDown,
  ChevronRight,
  Timer,
  Cpu,
  AlertCircle,
  FileInput,
  FileOutput,
} from "lucide-react";

const statusColor: Record<string, string> = {
  completed: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  success: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  running: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  failed: "bg-red-500/20 text-red-400 border-red-500/30",
  pending: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  awaiting_approval: "bg-violet-500/20 text-violet-400 border-violet-500/30",
  started: "bg-blue-500/20 text-blue-400 border-blue-500/30",
};

const statusIcon: Record<string, React.ReactNode> = {
  completed: <CheckCircle2 className="h-4 w-4 text-emerald-400" />,
  success: <CheckCircle2 className="h-4 w-4 text-emerald-400" />,
  failed: <XCircle className="h-4 w-4 text-red-400" />,
  running: <RefreshCw className="h-4 w-4 animate-spin text-blue-400" />,
  pending: <Clock className="h-4 w-4 text-amber-400" />,
  started: <RefreshCw className="h-4 w-4 animate-spin text-blue-400" />,
};

function JsonBlock({
  data,
  label,
  icon,
}: {
  data: Record<string, unknown> | null;
  label: string;
  icon: React.ReactNode;
}) {
  if (!data || Object.keys(data).length === 0) return null;

  // Truncate huge arrays/strings for readability
  const displayData: Record<string, unknown> = {};
  for (const [key, val] of Object.entries(data)) {
    if (Array.isArray(val) && (val as unknown[]).length > 20) {
      displayData[key] = `[Array of ${(val as unknown[]).length} items — truncated for display]`;
    } else if (typeof val === "string" && val.length > 500) {
      displayData[key] = val.slice(0, 500) + "… [truncated]";
    } else {
      displayData[key] = val;
    }
  }

  return (
    <div className="mt-3">
      <div className="flex items-center gap-2 mb-1.5 text-xs font-medium text-muted-foreground">
        {icon}
        {label}
      </div>
      <pre className="text-xs bg-slate-900 border border-slate-700 rounded-md p-3 overflow-auto max-h-64 text-green-300/90 leading-relaxed whitespace-pre-wrap break-all">
        {JSON.stringify(displayData, null, 2)}
      </pre>
    </div>
  );
}

function AgentLogEntry({ log }: { log: AgentLog }) {
  const [expanded, setExpanded] = useState(false);

  const hasDetails =
    log.input_summary ||
    log.output_summary ||
    log.duration_ms != null ||
    log.tokens_used != null ||
    log.error_message;

  return (
    <div className="relative flex gap-4 pb-6">
      {/* Timeline dot */}
      <div className="relative z-10 flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-border bg-card">
        {statusIcon[log.status] || <Clock className="h-4 w-4 text-muted-foreground" />}
      </div>

      {/* Card */}
      <div className="flex-1 rounded-lg border border-border/50 bg-muted/20 overflow-hidden">
        {/* Header — always visible, clickable */}
        <button
          className="w-full text-left p-4 hover:bg-muted/30 transition-colors disabled:cursor-default"
          onClick={() => setExpanded((v) => !v)}
          disabled={!hasDetails}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {hasDetails ? (
                expanded ? (
                  <ChevronDown className="h-4 w-4 text-muted-foreground" />
                ) : (
                  <ChevronRight className="h-4 w-4 text-muted-foreground" />
                )
              ) : (
                <div className="w-4" />
              )}
              <h3 className="text-sm font-semibold text-foreground">
                {log.agent_name
                  .replace(/_/g, " ")
                  .replace(/\b\w/g, (c) => c.toUpperCase())}
              </h3>
            </div>
            <Badge
              variant="secondary"
              className={statusColor[log.status] || "bg-muted text-muted-foreground"}
            >
              {log.status}
            </Badge>
          </div>

          {/* Quick stats row */}
          <div className="mt-2 flex flex-wrap gap-4 text-xs text-muted-foreground pl-6">
            {log.started_at && (
              <span>Started: {new Date(log.started_at).toLocaleTimeString()}</span>
            )}
            {log.completed_at && (
              <span>Completed: {new Date(log.completed_at).toLocaleTimeString()}</span>
            )}
            {log.duration_ms != null && (
              <span className="flex items-center gap-1">
                <Timer className="h-3 w-3" />
                {log.duration_ms.toLocaleString()} ms
              </span>
            )}
            {log.tokens_used != null && log.tokens_used > 0 && (
              <span className="flex items-center gap-1">
                <Cpu className="h-3 w-3" />
                {log.tokens_used.toLocaleString()} tokens
              </span>
            )}
          </div>
        </button>

        {/* Expandable detail section */}
        {expanded && hasDetails && (
          <div className="border-t border-border/40 px-5 pb-5">
            {/* Error */}
            {log.error_message && (
              <div className="mt-3 flex items-start gap-2 rounded-md bg-destructive/10 border border-destructive/20 p-3">
                <AlertCircle className="h-4 w-4 text-destructive mt-0.5 shrink-0" />
                <p className="text-xs text-destructive leading-relaxed">{log.error_message}</p>
              </div>
            )}

            {/* Input Summary */}
            <JsonBlock
              data={log.input_summary}
              label="Input Summary"
              icon={<FileInput className="h-3.5 w-3.5" />}
            />

            {/* Output Summary */}
            <JsonBlock
              data={log.output_summary}
              label="Output Summary"
              icon={<FileOutput className="h-3.5 w-3.5" />}
            />
          </div>
        )}
      </div>
    </div>
  );
}

export default function RunDetailPage() {
  const params = useParams();
  const router = useRouter();
  const runId = params.id as string;
  const [data, setData] = useState<WorkflowRunDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  async function loadRun() {
    setLoading(true);
    try {
      const result = await fetchWorkflowRun(runId);
      setData(result);
    } catch (err) {
      console.error("Error loading run detail:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadRun();
  }, [runId]);

  async function handleDelete() {
    setDeleting(true);
    try {
      await deleteWorkflowRun(runId);
      router.push("/runs");
    } catch (err) {
      console.error("Error deleting run:", err);
      alert("Failed to delete workflow run.");
      setDeleting(false);
    }
  }

  if (loading || !data) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <RefreshCw className="h-6 w-6 animate-spin text-primary" />
      </div>
    );
  }

  const { run, logs } = data;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/runs">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-foreground">
            {run.workflow_type.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
          </h1>
          <p className="text-xs text-muted-foreground font-mono">{run.id}</p>
        </div>
        <Badge
          variant="secondary"
          className={statusColor[run.status] || "bg-muted text-muted-foreground"}
        >
          {run.status}
        </Badge>

        <div className="ml-auto">
          <Button
            variant="destructive"
            size="sm"
            onClick={() => setShowDeleteDialog(true)}
            disabled={deleting || loading}
            className="bg-destructive/10 text-destructive hover:bg-destructive/20 border-destructive/20"
          >
            <Trash2 className={`mr-2 h-4 w-4 ${deleting ? "animate-pulse" : ""}`} />
            {deleting ? "Deleting..." : "Delete Run"}
          </Button>
        </div>
      </div>

      {/* Run Info */}
      <Card className="border-border/50 bg-card/50 backdrop-blur">
        <CardHeader>
          <CardTitle className="text-lg text-foreground">Run Details</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-2 gap-4 md:grid-cols-4">
          <div>
            <p className="text-xs text-muted-foreground">Status</p>
            <p className="text-sm font-medium text-foreground">{run.status}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Created</p>
            <p className="text-sm font-medium text-foreground">
              {new Date(run.created_at).toLocaleString()}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Started</p>
            <p className="text-sm font-medium text-foreground">
              {run.started_at ? new Date(run.started_at).toLocaleString() : "—"}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Completed</p>
            <p className="text-sm font-medium text-foreground">
              {run.completed_at ? new Date(run.completed_at).toLocaleString() : "—"}
            </p>
          </div>
          {run.error_message && (
            <div className="col-span-full">
              <p className="text-xs text-muted-foreground">Error</p>
              <p className="text-sm text-destructive">{run.error_message}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Agent Timeline */}
      <Card className="border-border/50 bg-card/50 backdrop-blur">
        <CardHeader>
          <CardTitle className="text-lg text-foreground">Agent Timeline</CardTitle>
          {logs.length > 0 && (
            <p className="text-xs text-muted-foreground mt-0.5">
              Click any agent entry to expand its input / output logs.
            </p>
          )}
        </CardHeader>
        <CardContent>
          {logs.length === 0 ? (
            <p className="text-sm text-muted-foreground">No agent logs yet</p>
          ) : (
            <div className="relative space-y-0">
              {/* Vertical timeline line */}
              <div className="absolute left-[18px] top-2 bottom-2 w-0.5 bg-border" />
              {logs.map((log) => (
                <AgentLogEntry key={log.id} log={log} />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent className="border-border bg-background text-foreground sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Delete Workflow Run</DialogTitle>
            <DialogDescription className="text-muted-foreground">
              Are you sure you want to delete this workflow run? This action cannot be
              undone and will delete all associated logs and reports.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="sm:justify-end">
            <Button
              type="button"
              variant="outline"
              onClick={() => setShowDeleteDialog(false)}
              className="border-border"
              disabled={deleting}
            >
              Cancel
            </Button>
            <Button
              type="button"
              variant="destructive"
              disabled={deleting}
              className="bg-destructive hover:bg-destructive/90 text-destructive-foreground"
              onClick={handleDelete}
            >
              {deleting ? "Deleting..." : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
