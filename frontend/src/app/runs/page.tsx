"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  fetchWorkflowRuns,
  deleteWorkflowRun,
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
import { 
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { RefreshCw, ExternalLink, Trash2 } from "lucide-react";

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
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [runToDelete, setRunToDelete] = useState<string | null>(null);

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

  async function handleDelete(runId: string) {
    setDeletingId(runId);
    try {
      await deleteWorkflowRun(runId);
      await loadRuns();
    } catch (err) {
      console.error("Error deleting run:", err);
      alert("Failed to delete workflow run.");
    } finally {
      setDeletingId(null);
      setRunToDelete(null);
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
                    <TableCell className="text-right space-x-2">
                      <Button 
                        variant="ghost" 
                        size="sm"
                        onClick={() => setRunToDelete(run.id)}
                        disabled={deletingId === run.id}
                        className="text-red-400 hover:text-red-300 hover:bg-red-400/10"
                      >
                        <Trash2 className={`h-4 w-4 ${deletingId === run.id ? "animate-pulse" : ""}`} />
                      </Button>
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

      {/* Delete Confirmation Dialog */}
      <Dialog open={!!runToDelete} onOpenChange={(open) => !open && setRunToDelete(null)}>
        <DialogContent className="border-white/10 bg-zinc-950 text-white sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Delete Workflow Run</DialogTitle>
            <DialogDescription className="text-zinc-400">
              Are you sure you want to delete this workflow run? This action cannot be undone and will delete all associated logs and reports.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="sm:justify-end">
            <Button
              type="button"
              variant="outline"
              onClick={() => setRunToDelete(null)}
              className="border-white/10"
              disabled={deletingId !== null}
            >
              Cancel
            </Button>
            <Button
              type="button"
              variant="destructive"
              disabled={deletingId !== null}
              className="bg-red-500 hover:bg-red-600 text-white"
              onClick={() => {
                if (runToDelete) handleDelete(runToDelete);
              }}
            >
              {deletingId ? "Deleting..." : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
