"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  fetchWorkflowRuns,
  type WorkflowRun,
} from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { RefreshCw, ExternalLink } from "lucide-react";

const statusColor: Record<string, string> = {
  completed: "bg-emerald-500/20 text-emerald-400",
  running: "bg-blue-500/20 text-blue-400",
  failed: "bg-red-500/20 text-red-400",
  pending: "bg-amber-500/20 text-amber-400",
  awaiting_approval: "bg-violet-500/20 text-violet-400",
};

export default function RunsPage() {
  const [runs, setRuns] = useState<WorkflowRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("all");

  async function loadRuns() {
    setLoading(true);
    try {
      const data = await fetchWorkflowRuns();
      setRuns(data);
    } catch (err) {
      console.error("Error loading runs:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadRuns();
    const interval = setInterval(loadRuns, 10000);
    return () => clearInterval(interval);
  }, []);

  const filteredRuns =
    filter === "all" ? runs : runs.filter((r) => r.status === filter);

  const filterOptions = ["all", "pending", "running", "awaiting_approval", "completed", "failed"];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Workflow Runs</h1>
          <p className="text-sm text-zinc-500">
            History of all workflow executions
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={loadRuns} disabled={loading}>
          <RefreshCw
            className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`}
          />
          Refresh
        </Button>
      </div>

      {/* Filters */}
      <div className="flex gap-2">
        {filterOptions.map((opt) => (
          <Button
            key={opt}
            variant={filter === opt ? "default" : "outline"}
            size="sm"
            onClick={() => setFilter(opt)}
            className={
              filter === opt
                ? "bg-violet-600 hover:bg-violet-500"
                : "border-white/10"
            }
          >
            {opt === "all" ? "All" : opt.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
          </Button>
        ))}
      </div>

      {/* Table */}
      <Card className="border-white/10 bg-zinc-900/50 backdrop-blur">
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow className="border-white/10 hover:bg-transparent">
                <TableHead className="text-zinc-400">Type</TableHead>
                <TableHead className="text-zinc-400">Status</TableHead>
                <TableHead className="text-zinc-400">Created</TableHead>
                <TableHead className="text-zinc-400">Error</TableHead>
                <TableHead className="text-zinc-400 text-right">
                  Actions
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredRuns.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-zinc-500">
                    {loading ? "Loading..." : "No workflow runs found"}
                  </TableCell>
                </TableRow>
              ) : (
                filteredRuns.map((run) => (
                  <TableRow
                    key={run.id}
                    className="border-white/5 hover:bg-white/5"
                  >
                    <TableCell className="font-medium text-zinc-200">
                      {run.workflow_type.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="secondary"
                        className={
                          statusColor[run.status] || "bg-zinc-700 text-zinc-300"
                        }
                      >
                        {run.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-zinc-400">
                      {new Date(run.created_at).toLocaleString()}
                    </TableCell>
                    <TableCell className="max-w-[200px] truncate text-red-400 text-xs">
                      {run.error_message || "—"}
                    </TableCell>
                    <TableCell className="text-right">
                      <Link href={`/runs/${run.id}`}>
                        <Button variant="ghost" size="sm">
                          <ExternalLink className="h-4 w-4" />
                        </Button>
                      </Link>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
