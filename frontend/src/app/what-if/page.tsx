"use client";

import React, { useEffect, useState } from "react";
import { 
  fetchMetadata, 
  simulateIntervention, 
  SimulateResponse 
} from "@/lib/api";
import { formatPercent, getTierColor } from "@/lib/utils";
import { 
  SlidersHorizontal, 
  Sparkles, 
  ArrowRight, 
  ShieldCheck, 
  CheckCircle2, 
  AlertTriangle 
} from "lucide-react";

export default function WhatIfPage() {
  const [metadata, setMetadata] = useState<any>(null);
  const [tutoringBoost, setTutoringBoost] = useState<number>(2);
  const [grantRelief, setGrantRelief] = useState<boolean>(true);
  const [gradeBoost, setGradeBoost] = useState<number>(1.5);
  const [simResult, setSimResult] = useState<SimulateResponse | null>(null);
  const [loading, setLoading] = useState(true);

  // Default at-risk student for what-if
  const baselineStudent = {
    "Curricular units 1st sem (credited)": 0,
    "Curricular units 1st sem (enrolled)": 6,
    "Curricular units 1st sem (evaluations)": 6,
    "Curricular units 1st sem (approved)": 0,
    "Curricular units 1st sem (grade)": 0.0,
    "Curricular units 1st sem (without evaluations)": 0,
    "Tuition fees up to date": 0,
    "Debtor": 1,
    "Scholarship holder": 0,
    "Age at enrollment": 28,
    "Gender": 1,
    "Admission grade": 105.0,
    "Previous qualification (grade)": 110.0,
    "Course": 9147,
    "Application order": 1,
    "Application mode": 39,
    "Daytime/evening attendance": 0,
    "Displaced": 0,
    "Educational special needs": 0,
    "International": 0,
    "Marital status": 2,
    "Nacionality": 1,
    "Previous qualification": 1,
    "Mother's qualification": 37,
    "Father's qualification": 37,
    "Mother's occupation": 9,
    "Father's occupation": 9,
    "Unemployment rate": 13.9,
    "Inflation rate": -0.3,
    "GDP": 0.79
  };

  const runSimulation = async (tutoring: number, grant: boolean, gpa: number) => {
    try {
      const res = await simulateIntervention(
        "early",
        baselineStudent,
        tutoring,
        grant,
        gpa
      );
      setSimResult(res);
      setLoading(false);
    } catch (e) {
      console.error("Simulation error:", e);
      setLoading(false);
    }
  };

  useEffect(() => {
    runSimulation(tutoringBoost, grantRelief, gradeBoost);
  }, []);

  const handleTutoringChange = (val: number) => {
    setTutoringBoost(val);
    runSimulation(val, grantRelief, gradeBoost);
  };

  const handleGrantToggle = (val: boolean) => {
    setGrantRelief(val);
    runSimulation(tutoringBoost, val, gradeBoost);
  };

  const handleGpaChange = (val: number) => {
    setGradeBoost(val);
    runSimulation(tutoringBoost, grantRelief, val);
  };

  if (loading || !simResult) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  const baseColors = getTierColor(simResult.baseline_tier);
  const simColors = getTierColor(simResult.simulated_tier);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-white">What-If Intervention Simulator</h1>
        <p className="text-sm text-slate-400 mt-1">
          Model the counterfactual impact of academic tutoring, hardship grants, and GPA recovery before allocating resources.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left: Intervention Controls */}
        <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-6">
          <div className="flex items-center gap-2">
            <SlidersHorizontal className="w-5 h-5 text-blue-400" />
            <h2 className="text-base font-semibold text-white">Intervention Controls</h2>
          </div>

          <div className="space-y-6">
            {/* Tutoring Units */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs font-medium">
                <span className="text-slate-300">Tutoring: Convert Failed Units to Passed</span>
                <span className="font-mono text-blue-400">+{tutoringBoost} Approved Units</span>
              </div>
              <input
                type="range"
                min="0"
                max="6"
                value={tutoringBoost}
                onChange={(e) => handleTutoringChange(Number(e.target.value))}
                className="w-full accent-blue-500 bg-slate-800 h-2 rounded-lg cursor-pointer"
              />
              <p className="text-[11px] text-slate-500">
                Automatically adjusts evaluations and sets passing grade threshold (&ge; 10.0/20).
              </p>
            </div>

            {/* Emergency Hardship Grant */}
            <div className="pt-4 border-t border-slate-800 flex items-center justify-between">
              <div>
                <span className="text-xs font-semibold text-slate-200 block">Emergency Hardship Grant</span>
                <span className="text-[11px] text-slate-400 block mt-0.5">
                  Clears overdue tuition and resolves institutional debt holds.
                </span>
              </div>
              <button
                onClick={() => handleGrantToggle(!grantRelief)}
                className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                  grantRelief ? "bg-blue-600" : "bg-slate-700"
                }`}
              >
                <span
                  className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                    grantRelief ? "translate-x-5" : "translate-x-0"
                  }`}
                />
              </button>
            </div>

            {/* Grade Improvement */}
            <div className="pt-4 border-t border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-xs font-medium">
                <span className="text-slate-300">Study Workshop: Grade Improvement</span>
                <span className="font-mono text-blue-400">+{gradeBoost.toFixed(1)} Points (0–20 Scale)</span>
              </div>
              <input
                type="range"
                min="0.0"
                max="4.0"
                step="0.5"
                value={gradeBoost}
                onChange={(e) => handleGpaChange(Number(e.target.value))}
                className="w-full accent-blue-500 bg-slate-800 h-2 rounded-lg cursor-pointer"
              />
            </div>

            {/* Validation Notice */}
            <div className="p-3.5 rounded-lg bg-slate-800/60 border border-slate-700/80 flex items-center gap-2.5 text-xs text-slate-300">
              <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>
                <strong>Dataset Integrity Guarantee:</strong> Approved ({simResult.validated_values["Curricular units 1st sem (approved)"]}) 
                &le; Evaluations ({simResult.validated_values["Curricular units 1st sem (evaluations)"]}) 
                &le; Enrolled ({simResult.validated_values["Curricular units 1st sem (enrolled)"]}).
              </span>
            </div>
          </div>
        </div>

        {/* Right: Before vs After Delta */}
        <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-6 flex flex-col justify-between">
          <div>
            <h2 className="text-base font-semibold text-white">Projected Risk Reduction</h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Comparative impact of configured interventions on calibrated attrition probability
            </p>
          </div>

          {/* Side by side comparison cards */}
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/60 space-y-2">
              <span className="text-xs text-slate-400 uppercase tracking-wider block font-medium">Baseline Risk</span>
              <div className="text-3xl font-bold font-mono text-white">
                {formatPercent(simResult.baseline_risk)}
              </div>
              <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold ${baseColors.badge}`}>
                {baseColors.label}
              </span>
            </div>

            <div className="p-4 rounded-lg bg-blue-500/10 border border-blue-500/30 space-y-2">
              <span className="text-xs text-blue-300 uppercase tracking-wider block font-medium">Simulated Risk</span>
              <div className="text-3xl font-bold font-mono text-blue-400">
                {formatPercent(simResult.simulated_risk)}
              </div>
              <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold ${simColors.badge}`}>
                {simColors.label}
              </span>
            </div>
          </div>

          {/* Delta Statement */}
          <div className="p-4 rounded-lg bg-slate-800/60 border border-slate-700 space-y-2">
            <div className="flex items-center gap-2">
              {simResult.risk_diff < 0 ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
              ) : (
                <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />
              )}
              <h3 className="text-sm font-semibold text-white">
                {simResult.risk_diff < -0.05 
                  ? `Achieves ${formatPercent(Math.abs(simResult.risk_diff))} Net Risk Reduction`
                  : "Marginal Impact with Current Parameters"}
              </h3>
            </div>
            <p className="text-xs text-slate-300">
              Intervention shifts this student from <strong>{simResult.baseline_tier} Risk</strong> to <strong>{simResult.simulated_tier} Risk</strong>. 
              Provides empirical justification for university bursar and academic counseling support.
            </p>
          </div>

          <div className="text-[11px] text-slate-500 text-center">
            *Simulation estimates model response to parameter shifts. Real-world efficacy requires tracking post-intervention student retention.
          </div>
        </div>
      </div>
    </div>
  );
}
