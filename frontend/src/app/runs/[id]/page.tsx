"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { fetchWorkflowRun, type WorkflowRunDetail } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { ArrowLeft, RefreshCw, CheckCircle2, XCircle, Clock } from "lucide-react";

const statusColor: Record<string, string> = {
  completed: "bg-emerald-500/20 text-emerald-400",
  success: "bg-emerald-500/20 text-emerald-400",
  running: "bg-blue-500/20 text-blue-400",
  failed: "bg-red-500/20 text-red-400",
  pending: "bg-amber-500/20 text-amber-400",
  awaiting_approval: "bg-violet-500/20 text-violet-400",
};

const statusIcon: Record<string, React.ReactNode> = {
  completed: <CheckCircle2 className="h-4 w-4 text-emerald-400" />,
  success: <CheckCircle2 className="h-4 w-4 text-emerald-400" />,
  failed: <XCircle className="h-4 w-4 text-red-400" />,
  running: <RefreshCw className="h-4 w-4 animate-spin text-blue-400" />,
  pending: <Clock className="h-4 w-4 text-amber-400" />,
};

export default function RunDetailPage() {
  const params = useParams();
  const runId = params.id as string;
  const [data, setData] = useState<WorkflowRunDetail | null>(null);
  const [loading, setLoading] = useState(true);

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

  if (loading || !data) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <RefreshCw className="h-6 w-6 animate-spin text-violet-400" />
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
          <h1 className="text-2xl font-bold text-white">
            {run.workflow_type.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
          </h1>
          <p className="text-xs text-zinc-500 font-mono">{run.id}</p>
        </div>
        <Badge
          variant="secondary"
          className={statusColor[run.status] || "bg-zinc-700 text-zinc-300"}
        >
          {run.status}
        </Badge>
      </div>

      {/* Run Info */}
      <Card className="border-white/10 bg-zinc-900/50 backdrop-blur">
        <CardHeader>
          <CardTitle className="text-lg text-white">Run Details</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-2 gap-4 md:grid-cols-4">
          <div>
            <p className="text-xs text-zinc-500">Status</p>
            <p className="text-sm font-medium text-zinc-200">{run.status}</p>
          </div>
          <div>
            <p className="text-xs text-zinc-500">Created</p>
            <p className="text-sm font-medium text-zinc-200">
              {new Date(run.created_at).toLocaleString()}
            </p>
          </div>
          <div>
            <p className="text-xs text-zinc-500">Started</p>
            <p className="text-sm font-medium text-zinc-200">
              {run.started_at ? new Date(run.started_at).toLocaleString() : "—"}
            </p>
          </div>
          <div>
            <p className="text-xs text-zinc-500">Completed</p>
            <p className="text-sm font-medium text-zinc-200">
              {run.completed_at
                ? new Date(run.completed_at).toLocaleString()
                : "—"}
            </p>
          </div>
          {run.error_message && (
            <div className="col-span-full">
              <p className="text-xs text-zinc-500">Error</p>
              <p className="text-sm text-red-400">{run.error_message}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Agent Timeline */}
      <Card className="border-white/10 bg-zinc-900/50 backdrop-blur">
        <CardHeader>
          <CardTitle className="text-lg text-white">Agent Timeline</CardTitle>
        </CardHeader>
        <CardContent>
          {logs.length === 0 ? (
            <p className="text-sm text-zinc-500">No agent logs yet</p>
          ) : (
            <div className="relative space-y-0">
              {/* Vertical timeline line */}
              <div className="absolute left-[18px] top-2 bottom-2 w-0.5 bg-white/10" />

              {logs.map((log, idx) => (
                <div key={log.id} className="relative flex gap-4 pb-6">
                  {/* Timeline dot */}
                  <div className="relative z-10 flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-white/10 bg-zinc-900">
                    {statusIcon[log.status] || (
                      <Clock className="h-4 w-4 text-zinc-500" />
                    )}
                  </div>

                  {/* Content */}
                  <div className="flex-1 rounded-lg border border-white/5 bg-zinc-900/50 p-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-sm font-semibold text-zinc-200">
                        {log.agent_name
                          .replace(/_/g, " ")
                          .replace(/\b\w/g, (c) => c.toUpperCase())}
                      </h3>
                      <Badge
                        variant="secondary"
                        className={
                          statusColor[log.status] ||
                          "bg-zinc-700 text-zinc-300"
                        }
                      >
                        {log.status}
                      </Badge>
                    </div>
                    <div className="mt-2 flex gap-4 text-xs text-zinc-500">
                      <span>
                        Started:{" "}
                        {log.started_at ? new Date(log.started_at).toLocaleTimeString() : "—"}
                      </span>
                      {log.completed_at && (
                        <span>
                          Completed:{" "}
                          {new Date(log.completed_at).toLocaleTimeString()}
                        </span>
                      )}
                    </div>
                    {log.error_message && (
                      <p className="mt-2 text-xs text-red-400">
                        Error: {log.error_message}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
