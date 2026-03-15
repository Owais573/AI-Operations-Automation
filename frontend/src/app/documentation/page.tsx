"use client";

import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { 
  BookOpen, 
  Play, 
  FileText, 
  ShieldCheck, 
  Clock, 
  Search, 
  Zap, 
  MessageSquare, 
  Send,
  ArrowRight,
  Workflow,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";

export default function DocumentationPage() {
  const [activeSection, setActiveSection] = useState("getting-started");

  const sections = [
    {
      id: "getting-started",
      title: "Getting Started",
      icon: BookOpen,
      content: "AI Operations Automation is an intelligent agentic platform designed to transform raw ERP data into strategic business insights. By combining multi-agent orchestration with human-in-the-loop validation, we ensure that your reports are not just accurate, but actionable."
    },
    {
      id: "workflows",
      title: "Workflow Engine",
      icon: Workflow,
      content: "Every automated report starts with a workflow. Our engine triggers a sequence of specialized agents to ensure data integrity and deep analysis:",
      items: [
        { label: "Ingestion Agent", desc: "Validates data structure and detects core metrics." },
        { label: "Cleaning Agent", desc: "LLM-driven deduplication and anomaly correction." },
        { label: "Analysis Agent", desc: "Performs multi-dimensional trend analysis." }
      ]
    },
    {
      id: "approvals",
      title: "Human-in-the-Loop",
      icon: ShieldCheck,
      content: "Integrity is our priority. Critical analysis results are paused at an Approval Gate, allowing you to review the AI's findings and recommendations before the final report is generated.",
      tip: "You can find pending checkpoints in the 'Approvals' section."
    },
    {
      id: "semantic-search",
      title: "Advanced Semantic Search",
      icon: Search,
      content: "Traditional keyword search often misses the context. Our Semantic Search uses vector embeddings to understand the 'meaning' of your queries, making it easier to discover historical patterns.",
      try: ["'inventory trends in Q1'", "'which products are growing?'", "'sales performance anomalies'"]
    },
    {
      id: "conversational-bi",
      title: "Conversational BI",
      icon: MessageSquare,
      content: "Interact with your data naturally. Once a report is generated, you can use the chat interface to ask complex follow-up questions and get strategic growth advice.",
      bullets: [
        "Ask for summaries of specific regions or time periods.",
        "Request growth strategies based on identified trends.",
        "Clarify specific data points within the report for deeper understanding."
      ]
    },
    {
      id: "deliveries",
      title: "Delivery & Automation",
      icon: Send,
      content: "Reports are delivered where your team works. Professional PDF generation ensures record-keeping, while Slack integration brings insights directly to your communication channels.",
      link: "/schedules"
    }
  ];

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveSection(entry.target.id);
          }
        });
      },
      { threshold: 0.5, rootMargin: "-100px 0px -50% 0px" }
    );

    sections.forEach((section) => {
      const el = document.getElementById(section.id);
      if (el) observer.observe(el);
    });

    return () => observer.disconnect();
  }, []);

  return (
    <div className="max-w-[1400px] mx-auto px-6 lg:px-10 pb-20">
      <div className="grid gap-12 lg:grid-cols-[280px_1fr] items-start">
        {/* Persistent sticky sidebar */}
        <aside className="hidden lg:block sticky top-0 h-screen self-start pt-10 overflow-y-auto no-scrollbar">
          <div className="space-y-8 pr-4">
            <div>
              <div className="flex items-center gap-3 text-muted-foreground mb-8 px-3">
                <div className="h-10 w-10 rounded-xl bg-foreground text-background flex items-center justify-center shadow-[0_10px_20px_-5px_rgba(0,0,0,0.5)]">
                  <BookOpen className="h-5 w-5" />
                </div>
                <div className="flex flex-col">
                  <span className="text-xs font-black uppercase tracking-widest text-foreground">Docs Center</span>
                  <span className="text-[10px] text-muted-foreground/60 font-medium tracking-tight">AI Ops v1.0.4</span>
                </div>
              </div>
              
              <p className="text-[10px] font-black text-foreground/30 uppercase tracking-[0.2em] px-3 mb-4">Navigation</p>
              <nav className="flex flex-col gap-1.5">
                {sections.map((s) => (
                  <a 
                    key={s.id} 
                    href={`#${s.id}`} 
                    className={`flex items-center gap-3 px-4 py-3 text-sm font-semibold rounded-2xl transition-all duration-500 group
                      ${activeSection === s.id 
                        ? "bg-foreground text-background shadow-[0_20px_40px_-10px_rgba(0,0,0,0.4)] translate-x-2" 
                        : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
                      }`}
                  >
                    <s.icon className={`h-4 w-4 transition-colors duration-300 ${activeSection === s.id ? "text-background" : "text-foreground/20 group-hover:text-foreground/60"}`} />
                    {s.title}
                  </a>
                ))}
              </nav>
            </div>

            <div className="pt-8 border-t border-border/50">
              <p className="text-[10px] font-black text-foreground/30 uppercase tracking-[0.2em] px-3 mb-4">Quick Access</p>
              <nav className="flex flex-col gap-1.5">
                 <a href="/reports" className="flex items-center gap-3 px-4 py-2.5 text-sm font-semibold text-muted-foreground hover:text-foreground hover:bg-muted/50 rounded-xl transition-all">
                   <FileText className="h-4 w-4 text-foreground/20" />
                   Reports Explorer
                 </a>
                 <a href="/schedules" className="flex items-center gap-3 px-4 py-2.5 text-sm font-semibold text-muted-foreground hover:text-foreground hover:bg-muted/50 rounded-xl transition-all">
                   <Clock className="h-4 w-4 text-foreground/20" />
                   Job Schedules
                 </a>
              </nav>
            </div>
          </div>
        </aside>

        {/* Content Area */}
        <div className="space-y-32 pt-10">
          {/* Section Header */}
          <div className="space-y-8 pb-20 border-b border-border/50 relative overflow-hidden">
            <div className="absolute top-0 right-0 -translate-y-1/2 translate-x-1/2 h-96 w-96 bg-foreground opacity-[0.02] rounded-full blur-3xl pointer-events-none" />
            
            <div className="space-y-4">
               <div className="h-1 w-12 bg-foreground rounded-full" />
               <h1 className="text-7xl font-black tracking-tighter leading-[0.9] text-foreground">
                 Master Your<br />
                 <span className="text-transparent bg-clip-text bg-gradient-to-r from-foreground to-foreground/40">AI Operations</span>
               </h1>
            </div>
            
            <p className="text-muted-foreground text-2xl max-w-3xl leading-relaxed font-medium">
              A comprehensive guide to orchestrating autonomous business intelligence, 
              managing expert-driven approvals, and scaling automated report delivery.
            </p>
          </div>

          {sections.map((section) => (
            <section 
              key={section.id} 
              id={section.id} 
              className="scroll-mt-10 space-y-12 animate-in fade-in slide-in-from-bottom-8 duration-1000"
            >
              <div className="space-y-2">
                <div className="flex items-center gap-3 text-muted-foreground mb-1">
                   <section.icon className="h-4 w-4" />
                   <span className="text-[10px] font-bold uppercase tracking-widest">{section.title}</span>
                </div>
                <h2 className="text-3xl font-bold tracking-tight">{section.title}</h2>
              </div>

              <div className="prose prose-neutral dark:prose-invert max-w-none">
                <p className="text-muted-foreground leading-loose text-lg">
                  {section.content}
                </p>

                {section.items && (
                  <div className="grid gap-4 mt-8 sm:grid-cols-2 lg:grid-cols-3">
                    {section.items.map((item, i) => (
                      <div key={i} className="group p-5 rounded-2xl border border-border bg-card hover:border-foreground/20 hover:shadow-xl transition-all duration-300">
                        <p className="text-xs font-bold uppercase tracking-wider mb-2 flex items-center gap-2">
                          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                          {item.label}
                        </p>
                        <p className="text-sm text-muted-foreground leading-relaxed">{item.desc}</p>
                      </div>
                    ))}
                  </div>
                )}

                {section.bullets && (
                  <ul className="mt-8 space-y-3">
                    {section.bullets.map((bullet, i) => (
                      <li key={i} className="flex items-center gap-4 p-4 rounded-xl bg-muted/20 border border-border/50 text-base group hover:bg-muted/40 transition-colors">
                        <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:translate-x-1 transition-transform" />
                        <span className="text-foreground/80">{bullet}</span>
                      </li>
                    ))}
                  </ul>
                )}

                {section.try && (
                   <div className="mt-10 p-8 rounded-[2rem] border border-border bg-foreground/[0.02] flex flex-col md:flex-row items-center gap-8 shadow-inner overflow-hidden relative">
                     <div className="absolute -top-10 -right-10 h-40 w-40 bg-emerald-500/5 rounded-full blur-3xl" />
                     <div className="h-14 w-14 rounded-2xl bg-emerald-500/10 flex items-center justify-center shrink-0 border border-emerald-500/20">
                       <Search className="h-7 w-7 text-emerald-600 dark:text-emerald-400" />
                     </div>
                     <div className="flex-1 space-y-4">
                        <p className="text-base font-bold">Try these conceptual queries:</p>
                        <div className="flex flex-wrap gap-2.5">
                          {section.try.map((t, i) => (
                            <span key={i} className="px-4 py-1.5 bg-background border border-border rounded-xl text-sm font-medium text-muted-foreground hover:border-foreground transition-colors cursor-default">
                              {t}
                            </span>
                          ))}
                        </div>
                     </div>
                   </div>
                )}

                {section.tip && (
                  <div className="mt-8 flex gap-5 p-6 rounded-2xl bg-amber-500/5 border border-amber-500/10">
                    <AlertTriangle className="h-6 w-6 text-amber-500 shrink-0 mt-1" />
                    <div className="space-y-1">
                      <p className="text-sm font-bold text-amber-600 dark:text-amber-400 uppercase tracking-widest">Pro Tip</p>
                      <p className="text-base text-muted-foreground italic leading-relaxed">{section.tip}</p>
                    </div>
                  </div>
                )}
              </div>
            </section>
          ))}
          
          {/* Support Section */}
          <section className="pt-20">
            <Card className="bg-foreground text-background border-none shadow-[0_32px_64px_-16px_rgba(0,0,0,0.3)] overflow-hidden relative rounded-[2.5rem]">
              <div className="absolute -bottom-20 -right-20 p-10 opacity-10">
                <Workflow className="h-96 w-96 rotate-12" />
              </div>
              <CardContent className="p-12 lg:p-20 relative z-10 space-y-8">
                <h3 className="text-4xl lg:text-5xl font-black tracking-tighter">Need custom<br />automation?</h3>
                <p className="text-background/80 max-w-2xl text-xl leading-relaxed font-medium">
                  The AI Operations engine is designed to be fully extensible. Build custom agents,
                  integrate unique data sources, or design complex multi-step state machines.
                </p>
                <div className="flex flex-wrap gap-6 pt-4">
                  <div className="px-8 py-4 bg-background text-foreground font-black rounded-2xl text-base shadow-xl hover:-translate-y-1 transition-all cursor-pointer">
                    Contact Architect
                  </div>
                  <div className="px-8 py-4 bg-background/10 border border-white/20 text-white font-bold rounded-2xl text-base hover:bg-background/20 transition-all cursor-pointer">
                    API Reference
                  </div>
                </div>
              </CardContent>
            </Card>
          </section>
        </div>
      </div>
    </div>
  );
}
