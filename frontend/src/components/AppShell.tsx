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

const NAV_GROUPS = [
  {
    title: "Workspace",
    items: [
      { href: "/", label: "Cohort Overview", icon: LayoutDashboard },
      { href: "/student", label: "Student Inspector", icon: UserCheck },
      { href: "/what-if", label: "What-If Lab", icon: SlidersHorizontal },
    ],
  },
  {
    title: "Operations",
    items: [
      { href: "/batch", label: "Batch Triage", icon: FileSpreadsheet },
      { href: "/governance", label: "Governance & Fairness", icon: ShieldAlert },
    ],
  },
];

const ROUTE_TITLES: Record<string, string> = {
  "/": "Cohort Overview",
  "/student": "Student Inspector",
  "/what-if": "What-If Intervention Lab",
  "/batch": "Batch Triage & CSV Scoring",
  "/governance": "Model Governance & Fairness",
};

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

  const pageTitle = ROUTE_TITLES[pathname] || "RetainAI";

  const SidebarContent = () => (
    <div className="flex flex-col justify-between h-full">
      <div>
        <div className="h-14 px-5 flex items-center justify-between border-b border-border">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-md bg-blue-600 flex items-center justify-center text-white">
              <GraduationCap className="w-4 h-4" />
            </div>
            <div className="leading-tight">
              <span className="font-semibold text-sm tracking-tight block">RetainAI</span>
              <span className="text-[10px] text-muted-foreground block">INT395 • Retention</span>
            </div>
          </Link>
          <button
            onClick={() => setMobileOpen(false)}
            className="lg:hidden p-1 text-muted-foreground hover:text-foreground"
            aria-label="Close navigation"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <nav className="p-3 space-y-5" aria-label="Main navigation">
          {NAV_GROUPS.map((group) => (
            <div key={group.title} className="space-y-1">
              <div className="px-3 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/80">
                {group.title}
              </div>
              {group.items.map((item) => {
                const Icon = item.icon;
                const active = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setMobileOpen(false)}
                    className={`flex items-center gap-2.5 px-3 py-1.5 text-[13px] font-medium rounded-md transition-colors ${
                      active
                        ? "bg-blue-600/10 text-blue-600 dark:text-blue-400"
                        : "text-muted-foreground hover:text-foreground hover:bg-muted/60"
                    }`}
                  >
                    <Icon className={`w-4 h-4 ${active ? "text-blue-500" : "text-muted-foreground"}`} />
                    {item.label}
                  </Link>
                );
              })}
            </div>
          ))}
        </nav>
      </div>

      <div className="p-3 border-t border-border">
        <div className="p-3 rounded-lg bg-muted/40 border border-border text-[11px] space-y-1.5">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="font-medium">XGBoost ({tag === "early" ? "Sem 1" : "Full"})</span>
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
          </div>
          <div className="grid grid-cols-2 gap-2 pt-1 border-t border-border/70">
            <div>
              <span className="text-muted-foreground block text-[10px]">ROC-AUC</span>
              <span className="font-mono font-semibold text-foreground">
                {tag === "early" ? "0.893" : "0.915"}
              </span>
            </div>
            <div>
              <span className="text-muted-foreground block text-[10px]">Recall</span>
              <span className="font-mono font-semibold text-emerald-500">
                {tag === "early" ? "89.4%" : "86.6%"}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen flex bg-background text-foreground">
      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex w-56 border-r border-border bg-card/40 flex-col shrink-0 sticky top-0 h-screen">
        <SidebarContent />
      </aside>

      {/* Mobile Drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden flex">
          <div className="fixed inset-0 bg-black/50" onClick={() => setMobileOpen(false)} />
          <aside className="relative w-56 bg-card border-r border-border z-10 flex flex-col">
            <SidebarContent />
          </aside>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-14 px-4 sm:px-6 border-b border-border flex items-center justify-between bg-background/85 backdrop-blur sticky top-0 z-20">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileOpen(true)}
              className="lg:hidden p-1.5 rounded-md border border-border text-muted-foreground hover:text-foreground"
              aria-label="Open navigation"
            >
              <Menu className="w-4 h-4" />
            </button>
            <span className="text-sm font-semibold tracking-tight">{pageTitle}</span>
            <span className="hidden md:inline-block text-xs text-muted-foreground">
              • Holdout N=885
            </span>
          </div>

          <div className="flex items-center gap-2.5">
            <div className="flex items-center p-0.5 rounded-md bg-muted border border-border">
              <button
                onClick={() => setTag("early")}
                className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                  tag === "early"
                    ? "bg-background text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                Sem 1 Early
              </button>
              <button
                onClick={() => setTag("full")}
                className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                  tag === "full"
                    ? "bg-background text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                Full Curriculum
              </button>
            </div>

            <button
              onClick={toggleTheme}
              className="p-1.5 rounded-md border border-border bg-card hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
              aria-label="Toggle light or dark theme"
              title="Toggle light or dark theme"
            >
              {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>
          </div>
        </header>

        <main className="p-4 sm:p-6 max-w-[1360px] w-full mx-auto flex-1">{children}</main>
      </div>
    </div>
  );
}
