"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  fetchRandomStudent,
  predictStudent,
  PredictResponse,
} from "@/lib/api";
import { formatPercent, getTierColor } from "@/lib/utils";
import { useStudent } from "@/context/StudentContext";
import { RefreshCw, Clock, BarChart3, Sliders } from "lucide-react";
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

export default function StudentDeepDivePage() {
  const {
    tag,
    metadata,
    studentValues,
    setStudentValues,
    targetLabel,
    setTargetLabel,
    selectedPersona,
    setSelectedPersona,
  } = useStudent();

  const [prediction, setPrediction] = useState<PredictResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"explain" | "edit">("explain");

  useEffect(() => {
    if (!studentValues || Object.keys(studentValues).length === 0) return;
    predictStudent(tag, studentValues)
      .then((pred) => {
        setPrediction(pred);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Prediction error:", err);
        setLoading(false);
      });
  }, [tag, studentValues]);

  const handlePersonaChange = (pName: string) => {
    if (!metadata) return;
    setSelectedPersona(pName);
    if (metadata.personas[pName]) {
      const p = metadata.personas[pName];
      setStudentValues(p.values);
      setTargetLabel(p.target);
    } else {
      setTargetLabel(null);
    }
  };

  const handleSampleRandom = async () => {
    try {
      const data = await fetchRandomStudent(tag);
      setStudentValues(data.values);
      setTargetLabel(data.outcome);
      setSelectedPersona("Custom Input");
    } catch (e) {
      console.error("Sampling error:", e);
    }
  };

  const updateField = (field: string, value: any) => {
    const next = { ...studentValues, [field]: value };

    // Enforce dataset consistency: approved <= evaluations <= enrolled
    if (field === "Curricular units 1st sem (enrolled)") {
      const enr = Number(value);
      if ((next["Curricular units 1st sem (approved)"] ?? 0) > enr) {
        next["Curricular units 1st sem (approved)"] = enr;
      }
      if ((next["Curricular units 1st sem (evaluations)"] ?? 0) < (next["Curricular units 1st sem (approved)"] ?? 0)) {
        next["Curricular units 1st sem (evaluations)"] = next["Curricular units 1st sem (approved)"];
      }
    }
    if (field === "Curricular units 1st sem (approved)") {
      const app = Number(value);
      if ((next["Curricular units 1st sem (enrolled)"] ?? 0) < app) {
        next["Curricular units 1st sem (enrolled)"] = app;
      }
      if ((next["Curricular units 1st sem (evaluations)"] ?? 0) < app) {
        next["Curricular units 1st sem (evaluations)"] = app;
      }
    }
    if (field === "Curricular units 1st sem (evaluations)") {
      const ev = Number(value);
      if (ev < (next["Curricular units 1st sem (approved)"] ?? 0)) {
        next["Curricular units 1st sem (evaluations)"] = next["Curricular units 1st sem (approved)"];
      }
    }

    setSelectedPersona("Custom Input");
    setTargetLabel(null);
    setStudentValues(next);
  };

  if (loading || !prediction || !metadata) {
    return (
      <div className="flex items-center justify-center min-h-[420px]">
        <div className="w-7 h-7 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const colors = getTierColor(prediction.tier);
  const courseMap: Record<string, string> = metadata.course_map || {};
  const courseOptions = metadata.specs_early?.Course?.options || Object.keys(courseMap).map(Number);

  const enrolled1 = Number(studentValues["Curricular units 1st sem (enrolled)"] ?? 0);
  const approved1 = Number(studentValues["Curricular units 1st sem (approved)"] ?? 0);
  const evals1 = Number(studentValues["Curricular units 1st sem (evaluations)"] ?? 0);
  const grade1 = Number(studentValues["Curricular units 1st sem (grade)"] ?? 0);
  const age = Number(studentValues["Age at enrollment"] ?? 20);
  const tuitionPaid = Number(studentValues["Tuition fees up to date"] ?? 1) === 1;
  const debtor = Number(studentValues["Debtor"] ?? 0) === 1;
  const scholarship = Number(studentValues["Scholarship holder"] ?? 0) === 1;
  const courseCode = Number(studentValues["Course"] ?? 9500);

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className="space-y-5"
    >
      {/* Compact Command Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-border">
        <div className="flex flex-wrap items-center gap-2.5">
          <select
            value={selectedPersona}
            onChange={(e) => handlePersonaChange(e.target.value)}
            aria-label="Select student persona"
            className="px-3 py-1.5 text-xs font-medium rounded-md bg-card border border-border focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="High-Risk Attrition">Persona: High-Risk Attrition</option>
            <option value="High-Performing Scholar">Persona: High-Performing Scholar</option>
            <option value="Borderline Struggling">Persona: Borderline Struggling</option>
            <option value="Custom Input">Custom Student</option>
          </select>

          <button
            onClick={handleSampleRandom}
            className="px-3 py-1.5 text-xs rounded-md font-medium bg-card hover:bg-muted border border-border inline-flex items-center gap-1.5 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5 text-muted-foreground" />
            Sample Random
          </button>

          {targetLabel && (
            <span className="text-[11px] px-2.5 py-1 rounded-md bg-blue-500/10 text-blue-500 border border-blue-500/20 font-medium">
              Recorded Target: {targetLabel}
            </span>
          )}
        </div>

        {/* Workspace Tab Switcher */}
        <div className="flex items-center p-0.5 rounded-lg bg-muted border border-border">
          <button
            onClick={() => setActiveTab("explain")}
            className={`px-3 py-1.5 rounded-md text-xs font-medium inline-flex items-center gap-1.5 transition-colors ${
              activeTab === "explain"
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5" />
            Explain & Advise
          </button>
          <button
            onClick={() => setActiveTab("edit")}
            className={`px-3 py-1.5 rounded-md text-xs font-medium inline-flex items-center gap-1.5 transition-colors ${
              activeTab === "edit"
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <Sliders className="w-3.5 h-3.5" />
            Edit Parameters
          </button>
        </div>
      </div>

      {/* 12-Col Master-Detail Split Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Sticky Left Telemetry Rail (4 cols) */}
        <div className="lg:col-span-4 lg:sticky lg:top-20 p-5 rounded-xl bg-card border border-border space-y-5">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
              Risk Telemetry
            </span>
            <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${colors.badge}`}>
              {colors.label}
            </span>
          </div>

          <div className="flex flex-col items-center py-2">
            <div className="relative w-40 h-40 flex items-center justify-center">
              <svg className="w-full h-full transform -rotate-90" viewBox="0 0 176 176">
                <circle
                  cx="88"
                  cy="88"
                  r="72"
                  stroke="currentColor"
                  className="text-muted"
                  strokeWidth="11"
                  fill="transparent"
                />
                <motion.circle
                  cx="88"
                  cy="88"
                  r="72"
                  stroke={
                    prediction.tier === "High"
                      ? "#EF4444"
                      : prediction.tier === "Medium"
                      ? "#F59E0B"
                      : "#10B981"
                  }
                  strokeWidth="11"
                  strokeDasharray={452}
                  animate={{ strokeDashoffset: 452 - 452 * prediction.risk }}
                  transition={{ duration: 0.5, ease: "easeOut" }}
                  strokeLinecap="round"
                  fill="transparent"
                />
              </svg>
              <div className="absolute flex flex-col items-center text-center">
                <span className="text-3xl font-bold font-mono tracking-tight">
                  {formatPercent(prediction.risk)}
                </span>
                <span className="text-[10px] text-muted-foreground font-medium">
                  P(Dropout)
                </span>
              </div>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-muted/40 border border-border text-xs space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Cutoff (5:1 cost)</span>
              <span className="font-mono font-semibold">{formatPercent(prediction.threshold)}</span>
            </div>
            <p className={`text-[11px] font-medium ${prediction.flagged ? "text-red-500" : "text-emerald-500"}`}>
              {prediction.flagged
                ? "Flagged for advisor intervention"
                : "Below intervention threshold"}
            </p>
          </div>

          <div className="space-y-2.5 pt-3 border-t border-border text-xs">
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-muted-foreground">Graduate</span>
                <span className="font-mono text-emerald-500">{formatPercent(prediction.probs.Graduate)}</span>
              </div>
              <div className="w-full bg-muted h-1.5 rounded-full overflow-hidden">
                <div className="bg-emerald-500 h-full transition-all duration-300" style={{ width: `${prediction.probs.Graduate * 100}%` }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-muted-foreground">Enrolled</span>
                <span className="font-mono text-amber-500">{formatPercent(prediction.probs.Enrolled)}</span>
              </div>
              <div className="w-full bg-muted h-1.5 rounded-full overflow-hidden">
                <div className="bg-amber-500 h-full transition-all duration-300" style={{ width: `${prediction.probs.Enrolled * 100}%` }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-muted-foreground">Dropout</span>
                <span className="font-mono text-red-500">{formatPercent(prediction.probs.Dropout)}</span>
              </div>
              <div className="w-full bg-muted h-1.5 rounded-full overflow-hidden">
                <div className="bg-red-500 h-full transition-all duration-300" style={{ width: `${prediction.probs.Dropout * 100}%` }} />
              </div>
            </div>
          </div>
        </div>

        {/* Right Interactive Workspace (8 cols) */}
        <div className="lg:col-span-8 space-y-5">
          {activeTab === "explain" ? (
            <>
              <div className="p-5 rounded-xl bg-card border border-border space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <h2 className="text-sm font-semibold">Prescriptive Mentoring Playbook</h2>
                    <p className="text-xs text-muted-foreground mt-0.5">{prediction.guideline}</p>
                  </div>
                  <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-muted text-xs border border-border">
                    <Clock className="w-3.5 h-3.5 text-blue-500" />
                    <span>{prediction.review_window}</span>
                  </div>
                </div>

                <ul className="space-y-2 pt-3 border-t border-border text-xs">
                  {prediction.talking_points.map((pt, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 shrink-0" />
                      <span>{pt}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="p-5 rounded-xl bg-card border border-border space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <h3 className="text-sm font-semibold">TreeSHAP Feature Attribution</h3>
                    <p className="text-xs text-muted-foreground">
                      Log-odds contribution pushing prediction toward or away from dropout
                    </p>
                  </div>
                  <div className="flex items-center gap-3 text-[11px]">
                    <span className="flex items-center gap-1 text-red-500">
                      <span className="w-2 h-2 rounded-sm bg-red-500" /> Increases Risk
                    </span>
                    <span className="flex items-center gap-1 text-blue-500">
                      <span className="w-2 h-2 rounded-sm bg-blue-500" /> Reduces Risk
                    </span>
                  </div>
                </div>

                <div className="h-80 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={prediction.contributions}
                      layout="vertical"
                      margin={{ top: 4, right: 20, left: 165, bottom: 4 }}
                    >
                      <XAxis type="number" stroke="#94A3B8" fontSize={11} />
                      <YAxis
                        dataKey="display"
                        type="category"
                        stroke="#94A3B8"
                        fontSize={11}
                        width={155}
                        tick={{ fill: "currentColor" }}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "#0F172A",
                          borderColor: "#334155",
                          fontSize: "12px",
                          borderRadius: "8px",
                          color: "#F8FAFC",
                        }}
                      />
                      <ReferenceLine x={0} stroke="#64748B" strokeWidth={1} />
                      <Bar dataKey="impact" radius={[0, 4, 4, 0]}>
                        {prediction.contributions.map((entry, index) => (
                          <Cell
                            key={`cell-${index}`}
                            fill={entry.impact > 0 ? "#EF4444" : "#3B82F6"}
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                <p className="text-[11px] text-muted-foreground text-center">
                  TreeSHAP reflects model feature reliance on this cohort, not real-world causation.
                </p>
              </div>
            </>
          ) : (
            <div className="p-6 rounded-xl bg-card border border-border grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Semester 1 Academics
                </h3>

                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span>Enrolled Units</span>
                    <span className="font-mono font-semibold">{enrolled1}</span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={26}
                    value={enrolled1}
                    onChange={(e) => updateField("Curricular units 1st sem (enrolled)", Number(e.target.value))}
                    className="w-full accent-blue-500 cursor-pointer"
                  />
                </div>

                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span>Approved Units</span>
                    <span className="font-mono font-semibold">{approved1}</span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={Math.max(enrolled1, 0)}
                    value={approved1}
                    onChange={(e) => updateField("Curricular units 1st sem (approved)", Number(e.target.value))}
                    className="w-full accent-blue-500 cursor-pointer"
                  />
                </div>

                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span>Evaluation Moments</span>
                    <span className="font-mono font-semibold">{evals1}</span>
                  </div>
                  <input
                    type="range"
                    min={approved1}
                    max={45}
                    value={evals1}
                    onChange={(e) => updateField("Curricular units 1st sem (evaluations)", Number(e.target.value))}
                    className="w-full accent-blue-500 cursor-pointer"
                  />
                </div>

                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span>Average Grade (0–20)</span>
                    <span className="font-mono font-semibold">{grade1.toFixed(1)}</span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={20}
                    step={0.5}
                    value={grade1}
                    onChange={(e) => updateField("Curricular units 1st sem (grade)", Number(e.target.value))}
                    className="w-full accent-blue-500 cursor-pointer"
                  />
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Financial & Demographics
                </h3>

                <div className="flex items-center justify-between text-xs">
                  <span>Tuition Fees Current</span>
                  <button
                    onClick={() => updateField("Tuition fees up to date", tuitionPaid ? 0 : 1)}
                    className={`px-3 py-1 rounded-md font-medium border ${
                      tuitionPaid
                        ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/30"
                        : "bg-red-500/10 text-red-500 border-red-500/30"
                    }`}
                  >
                    {tuitionPaid ? "Paid" : "Overdue"}
                  </button>
                </div>

                <div className="flex items-center justify-between text-xs">
                  <span>Institutional Debtor</span>
                  <button
                    onClick={() => updateField("Debtor", debtor ? 0 : 1)}
                    className={`px-3 py-1 rounded-md font-medium border ${
                      debtor
                        ? "bg-red-500/10 text-red-500 border-red-500/30"
                        : "bg-muted text-muted-foreground border-border"
                    }`}
                  >
                    {debtor ? "Has Debt" : "No Debt"}
                  </button>
                </div>

                <div className="flex items-center justify-between text-xs">
                  <span>Scholarship Holder</span>
                  <button
                    onClick={() => updateField("Scholarship holder", scholarship ? 0 : 1)}
                    className={`px-3 py-1 rounded-md font-medium border ${
                      scholarship
                        ? "bg-blue-500/10 text-blue-500 border-blue-500/30"
                        : "bg-muted text-muted-foreground border-border"
                    }`}
                  >
                    {scholarship ? "Yes" : "No"}
                  </button>
                </div>

                <div className="space-y-1 pt-2">
                  <div className="flex justify-between text-xs">
                    <span>Age at Enrollment</span>
                    <span className="font-mono font-semibold">{age} yrs</span>
                  </div>
                  <input
                    type="range"
                    min={17}
                    max={70}
                    value={age}
                    onChange={(e) => updateField("Age at enrollment", Number(e.target.value))}
                    className="w-full accent-blue-500 cursor-pointer"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs block">Degree Programme</label>
                  <select
                    value={courseCode}
                    onChange={(e) => updateField("Course", Number(e.target.value))}
                    className="w-full px-3 py-1.5 text-xs rounded-md bg-background border border-border focus:outline-none focus:ring-1 focus:ring-blue-500"
                  >
                    {courseOptions.map((c: number) => (
                      <option key={c} value={c}>
                        {courseMap[String(c)] || `Course ${c}`}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
