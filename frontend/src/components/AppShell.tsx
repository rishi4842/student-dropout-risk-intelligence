"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  GraduationCap,
  Sun,
  Moon,
  Menu,
  X,
} from "lucide-react";

const NAV_ITEMS = [
  { href: "/student", label: "Risk Assessment" },
  { href: "/", label: "Cohort Overview" },
  { href: "/what-if", label: "What-If Lab" },
  { href: "/batch", label: "Batch Triage" },
  { href: "/governance", label: "Governance" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [darkMode, setDarkMode] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const toggleTheme = () => {
    const next = !darkMode;
    setDarkMode(next);
    if (typeof document !== "undefined") {
      document.documentElement.classList.toggle("dark", next);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground">
      {/* Sticky Top Navigation Shell (No Left Sidebar) */}
      <header className="sticky top-0 z-30 border-b border-border bg-card/95 backdrop-blur">
        <div className="max-w-[1440px] mx-auto px-4 sm:px-8 h-16 flex items-center justify-between gap-4">
          {/* Left: Brand */}
          <Link href="/student" className="flex items-center gap-2.5 shrink-0">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white">
              <GraduationCap className="w-4 h-4" />
            </div>
            <div className="leading-tight">
              <span className="font-semibold text-sm tracking-tight block">
                Retention Intelligence
              </span>
              <span className="text-[11px] text-muted-foreground block">
                Student Success Analytics
              </span>
            </div>
          </Link>

          {/* Center: Horizontal Navigation */}
          <nav className="hidden md:flex items-center gap-6 h-full" aria-label="Main navigation">
            {NAV_ITEMS.map((item) => {
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`h-full inline-flex items-center text-[13px] font-medium border-b-2 transition-colors ${
                    active
                      ? "border-blue-600 text-foreground"
                      : "border-transparent text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>

          {/* Right: Subtle Model Status & Theme Toggle */}
          <div className="flex items-center gap-3 shrink-0">
            <div className="hidden lg:block text-right text-xs leading-tight">
              <span className="inline-flex items-center gap-1.5 font-medium text-foreground">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-600" />
                Model Active
              </span>
              <span className="block text-[11px] text-muted-foreground">
                Holdout: 885 students
              </span>
            </div>

            <button
              onClick={toggleTheme}
              className="p-2 rounded-md border border-border bg-background hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
              aria-label="Toggle light or dark theme"
              title="Toggle light or dark theme"
            >
              {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>

            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="md:hidden p-2 rounded-md border border-border text-muted-foreground hover:text-foreground"
              aria-label="Toggle navigation menu"
            >
              {mobileOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {/* Mobile Top Dropdown Menu */}
        {mobileOpen && (
          <nav className="md:hidden border-t border-border bg-card px-4 py-3 space-y-1" aria-label="Mobile navigation">
            {NAV_ITEMS.map((item) => {
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileOpen(false)}
                  className={`block px-3 py-2 rounded-md text-sm font-medium ${
                    active
                      ? "bg-blue-600/10 text-blue-600"
                      : "text-muted-foreground hover:text-foreground hover:bg-muted"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        )}
      </header>

      {/* Full-Width Centered Canvas */}
      <main className="flex-1 w-full max-w-[1440px] mx-auto px-4 sm:px-8 py-8">
        {children}
      </main>
    </div>
  );
}
