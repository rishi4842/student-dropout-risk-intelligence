"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { 
  AlertTriangle, 
  CheckCircle2, 
  TrendingDown, 
  Users, 
  ShieldCheck, 
  ArrowRight,
  Search,
  Filter
} from "lucide-react";
import { fetchGovernance, uploadBatchFile } from "@/lib/api";
import { formatPercent } from "@/lib/utils";

export default function OverviewPage() {
  const [govData, setGovData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Sample priority students from benchmark test cohort
  const priorityStudents = [
    { id: 1042, course: "Management", age: 28, enrolled: 6, approved: 0, grade: 0.0, tuition: false, debt: true, risk: 0.908, tier: "High" },
    { id: 2185, course: "Informatics Engineering", age: 25, enrolled: 6, approved: 1, grade: 10.2, tuition: false, debt: false, risk: 0.742, tier: "High" },
    { id: 3319, course: "Social Service", age: 23, enrolled: 6, approved: 2, grade: 11.0, tuition: true, debt: true, risk: 0.584, tier: "High" },
    { id: 1408, course: "Tourism", age: 24, enrolled: 6, approved: 3, grade: 11.4, tuition: true, debt: false, risk: 0.321, tier: "Medium" },
    { id: 4091, course: "Agronomy", age: 21, enrolled: 6, approved: 4, grade: 12.0, tuition: true, debt: false, risk: 0.195, tier: "Medium" },
    { id: 2874, course: "Nursing", age: 19, enrolled: 6, approved: 6, grade: 16.2, tuition: true, debt: false, risk: 0.024, tier: "Low" }
  ];

  useEffect(() => {
    fetchGovernance()
      .then((data) => {
        setGovData(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Governance fetch error:", err);
        setLoading(false);
      });
  }, []);

  return (
    <div className="space-y-8">
      {/* Title & Description */}
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-white">Cohort Retention Overview</h1>
        <p className="text-sm text-slate-400 mt-1">
          Real-time institutional early-warning analytics and prioritized advisor triage queue.
        </p>
      </div>

      {/* Top Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider">Test Cohort</span>
            <Users className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold tracking-tight text-white">885</div>
          <p className="text-xs text-slate-400">Students in single-pass holdout validation</p>
        </div>

        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider">Early ROC-AUC</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold tracking-tight text-white">0.893</div>
          <p className="text-xs text-slate-400">Predictable after Semester 1 alone (vs 0.915 Full)</p>
        </div>

        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider">Dropout Recall</span>
            <CheckCircle2 className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold tracking-tight text-white">89.4%</div>
          <p className="text-xs text-slate-400">254 of 284 departing students identified early</p>
        </div>

        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider">Cost Reduction</span>
            <TrendingDown className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold tracking-tight text-white">77.2%</div>
          <p className="text-xs text-slate-400">vs Flag Nobody (and ~46% vs Flag All)</p>
        </div>
      </div>

      {/* Middle Section: Triage Strategy & Cohort Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Triage Tiers Breakdown */}
        <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4 lg:col-span-1">
          <div>
            <h2 className="text-base font-semibold text-white">Operational Triage Policy</h2>
            <p className="text-xs text-slate-400 mt-0.5">Three-tier protocol prevents faculty alert fatigue</p>
          </div>

          <div className="space-y-3">
            <div className="p-3.5 rounded-lg border border-red-500/20 bg-red-500/5 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-red-400 uppercase tracking-wider">High Risk (P ≥ 50%)</span>
                <span className="text-xs font-mono text-red-300">~25.6% Cohort</span>
              </div>
              <p className="text-xs text-slate-300">
                Mandatory 1-on-1 advisor outreach within 7 days. Focus on bursar hardship & remedial tracks.
              </p>
            </div>

            <div className="p-3.5 rounded-lg border border-amber-500/20 bg-amber-500/5 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-amber-400 uppercase tracking-wider">Medium Risk (16% ≤ P &lt; 50%)</span>
                <span className="text-xs font-mono text-amber-300">~22.7% Cohort</span>
              </div>
              <p className="text-xs text-slate-300">
                Light-touch support: automated progress nudges, peer study groups, and monthly check-in.
              </p>
            </div>

            <div className="p-3.5 rounded-lg border border-emerald-500/20 bg-emerald-500/5 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">Low Risk (P &lt; 16%)</span>
                <span className="text-xs font-mono text-emerald-300">~51.7% Cohort</span>
              </div>
              <p className="text-xs text-slate-300">
                Standard academic milestones. Minimal intervention required.
              </p>
            </div>
          </div>
        </div>

        {/* Priority Action Queue */}
        <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4 lg:col-span-2">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-semibold text-white">Priority Student Outreach Queue</h2>
              <p className="text-xs text-slate-400 mt-0.5">Students ranked by urgency based on calibrated dropout risk</p>
            </div>
            <Link 
              href="/batch" 
              className="text-xs font-medium text-blue-400 hover:text-blue-300 flex items-center gap-1 transition-colors"
            >
              Upload Batch CSV <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 font-medium">
                  <th className="py-2.5 px-3">Student ID</th>
                  <th className="py-2.5 px-3">Degree Programme</th>
                  <th className="py-2.5 px-3">Sem 1 Performance</th>
                  <th className="py-2.5 px-3">Tuition Status</th>
                  <th className="py-2.5 px-3">Risk Score</th>
                  <th className="py-2.5 px-3">Tier Action</th>
                  <th className="py-2.5 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-200">
                {priorityStudents.map((s) => (
                  <tr key={s.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 px-3 font-mono font-medium text-slate-300">#{s.id}</td>
                    <td className="py-3 px-3">{s.course}</td>
                    <td className="py-3 px-3 text-slate-300">
                      {s.approved}/{s.enrolled} approved • {s.grade.toFixed(1)}/20
                    </td>
                    <td className="py-3 px-3">
                      {s.tuition ? (
                        <span className="text-emerald-400 font-medium">Current</span>
                      ) : (
                        <span className="text-red-400 font-medium">Overdue Debt</span>
                      )}
                    </td>
                    <td className="py-3 px-3 font-mono font-semibold">
                      {formatPercent(s.risk)}
                    </td>
                    <td className="py-3 px-3">
                      {s.tier === "High" ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold tracking-wider bg-red-500/10 text-red-400 border border-red-500/30">
                          HIGH RISK
                        </span>
                      ) : s.tier === "Medium" ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold tracking-wider bg-amber-500/10 text-amber-400 border border-amber-500/30">
                          MEDIUM RISK
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                          LOW RISK
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-3 text-right">
                      <Link 
                        href="/student" 
                        className="text-xs text-blue-400 hover:text-blue-300 font-medium"
                      >
                        Inspect →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
