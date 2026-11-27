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
import {
  RefreshCw,
  Clock,
  Sliders,
  ChevronDown,
  ChevronUp,
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
  const [editorOpen, setEditorOpen] = useState(true);

  useEffect(() => {
    if (!studentValues || Object.keys(studentValues).length === 0) return;
    setLoading(true);
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
        <div className="text-center space-y-3">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs text-muted-foreground">Computing calibrated risk & TreeSHAP...</p>
        </div>
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
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="space-y-6"
    >
      {/* Top Controls Bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-xl bg-card border border-border">
        <div>
          <h1 className="text-lg font-semibold tracking-tight">Student Deep Dive & Explainability</h1>
          <p className="text-xs text-muted-foreground">
            Calibrated risk score, TreeSHAP feature attributions, and interactive profile editor
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <select
            value={selectedPersona}
            onChange={(e) => handlePersonaChange(e.target.value)}
            aria-label="Select student persona"
            className="px-3 py-1.5 text-xs rounded-md bg-background border border-border focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="High-Risk Attrition">Persona: High-Risk Attrition</option>
            <option value="High-Performing Scholar">Persona: High-Performing Scholar</option>
            <option value="Borderline Struggling">Persona: Borderline Struggling</option>
            <option value="Custom Input">Custom Input</option>
          </select>

          <button
            onClick={handleSampleRandom}
            className="px-3 py-1.5 text-xs rounded-md font-medium bg-muted hover:bg-muted/80 border border-border flex items-center gap-1.5 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5 text-muted-foreground" />
            Sample Random
          </button>
        </div>
      </div>

      {targetLabel && (
        <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20 text-xs text-blue-600 dark:text-blue-300 flex items-center justify-between">
          <span>
            Historical Ground Truth Label: <strong>{targetLabel}</strong>
          </span>
          <span className="font-mono text-[11px] opacity-80">UCI 697 Record</span>
        </div>
      )}

      {/* Main Score & Action Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Animated Gauge & Probabilities */}
        <div className="p-6 rounded-xl bg-card border border-border space-y-6 flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                Dropout Risk Score
              </span>
              <span className={`px-2.5 py-0.5 rounded text-[11px] font-semibold border ${colors.badge}`}>
                {colors.label}
              </span>
            </div>

            <div className="flex flex-col items-center justify-center py-4">
              <div className="relative w-44 h-44 flex items-center justify-center">
                <svg className="w-full h-full transform -rotate-90" viewBox="0 0 176 176">
                  <circle
                    cx="88"
                    cy="88"
                    r="72"
                    stroke="currentColor"
                    className="text-muted"
                    strokeWidth="12"
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
                    strokeWidth="12"
                    strokeDasharray={452}
                    initial={{ strokeDashoffset: 452 }}
                    animate={{ strokeDashoffset: 452 - 452 * prediction.risk }}
                    transition={{ duration: 0.7, ease: "easeOut" }}
                    strokeLinecap="round"
                    fill="transparent"
                  />
                </svg>
                <div className="absolute flex flex-col items-center justify-center text-center">
                  <span className="text-3xl font-bold font-mono tracking-tight">
                    {formatPercent(prediction.risk)}
                  </span>
                  <span className="text-[11px] text-muted-foreground mt-0.5 font-medium">
                    Calibrated P(Dropout)
                  </span>
                </div>
              </div>
            </div>

            <div className="p-3.5 rounded-lg bg-muted/50 border border-border text-xs space-y-1">
              <div className="flex items-center justify-between font-medium">
                <span className="text-muted-foreground">Cost-Optimal Cutoff (t)</span>
                <span className="font-mono">{formatPercent(prediction.threshold)}</span>
              </div>
              <p className="text-[11px]">
                {prediction.flagged ? (
                  <span className="text-red-500 font-medium">
                    Flagged for advisor outreach (Risk ≥ Cutoff).
                  </span>
                ) : (
                  <span className="text-emerald-500 font-medium">
                    Below intervention cutoff (Risk &lt; Cutoff).
                  </span>
                )}
              </p>
            </div>
          </div>

          <div className="pt-4 border-t border-border space-y-2">
            <span className="text-xs font-medium text-muted-foreground block">
              Outcome Probabilities
            </span>
            <div className="space-y-2 text-xs">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span>P(Graduate)</span>
                  <span className="font-mono font-medium text-emerald-500">
                    {formatPercent(prediction.probs.Graduate)}
                  </span>
                </div>
                <div className="w-full bg-muted h-1.5 rounded-full overflow-hidden">
                  <div
                    className="bg-emerald-500 h-full rounded-full transition-all duration-500"
                    style={{ width: `${prediction.probs.Graduate * 100}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <span>P(Enrolled / Persist)</span>
                  <span className="font-mono font-medium text-amber-500">
                    {formatPercent(prediction.probs.Enrolled)}
                  </span>
                </div>
                <div className="w-full bg-muted h-1.5 rounded-full overflow-hidden">
                  <div
                    className="bg-amber-500 h-full rounded-full transition-all duration-500"
                    style={{ width: `${prediction.probs.Enrolled * 100}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <span>P(Dropout)</span>
                  <span className="font-mono font-medium text-red-500">
                    {formatPercent(prediction.probs.Dropout)}
                  </span>
                </div>
                <div className="w-full bg-muted h-1.5 rounded-full overflow-hidden">
                  <div
                    className="bg-red-500 h-full rounded-full transition-all duration-500"
                    style={{ width: `${prediction.probs.Dropout * 100}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Prescriptive Advisor & SHAP Waterfall */}
        <div className="space-y-6 lg:col-span-2">
          <div className="p-6 rounded-xl bg-card border border-border space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <h2 className="text-base font-semibold">Prescriptive Mentoring Advisor</h2>
                <p className="text-xs text-muted-foreground mt-0.5">{prediction.guideline}</p>
              </div>
              <div className="flex items-center gap-1.5 px-3 py-1 rounded-md bg-muted text-xs border border-border shrink-0">
                <Clock className="w-3.5 h-3.5 text-blue-500" />
                <span>Review: {prediction.review_window}</span>
              </div>
            </div>

            <div className="space-y-2 pt-3 border-t border-border">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground block">
                Top Evidence-Based Talking Points
              </span>
              <ul className="space-y-2 text-xs">
                {prediction.talking_points.map((pt, i) => (
                  <li key={i} className="flex items-start gap-2.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 shrink-0" />
                    <span>{pt}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="p-6 rounded-xl bg-card border border-border space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <h3 className="text-base font-semibold">TreeSHAP Feature Attribution</h3>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Log-odds contribution pushing prediction toward or away from dropout
                </p>
              </div>
              <div className="flex items-center gap-3 text-xs">
                <span className="flex items-center gap-1.5 text-red-500">
                  <span className="w-2.5 h-2.5 rounded-sm bg-red-500" /> Increases Risk
                </span>
                <span className="flex items-center gap-1.5 text-blue-500">
                  <span className="w-2.5 h-2.5 rounded-sm bg-blue-500" /> Reduces Risk
                </span>
              </div>
            </div>

            <div className="h-72 w-full pt-2">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={prediction.contributions}
                  layout="vertical"
                  margin={{ top: 5, right: 24, left: 160, bottom: 5 }}
                >
                  <XAxis type="number" stroke="#94A3B8" fontSize={11} />
                  <YAxis
                    dataKey="display"
                    type="category"
                    stroke="#94A3B8"
                    fontSize={11}
                    width={150}
                    tick={{ fill: "currentColor" }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#0F172A",
                      borderColor: "#334155",
                      fontSize: "12px",
                      borderRadius: "6px",
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
        </div>
      </div>

      {/* Interactive Student Profile Editor */}
      <div className="rounded-xl bg-card border border-border overflow-hidden">
        <button
          onClick={() => setEditorOpen(!editorOpen)}
          className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-muted/40 transition-colors"
        >
          <div className="flex items-center gap-2.5">
            <Sliders className="w-4 h-4 text-blue-500" />
            <div>
              <span className="text-sm font-semibold block">Interactive Student Parameter Studio</span>
              <span className="text-xs text-muted-foreground">
                Edit Semester 1 academics, tuition status, and demographics with live re-scoring
              </span>
            </div>
          </div>
          {editorOpen ? <ChevronUp className="w-4 h-4 text-muted-foreground" /> : <ChevronDown className="w-4 h-4 text-muted-foreground" />}
        </button>

        {editorOpen && (
          <div className="p-6 pt-2 border-t border-border grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Academic Inputs */}
            <div className="space-y-4">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Semester 1 Academics
              </h4>

              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span>Enrolled Units</span>
                  <span className="font-mono font-medium">{enrolled1}</span>
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
                  <span className="font-mono font-medium">{approved1}</span>
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
                  <span className="font-mono font-medium">{evals1}</span>
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
                  <span className="font-mono font-medium">{grade1.toFixed(1)}</span>
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

            {/* Financial Inputs */}
            <div className="space-y-4">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Financial & Enrollment
              </h4>

              <div className="flex items-center justify-between text-xs">
                <span>Tuition Fees Up to Date</span>
                <button
                  onClick={() => updateField("Tuition fees up to date", tuitionPaid ? 0 : 1)}
                  className={`px-3 py-1 rounded-md font-medium border transition-colors ${
                    tuitionPaid
                      ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/30"
                      : "bg-red-500/10 text-red-500 border-red-500/30"
                  }`}
                >
                  {tuitionPaid ? "Yes (Current)" : "No (Overdue)"}
                </button>
              </div>

              <div className="flex items-center justify-between text-xs">
                <span>Institutional Debtor</span>
                <button
                  onClick={() => updateField("Debtor", debtor ? 0 : 1)}
                  className={`px-3 py-1 rounded-md font-medium border transition-colors ${
                    debtor
                      ? "bg-red-500/10 text-red-500 border-red-500/30"
                      : "bg-muted text-muted-foreground border-border"
                  }`}
                >
                  {debtor ? "Has Unpaid Debt" : "No Debt"}
                </button>
              </div>

              <div className="flex items-center justify-between text-xs">
                <span>Scholarship Holder</span>
                <button
                  onClick={() => updateField("Scholarship holder", scholarship ? 0 : 1)}
                  className={`px-3 py-1 rounded-md font-medium border transition-colors ${
                    scholarship
                      ? "bg-blue-500/10 text-blue-500 border-blue-500/30"
                      : "bg-muted text-muted-foreground border-border"
                  }`}
                >
                  {scholarship ? "Yes (Grantee)" : "No"}
                </button>
              </div>
            </div>

            {/* Demographic Inputs */}
            <div className="space-y-4">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Demographics & Programme
              </h4>

              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span>Age at Enrollment</span>
                  <span className="font-mono font-medium">{age} yrs</span>
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

              <div className="space-y-1.5">
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
    </motion.div>
  );
}
