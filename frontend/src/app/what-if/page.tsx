"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { simulateIntervention, SimulateResponse } from "@/lib/api";
import { formatPercent, getTierColor } from "@/lib/utils";
import { useStudent } from "@/context/StudentContext";
import {
  SlidersHorizontal,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from "recharts";

export default function WhatIfPage() {
  const { tag, studentValues, selectedPersona } = useStudent();
  const [tutoringBoost, setTutoringBoost] = useState<number>(2);
  const [grantRelief, setGrantRelief] = useState<boolean>(true);
  const [gradeBoost, setGradeBoost] = useState<number>(1.5);
  const [simResult, setSimResult] = useState<SimulateResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const baseEnrolled = Number(studentValues?.["Curricular units 1st sem (enrolled)"] ?? 0);
  const baseApproved = Number(studentValues?.["Curricular units 1st sem (approved)"] ?? 0);
  const maxTutoringBoost = Math.max(0, baseEnrolled - baseApproved);

  useEffect(() => {
    if (!studentValues || Object.keys(studentValues).length === 0) return;
    const clampedBoost = Math.min(tutoringBoost, maxTutoringBoost);
    simulateIntervention(tag, studentValues, clampedBoost, grantRelief, gradeBoost)
      .then((res) => {
        setSimResult(res);
        setLoading(false);
      })
      .catch((e) => {
        console.error("Simulation error:", e);
        setLoading(false);
      });
  }, [tag, studentValues, tutoringBoost, grantRelief, gradeBoost, maxTutoringBoost]);

  if (loading || !simResult) {
    return (
      <div className="flex items-center justify-center min-h-[420px]">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const baseColors = getTierColor(simResult.baseline_tier);
  const simColors = getTierColor(simResult.simulated_tier);

  const chartData = [
    {
      name: "Baseline Risk",
      riskPct: Number((simResult.baseline_risk * 100).toFixed(1)),
      tier: simResult.baseline_tier,
    },
    {
      name: "Post-Intervention",
      riskPct: Number((simResult.simulated_risk * 100).toFixed(1)),
      tier: simResult.simulated_tier,
    },
  ];

  const cutoffPct = tag === "early" ? 16 : 18;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="space-y-8"
    >
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">What-If Intervention Simulator</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Simulate academic tutoring, emergency hardship grants, and grade recovery for the currently selected student ({selectedPersona}).
          </p>
        </div>
        <span className="text-xs font-mono text-muted-foreground">
          Pipeline: {tag === "early" ? "Semester 1 Early-Warning" : "Full Curriculum"}
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left: Intervention Controls */}
        <div className="p-6 rounded-xl bg-card border border-border space-y-6">
          <div className="flex items-center gap-2">
            <SlidersHorizontal className="w-5 h-5 text-blue-500" />
            <h2 className="text-base font-semibold">Intervention Controls</h2>
          </div>

          <div className="space-y-6">
            {/* Tutoring Units */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs font-medium">
                <span>Tutoring: Convert Failed Units to Passed</span>
                <span className="font-mono text-blue-500">
                  +{Math.min(tutoringBoost, maxTutoringBoost)} Approved Units
                </span>
              </div>
              {baseEnrolled === 0 ? (
                <p className="text-xs text-amber-500 bg-amber-500/10 border border-amber-500/20 rounded-md p-2.5">
                  Student has 0 enrolled units. Enroll the student in units on the Student page before simulating tutoring.
                </p>
              ) : maxTutoringBoost === 0 ? (
                <p className="text-xs text-emerald-500 bg-emerald-500/10 border border-emerald-500/20 rounded-md p-2.5">
                  Student has already passed all {baseEnrolled} enrolled units.
                </p>
              ) : (
                <input
                  type="range"
                  min={0}
                  max={maxTutoringBoost}
                  value={Math.min(tutoringBoost, maxTutoringBoost)}
                  onChange={(e) => setTutoringBoost(Number(e.target.value))}
                  className="w-full accent-blue-500 h-2 rounded-lg cursor-pointer"
                />
              )}
              <p className="text-[11px] text-muted-foreground">
                Automatically clamps approved units &le; enrolled ({baseEnrolled}) and updates evaluations &ge; approved.
              </p>
            </div>

            {/* Emergency Hardship Grant */}
            <div className="pt-4 border-t border-border flex items-center justify-between">
              <div>
                <span className="text-xs font-semibold block">Emergency Hardship Grant</span>
                <span className="text-[11px] text-muted-foreground block mt-0.5">
                  Clears overdue tuition and resolves institutional debt holds.
                </span>
              </div>
              <button
                onClick={() => setGrantRelief(!grantRelief)}
                aria-label="Toggle emergency hardship grant"
                className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out ${
                  grantRelief ? "bg-blue-600" : "bg-muted"
                }`}
              >
                <span
                  className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow transition duration-200 ease-in-out ${
                    grantRelief ? "translate-x-5" : "translate-x-0"
                  }`}
                />
              </button>
            </div>

            {/* Grade Improvement */}
            <div className="pt-4 border-t border-border space-y-2">
              <div className="flex items-center justify-between text-xs font-medium">
                <span>Study Workshop: Grade Improvement</span>
                <span className="font-mono text-blue-500">+{gradeBoost.toFixed(1)} Points (0–20 Scale)</span>
              </div>
              <input
                type="range"
                min={0.0}
                max={4.0}
                step={0.5}
                value={gradeBoost}
                onChange={(e) => setGradeBoost(Number(e.target.value))}
                className="w-full accent-blue-500 h-2 rounded-lg cursor-pointer"
              />
            </div>

            {/* Validation Notice */}
            <div className="p-3.5 rounded-lg bg-muted/60 border border-border flex items-center gap-2.5 text-xs">
              <ShieldCheck className="w-4 h-4 text-emerald-500 shrink-0" />
              <span>
                <strong>Dataset Integrity Guarantee:</strong> Approved (
                {simResult.validated_values["Curricular units 1st sem (approved)"]}) &le; Evaluations (
                {simResult.validated_values["Curricular units 1st sem (evaluations)"]}) &le; Enrolled (
                {simResult.validated_values["Curricular units 1st sem (enrolled)"]}).
              </span>
            </div>
          </div>
        </div>

        {/* Right: Before vs After Delta & Chart */}
        <div className="p-6 rounded-xl bg-card border border-border space-y-6 flex flex-col justify-between">
          <div>
            <h2 className="text-base font-semibold">Projected Risk Reduction</h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              Before vs. after calibrated attrition probability
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 rounded-lg bg-muted/40 border border-border space-y-2">
              <span className="text-xs text-muted-foreground uppercase tracking-wider block font-medium">
                Baseline Risk
              </span>
              <div className="text-3xl font-bold font-mono">{formatPercent(simResult.baseline_risk)}</div>
              <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold border ${baseColors.badge}`}>
                {baseColors.label}
              </span>
            </div>

            <div className="p-4 rounded-lg bg-blue-500/10 border border-blue-500/30 space-y-2">
              <span className="text-xs text-blue-500 uppercase tracking-wider block font-medium">
                Simulated Risk
              </span>
              <div className="text-3xl font-bold font-mono text-blue-500">
                {formatPercent(simResult.simulated_risk)}
              </div>
              <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold border ${simColors.badge}`}>
                {simColors.label}
              </span>
            </div>
          </div>

          <div className="h-44 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                <XAxis dataKey="name" stroke="#94A3B8" fontSize={11} />
                <YAxis domain={[0, 100]} stroke="#94A3B8" fontSize={11} unit="%" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#0F172A",
                    borderColor: "#334155",
                    borderRadius: "8px",
                    fontSize: "12px",
                    color: "#F8FAFC",
                  }}
                />
                <ReferenceLine y={cutoffPct} stroke="#F59E0B" strokeDasharray="3 3" label={{ value: `Cutoff ${cutoffPct}%`, fill: "#F59E0B", fontSize: 10, position: "insideTopRight" }} />
                <Bar dataKey="riskPct" radius={[6, 6, 0, 0]} barSize={48}>
                  {chartData.map((entry, idx) => (
                    <Cell
                      key={`sim-${idx}`}
                      fill={
                        entry.tier === "High"
                          ? "#EF4444"
                          : entry.tier === "Medium"
                          ? "#F59E0B"
                          : "#10B981"
                      }
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="p-4 rounded-lg bg-muted/50 border border-border space-y-1.5">
            <div className="flex items-center gap-2">
              {simResult.risk_diff < -0.02 ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
              ) : (
                <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0" />
              )}
              <h3 className="text-sm font-semibold">
                {simResult.risk_diff < -0.05
                  ? `Achieves ${formatPercent(Math.abs(simResult.risk_diff))} Net Risk Reduction`
                  : simResult.risk_diff < 0
                  ? `Modest Reduction (${formatPercent(Math.abs(simResult.risk_diff))})`
                  : "No Risk Reduction Under Current Parameters"}
              </h3>
            </div>
            <p className="text-xs text-muted-foreground">
              Tier trajectory: <strong>{simResult.baseline_tier} Risk</strong> &rarr;{" "}
              <strong>{simResult.simulated_tier} Risk</strong>. Simulations estimate model response, not guaranteed causal outcomes.
            </p>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
