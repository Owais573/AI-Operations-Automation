"use client";

import { useEffect, useState } from "react";
import {
  fetchDashboardStats,
  fetchDashboardActivity,
  triggerWorkflow,
  type DashboardStats,
  type ActivityItem,
} from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Play,
  CheckCircle2,
  XCircle,
  Clock,
  FileText,
  ShieldCheck,
  RefreshCw,
} from "lucide-react";

const statusColor: Record<string, string> = {
  completed: "bg-emerald-500/20 text-emerald-400",
  running: "bg-blue-500/20 text-blue-400",
  failed: "bg-red-500/20 text-red-400",
  pending: "bg-amber-500/20 text-amber-400",
  awaiting_approval: "bg-violet-500/20 text-violet-400",
};

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [activity, setActivity] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);

  async function loadData() {
    setLoading(true);
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
    const interval = setInterval(loadData, 15000);
    return () => clearInterval(interval);
  }, []);

  async function handleQuickRun() {
    setTriggering(true);
    try {
      await triggerWorkflow({
        workflow_type: "sales_report",
        file_path: "f:/Antigravity/AI Operations Automation/data/mock_sales_data.csv",
      });
      setTimeout(loadData, 2000);
    } catch (err) {
      console.error("Failed to trigger workflow:", err);
    } finally {
      setTriggering(false);
    }
  }

  if (loading && !stats) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <RefreshCw className="h-6 w-6 animate-spin text-violet-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-sm text-zinc-500">
            Real-time overview of your AI automation pipeline
          </p>
        </div>
        <Button
          onClick={handleQuickRun}
          disabled={triggering}
          className="bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500"
        >
          {triggering ? (
            <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Play className="mr-2 h-4 w-4" />
          )}
          Quick Run
        </Button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card className="border-white/10 bg-zinc-900/50 backdrop-blur">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-zinc-400">
                Total Runs
              </CardTitle>
              <Play className="h-4 w-4 text-violet-400" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-white">
                {stats.total_runs}
              </div>
            </CardContent>
          </Card>

          <Card className="border-white/10 bg-zinc-900/50 backdrop-blur">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-zinc-400">
                Success Rate
              </CardTitle>
              <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-white">
                {stats.success_rate_percentage}%
              </div>
              <p className="text-xs text-zinc-500 mt-1">
                {stats.successful_runs} succeeded · {stats.failed_runs} failed
              </p>
            </CardContent>
          </Card>

          <Card className="border-white/10 bg-zinc-900/50 backdrop-blur">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-zinc-400">
                Reports Generated
              </CardTitle>
              <FileText className="h-4 w-4 text-blue-400" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-white">
                {stats.total_reports_generated}
              </div>
            </CardContent>
          </Card>

          <Card className="border-white/10 bg-zinc-900/50 backdrop-blur">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-zinc-400">
                Pending Approvals
              </CardTitle>
              <ShieldCheck className="h-4 w-4 text-amber-400" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-white">
                {stats.pending_human_approvals}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Recent Activity */}
      <Card className="border-white/10 bg-zinc-900/50 backdrop-blur">
        <CardHeader>
          <CardTitle className="text-lg text-white">Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          {activity.length === 0 ? (
            <p className="text-sm text-zinc-500">No recent activity</p>
          ) : (
            <div className="space-y-3">
              {activity.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between rounded-lg border border-white/5 bg-zinc-900 px-4 py-3"
                >
                  <div className="flex items-center gap-3">
                    <Clock className="h-4 w-4 text-zinc-500" />
                    <div>
                      <p className="text-sm font-medium text-zinc-200">
                        {item.workflow_type.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                      </p>
                      <p className="text-xs text-zinc-500">
                        {new Date(item.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <Badge
                    variant="secondary"
                    className={statusColor[item.status] || "bg-zinc-700 text-zinc-300"}
                  >
                    {item.status}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
