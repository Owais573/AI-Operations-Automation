import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/sidebar";
import { Toaster } from "@/components/ui/sonner";
import Link from "next/link";
import { LayoutDashboard, Play, FileText, ShieldCheck, Clock } from "lucide-react";
import { ThemeProvider } from "@/components/theme-provider";

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
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.className} antialiased`}>
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem
          disableTransitionOnChange
        >
          <div className="flex bg-background text-foreground transitioning-colors duration-500">
            <div className="hidden md:block">
              <Sidebar />
            </div>
            <main className="flex-1 md:ml-64 min-h-screen p-4 md:p-6 pb-24 md:pb-6">
              {children}
            </main>
            
            {/* Mobile Bottom Navigation */}
            <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 flex items-center justify-around bg-card/80 backdrop-blur-md border-t border-border px-2 py-3 pb-safe">
              <Link href="/" className="flex flex-col items-center gap-1 text-muted-foreground hover:text-primary transition-all duration-300">
                <LayoutDashboard className="h-5 w-5" />
                <span className="text-[10px] font-medium">Home</span>
              </Link>
              <Link href="/runs" className="flex flex-col items-center gap-1 text-muted-foreground hover:text-primary transition-all duration-300">
                <Play className="h-5 w-5" />
                <span className="text-[10px] font-medium">Runs</span>
              </Link>
              <Link href="/reports" className="flex flex-col items-center gap-1 text-muted-foreground hover:text-primary transition-all duration-300">
                <FileText className="h-5 w-5" />
                <span className="text-[10px] font-medium">Reports</span>
              </Link>
              <Link href="/approvals" className="flex flex-col items-center gap-1 text-muted-foreground hover:text-primary transition-all duration-300">
                <ShieldCheck className="h-5 w-5" />
                <span className="text-[10px] font-medium">Approvals</span>
              </Link>
              <Link href="/schedules" className="flex flex-col items-center gap-1 text-muted-foreground hover:text-primary transition-all duration-300">
                <Clock className="h-5 w-5" />
                <span className="text-[10px] font-medium">Schedules</span>
              </Link>
            </nav>
          </div>

          <Toaster position="bottom-right" richColors />
        </ThemeProvider>
      </body>
    </html>
  );
}
