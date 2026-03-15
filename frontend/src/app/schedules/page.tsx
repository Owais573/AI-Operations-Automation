"use client";

import { useEffect, useState } from "react";
import { 
  fetchSchedules, 
  createIntervalSchedule, 
  createCronSchedule, 
  deleteSchedule, 
  type Schedule 
} from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/Input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  Clock, 
  Calendar, 
  Plus, 
  Trash2, 
  RefreshCw, 
  Play, 
  Settings2,
  AlertCircle,
  CheckCircle2,
  Activity,
  Zap,
  ChevronRight,
  Database
} from "lucide-react";
import { toast } from "sonner";

export default function SchedulesPage() {
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [loading, setLoading] = useState(true);
  const [isAdding, setIsAdding] = useState(false);
  
  // Form state
  const [activeTab, setActiveTab] = useState("interval");
  const [jobId, setJobId] = useState("");
  const [workflowType, setWorkflowType] = useState("sales_performance");
  const [filePath, setFilePath] = useState("data/sales_data.csv");
  const [hours, setHours] = useState(24);
  const [cronExpression, setCronExpression] = useState("0 8 * * 1-5");

  async function loadSchedules() {
    setLoading(true);
    try {
      const data = await fetchSchedules();
      setSchedules(data);
    } catch (err) {
      console.error("Error loading schedules:", err);
      toast.error("Failed to load schedules");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadSchedules();
  }, []);

  async function handleAddSchedule() {
    if (!jobId.trim() || !filePath.trim()) {
      toast.error("Job ID and File Path are required");
      return;
    }

    try {
      if (activeTab === "interval") {
        await createIntervalSchedule({
          job_id: jobId,
          workflow_type: workflowType,
          file_path: filePath,
          hours: hours,
        });
      } else {
        await createCronSchedule({
          job_id: jobId,
          workflow_type: workflowType,
          file_path: filePath,
          cron_expression: cronExpression,
        });
      }
      
      toast.success("Schedule created successfully");
      setIsAdding(false);
      resetForm();
      loadSchedules();
    } catch (err: any) {
      toast.error(err.message || "Failed to create schedule");
    }
  }

  async function handleDelete(id: string) {
    try {
      await deleteSchedule(id);
      toast.success("Schedule removed");
      loadSchedules();
    } catch (err: any) {
      toast.error(err.message || "Failed to delete schedule");
    }
  }

  function resetForm() {
    setJobId("");
    setFilePath("data/sales_data.csv");
    setHours(24);
    setCronExpression("0 8 * * 1-5");
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground tracking-tight">Automation Scheduler</h1>
          <p className="text-muted-foreground mt-1">Manage recurring workflow executions and data synchronization jobs</p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" size="sm" onClick={loadSchedules} disabled={loading} className="border-border bg-card/50">
            <RefreshCw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            Sync
          </Button>
          <Dialog open={isAdding} onOpenChange={setIsAdding}>
            <DialogTrigger render={
              <Button size="sm" className="bg-primary hover:bg-primary/90 shadow-lg shadow-primary/20">
                <Plus className="mr-2 h-4 w-4" />
                New Schedule
              </Button>
            } />
            <DialogContent className="sm:max-w-[500px] bg-background border-border p-0 overflow-hidden">
              <DialogHeader className="p-6 pb-0">
                <DialogTitle className="text-xl text-foreground flex items-center gap-2">
                  <Settings2 className="h-5 w-5 text-primary" />
                  Configure Schedule
                </DialogTitle>
                <CardDescription className="text-muted-foreground">
                  Set up a recurring trigger for your data automation pipeline.
                </CardDescription>
              </DialogHeader>

              <div className="p-6 pt-4 space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-xs font-bold text-muted-foreground uppercase tracking-widest">Unique Job ID</label>
                    <Input 
                      placeholder="e.g. daily-sales-audit" 
                      value={jobId} 
                      onChange={(e) => setJobId(e.target.value)}
                      className="bg-muted/50 border-border focus-visible:ring-primary"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-xs font-bold text-muted-foreground uppercase tracking-widest">Workflow Type</label>
                    <select 
                      className="w-full h-9 rounded-md border border-border bg-muted/50 px-3 py-1 text-sm text-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary"
                      value={workflowType}
                      onChange={(e) => setWorkflowType(e.target.value)}
                    >
                      <option value="sales_performance">Sales Performance</option>
                      <option value="operational_efficiency">Operational Efficiency</option>
                      <option value="financial_audit">Financial Audit</option>
                    </select>
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-bold text-muted-foreground uppercase tracking-widest">Data Source Path</label>
                  <Input 
                    placeholder="data/input.csv" 
                    value={filePath} 
                    onChange={(e) => setFilePath(e.target.value)}
                    className="bg-muted/50 border-border focus-visible:ring-primary"
                  />
                  <p className="text-[10px] text-muted-foreground/70">Enter the path to the CSV file relative to the backend root.</p>
                </div>

                <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                  <TabsList className="grid w-full grid-cols-2 bg-muted p-1">
                    <TabsTrigger value="interval" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground text-xs">
                      <Clock className="mr-2 h-3 w-3" /> Interval
                    </TabsTrigger>
                    <TabsTrigger value="cron" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground text-xs">
                      <Calendar className="mr-2 h-3 w-3" /> Cron
                    </TabsTrigger>
                  </TabsList>
                  <TabsContent value="interval" className="mt-4 p-4 rounded-lg bg-muted/30 border border-border/50">
                    <div className="space-y-2">
                      <label className="text-[11px] font-bold text-muted-foreground uppercase">Repeat every X hours</label>
                      <div className="flex items-center gap-4">
                        <Input 
                          type="number" 
                          value={hours} 
                          onChange={(e) => setHours(parseInt(e.target.value))}
                          className="w-24 bg-muted border-border"
                        />
                        <span className="text-sm text-muted-foreground">Hours</span>
                      </div>
                    </div>
                  </TabsContent>
                  <TabsContent value="cron" className="mt-4 p-4 rounded-lg bg-muted/30 border border-border/50">
                    <div className="space-y-2">
                      <label className="text-[11px] font-bold text-muted-foreground uppercase">Cron Expression</label>
                      <Input 
                        placeholder="0 8 * * 1-5" 
                        value={cronExpression} 
                        onChange={(e) => setCronExpression(e.target.value)}
                        className="bg-muted border-border"
                      />
                      <p className="text-[10px] text-muted-foreground/70">Standard 5-field cron (min, hr, day, mon, weekday)</p>
                    </div>
                  </TabsContent>
                </Tabs>
              </div>

              <DialogFooter className="p-6 bg-muted/40 border-t border-border/50">
                <Button variant="ghost" size="sm" onClick={() => setIsAdding(false)} className="text-muted-foreground hover:text-foreground">Cancel</Button>
                <Button size="sm" onClick={handleAddSchedule} className="bg-primary hover:bg-primary/90">Save Schedule</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-4">
        <Card className="bg-card/50 border-border backdrop-blur overflow-hidden">
          <CardContent className="p-6 flex items-center gap-4">
            <div className="h-10 w-10 rounded-full bg-emerald-500/10 flex items-center justify-center text-emerald-400 shadow-inner">
              <Zap className="h-5 w-5" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground leading-none">{schedules.length}</p>
              <p className="text-[10px] text-muted-foreground font-bold uppercase tracking-widest mt-1">Active Jobs</p>
            </div>
          </CardContent>
          <div className="h-1 bg-emerald-500/20" />
        </Card>
        
        <Card className="bg-card/50 border-border backdrop-blur overflow-hidden">
          <CardContent className="p-6 flex items-center gap-4">
            <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center text-primary shadow-inner">
              <Activity className="h-5 w-5" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground leading-none">Healthy</p>
              <p className="text-[10px] text-muted-foreground font-bold uppercase tracking-widest mt-1">System Status</p>
            </div>
          </CardContent>
          <div className="h-1 bg-primary/20" />
        </Card>
      </div>

      <Card className="border-border bg-card/40 backdrop-blur">
        <CardContent className="p-0">
          <Table>
            <TableHeader className="bg-muted/20 border-b border-border/50">
              <TableRow className="hover:bg-transparent">
                <TableHead className="w-[200px] text-muted-foreground text-[10px] uppercase font-bold tracking-widest">Job Name</TableHead>
                <TableHead className="text-muted-foreground text-[10px] uppercase font-bold tracking-widest">Configuration</TableHead>
                <TableHead className="text-muted-foreground text-[10px] uppercase font-bold tracking-widest">Next Run</TableHead>
                <TableHead className="text-right text-muted-foreground text-[10px] uppercase font-bold tracking-widest">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={4} className="h-32 text-center">
                    <RefreshCw className="h-6 w-6 animate-spin mx-auto text-violet-500 opacity-50" />
                  </TableCell>
                </TableRow>
              ) : schedules.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="h-32 text-center text-muted-foreground italic">
                    No active schedules found. Create one to get started.
                  </TableCell>
                </TableRow>
              ) : (
                schedules.map((schedule) => (
                  <TableRow key={schedule.job_id} className="border-border/50 hover:bg-muted transition-colors group">
                    <TableCell className="font-medium text-foreground">
                      <div className="flex flex-col">
                        <span className="flex items-center gap-2">
                          {schedule.job_id}
                          {schedule.next_run && (
                            <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                          )}
                        </span>
                        <Badge variant="ghost" className="p-0 text-[9px] text-muted-foreground font-mono text-left w-fit h-auto flex items-center gap-1">
                          <ChevronRight className="h-2 w-2" />
                          {schedule.kwargs.workflow_type as string}
                        </Badge>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="flex items-center gap-1 text-[11px] text-foreground bg-muted px-2 py-1 rounded-md border border-border">
                          <Database className="h-3 w-3 text-muted-foreground" />
                          {schedule.kwargs.file_path as string}
                        </div>
                        <Badge variant="outline" className="text-[10px] bg-muted border-border text-muted-foreground capitalize h-5">
                          {schedule.trigger.includes('interval') ? 'Interval' : 'Cron'}
                        </Badge>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-col">
                        <span className="text-xs text-foreground">
                          {schedule.next_run ? new Date(schedule.next_run).toLocaleString() : 'Not scheduled'}
                        </span>
                        <span className="text-[10px] text-muted-foreground font-mono">
                          {schedule.trigger.replace(/trigger\[|\]/g, '')}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                         <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-foreground hover:bg-muted">
                           <Play className="h-4 w-4" />
                         </Button>
                         <Button variant="ghost" size="icon" className="h-8 w-8 text-red-500 hover:text-red-600 hover:bg-red-500/10" onClick={() => handleDelete(schedule.job_id)}>
                           <Trash2 className="h-4 w-4" />
                         </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
      
      <div className="grid gap-6 md:grid-cols-2">
         <Card className="bg-muted/30 border-dashed border-border">
           <CardHeader>
             <CardTitle className="text-sm text-foreground flex items-center gap-2">
               <AlertCircle className="h-4 w-4 text-primary" />
               Scheduling Tips
             </CardTitle>
           </CardHeader>
           <CardContent className="space-y-2">
             <p className="text-xs text-muted-foreground leading-relaxed">
               • Use <strong>Interval</strong> for simple repeating tasks (e.g. every 24 hours).
             </p>
             <p className="text-xs text-muted-foreground leading-relaxed">
               • <strong>Cron</strong> allows precision timing like "Every weekday at 8:00 AM".
             </p>
             <p className="text-xs text-muted-foreground leading-relaxed">
               • Job IDs must be <strong>unique</strong>. Saving a duplicate ID will overwrite the existing job.
             </p>
           </CardContent>
         </Card>

         <Card className="bg-muted/30 border-dashed border-border">
           <CardHeader>
             <CardTitle className="text-sm text-foreground flex items-center gap-2">
               <CheckCircle2 className="h-4 w-4 text-emerald-500" />
               Execution Monitor
             </CardTitle>
           </CardHeader>
           <CardContent className="space-y-2">
             <p className="text-xs text-muted-foreground leading-relaxed">
               All scheduled runs are logged in the <strong>Run History</strong> table automatically.
             </p>
             <p className="text-xs text-muted-foreground leading-relaxed">
               Failed jobs will trigger automatic retries if configured in the orchestration graph.
             </p>
             <p className="text-xs text-muted-foreground leading-relaxed">
               Schedules are persisted in Supabase and will resume after server restarts.
             </p>
           </CardContent>
         </Card>
      </div>
    </div>
  );
}
