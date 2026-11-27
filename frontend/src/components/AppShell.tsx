"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  UserCheck,
  SlidersHorizontal,
  FileSpreadsheet,
  ShieldAlert,
  GraduationCap,
  Sun,
  Moon,
  Menu,
  X,
} from "lucide-react";
import { useStudent } from "@/context/StudentContext";

const NAV_ITEMS = [
  { href: "/", label: "Overview & Cohort", icon: LayoutDashboard },
  { href: "/student", label: "Student Deep Dive", icon: UserCheck },
  { href: "/what-if", label: "What-If Simulator", icon: SlidersHorizontal },
  { href: "/batch", label: "Batch Triage & Upload", icon: FileSpreadsheet },
  { href: "/governance", label: "Fairness & Governance", icon: ShieldAlert },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { tag, setTag } = useStudent();
  const [darkMode, setDarkMode] = useState(true);
  const [mobileOpen, setMobileOpen] = useState(false);

  const toggleTheme = () => {
    const next = !darkMode;
    setDarkMode(next);
    if (typeof document !== "undefined") {
      document.documentElement.classList.toggle("dark", next);
    }
  };

  const SidebarContent = () => (
    <div className="flex flex-col justify-between h-full">
      <div>
        <div className="h-16 px-6 flex items-center justify-between border-b border-border">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-sm">
              <GraduationCap className="w-4 h-4" />
            </div>
            <div>
              <span className="font-semibold text-sm tracking-tight block">RetainAI</span>
              <span className="text-[11px] text-muted-foreground block -mt-0.5">
                Retention Intelligence
              </span>
            </div>
          </div>
          <button
            onClick={() => setMobileOpen(false)}
            className="lg:hidden p-1 text-muted-foreground hover:text-foreground"
            aria-label="Close navigation"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <nav className="p-3 space-y-1" aria-label="Main navigation">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMobileOpen(false)}
                className={`flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                  active
                    ? "bg-blue-600/10 text-blue-600 dark:text-blue-400 border border-blue-500/20"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted/60 border border-transparent"
                }`}
              >
                <Icon className={`w-4 h-4 ${active ? "text-blue-500" : "text-muted-foreground"}`} />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="p-4 border-t border-border space-y-3">
        <div className="p-3 rounded-lg bg-muted/50 border border-border text-xs space-y-1.5">
          <div className="flex items-center justify-between text-muted-foreground font-medium">
            <span>Active Pipeline</span>
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
          </div>
          <p className="font-semibold text-foreground">
            {tag === "early" ? "Tuned XGBoost (Early)" : "Tuned XGBoost (Full)"}
          </p>
          <div className="flex items-center justify-between text-[11px] text-muted-foreground pt-1 border-t border-border">
            <span>Holdout ROC-AUC</span>
            <span className="text-blue-500 font-mono font-semibold">
              {tag === "early" ? "0.893" : "0.915"}
            </span>
          </div>
          <div className="flex items-center justify-between text-[11px] text-muted-foreground">
            <span>Dropout Recall</span>
            <span className="text-emerald-500 font-mono font-semibold">
              {tag === "early" ? "89.4%" : "86.6%"}
            </span>
          </div>
          <div className="flex items-center justify-between text-[11px] text-muted-foreground">
            <span>Cutoff (5:1 cost)</span>
            <span className="font-mono font-semibold">{tag === "early" ? "16%" : "18%"}</span>
          </div>
        </div>
        <div className="text-[11px] text-muted-foreground text-center">
          IPP Portalegre Dataset (CC BY 4.0)
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen flex bg-background text-foreground">
      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex w-64 border-r border-border bg-card/50 flex-col shrink-0">
        <SidebarContent />
      </aside>

      {/* Mobile Drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden flex">
          <div className="fixed inset-0 bg-black/50" onClick={() => setMobileOpen(false)} />
          <aside className="relative w-64 bg-card border-r border-border z-10 flex flex-col">
            <SidebarContent />
          </aside>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 px-4 sm:px-8 border-b border-border flex items-center justify-between bg-background/80 backdrop-blur sticky top-0 z-10">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileOpen(true)}
              className="lg:hidden p-2 rounded-md border border-border text-muted-foreground hover:text-foreground"
              aria-label="Open navigation"
            >
              <Menu className="w-4 h-4" />
            </button>

            <div className="flex items-center p-0.5 rounded-lg bg-muted border border-border">
              <button
                onClick={() => setTag("early")}
                className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
                  tag === "early"
                    ? "bg-blue-600 text-white shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                Semester 1 (Early)
              </button>
              <button
                onClick={() => setTag("full")}
                className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
                  tag === "full"
                    ? "bg-blue-600 text-white shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                Full Curriculum
              </button>
            </div>

            <span className="hidden md:inline-flex text-xs px-2.5 py-1 rounded-full font-medium bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
              Holdout Verified (N=885)
            </span>
          </div>

          <div className="flex items-center gap-3">
            <span className="hidden sm:inline text-xs text-muted-foreground font-medium">
              INT395 • Rishikesh Boppa
            </span>
            <button
              onClick={toggleTheme}
              className="p-2 rounded-md border border-border bg-card hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
              aria-label="Toggle light or dark theme"
              title="Toggle light or dark theme"
            >
              {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>
          </div>
        </header>

        <main className="p-4 sm:p-8 max-w-7xl w-full mx-auto flex-1">{children}</main>
      </div>
    </div>
  );
}
