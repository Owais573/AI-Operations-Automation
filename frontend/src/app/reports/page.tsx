"use client";

import { useEffect, useState, useRef } from "react";
import { fetchReports, fetchReport, type Report, chatWithReport, searchReports } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/Input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  RefreshCw,
  FileText,
  Download,
  Eye,
  FileWarning,
  MessageSquare,
  BarChart3,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  Target,
  Lightbulb,
  Zap,
  Send,
  User,
  Bot,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
} from "recharts";
import { toast } from "sonner";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [fetchingDetail, setFetchingDetail] = useState(false);
  const [sharingReportId, setSharingReportId] = useState<string | null>(null);
  
  // Search state
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  
  // Chat state
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [isChatting, setIsChatting] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

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

  async function handleSearch() {
    if (!searchQuery.trim()) {
      loadReports();
      return;
    }
    
    setIsSearching(true);
    try {
      const data = await searchReports(searchQuery);
      setReports(data);
      if (data.length === 0) {
        toast.info("No reports matched your search query.");
      }
    } catch (err) {
      toast.error("Search failed. Falling back to simple list.");
      loadReports();
    } finally {
      setIsSearching(false);
    }
  }

  useEffect(() => {
    loadReports();
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [chatMessages]);

  async function handleOpenPreview(reportId: string) {
    setFetchingDetail(true);
    setChatMessages([]);
    setChatInput("");
    try {
      const detail = await fetchReport(reportId);
      setSelectedReport(detail);
    } catch (err) {
      toast.error("Failed to load report details");
    } finally {
      setFetchingDetail(false);
    }
  }

  async function handleSendMessage() {
    if (!chatInput.trim() || !selectedReport || isChatting) return;

    const userMsg: ChatMessage = { role: "user", content: chatInput };
    setChatMessages((prev) => [...prev, userMsg]);
    setChatInput("");
    setIsChatting(true);

    try {
      const response = await chatWithReport(selectedReport.id, userMsg.content, chatMessages);
      const botMsg: ChatMessage = { role: "assistant", content: response.answer };
      setChatMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      toast.error(err.message || "Failed to get AI response");
    } finally {
      setIsChatting(false);
    }
  }

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
          <h1 className="text-2xl font-bold">Reports</h1>
          <p className="text-sm text-muted-foreground">
            Generated reports from completed workflows
          </p>
        </div>
        <div className="flex items-center gap-2">
           <Button variant="outline" size="sm" onClick={loadReports} disabled={loading}>
            <RefreshCw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>
      </div>

      <div className="flex items-center gap-4 bg-muted/40 p-3 rounded-xl border border-border">
        <div className="relative flex-1">
          <Input 
            placeholder="Search reports semantically (e.g. 'high revenue products in June')..." 
            className="pl-10 bg-background/50 border-input focus-visible:ring-violet-500 transition-all"
            value={searchQuery}
            onChange={(e: any) => setSearchQuery(e.target.value)}
            onKeyDown={(e: any) => e.key === 'Enter' && handleSearch()}
          />
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
            {isSearching ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Eye className="h-4 w-4" />}
          </div>
        </div>
        <Button 
          variant="secondary" 
          size="sm" 
          onClick={handleSearch} 
          disabled={isSearching}
          className="bg-violet-600/20 text-violet-400 hover:bg-violet-600/30 border border-violet-500/20"
        >
          {isSearching ? "Searching..." : "Search"}
        </Button>
      </div>

      {reports.length === 0 && !loading ? (
        <Card className="border-border bg-card/50 backdrop-blur shadow-sm">
          <CardContent className="flex flex-col items-center justify-center py-16">
            <FileText className="h-12 w-12 text-muted-foreground/30 mb-4" />
            <p className="text-muted-foreground">No reports generated yet</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {reports.map((report) => (
            <Card
              key={report.id}
              className="border-border bg-card/50 backdrop-blur shadow-sm transition-all hover:border-violet-500/30 overflow-hidden group"
            >
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-4">
                  <CardTitle className="text-base truncate group-hover:text-violet-500 transition-colors">
                    {report.title}
                  </CardTitle>
                </div>
                <p className="text-[10px] text-muted-foreground font-mono uppercase tracking-wider">
                  {new Date(report.created_at).toLocaleString()}
                </p>
              </CardHeader>
              <CardContent className="flex flex-col sm:flex-row flex-wrap gap-2">
                <Dialog>
                  <DialogTrigger render={
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="w-full sm:w-auto border-border hover:border-violet-500/50 hover:bg-violet-500/5 transition-all" 
                      onClick={() => handleOpenPreview(report.id)}
                    >
                      <Eye className="mr-2 h-4 w-4" />
                      Preview
                    </Button>
                  } />
                  <DialogContent className="sm:max-w-4xl md:max-w-5xl max-h-[90vh] w-[95vw] overflow-hidden bg-background border-border p-0 flex flex-col shadow-2xl">
                    <DialogHeader className="p-6 pb-2 border-b border-border bg-muted/20">
                      <div className="flex items-center justify-between">
                        <DialogTitle className="flex items-center gap-2">
                          <FileText className="h-5 w-5 text-violet-500" />
                          {selectedReport?.title || report.title}
                        </DialogTitle>
                        {selectedReport?.insights?.confidence_score && (
                          <Badge variant="outline" className="text-[10px] bg-emerald-500/10 text-emerald-600 border-emerald-500/20">
                            {Math.round(selectedReport.insights.confidence_score * 100)}% Confidence
                          </Badge>
                        )}
                      </div>
                    </DialogHeader>

                    {fetchingDetail ? (
                      <div className="h-64 flex items-center justify-center">
                        <RefreshCw className="h-8 w-8 animate-spin text-violet-500" />
                      </div>
                    ) : (
                      <Tabs defaultValue="content" className="flex-1 flex flex-col overflow-hidden">
                      <div className="px-6 border-b border-border bg-muted/30">
                        <TabsList className="bg-transparent border-none gap-4">
                          <TabsTrigger 
                            value="content" 
                            className="data-[state=active]:bg-transparent data-[state=active]:border-b-2 data-[state=active]:border-violet-500 rounded-none px-0 py-3 text-xs shadow-none border-b-2 border-transparent"
                          >
                            Report Content
                          </TabsTrigger>
                          <TabsTrigger 
                            value="insights"
                            className="data-[state=active]:bg-transparent data-[state=active]:border-b-2 data-[state=active]:border-violet-500 rounded-none px-0 py-3 text-xs shadow-none border-b-2 border-transparent"
                          >
                            AI Insights
                          </TabsTrigger>
                          <TabsTrigger 
                            value="chat"
                            className="data-[state=active]:bg-transparent data-[state=active]:border-b-2 data-[state=active]:border-violet-500 rounded-none px-0 py-3 text-xs shadow-none border-b-2 border-transparent"
                          >
                            Conversational BI
                          </TabsTrigger>
                          {selectedReport?.measurements && selectedReport.measurements.length > 0 && (
                            <TabsTrigger 
                              value="charts"
                              className="data-[state=active]:bg-transparent data-[state=active]:border-b-2 data-[state=active]:border-violet-500 rounded-none px-0 py-3 text-xs shadow-none border-b-2 border-transparent"
                            >
                              Visual Explorer
                            </TabsTrigger>
                          )}
                        </TabsList>
                      </div>

                        <div className="flex-1 overflow-y-auto p-6 pt-4">
                          <TabsContent value="content" className="mt-0 focus-visible:outline-none">
                            <div className="prose prose-sm dark:prose-invert max-w-none">
                              {selectedReport?.content_markdown ? (
                                <div className="text-foreground/90">
                                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                    {selectedReport.content_markdown}
                                  </ReactMarkdown>
                                </div>
                              ) : (
                                <p className="text-sm text-muted-foreground italic">No content available.</p>
                              )}
                            </div>
                          </TabsContent>

                          <TabsContent value="insights" className="mt-0 focus-visible:outline-none space-y-6">
                            {/* Executive Summary */}
                            {selectedReport?.insights?.executive_summary && (
                              <div className="p-4 rounded-xl bg-violet-500/10 border border-violet-500/20 shadow-sm">
                                <h4 className="text-xs font-bold text-violet-600 dark:text-violet-400 uppercase tracking-widest mb-2 flex items-center gap-2">
                                  <Target className="h-3 w-3" />
                                  Executive Summary
                                </h4>
                                <p className="text-sm text-foreground/80 leading-relaxed italic">
                                  "{selectedReport.insights.executive_summary}"
                                </p>
                              </div>
                            )}

                            {/* Anomalies Highlighted */}
                            {selectedReport?.insights?.anomalies_detected && selectedReport.insights.anomalies_detected.length > 0 && (
                              <div className="space-y-3">
                                <h3 className="text-xs font-bold text-foreground uppercase tracking-widest flex items-center gap-2">
                                  <AlertTriangle className="h-3 w-3 text-red-500" />
                                  Anomaly Detection Feed
                                </h3>
                                <div className="grid gap-3">
                                  {selectedReport.insights.anomalies_detected.map((anomaly: any, i: number) => (
                                    <div key={i} className="flex gap-4 p-3 rounded-lg bg-red-500/5 border border-red-500/10 hover:bg-red-500/10 transition-colors">
                                      <div className={`mt-1 h-2 w-2 rounded-full shrink-0 ${anomaly.severity === 'critical' ? 'bg-red-500 animate-pulse' : 'bg-amber-500'}`} />
                                      <div className="space-y-1">
                                        <div className="flex items-center gap-2">
                                          <p className="text-xs font-bold">{anomaly.affected_metric || 'Anomalous Trend'}</p>
                                          <Badge variant="outline" className={`text-[9px] uppercase ${anomaly.severity === 'critical' ? 'text-red-500 border-red-500/30' : 'text-amber-500 border-amber-500/30'}`}>
                                            {anomaly.severity}
                                          </Badge>
                                        </div>
                                        <p className="text-xs text-muted-foreground">{anomaly.description}</p>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Key Findings */}
                            {selectedReport?.insights?.key_findings && selectedReport.insights.key_findings.length > 0 && (
                              <div className="space-y-3 pt-4 border-t border-border">
                                <h3 className="text-xs font-bold text-foreground uppercase tracking-widest flex items-center gap-2">
                                  <CheckCircle2 className="h-3 w-3 text-emerald-500" />
                                  Key Findings & Schema Discoveries
                                </h3>
                                <div className="grid gap-3 sm:grid-cols-2">
                                  {selectedReport.insights.key_findings.map((finding: any, i: number) => (
                                    <div key={i} className="p-3 rounded-lg bg-muted/40 border border-border space-y-2">
                                      <div className="flex items-start justify-between">
                                        <Badge variant="outline" className="text-[9px] uppercase border-border text-muted-foreground">
                                          {finding.category}
                                        </Badge>
                                        <div className={`h-1.5 w-1.5 rounded-full ${finding.impact === 'high' ? 'bg-violet-500' : 'bg-muted-foreground'}`} />
                                      </div>
                                      <p className="text-xs font-bold text-foreground/90">{finding.finding}</p>
                                      <p className="text-[11px] text-muted-foreground leading-snug">{finding.details}</p>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Recommendations */}
                            {selectedReport?.insights?.recommendations && selectedReport.insights.recommendations.length > 0 && (
                              <div className="space-y-3 pt-4 border-t border-border">
                                <h3 className="text-xs font-bold text-foreground uppercase tracking-widest flex items-center gap-2">
                                  <Lightbulb className="h-3 w-3 text-amber-500" />
                                  Actionable Recommendations
                                </h3>
                                <div className="grid gap-3">
                                  {selectedReport.insights.recommendations.map((rec: any, i: number) => (
                                    <div key={i} className="flex gap-4 p-4 rounded-xl bg-amber-500/5 border border-amber-500/10">
                                      <div className="h-8 w-8 rounded-full bg-amber-500/10 flex items-center justify-center shrink-0">
                                        <Zap className="h-4 w-4 text-amber-500 shadow-sm" />
                                      </div>
                                      <div className="space-y-1">
                                        <p className="text-sm font-bold text-amber-700 dark:text-amber-200">{rec.title}</p>
                                        <p className="text-xs text-muted-foreground">{rec.description}</p>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </TabsContent>

                          <TabsContent value="chat" className="mt-0 focus-visible:outline-none flex flex-col h-[60vh]">
                            <div className="flex-1 overflow-y-auto space-y-4 pr-2 custom-scrollbar mb-4" ref={scrollRef}>
                              {chatMessages.length === 0 ? (
                                <div className="h-full flex flex-col items-center justify-center text-center space-y-4 px-12">
                                  <div className="h-12 w-12 rounded-full bg-violet-500/10 flex items-center justify-center">
                                    <Bot className="h-6 w-6 text-violet-500" />
                                  </div>
                                  <div>
                                    <h4 className="text-sm font-bold">Chat with your Data</h4>
                                    <p className="text-xs text-muted-foreground mt-1">
                                      Ask questions about performance, specific anomalies, or trends found in this report.
                                    </p>
                                  </div>
                                  <div className="flex flex-wrap justify-center gap-2">
                                    {["Summarize the top products", "Why was there a drop in cost?", "What are the key risks?"].map((q) => (
                                      <Button 
                                        key={q} 
                                        variant="outline" 
                                        size="sm" 
                                        className="text-[10px] border-border hover:border-violet-500/30 h-auto py-1"
                                        onClick={() => { setChatInput(q); }}
                                      >
                                        {q}
                                      </Button>
                                    ))}
                                  </div>
                                </div>
                              ) : (
                                chatMessages.map((msg, i) => (
                                  <div key={i} className={`flex gap-3 ${msg.role === 'assistant' ? '' : 'flex-row-reverse'}`}>
                                    <div className={`h-8 w-8 rounded-full flex items-center justify-center shrink-0 shadow-sm ${msg.role === 'assistant' ? 'bg-violet-500/20 text-violet-600 dark:text-violet-400' : 'bg-muted text-muted-foreground'}`}>
                                      {msg.role === 'assistant' ? <Bot className="h-4 w-4" /> : <User className="h-4 w-4" />}
                                    </div>
                                    <div className={`p-3 rounded-2xl max-w-[80%] text-sm shadow-sm ${msg.role === 'assistant' ? 'bg-muted/80 border border-border text-foreground/90' : 'bg-violet-600 text-white'}`}>
                                      {msg.content}
                                    </div>
                                  </div>
                                ))
                              )}
                              {isChatting && (
                                <div className="flex gap-3">
                                  <div className="h-8 w-8 rounded-full bg-violet-500/20 text-violet-400 flex items-center justify-center shrink-0">
                                    <Bot className="h-4 w-4" />
                                  </div>
                                  <div className="p-3 rounded-2xl bg-muted/80 border border-border flex items-center gap-1">
                                    <div className="h-1.5 w-1.5 bg-muted-foreground/50 rounded-full animate-bounce [animation-delay:-0.3s]" />
                                    <div className="h-1.5 w-1.5 bg-muted-foreground/50 rounded-full animate-bounce [animation-delay:-0.15s]" />
                                    <div className="h-1.5 w-1.5 bg-muted-foreground/50 rounded-full animate-bounce" />
                                  </div>
                                </div>
                              )}
                            </div>
                            
                            <div className="relative">
                              <Input 
                                placeholder="Ask a question about this report..." 
                                className="pr-12 bg-muted/30 border-input focus-visible:ring-violet-500"
                                value={chatInput}
                                onChange={(e: any) => setChatInput(e.target.value)}
                                onKeyDown={(e: any) => e.key === 'Enter' && handleSendMessage()}
                                disabled={isChatting}
                              />
                              <Button 
                                size="icon" 
                                className="absolute right-1 top-1 h-8 w-8 bg-violet-600 hover:bg-violet-700"
                                onClick={handleSendMessage}
                                disabled={!chatInput.trim() || isChatting}
                              >
                                <Send className="h-4 w-4" />
                              </Button>
                            </div>
                          </TabsContent>

                          <TabsContent value="charts" className="mt-0 focus-visible:outline-none space-y-8 pb-10">
                             <div className="space-y-4">
                               <div className="flex items-center justify-between">
                                 <div>
                                   <h3 className="text-xs font-bold text-foreground uppercase tracking-widest flex items-center gap-2">
                                     <BarChart3 className="h-3 w-3 text-violet-500" />
                                     Measurement Distribution
                                   </h3>
                                 </div>
                               </div>
                               <div className="h-72 w-full bg-muted/20 rounded-xl border border-border p-4">
                                 <ResponsiveContainer width="100%" height="100%">
                                   <BarChart data={selectedReport?.measurements?.slice(0, 10)}>
                                     <CartesianGrid strokeDasharray="3 3" stroke="#ffffff05" vertical={false} />
                                     <XAxis 
                                       dataKey={Object.keys(selectedReport?.measurements?.[0] || {}).find(k => k.toLowerCase().includes('name') || k.toLowerCase().includes('category') || k.toLowerCase().includes('product')) || "id"} 
                                       stroke="#666" 
                                       fontSize={10}
                                       tickLine={false}
                                       axisLine={false}
                                     />
                                     <YAxis stroke="#666" fontSize={10} tickLine={false} axisLine={false} />
                                     <Tooltip 
                                       contentStyle={{ backgroundColor: "var(--popover)", border: "1px solid var(--border)", borderRadius: "8px", fontSize: "12px", color: "var(--popover-foreground)" }}
                                       itemStyle={{ color: "var(--primary)" }}
                                     />
                                     <Bar 
                                       dataKey={Object.keys(selectedReport?.measurements?.[0] || {}).find(k => k.toLowerCase().includes('revenue') || k.toLowerCase().includes('value') || k.toLowerCase().includes('total') || k.toLowerCase().includes('count')) || "value"} 
                                       fill="#8b5cf6" 
                                       radius={[4, 4, 0, 0]} 
                                     />
                                   </BarChart>
                                 </ResponsiveContainer>
                               </div>
                             </div>

                             <div className="space-y-4">
                               <h3 className="text-xs font-bold text-foreground uppercase tracking-widest flex items-center gap-2">
                                 <TrendingUp className="h-3 w-3 text-blue-500" />
                                 Relationship Trends
                               </h3>
                               <div className="h-72 w-full bg-muted/20 rounded-xl border border-border p-4">
                                 <ResponsiveContainer width="100%" height="100%">
                                   <LineChart data={selectedReport?.measurements}>
                                     <CartesianGrid strokeDasharray="3 3" stroke="#88888810" vertical={false} />
                                     <XAxis 
                                       dataKey={Object.keys(selectedReport?.measurements?.[0] || {}).find(k => k.toLowerCase().includes('date') || k.toLowerCase().includes('time')) || "id"} 
                                       stroke="#888" 
                                       fontSize={10}
                                       tickLine={false}
                                       axisLine={false}
                                     />
                                     <YAxis stroke="#888" fontSize={10} tickLine={false} axisLine={false} />
                                     <Tooltip contentStyle={{ backgroundColor: "var(--popover)", border: "1px solid var(--border)", borderRadius: "8px", fontSize: "12px", color: "var(--popover-foreground)" }} />
                                     <Line 
                                       type="monotone" 
                                       dataKey={Object.keys(selectedReport?.measurements?.[0] || {}).find(k => k.toLowerCase().includes('revenue') || k.toLowerCase().includes('value') || k.toLowerCase().includes('total') || k.toLowerCase().includes('count')) || "value"} 
                                       stroke="#3b82f6" 
                                       strokeWidth={2}
                                       dot={{ r: 4, fill: "#3b82f6", strokeWidth: 0 }}
                                     />
                                   </LineChart>
                                 </ResponsiveContainer>
                               </div>
                             </div>
                          </TabsContent>
                        </div>
                      </Tabs>
                    )}
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
                      className="w-full sm:w-auto border-border hover:bg-muted"
                    >
                      <Download className="mr-2 h-4 w-4" />
                      PDF
                    </Button>
                  </a>
                ) : (
                  <Button
                    variant="outline"
                    disabled
                    className="w-full sm:w-auto border-border text-muted-foreground cursor-not-allowed"
                  >
                    <FileWarning className="mr-2 h-4 w-4" />
                    No PDF
                  </Button>
                )}

                <Button
                  variant="outline"
                  size="sm"
                  className="w-full sm:w-auto border-border hover:bg-[#4A154B] hover:text-white transition-all sm:ml-auto shadow-sm"
                  onClick={() => handleShareToSlack(report.id)}
                  disabled={sharingReportId === report.id}
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
