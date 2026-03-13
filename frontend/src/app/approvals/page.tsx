"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  fetchPendingApprovals,
  approveWorkflow,
  rejectWorkflow,
  fetchWorkflowRun,
  type Approval,
} from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  RefreshCw,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Eye,
} from "lucide-react";

export default function ApprovalsPage() {
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [loading, setLoading] = useState(true);
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [generatingReport, setGeneratingReport] = useState(false);
  const [notes, setNotes] = useState<Record<string, string>>({});
  const router = useRouter();
  const processingIdRef = useRef<string | null>(null);

  async function loadApprovals() {
    if (processingIdRef.current) return;
    
    setLoading(true);
    try {
      const data = await fetchPendingApprovals();
      if (!processingIdRef.current) {
        setApprovals(data);
      }
    } catch (err) {
      console.error("Error loading approvals:", err);
    } finally {
      if (!processingIdRef.current) {
        setLoading(false);
      }
    }
  }

  useEffect(() => {
    loadApprovals();
    const interval = setInterval(loadApprovals, 15000);
    return () => clearInterval(interval);
  }, []);

  async function handleApprove(approvalId: string) {
    setProcessingId(approvalId);
    processingIdRef.current = approvalId;
    setGeneratingReport(true);
    try {
      const { run_id } = await approveWorkflow(approvalId, notes[approvalId] || "");
      
      // Poll for completion
      while (true) {
        await new Promise((resolve) => setTimeout(resolve, 3000));
        const runDetail = await fetchWorkflowRun(run_id);
        const status = runDetail.run?.status;
        if (status === "completed") {
          router.push("/reports");
          return;
        } else if (status === "failed") {
          alert("Workflow generation failed. Please check the workflow runs page.");
          setApprovals((prev) => prev.filter((a) => a.id !== approvalId));
          break;
        }
      }
    } catch (err) {
      console.error("Error approving:", err);
      alert("An error occurred during approval.");
      setApprovals((prev) => prev.filter((a) => a.id !== approvalId));
    } finally {
      setProcessingId(null);
      processingIdRef.current = null;
      setGeneratingReport(false);
    }
  }

  async function handleReject(approvalId: string) {
    setProcessingId(approvalId);
    processingIdRef.current = approvalId;
    try {
      await rejectWorkflow(approvalId, notes[approvalId] || "");
      setApprovals((prev) => prev.filter((a) => a.id !== approvalId));
    } catch (err) {
      console.error("Error rejecting:", err);
    } finally {
      setProcessingId(null);
      processingIdRef.current = null;
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Approval Queue</h1>
          <p className="text-sm text-zinc-500">
            Review AI analysis before final report generation
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={loadApprovals} disabled={loading}>
          <RefreshCw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {approvals.length === 0 && !loading ? (
        <Card className="border-white/10 bg-zinc-900/50 backdrop-blur">
          <CardContent className="flex flex-col items-center justify-center py-16">
            <ShieldCheck className="h-12 w-12 text-zinc-600 mb-4" />
            <p className="text-zinc-500">No pending approvals</p>
            <p className="text-xs text-zinc-600 mt-1">
              All workflows have been reviewed
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {approvals.map((approval) => {
            const snapshot = (approval.data_snapshot as any) || {};
            const insights = snapshot.insights || snapshot;
            const summary = insights.executive_summary || "No summary available";
            const findings = insights.key_findings || [];

            return (
              <Card
                key={approval.id}
                className="border-white/10 bg-zinc-900/50 backdrop-blur"
              >
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-base text-white">
                        {approval.workflow_runs?.workflow_type
                          ?.replace(/_/g, " ")
                          .replace(/\b\w/g, (c: string) => c.toUpperCase()) ||
                          "Workflow Approval"}
                      </CardTitle>
                      <p className="text-xs text-zinc-500 mt-1">
                        Checkpoint: {approval.checkpoint_name} ·{" "}
                        {new Date(approval.created_at).toLocaleString()}
                      </p>
                    </div>
                    <Badge
                      variant="secondary"
                      className="bg-amber-500/20 text-amber-400"
                    >
                      Pending Review
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Executive Summary */}
                  <div className="rounded-lg border border-white/5 bg-zinc-900 p-4">
                    <h4 className="text-xs font-semibold uppercase text-zinc-500 mb-2">
                      Executive Summary
                    </h4>
                    <p className="text-sm text-zinc-300">{summary}</p>
                  </div>

                  {/* Key Findings Preview */}
                  {findings.length > 0 && (
                    <div className="rounded-lg border border-white/5 bg-zinc-900 p-4">
                      <h4 className="text-xs font-semibold uppercase text-zinc-500 mb-2">
                        Key Findings ({findings.length})
                      </h4>
                      <ul className="space-y-1">
                        {(findings as Record<string, string>[]).slice(0, 3).map(
                          (f, i) => (
                            <li key={i} className="text-sm text-zinc-400">
                              • {f.finding || JSON.stringify(f)}
                            </li>
                          )
                        )}
                      </ul>
                    </div>
                  )}

                  {/* Full Data Preview */}
                  <Dialog>
                    <DialogTrigger render={<Button variant="outline" size="sm" className="border-white/10" />}>
                      <Eye className="mr-2 h-4 w-4" />
                      View Full Analysis
                    </DialogTrigger>
                    <DialogContent className="sm:max-w-3xl md:max-w-4xl max-h-[80vh] w-[90vw] overflow-y-auto bg-zinc-950 border-white/10 p-6">
                      <DialogHeader>
                        <DialogTitle className="text-white">
                          Full Analysis Data
                        </DialogTitle>
                      </DialogHeader>
                      <pre className="mt-4 text-sm text-zinc-400 whitespace-pre-wrap">
                        {JSON.stringify(approval.data_snapshot, null, 2)}
                      </pre>
                    </DialogContent>
                  </Dialog>

                  {/* Reviewer Notes */}
                  <Textarea
                    placeholder="Add reviewer notes (optional)..."
                    value={notes[approval.id] || ""}
                    onChange={(e) =>
                      setNotes((prev) => ({
                        ...prev,
                        [approval.id]: e.target.value,
                      }))
                    }
                    className="border-white/10 bg-zinc-900 text-zinc-200 placeholder:text-zinc-600"
                  />

                  {/* Action Buttons */}
                  <div className="flex gap-3">
                    <Button
                      onClick={() => handleApprove(approval.id)}
                      disabled={processingId === approval.id || generatingReport}
                      className="bg-emerald-600 hover:bg-emerald-500"
                    >
                      {processingId === approval.id && generatingReport ? (
                        <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                      ) : (
                        <CheckCircle2 className="mr-2 h-4 w-4" />
                      )}
                      {processingId === approval.id && generatingReport
                        ? "Generating Report..."
                        : "Approve & Generate Report"}
                    </Button>
                    <Button
                      onClick={() => handleReject(approval.id)}
                      disabled={processingId === approval.id}
                      variant="destructive"
                    >
                      <XCircle className="mr-2 h-4 w-4" />
                      Reject
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
