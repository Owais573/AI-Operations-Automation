"use client";

import { useEffect, useState } from "react";
import { fetchReports, type Report } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { RefreshCw, FileText, Download, Eye } from "lucide-react";

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);

  async function loadReports() {
    setLoading(true);
    try {
      const data = await fetchReports();
      setReports(data);
    } catch (err) {
      console.error("Error loading reports:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadReports();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Reports</h1>
          <p className="text-sm text-zinc-500">
            Generated reports from completed workflows
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={loadReports} disabled={loading}>
          <RefreshCw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {reports.length === 0 && !loading ? (
        <Card className="border-white/10 bg-zinc-900/50 backdrop-blur">
          <CardContent className="flex flex-col items-center justify-center py-16">
            <FileText className="h-12 w-12 text-zinc-600 mb-4" />
            <p className="text-zinc-500">No reports generated yet</p>
            <p className="text-xs text-zinc-600 mt-1">
              Run a workflow and approve it to generate a report
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {reports.map((report) => (
            <Card
              key={report.id}
              className="border-white/10 bg-zinc-900/50 backdrop-blur transition-all hover:border-violet-500/30"
            >
              <CardHeader>
                <CardTitle className="text-base text-white">
                  {report.title}
                </CardTitle>
                <p className="text-xs text-zinc-500">
                  {new Date(report.created_at).toLocaleString()}
                </p>
              </CardHeader>
              <CardContent className="flex gap-2">
                <Dialog>
                  <DialogTrigger>
                    <Button
                      variant="outline"
                      size="sm"
                      className="border-white/10"
                      onClick={() => setSelectedReport(report)}
                    >
                      <Eye className="mr-2 h-4 w-4" />
                      Preview
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="max-h-[80vh] max-w-3xl overflow-y-auto bg-zinc-950 border-white/10">
                    <DialogHeader>
                      <DialogTitle className="text-white">
                        {selectedReport?.title || report.title}
                      </DialogTitle>
                    </DialogHeader>
                    <div className="prose prose-invert prose-sm max-w-none mt-4">
                      <pre className="whitespace-pre-wrap text-xs text-zinc-300">
                        {report.content_markdown || "No content available."}
                      </pre>
                    </div>
                  </DialogContent>
                </Dialog>

                {report.pdf_public_url && (
                  <a
                    href={report.pdf_public_url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <Button
                      variant="outline"
                      size="sm"
                      className="border-white/10"
                    >
                      <Download className="mr-2 h-4 w-4" />
                      PDF
                    </Button>
                  </a>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
