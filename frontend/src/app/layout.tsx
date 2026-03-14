import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/sidebar";
import { Toaster } from "@/components/ui/sonner";
import Link from "next/link";
import { LayoutDashboard, Play, FileText, ShieldCheck, Clock } from "lucide-react";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AI Operations Automation",
  description:
    "AI-powered operational automation platform for business reporting",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-zinc-950 text-zinc-100 antialiased`}>
        <div className="hidden md:block">
          <Sidebar />
        </div>
        <main className="md:ml-64 min-h-screen p-4 md:p-6 pb-24 md:pb-6">{children}</main>
        
        {/* Mobile Bottom Navigation */}
        <div className="md:hidden fixed bottom-0 left-0 right-0 z-50 flex items-center justify-around bg-zinc-950 border-t border-white/10 px-2 py-3 pb-safe">
          <Link href="/" className="flex flex-col items-center gap-1 text-zinc-400 hover:text-violet-400">
            <LayoutDashboard className="h-5 w-5" />
            <span className="text-[10px]">Home</span>
          </Link>
          <Link href="/runs" className="flex flex-col items-center gap-1 text-zinc-400 hover:text-violet-400">
            <Play className="h-5 w-5" />
            <span className="text-[10px]">Runs</span>
          </Link>
          <Link href="/reports" className="flex flex-col items-center gap-1 text-zinc-400 hover:text-violet-400">
            <FileText className="h-5 w-5" />
            <span className="text-[10px]">Reports</span>
          </Link>
          <Link href="/approvals" className="flex flex-col items-center gap-1 text-zinc-400 hover:text-violet-400">
            <ShieldCheck className="h-5 w-5" />
            <span className="text-[10px]">Approvals</span>
          </Link>
          <Link href="/schedules" className="flex flex-col items-center gap-1 text-zinc-400 hover:text-violet-400">
            <Clock className="h-5 w-5" />
            <span className="text-[10px]">Schedules</span>
          </Link>
        </div>

        <Toaster theme="dark" position="bottom-right" />
      </body>
    </html>
  );
}
