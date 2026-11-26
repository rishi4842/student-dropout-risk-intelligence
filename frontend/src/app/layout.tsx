import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";
import { 
  LayoutDashboard, 
  UserCheck, 
  SlidersHorizontal, 
  FileSpreadsheet, 
  ShieldAlert,
  GraduationCap
} from "lucide-react";

export const metadata: Metadata = {
  title: "RetainAI • Higher Education Student Retention Intelligence",
  description: "Interpretable early-warning machine learning system for higher education student retention",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="font-sans min-h-screen flex bg-[#0B0F17] text-slate-100 antialiased">
        {/* Sidebar */}
        <aside className="w-64 border-r border-slate-800/80 bg-[#070B12] flex flex-col justify-between shrink-0">
          <div>
            {/* Brand Logo */}
            <div className="h-16 px-6 flex items-center gap-3 border-b border-slate-800/80">
              <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-sm shadow-blue-500/20">
                <GraduationCap className="w-5 h-5" />
              </div>
              <div>
                <span className="font-semibold text-sm tracking-tight text-white block">RetainAI</span>
                <span className="text-[11px] text-slate-400 block -mt-0.5">Retention SaaS • INT395</span>
              </div>
            </div>

            {/* Navigation Links */}
            <nav className="p-4 space-y-1">
              <Link 
                href="/" 
                className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md text-slate-300 hover:text-white hover:bg-slate-800/60 transition-colors"
              >
                <LayoutDashboard className="w-4 h-4 text-slate-400" />
                Overview & Cohort
              </Link>

              <Link 
                href="/student" 
                className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md text-slate-300 hover:text-white hover:bg-slate-800/60 transition-colors"
              >
                <UserCheck className="w-4 h-4 text-slate-400" />
                Student Deep Dive
              </Link>

              <Link 
                href="/what-if" 
                className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md text-slate-300 hover:text-white hover:bg-slate-800/60 transition-colors"
              >
                <SlidersHorizontal className="w-4 h-4 text-slate-400" />
                What-If Simulator
              </Link>

              <Link 
                href="/batch" 
                className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md text-slate-300 hover:text-white hover:bg-slate-800/60 transition-colors"
              >
                <FileSpreadsheet className="w-4 h-4 text-slate-400" />
                Batch Triage & Upload
              </Link>

              <Link 
                href="/governance" 
                className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md text-slate-300 hover:text-white hover:bg-slate-800/60 transition-colors"
              >
                <ShieldAlert className="w-4 h-4 text-slate-400" />
                Fairness & Governance
              </Link>
            </nav>
          </div>

          {/* Model Status Card in Sidebar Footer */}
          <div className="p-4 border-t border-slate-800/80">
            <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 text-xs space-y-1.5">
              <div className="flex items-center justify-between text-slate-400 font-medium">
                <span>Production Model</span>
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              </div>
              <p className="text-slate-200 font-semibold">Tuned XGBoost (Early)</p>
              <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1 border-t border-slate-800/60">
                <span>Holdout ROC-AUC</span>
                <span className="text-blue-400 font-mono">0.893</span>
              </div>
              <div className="flex items-center justify-between text-[11px] text-slate-400">
                <span>Dropout Recall</span>
                <span className="text-emerald-400 font-mono">89.4%</span>
              </div>
              <div className="flex items-center justify-between text-[11px] text-slate-400">
                <span>Cost Reduction</span>
                <span className="text-blue-400 font-mono">77.2%</span>
              </div>
            </div>
            <div className="mt-3 text-[11px] text-slate-500 text-center">
              IPP Portalegre Dataset (CC BY 4.0)
            </div>
          </div>
        </aside>

        {/* Main Content Viewport */}
        <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
          {/* Header */}
          <header className="h-16 px-8 border-b border-slate-800/80 flex items-center justify-between bg-[#0B0F17]/80 backdrop-blur sticky top-0 z-10">
            <div className="flex items-center gap-3">
              <span className="text-xs px-2.5 py-1 rounded-full font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">
                5:1 Cost-Optimal Cutoff (t = 0.16)
              </span>
              <span className="text-xs px-2.5 py-1 rounded-full font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Test Cohort Verified (N=885)
              </span>
              <span className="text-xs px-2.5 py-1 rounded-full font-medium bg-slate-800 text-slate-300 border border-slate-700">
                Decision Support Only
              </span>
            </div>
            <div className="flex items-center gap-4 text-xs text-slate-400 font-medium">
              <span>Author: Rishikesh Boppa</span>
              <span>•</span>
              <span>Lovely Professional University</span>
            </div>
          </header>

          {/* Page Body */}
          <main className="p-8 max-w-7xl w-full mx-auto">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
