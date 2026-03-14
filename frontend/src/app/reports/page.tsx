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
import { RefreshCw, FileText, Download, Eye, FileWarning, MessageSquare } from "lucide-react";
import { toast } from "sonner";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [sharingReportId, setSharingReportId] = useState<string | null>(null);

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

  async function handleShareToSlack(reportId: string) {
    setSharingReportId(reportId);
    try {
      const { shareReportToSlack } = await import("@/lib/api");
      await shareReportToSlack(reportId);
      toast.success("Report successfully shared to Slack!");
    } catch (err: any) {
      console.error("Slack share error:", err);
      toast.error(err.message || "Failed to share report to Slack.");
    } finally {
      setSharingReportId(null);
    }
  }

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
              <CardContent className="flex flex-col sm:flex-row flex-wrap gap-2">
                <Dialog>
                  <DialogTrigger render={<Button variant="outline" size="sm" className="w-full sm:w-auto border-white/10" onClick={() => setSelectedReport(report)} />}>
                    <Eye className="mr-2 h-4 w-4" />
                    Preview
                  </DialogTrigger>
                  <DialogContent className="sm:max-w-3xl md:max-w-4xl max-h-[80vh] w-[90vw] overflow-y-auto bg-zinc-950 border-white/10 p-6">
                    <DialogHeader>
                      <DialogTitle className="text-white">
                        {selectedReport?.title || report.title}
                      </DialogTitle>
                    </DialogHeader>
                    <div className="prose prose-invert prose-sm max-w-none mt-4 border-t border-white/10 pt-4">
                      {selectedReport?.content_markdown ? (
                        <div className="text-zinc-300">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {selectedReport.content_markdown}
                          </ReactMarkdown>
                        </div>
                      ) : (
                        <p className="text-sm text-zinc-500 italic">No content available.</p>
                      )}
                    </div>
                  </DialogContent>
                </Dialog>

                {report.pdf_public_url ? (
                  <a
                    href={report.pdf_public_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="w-full sm:w-auto"
                  >
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full sm:w-auto border-white/10 hover:bg-white/5"
                    >
                      <Download className="mr-2 h-4 w-4" />
                      PDF
                    </Button>
                  </a>
                ) : (
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full sm:w-auto border-white/10 text-zinc-500 cursor-not-allowed"
                    title="PDF generation failed for this report (Markdown only)"
                  >
                    <FileWarning className="mr-2 h-4 w-4" />
                    No PDF
                  </Button>
                )}

                <Button
                  variant="outline"
                  size="sm"
                  className="w-full sm:w-auto border-white/10 hover:bg-[#4A154B] hover:text-white transition-colors sm:ml-auto"
                  onClick={() => handleShareToSlack(report.id)}
                  disabled={sharingReportId === report.id}
                  title="Share this report to the configured Slack channel"
                >
                  {sharingReportId === report.id ? (
                    <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <MessageSquare className="mr-2 h-4 w-4" />
                  )}
                  Share to Slack
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
