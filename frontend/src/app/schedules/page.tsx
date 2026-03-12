"use client";

import { useEffect, useState } from "react";
import { fetchSchedules, type Schedule } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { RefreshCw, Clock, Calendar } from "lucide-react";

export default function SchedulesPage() {
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [loading, setLoading] = useState(true);

  async function loadSchedules() {
    setLoading(true);
    try {
      const data = await fetchSchedules();
      setSchedules(data);
    } catch (err) {
      console.error("Error loading schedules:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadSchedules();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Schedules</h1>
          <p className="text-sm text-zinc-500">
            Automated workflow schedules
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={loadSchedules} disabled={loading}>
          <RefreshCw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      <Card className="border-white/10 bg-zinc-900/50 backdrop-blur">
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow className="border-white/10 hover:bg-transparent">
                <TableHead className="text-zinc-400">Job ID</TableHead>
                <TableHead className="text-zinc-400">Workflow Type</TableHead>
                <TableHead className="text-zinc-400">Trigger</TableHead>
                <TableHead className="text-zinc-400">Next Run</TableHead>
                <TableHead className="text-zinc-400">Data Source</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {schedules.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-12">
                    <div className="flex flex-col items-center gap-2">
                      <Calendar className="h-8 w-8 text-zinc-600" />
                      <p className="text-sm text-zinc-500">
                        {loading ? "Loading..." : "No active schedules"}
                      </p>
                      <p className="text-xs text-zinc-600">
                        Use the API to create schedules
                      </p>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                schedules.map((schedule) => (
                  <TableRow
                    key={schedule.job_id}
                    className="border-white/5 hover:bg-white/5"
                  >
                    <TableCell className="font-mono text-sm text-violet-400">
                      {schedule.job_id}
                    </TableCell>
                    <TableCell className="text-zinc-200">
                      {(schedule.kwargs.workflow_type as string || "—")
                        .replace(/_/g, " ")
                        .replace(/\b\w/g, (c) => c.toUpperCase())}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="secondary"
                        className="bg-indigo-500/20 text-indigo-400"
                      >
                        <Clock className="mr-1 h-3 w-3" />
                        {schedule.trigger}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-zinc-400 text-sm">
                      {schedule.next_run
                        ? new Date(schedule.next_run).toLocaleString()
                        : "—"}
                    </TableCell>
                    <TableCell className="text-zinc-500 text-xs font-mono">
                      {(schedule.kwargs.file_path as string) || "—"}
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
