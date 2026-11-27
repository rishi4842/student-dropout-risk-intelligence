"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  CheckCircle2,
  TrendingDown,
  Users,
  ShieldCheck,
  ArrowRight,
  Search,
} from "lucide-react";
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
        <div className="text-center space-y-3">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs text-muted-foreground">Loading holdout cohort analytics...</p>
        </div>
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

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="space-y-8"
    >
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Cohort Retention Overview</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Real holdout test cohort analytics ({overview.n_test} students) and prioritized advisor outreach queue.
          </p>
        </div>
        <span className="text-xs font-mono text-muted-foreground">
          Pipeline: {tag === "early" ? "Semester 1 Early-Warning" : "Full Curriculum (Sem 1 & 2)"}
        </span>
      </div>

      {/* Top KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-xl bg-card border border-border space-y-2">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs font-medium uppercase tracking-wider">Holdout Cohort</span>
            <Users className="w-4 h-4 text-blue-500" />
          </div>
          <div className="text-2xl font-bold font-mono">{overview.n_test}</div>
          <p className="text-xs text-muted-foreground">Unseen students evaluated strictly once</p>
        </div>

        <div className="p-5 rounded-xl bg-card border border-border space-y-2">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs font-medium uppercase tracking-wider">Dropout ROC-AUC</span>
            <ShieldCheck className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="text-2xl font-bold font-mono">{overview.roc_auc.toFixed(3)}</div>
          <p className="text-xs text-muted-foreground">
            {tag === "early" ? "Semester 1 data only (vs 0.915 Full)" : "All 36 curriculum features"}
          </p>
        </div>

        <div className="p-5 rounded-xl bg-card border border-border space-y-2">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs font-medium uppercase tracking-wider">Dropout Recall</span>
            <CheckCircle2 className="w-4 h-4 text-blue-500" />
          </div>
          <div className="text-2xl font-bold font-mono">{formatPercent(overview.recall)}</div>
          <p className="text-xs text-muted-foreground">
            At {formatPercent(overview.threshold)} cost-optimal cutoff
          </p>
        </div>

        <div className="p-5 rounded-xl bg-card border border-border space-y-2">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs font-medium uppercase tracking-wider">Cost Reduction</span>
            <TrendingDown className="w-4 h-4 text-violet-500" />
          </div>
          <div className="text-2xl font-bold font-mono">{overview.cost_reduction_nobody}</div>
          <p className="text-xs text-muted-foreground">
            vs Flag Nobody ({overview.cost_reduction_all} vs Flag All)
          </p>
        </div>
      </div>

      {/* Middle Row: Risk Distribution Histogram + Triage Policy */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="p-6 rounded-xl bg-card border border-border space-y-4 lg:col-span-2">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h2 className="text-base font-semibold">Cohort Risk Score Distribution</h2>
              <p className="text-xs text-muted-foreground">
                Calibrated dropout probabilities across all {overview.n_test} holdout students
              </p>
            </div>
            <div className="flex items-center gap-3 text-xs">
              <span className="flex items-center gap-1.5 text-emerald-500">
                <span className="w-2.5 h-2.5 rounded-sm bg-emerald-500" /> Low
              </span>
              <span className="flex items-center gap-1.5 text-amber-500">
                <span className="w-2.5 h-2.5 rounded-sm bg-amber-500" /> Medium
              </span>
              <span className="flex items-center gap-1.5 text-red-500">
                <span className="w-2.5 h-2.5 rounded-sm bg-red-500" /> High
              </span>
            </div>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={overview.risk_distribution} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
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

        <div className="p-6 rounded-xl bg-card border border-border space-y-4">
          <div>
            <h2 className="text-base font-semibold">Operational Triage Tiers</h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              Three-tier protocol prevents mentor alert fatigue
            </p>
          </div>

          <div className="space-y-3">
            <div className="p-3.5 rounded-lg border border-red-500/20 bg-red-500/5 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-red-500 uppercase tracking-wider">
                  High Risk (P ≥ 50%)
                </span>
                <span className="text-xs font-mono text-red-400">
                  {overview.tier_counts.High} students
                </span>
              </div>
              <p className="text-xs text-muted-foreground">
                Priority 1-on-1 advisor outreach within 7 days.
              </p>
            </div>

            <div className="p-3.5 rounded-lg border border-amber-500/20 bg-amber-500/5 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-amber-500 uppercase tracking-wider">
                  Medium Risk ({formatPercent(overview.threshold)}–50%)
                </span>
                <span className="text-xs font-mono text-amber-400">
                  {overview.tier_counts.Medium} students
                </span>
              </div>
              <p className="text-xs text-muted-foreground">
                Automated check-ins, tutoring, and monthly review.
              </p>
            </div>

            <div className="p-3.5 rounded-lg border border-emerald-500/20 bg-emerald-500/5 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-emerald-500 uppercase tracking-wider">
                  Low Risk (P &lt; {formatPercent(overview.threshold)})
                </span>
                <span className="text-xs font-mono text-emerald-400">
                  {overview.tier_counts.Low} students
                </span>
              </div>
              <p className="text-xs text-muted-foreground">
                Standard advising schedule.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Priority Student Queue Table */}
      <div className="p-6 rounded-xl bg-card border border-border space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-base font-semibold">Priority Holdout Student Queue</h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              Real holdout cohort records ranked by calibrated dropout risk. Click Inspect to open in Student Deep Dive.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-muted-foreground absolute left-2.5 top-2.5" />
              <input
                type="text"
                placeholder="Search ID or course..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-8 pr-3 py-1.5 text-xs rounded-md bg-background border border-border focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>

            <select
              value={tierFilter}
              onChange={(e) => setTierFilter(e.target.value as any)}
              className="px-2.5 py-1.5 text-xs rounded-md bg-background border border-border focus:outline-none focus:ring-1 focus:ring-blue-500"
              aria-label="Filter by risk tier"
            >
              <option value="All">All Tiers</option>
              <option value="High">High Risk</option>
              <option value="Medium">Medium Risk</option>
              <option value="Low">Low Risk</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-border text-muted-foreground font-medium">
                <th className="py-2.5 px-3">Student ID</th>
                <th className="py-2.5 px-3">Degree Programme</th>
                <th className="py-2.5 px-3">Sem 1 Performance</th>
                <th className="py-2.5 px-3">Tuition</th>
                <th className="py-2.5 px-3">Risk Score</th>
                <th className="py-2.5 px-3">Tier</th>
                <th className="py-2.5 px-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filteredStudents.map((s) => (
                <tr key={s.id} className="hover:bg-muted/40 transition-colors">
                  <td className="py-3 px-3 font-mono font-medium">#{s.id}</td>
                  <td className="py-3 px-3">{s.course}</td>
                  <td className="py-3 px-3 text-muted-foreground">
                    {s.approved}/{s.enrolled} approved • {s.grade.toFixed(1)}/20
                  </td>
                  <td className="py-3 px-3">
                    {s.tuition ? (
                      <span className="text-emerald-500 font-medium">Paid</span>
                    ) : (
                      <span className="text-red-500 font-medium">Overdue</span>
                    )}
                  </td>
                  <td className="py-3 px-3 font-mono font-semibold">{formatPercent(s.risk)}</td>
                  <td className="py-3 px-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-semibold tracking-wider border ${
                        s.tier === "High"
                          ? "bg-red-500/10 text-red-500 border-red-500/30"
                          : s.tier === "Medium"
                          ? "bg-amber-500/10 text-amber-500 border-amber-500/30"
                          : "bg-emerald-500/10 text-emerald-500 border-emerald-500/30"
                      }`}
                    >
                      {s.tier.toUpperCase()} RISK
                    </span>
                  </td>
                  <td className="py-3 px-3 text-right">
                    <button
                      onClick={() => handleInspect(s)}
                      className="inline-flex items-center gap-1 text-xs text-blue-500 hover:text-blue-400 font-medium"
                    >
                      Inspect <ArrowRight className="w-3 h-3" />
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
