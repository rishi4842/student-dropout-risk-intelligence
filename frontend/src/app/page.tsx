"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { ArrowRight, Search } from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { fetchOverview, OverviewResponse } from "@/lib/api";
import { formatPercent } from "@/lib/utils";
import { useStudent } from "@/context/StudentContext";

export default function OverviewPage() {
  const router = useRouter();
  const { tag, selectStudentFromOverview } = useStudent();
  const [overview, setOverview] = useState<OverviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [tierFilter, setTierFilter] = useState<"All" | "High" | "Medium" | "Low">("All");

  useEffect(() => {
    setLoading(true);
    fetchOverview(tag)
      .then((data) => {
        setOverview(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Overview fetch error:", err);
        setLoading(false);
      });
  }, [tag]);

  if (loading || !overview) {
    return (
      <div className="flex items-center justify-center min-h-[420px]">
        <div className="w-7 h-7 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const filteredStudents = overview.priority_students.filter((s) => {
    const matchesTier = tierFilter === "All" || s.tier === tierFilter;
    const matchesSearch =
      searchTerm === "" ||
      s.course.toLowerCase().includes(searchTerm.toLowerCase()) ||
      String(s.id).includes(searchTerm);
    return matchesTier && matchesSearch;
  });

  const handleInspect = (student: OverviewResponse["priority_students"][0]) => {
    selectStudentFromOverview(student.values, `${student.actual_outcome} (Holdout ID #${student.id})`);
    router.push("/student");
  };

  const total = overview.n_test || 1;
  const highPct = (overview.tier_counts.High / total) * 100;
  const medPct = (overview.tier_counts.Medium / total) * 100;
  const lowPct = (overview.tier_counts.Low / total) * 100;

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className="space-y-6"
    >
      {/* Unified KPI Strip */}
      <div className="grid grid-cols-2 lg:grid-cols-4 divide-y lg:divide-y-0 lg:divide-x divide-border rounded-xl bg-card border border-border">
        <div className="p-4 sm:p-5">
          <span className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
            Holdout Cohort
          </span>
          <div className="text-2xl font-bold font-mono mt-1">{overview.n_test}</div>
          <span className="text-[11px] text-muted-foreground">Single-pass test students</span>
        </div>
        <div className="p-4 sm:p-5">
          <span className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
            Dropout ROC-AUC
          </span>
          <div className="text-2xl font-bold font-mono mt-1">{overview.roc_auc.toFixed(3)}</div>
          <span className="text-[11px] text-muted-foreground">
            {tag === "early" ? "Semester 1 only" : "Full curriculum"}
          </span>
        </div>
        <div className="p-4 sm:p-5">
          <span className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
            Dropout Recall
          </span>
          <div className="text-2xl font-bold font-mono mt-1 text-emerald-500">
            {formatPercent(overview.recall)}
          </div>
          <span className="text-[11px] text-muted-foreground">
            At {formatPercent(overview.threshold)} cutoff
          </span>
        </div>
        <div className="p-4 sm:p-5">
          <span className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
            Cost Reduction
          </span>
          <div className="text-2xl font-bold font-mono mt-1 text-blue-500">
            {overview.cost_reduction_nobody}
          </div>
          <span className="text-[11px] text-muted-foreground">
            vs nobody ({overview.cost_reduction_all} vs all)
          </span>
        </div>
      </div>

      {/* 12-Col Bento Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-8 p-5 rounded-xl bg-card border border-border space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold">Risk Score Distribution</h2>
              <p className="text-xs text-muted-foreground">
                Calibrated dropout probabilities across {overview.n_test} holdout students
              </p>
            </div>
            <div className="flex items-center gap-3 text-[11px]">
              <span className="flex items-center gap-1 text-emerald-500">
                <span className="w-2 h-2 rounded-full bg-emerald-500" /> Low
              </span>
              <span className="flex items-center gap-1 text-amber-500">
                <span className="w-2 h-2 rounded-full bg-amber-500" /> Medium
              </span>
              <span className="flex items-center gap-1 text-red-500">
                <span className="w-2 h-2 rounded-full bg-red-500" /> High
              </span>
            </div>
          </div>

          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={overview.risk_distribution} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
                <XAxis dataKey="bucket" stroke="#94A3B8" fontSize={11} />
                <YAxis stroke="#94A3B8" fontSize={11} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#0F172A",
                    borderColor: "#334155",
                    borderRadius: "8px",
                    fontSize: "12px",
                    color: "#F8FAFC",
                  }}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {overview.risk_distribution.map((entry, idx) => (
                    <Cell
                      key={`bin-${idx}`}
                      fill={
                        entry.zone === "High"
                          ? "#EF4444"
                          : entry.zone === "Medium"
                          ? "#F59E0B"
                          : "#10B981"
                      }
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="lg:col-span-4 p-5 rounded-xl bg-card border border-border flex flex-col justify-between space-y-4">
          <div>
            <h2 className="text-sm font-semibold">Triage Tier Breakdown</h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              Cohort split under 5:1 cost threshold
            </p>
            {/* Proportional stacked bar */}
            <div className="h-2.5 w-full rounded-full overflow-hidden flex mt-4 bg-muted">
              <div className="bg-red-500 h-full" style={{ width: `${highPct}%` }} />
              <div className="bg-amber-500 h-full" style={{ width: `${medPct}%` }} />
              <div className="bg-emerald-500 h-full" style={{ width: `${lowPct}%` }} />
            </div>
          </div>

          <div className="space-y-2.5 text-xs">
            <div className="flex items-center justify-between p-2.5 rounded-lg bg-muted/40 border border-border">
              <div>
                <span className="font-semibold text-red-500 block">High Risk (≥ 50%)</span>
                <span className="text-[11px] text-muted-foreground">1-on-1 outreach within 7d</span>
              </div>
              <span className="font-mono font-semibold">{overview.tier_counts.High}</span>
            </div>

            <div className="flex items-center justify-between p-2.5 rounded-lg bg-muted/40 border border-border">
              <div>
                <span className="font-semibold text-amber-500 block">
                  Medium ({formatPercent(overview.threshold)}–50%)
                </span>
                <span className="text-[11px] text-muted-foreground">Tutoring & monthly check</span>
              </div>
              <span className="font-mono font-semibold">{overview.tier_counts.Medium}</span>
            </div>

            <div className="flex items-center justify-between p-2.5 rounded-lg bg-muted/40 border border-border">
              <div>
                <span className="font-semibold text-emerald-500 block">
                  Low (&lt; {formatPercent(overview.threshold)})
                </span>
                <span className="text-[11px] text-muted-foreground">Standard advising</span>
              </div>
              <span className="font-mono font-semibold">{overview.tier_counts.Low}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Priority Queue Table */}
      <div className="rounded-xl bg-card border border-border overflow-hidden">
        <div className="p-4 sm:px-5 border-b border-border flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-sm font-semibold">Priority Holdout Student Queue</h2>
            <p className="text-xs text-muted-foreground">
              Click Inspect to load any student into the interactive inspector
            </p>
          </div>
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-muted-foreground absolute left-2.5 top-2" />
              <input
                type="text"
                placeholder="Search ID or course..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-8 pr-3 py-1 text-xs rounded-md bg-background border border-border focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
            <select
              value={tierFilter}
              onChange={(e) => setTierFilter(e.target.value as any)}
              className="px-2.5 py-1 text-xs rounded-md bg-background border border-border focus:outline-none focus:ring-1 focus:ring-blue-500"
              aria-label="Filter by risk tier"
            >
              <option value="All">All Tiers</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-border text-muted-foreground bg-muted/30">
                <th className="py-2.5 px-4 font-medium">ID</th>
                <th className="py-2.5 px-4 font-medium">Degree Programme</th>
                <th className="py-2.5 px-4 font-medium">Sem 1 Units & Grade</th>
                <th className="py-2.5 px-4 font-medium">Tuition</th>
                <th className="py-2.5 px-4 font-medium">Risk</th>
                <th className="py-2.5 px-4 font-medium">Tier</th>
                <th className="py-2.5 px-4 font-medium text-right">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filteredStudents.map((s) => (
                <tr key={s.id} className="hover:bg-muted/30 transition-colors">
                  <td className="py-2.5 px-4 font-mono">#{s.id}</td>
                  <td className="py-2.5 px-4 font-medium">{s.course}</td>
                  <td className="py-2.5 px-4 text-muted-foreground">
                    {s.approved}/{s.enrolled} passed • {s.grade.toFixed(1)}/20
                  </td>
                  <td className="py-2.5 px-4">
                    <span className={s.tuition ? "text-emerald-500" : "text-red-500 font-medium"}>
                      {s.tuition ? "Paid" : "Overdue"}
                    </span>
                  </td>
                  <td className="py-2.5 px-4 font-mono font-semibold">{formatPercent(s.risk)}</td>
                  <td className="py-2.5 px-4">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${
                        s.tier === "High"
                          ? "bg-red-500/10 text-red-500 border-red-500/30"
                          : s.tier === "Medium"
                          ? "bg-amber-500/10 text-amber-500 border-amber-500/30"
                          : "bg-emerald-500/10 text-emerald-500 border-emerald-500/30"
                      }`}
                    >
                      {s.tier.toUpperCase()}
                    </span>
                  </td>
                  <td className="py-2.5 px-4 text-right">
                    <button
                      onClick={() => handleInspect(s)}
                      className="inline-flex items-center gap-1 text-blue-500 hover:text-blue-400 font-medium"
                    >
                      Open <ArrowRight className="w-3 h-3" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </motion.div>
  );
}
