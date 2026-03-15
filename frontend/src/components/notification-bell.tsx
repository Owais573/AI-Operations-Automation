"use client";

import { useState, useEffect } from "react";
import { Bell, CheckCircle2, XCircle, Info, Clock, ShieldCheck } from "lucide-react";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { fetchDashboardActivity, fetchPendingApprovals, type ActivityItem } from "@/lib/api";

export function NotificationBell() {
  const [notifications, setNotifications] = useState<any[]>([]);
  const [hasNew, setHasNew] = useState(false);
  const [prevCount, setPrevCount] = useState(0);

  async function checkNotifications() {
    try {
      const [activity, approvals] = await Promise.all([
        fetchDashboardActivity(),
        fetchPendingApprovals(),
      ]);

      const items: any[] = [];

      // Process activity (status changes)
      activity.slice(0, 5).forEach((item: ActivityItem) => {
        if (item.status === 'completed' || item.status === 'failed') {
          items.push({
            id: item.id,
            title: `Workflow ${item.status}`,
            description: `${item.workflow_type.replace(/_/g, ' ')} has finished.`,
            type: item.status,
            time: item.created_at,
          });
        }
      });

      // Process approvals
      approvals.forEach((app: any) => {
        items.push({
          id: app.id,
          title: "Approval Required",
          description: `Checkpoint reached: ${app.checkpoint_name}`,
          type: "approval",
          time: app.created_at,
        });
      });

      // Sort by time
      items.sort((a, b) => new Date(b.time).getTime() - new Date(a.time).getTime());
      
      setNotifications(items);
      
      if (items.length > prevCount) {
        setHasNew(true);
        setPrevCount(items.length);
      }
    } catch (err) {
      console.error("Failed to fetch notifications:", err);
    }
  }

  useEffect(() => {
    checkNotifications();
    const interval = setInterval(checkNotifications, 10000);
    return () => clearInterval(interval);
  }, [prevCount]);

  function handleOpen() {
    setHasNew(false);
  }

  return (
    <Popover onOpenChange={handleOpen}>
      <PopoverTrigger
        render={
          <Button variant="ghost" size="icon" className="relative h-9 w-9 rounded-full hover:bg-muted font-normal">
            <Bell className="h-5 w-5 text-muted-foreground" />
            {hasNew && (
              <span className="absolute top-2 right-2 flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
              </span>
            )}
          </Button>
        }
      />
      <PopoverContent className="w-80 p-0 overflow-hidden border-border bg-card shadow-2xl" align="end">
        <div className="p-4 border-b border-border flex items-center justify-between bg-muted/30">
          <h4 className="text-sm font-bold">Notifications</h4>
          <Badge variant="outline" className="text-[10px] uppercase font-bold px-1.5 py-0">
            {notifications.length} Total
          </Badge>
        </div>
        <div className="max-h-[400px] overflow-y-auto">
          {notifications.length === 0 ? (
            <div className="p-10 text-center space-y-2">
              <div className="h-10 w-10 rounded-full bg-muted flex items-center justify-center mx-auto">
                <Bell className="h-5 w-5 text-muted-foreground/50" />
              </div>
              <p className="text-sm text-muted-foreground">No recent notifications</p>
            </div>
          ) : (
            <div className="divide-y divide-border/50">
              {notifications.map((n) => (
                <div key={n.id} className="p-4 hover:bg-muted/50 transition-colors flex gap-4">
                  <div className="mt-1">
                    {n.type === 'completed' && <CheckCircle2 className="h-4 w-4 text-emerald-500" />}
                    {n.type === 'failed' && <XCircle className="h-4 w-4 text-red-500" />}
                    {n.type === 'approval' && <ShieldCheck className="h-4 w-4 text-amber-500" />}
                    {!['completed', 'failed', 'approval'].includes(n.type) && <Info className="h-4 w-4 text-blue-500" />}
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs font-bold leading-none">{n.title}</p>
                    <p className="text-[11px] text-muted-foreground leading-snug">{n.description}</p>
                    <p className="text-[10px] text-muted-foreground/60 flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {new Date(n.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        {notifications.length > 0 && (
          <div className="p-2 border-t border-border bg-muted/10">
            <Button variant="ghost" className="w-full text-xs text-muted-foreground h-8" size="sm">
              Mark all as read
            </Button>
          </div>
        )}
      </PopoverContent>
    </Popover>
  );
}
