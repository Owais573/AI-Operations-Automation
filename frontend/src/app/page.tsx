"use client";

import { useEffect, useState } from "react";
import {
  fetchDashboardStats,
  fetchDashboardActivity,
  fetchWorkflowRun,
  uploadWorkflowFile,
  type DashboardStats,
  type ActivityItem,
} from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { FileUpload } from "@/components/file-upload";
import {
  RefreshCw,
  BarChart3,
  Box,
  TrendingUp,
  Play,
  CheckCircle2,
  Clock,
  FileText,
  ShieldCheck,
  Zap,
  ArrowUpRight,
} from "lucide-react";
import { toast } from "sonner";

const REPORT_TYPES = [
  { id: "sales_report", label: "Sales Analysis", icon: TrendingUp, color: "text-blue-500", bgColor: "bg-blue-500/10" },
  { id: "inventory_report", label: "Inventory Audit", icon: Box, color: "text-emerald-500", bgColor: "bg-emerald-500/10" },
  { id: "financial_report", label: "Financial Audit", icon: BarChart3, color: "text-amber-500", bgColor: "bg-amber-500/10" },
];

const statusColor: Record<string, string> = {
  completed: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
  running: "bg-blue-500/10 text-blue-500 border-blue-500/20",
  failed: "bg-red-500/10 text-red-500 border-red-500/20",
  pending: "bg-amber-500/10 text-amber-500 border-amber-500/20",
  awaiting_approval: "bg-violet-500/10 text-violet-500 border-violet-500/20",
};

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [activity, setActivity] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);
  const [selectedReport, setSelectedReport] = useState("sales_report");

  async function loadData() {
    try {
      const [s, a] = await Promise.all([
        fetchDashboardStats(),
        fetchDashboardActivity(),
      ]);
      setStats(s);
      setActivity(a);
    } catch (err) {
      console.error("Failed to load dashboard:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, []);

  async function handleFileUpload(file: File) {
    setTriggering(true);
    try {
      const result = await uploadWorkflowFile(file, selectedReport);
      toast.success("Workflow Started", {
        description: `Successfully uploaded ${file.name}. View progress in 'Runs'.`,
      });

      // ── Sheet warning check ─────────────────────────────────────────────
      // If the backend detected a fallback_first_sheet scenario (no sheets
      // matched the selected report type), show a non-blocking warning toast.
      if (result?.run_id) {
        const checkSheetWarning = async () => {
          try {
            const runDetail = await fetchWorkflowRun(result.run_id);
            const ingestionLog = runDetail?.logs?.find(
              (log) => log.agent_name === "ingestion_agent"
            );
            const sheetWarning = (ingestionLog?.output_summary?.metadata as Record<string, unknown>)?.sheet_warning as string | undefined;
            if (sheetWarning) {
              toast.warning("Sheet Mismatch Detected", {
                description: sheetWarning,
                duration: 8000,
              });
            }
          } catch {
            // Non-fatal — silently ignore if log isn't ready yet
          }
        };
        // Delay to let the ingestion agent complete before we check
        setTimeout(checkSheetWarning, 4000);
      }
      // ───────────────────────────────────────────────────────────────────

      loadData();
    } catch (err) {
      toast.error("Upload Failed", {
        description: err instanceof Error ? err.message : "Could not start workflow",
      });
    } finally {
      setTriggering(false);
    }
  }

  if (loading && !stats) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <RefreshCw className="h-6 w-6 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-10">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-3xl font-extrabold tracking-tight">Operations Dashboard</h1>
          <p className="text-muted-foreground">
            Monitor and trigger your autonomous operational agent pipelines
          </p>
        </div>
        <div className="flex items-center gap-4 bg-card border px-4 py-2 rounded-xl shadow-sm">
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">System Live</span>
          </div>
          <div className="h-4 w-[1px] bg-border" />
          <p className="text-xs font-medium text-muted-foreground">
            {new Date().toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric' })}
          </p>
        </div>
      </div>

      {/* Stats Cards Section */}
      {stats && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card className="border-border/50 bg-card/50 backdrop-blur hover:shadow-md transition-all">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total Runs</CardTitle>
              <Play className="h-4 w-4 text-violet-500" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{stats.total_runs}</div>
              <p className="text-[10px] text-muted-foreground mt-1 uppercase tracking-tighter">Lifetime Executions</p>
            </CardContent>
          </Card>

          <Card className="border-border/50 bg-card/50 backdrop-blur hover:shadow-md transition-all">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Success Rate</CardTitle>
              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-emerald-500">{stats.success_rate_percentage}%</div>
              <p className="text-[10px] text-muted-foreground mt-1 uppercase tracking-tighter">
                {stats.successful_runs} Succeeded · {stats.failed_runs} Failed
              </p>
            </CardContent>
          </Card>

          <Card className="border-border/50 bg-card/50 backdrop-blur hover:shadow-md transition-all">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Reports Generated</CardTitle>
              <FileText className="h-4 w-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{stats.total_reports_generated}</div>
              <p className="text-[10px] text-muted-foreground mt-1 uppercase tracking-tighter">Verified Insights</p>
            </CardContent>
          </Card>

          <Card className="border-border/50 bg-card/50 backdrop-blur hover:shadow-md transition-all">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Awaiting Human</CardTitle>
              <ShieldCheck className="h-4 w-4 text-amber-500" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{stats.pending_human_approvals}</div>
              <p className="text-[10px] text-muted-foreground mt-1 uppercase tracking-tighter">In Approval Queue</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Grid: Upload & Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left: Trigger Section */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="border-none bg-card shadow-lg overflow-hidden ring-1 ring-border/50">
            <div className="h-1.5 w-full bg-gradient-to-r from-primary to-violet-500" />
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-5 w-5 text-primary" />
                Trigger New Workflow
              </CardTitle>
              <p className="text-xs text-muted-foreground">Start an AI-driven data analysis pipeline</p>
            </CardHeader>
            <CardContent className="space-y-8">
              <div className="space-y-4">
                <label className="text-sm font-bold flex items-center gap-2">
                  <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary/10 text-[10px] text-primary">1</span>
                  Select Report Type
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  {REPORT_TYPES.map((type) => {
                    const Icon = type.icon;
                    const isActive = selectedReport === type.id;
                    return (
                      <button
                        key={type.id}
                        onClick={() => setSelectedReport(type.id)}
                        className={`group relative flex flex-col items-center gap-4 p-5 rounded-2xl border-2 transition-all duration-300
                          ${isActive 
                            ? "border-primary bg-primary/5 shadow-sm scale-[1.02]" 
                            : "border-border hover:border-primary/30 hover:bg-muted/50"}
                        `}
                      >
                        <div className={`p-3 rounded-xl transition-colors ${isActive ? type.bgColor : "bg-muted"}`}>
                          <Icon className={`h-6 w-6 ${isActive ? type.color : "text-muted-foreground"}`} />
                        </div>
                        <span className={`text-xs font-bold ${isActive ? "text-foreground" : "text-muted-foreground"}`}>
                          {type.label}
                        </span>
                        {isActive && (
                          <div className="absolute top-2 right-2">
                             <CheckCircle2 className="h-4 w-4 text-primary" />
                          </div>
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="space-y-4">
                <label className="text-sm font-bold flex items-center gap-2">
                  <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary/10 text-[10px] text-primary">2</span>
                  Upload Dataset
                </label>
                <FileUpload 
                  onUpload={handleFileUpload} 
                  isUploading={triggering} 
                />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right: Recent Activity */}
        <div className="space-y-6">
          <Card className="border-border/50 shadow-md h-full flex flex-col">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-lg font-bold">Recent Activity</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent className="flex-1 overflow-y-auto">
              {activity.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-10 text-center space-y-2">
                  <div className="h-10 w-10 rounded-full bg-muted flex items-center justify-center">
                    <Clock className="h-5 w-5 text-muted-foreground/50" />
                  </div>
                  <p className="text-sm text-muted-foreground">No recent activity detected.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {activity.slice(0, 8).map((item) => (
                    <div
                      key={item.id}
                      className="group flex items-start justify-between gap-4 p-3 rounded-xl border border-border/50 bg-muted/30 hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex gap-3">
                         <div className={`mt-1 h-2 w-2 rounded-full ${item.status === 'completed' ? 'bg-emerald-500' : item.status === 'failed' ? 'bg-red-500' : 'bg-blue-500 animate-pulse'}`} />
                         <div className="space-y-0.5">
                            <p className="text-xs font-bold truncate max-w-[120px]">
                              {item.workflow_type.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                            </p>
                            <p className="text-[10px] text-muted-foreground">
                              {new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </p>
                         </div>
                      </div>
                      <Badge variant="outline" className={`text-[10px] uppercase font-bold px-1.5 py-0 ${statusColor[item.status]}`}>
                        {item.status.replace(/_/g, " ")}
                      </Badge>
                    </div>
                  ))}
                  <Button variant="ghost" size="sm" className="w-full text-xs text-muted-foreground group" nativeButton={false} render={
                    <a href="/runs" />
                  }>
                    View All Runs
                    <ArrowUpRight className="ml-1 h-3 w-3 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
