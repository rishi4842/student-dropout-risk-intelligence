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
  PanelLeftClose,
  PanelLeftOpen,
} from "lucide-react";
import { useStudent } from "@/context/StudentContext";

const NAV_ITEMS = [
  { href: "/", label: "Cohort Overview", icon: LayoutDashboard },
  { href: "/student", label: "Risk Assessment", icon: UserCheck },
  { href: "/what-if", label: "What-If Lab", icon: SlidersHorizontal },
  { href: "/batch", label: "Batch Triage", icon: FileSpreadsheet },
  { href: "/governance", label: "Governance & Fairness", icon: ShieldAlert },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { tag, setTag } = useStudent();
  const [darkMode, setDarkMode] = useState(true);
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const toggleTheme = () => {
    const next = !darkMode;
    setDarkMode(next);
    if (typeof document !== "undefined") {
      document.documentElement.classList.toggle("dark", next);
    }
  };

  const SidebarContent = ({ isMobile = false }: { isMobile?: boolean }) => {
    const isMini = collapsed && !isMobile;
    return (
      <div className="flex flex-col justify-between h-full">
        <div>
          <div className="h-14 px-4 flex items-center justify-between border-b border-border">
            <Link href="/" className="flex items-center gap-2.5 min-w-0">
              <div className="w-7 h-7 rounded-md bg-blue-600 flex items-center justify-center text-white shrink-0">
                <GraduationCap className="w-4 h-4" />
              </div>
              {!isMini && (
                <div className="leading-tight truncate">
                  <span className="font-semibold text-sm tracking-tight block">
                    Retention Intelligence
                  </span>
                  <span className="text-[10px] text-muted-foreground block">
                    Student Success Analytics
                  </span>
                </div>
              )}
            </Link>

            {isMobile ? (
              <button
                onClick={() => setMobileOpen(false)}
                className="p-1 text-muted-foreground hover:text-foreground"
                aria-label="Close navigation"
              >
                <X className="w-4 h-4" />
              </button>
            ) : (
              <button
                onClick={() => setCollapsed(!collapsed)}
                className="p-1 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
                aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
                title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
              >
                {collapsed ? (
                  <PanelLeftOpen className="w-4 h-4" />
                ) : (
                  <PanelLeftClose className="w-4 h-4" />
                )}
              </button>
            )}
          </div>

          <nav className="p-2.5 space-y-1" aria-label="Main navigation">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  title={isMini ? item.label : undefined}
                  onClick={() => setMobileOpen(false)}
                  className={`flex items-center ${
                    isMini ? "justify-center px-2" : "gap-2.5 px-3"
                  } py-2 text-[13px] font-medium rounded-md transition-colors ${
                    active
                      ? "bg-blue-600/10 text-blue-600 dark:text-blue-400"
                      : "text-muted-foreground hover:text-foreground hover:bg-muted/60"
                  }`}
                >
                  <Icon
                    className={`w-4 h-4 shrink-0 ${
                      active ? "text-blue-500" : "text-muted-foreground"
                    }`}
                  />
                  {!isMini && <span className="truncate">{item.label}</span>}
                </Link>
              );
            })}
          </nav>
        </div>

        {!isMini && (
          <div className="p-3 border-t border-border">
            <div className="text-[11px] space-y-1.5">
              <div className="flex items-center justify-between text-muted-foreground font-medium">
                <span>Model Information</span>
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Holdout cohort</span>
                <span className="font-mono">885</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">ROC-AUC</span>
                <span className="font-mono">{tag === "early" ? "0.893" : "0.915"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Recall</span>
                <span className="font-mono">{tag === "early" ? "89.4%" : "86.6%"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Threshold</span>
                <span className="font-mono">{tag === "early" ? "16%" : "18%"}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen flex bg-background text-foreground">
      {/* Desktop Collapsible Sidebar */}
      <aside
        className={`hidden lg:flex ${
          collapsed ? "w-16" : "w-[248px]"
        } border-r border-border bg-card/30 flex-col shrink-0 sticky top-0 h-screen transition-all duration-200`}
      >
        <SidebarContent />
      </aside>

      {/* Mobile Drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden flex">
          <div className="fixed inset-0 bg-black/50" onClick={() => setMobileOpen(false)} />
          <aside className="relative w-[248px] bg-card border-r border-border z-10 flex flex-col">
            <SidebarContent isMobile />
          </aside>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-14 px-4 sm:px-6 border-b border-border flex items-center justify-between bg-background/90 backdrop-blur sticky top-0 z-20">
          <div className="flex items-center gap-3 min-w-0">
            <button
              onClick={() => setMobileOpen(true)}
              className="lg:hidden p-1.5 rounded-md border border-border text-muted-foreground hover:text-foreground"
              aria-label="Open navigation"
            >
              <Menu className="w-4 h-4" />
            </button>
            <div className="flex items-center gap-2 truncate">
              <span className="text-sm font-semibold tracking-tight truncate">
                Student Retention & Early-Warning Intelligence
              </span>
              <span className="hidden md:inline-block text-[11px] px-2 py-0.5 rounded bg-blue-500/10 text-blue-500 font-medium">
                {tag === "early" ? "Early Warning" : "Full Curriculum"}
              </span>
              <span className="hidden xl:inline-block text-[11px] px-2 py-0.5 rounded bg-muted text-muted-foreground">
                Supervised Learning
              </span>
              <span className="hidden xl:inline-block text-[11px] px-2 py-0.5 rounded bg-muted text-muted-foreground font-mono">
                Model v1.0
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <div className="hidden sm:flex items-center p-0.5 rounded-md bg-muted border border-border">
              <button
                onClick={() => setTag("early")}
                className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                  tag === "early"
                    ? "bg-background text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                Early Warning
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

            <span className="hidden md:inline-flex items-center gap-1.5 text-xs text-muted-foreground">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              Model Status: Active
            </span>

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

        <main className="p-4 sm:p-6 max-w-[1440px] w-full mx-auto flex-1">{children}</main>
      </div>
    </div>
  );
}
