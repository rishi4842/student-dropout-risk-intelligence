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
import { RefreshCw, BarChart3, Sliders } from "lucide-react";
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

const PRESET_DESCRIPTIONS: Record<string, string> = {
  "High-Risk Attrition": "Elevated academic and financial risk.",
  "High-Performing Scholar": "Strong grades, scholarship, fees current.",
  "Borderline Struggling": "Mixed pass rate, moderate retention risk.",
  "Custom Input": "Custom or sampled student parameters.",
};

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
  const credited1 = Number(studentValues["Curricular units 1st sem (credited)"] ?? 0);
  const withoutEval1 = Number(studentValues["Curricular units 1st sem (without evaluations)"] ?? 0);
  const age = Number(studentValues["Age at enrollment"] ?? 20);
  const gender = Number(studentValues["Gender"] ?? 0);
  const admGrade = Number(studentValues["Admission grade"] ?? 125);
  const prevGrade = Number(studentValues["Previous qualification (grade)"] ?? 130);
  const tuitionPaid = Number(studentValues["Tuition fees up to date"] ?? 1) === 1;
  const debtor = Number(studentValues["Debtor"] ?? 0) === 1;
  const scholarship = Number(studentValues["Scholarship holder"] ?? 0) === 1;
  const daytime = Number(studentValues["Daytime/evening attendance"] ?? 1) === 1;
  const displaced = Number(studentValues["Displaced"] ?? 1) === 1;
  const courseCode = Number(studentValues["Course"] ?? 9500);
  const unemp = Number(studentValues["Unemployment rate"] ?? 10.8);
  const infl = Number(studentValues["Inflation rate"] ?? 1.4);
  const gdp = Number(studentValues["GDP"] ?? 1.74);

  const courseName = courseMap[String(courseCode)] || `Course ${courseCode}`;
  const riskGapPP = (prediction.risk - prediction.threshold) * 100;
  const tPct = Math.round(prediction.threshold * 100);
  const highPct = 50;
  const posPct = Math.min(Math.max(prediction.risk * 100, 0), 100);

  // Normalize outcome probabilities for clean display
  const pDrop = prediction.probs.Dropout;
  const pEnr = prediction.probs.Enrolled;
  const pGrad = prediction.probs.Graduate;
  const pSum = pDrop + pEnr + pGrad || 1;
  const outcomes = [
    { label: "Graduate", val: pGrad / pSum, color: "bg-emerald-500" },
    { label: "Persist", val: pEnr / pSum, color: "bg-blue-500" },
    { label: "Dropout", val: pDrop / pSum, color: "bg-red-500" },
  ];
  const topOutcome = outcomes.reduce((a, b) => (a.val >= b.val ? a : b)).label;

  const upFactors = prediction.contributions.filter((c) => c.impact > 0).slice(0, 3);
  const downFactors = prediction.contributions.filter((c) => c.impact < 0).slice(0, 3);

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className="space-y-6"
    >
      {/* Top Section */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 pb-4 border-b border-border">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Risk Assessment</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Identify early signs of student attrition and understand the factors driving the prediction.
          </p>
          <div className="mt-2.5 text-xs text-muted-foreground flex flex-wrap items-center gap-x-2 gap-y-1">
            <span>
              Student Profile: <strong className="text-foreground">{selectedPersona}</strong>
            </span>
            <span>·</span>
            <span>{courseName}</span>
            <span>·</span>
            <span>Age {age}</span>
            <span>·</span>
            <span>{tag === "early" ? "Semester 1" : "Semesters 1 & 2"}</span>
            {targetLabel && (
              <>
                <span>·</span>
                <span className="text-blue-500 font-medium">Recorded: {targetLabel}</span>
              </>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={handleSampleRandom}
            className="px-3 py-1.5 text-xs rounded-md font-medium bg-card hover:bg-muted border border-border inline-flex items-center gap-1.5 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5 text-muted-foreground" />
            Sample Random
          </button>
          <div className="flex items-center p-0.5 rounded-md bg-muted border border-border">
            <button
              onClick={() => setActiveTab("explain")}
              className={`px-3 py-1.5 rounded text-xs font-medium inline-flex items-center gap-1.5 transition-colors ${
                activeTab === "explain"
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <BarChart3 className="w-3.5 h-3.5" />
              Assessment
            </button>
            <button
              onClick={() => setActiveTab("edit")}
              className={`px-3 py-1.5 rounded text-xs font-medium inline-flex items-center gap-1.5 transition-colors ${
                activeTab === "edit"
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Sliders className="w-3.5 h-3.5" />
              Student Profile
            </button>
          </div>
        </div>
      </div>

      {/* Selectable Student Presets Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {["High-Risk Attrition", "High-Performing Scholar", "Borderline Struggling", "Custom Input"].map(
          (name) => {
            const active = selectedPersona === name;
            return (
              <button
                key={name}
                onClick={() => handlePersonaChange(name)}
                className={`text-left p-3 rounded-lg border transition-colors ${
                  active
                    ? "border-blue-500 bg-blue-500/5"
                    : "border-border bg-card/50 hover:bg-muted/40"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className={`text-xs font-semibold ${active ? "text-blue-500" : "text-foreground"}`}>
                    {name}
                  </span>
                  {active && <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />}
                </div>
                <p className="text-[11px] text-muted-foreground mt-0.5 line-clamp-1">
                  {PRESET_DESCRIPTIONS[name]}
                </p>
              </button>
            );
          }
        )}
      </div>

      {activeTab === "explain" ? (
        <div className="space-y-8">
          {/* Primary Risk KPI + Risk Spectrum + Multiclass Probability */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            {/* Primary Risk Focal Panel */}
            <div className="lg:col-span-5 p-6 rounded-xl bg-card border border-border space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                  Attrition Risk
                </span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${colors.badge}`}>
                  {colors.label}
                </span>
              </div>

              <div className="text-5xl font-bold font-mono tracking-tight">
                {formatPercent(prediction.risk)}
              </div>

              <p className="text-xs text-muted-foreground">
                {prediction.flagged
                  ? "Student is currently above the intervention threshold."
                  : "Student is currently below the intervention threshold."}
              </p>

              <div className="pt-4 border-t border-border grid grid-cols-2 gap-4 text-xs">
                <div>
                  <span className="text-muted-foreground block text-[11px]">Operational threshold</span>
                  <span className="font-mono font-semibold text-sm">{formatPercent(prediction.threshold)}</span>
                </div>
                <div>
                  <span className="text-muted-foreground block text-[11px]">Risk gap</span>
                  <span className="font-mono font-semibold text-sm">
                    {riskGapPP >= 0 ? "+" : ""}
                    {riskGapPP.toFixed(1)} percentage points
                  </span>
                </div>
              </div>
            </div>

            {/* Right: Segmented Risk Scale & Multiclass Probability */}
            <div className="lg:col-span-7 space-y-6">
              <div>
                <h2 className="text-sm font-semibold mb-3">Risk Spectrum</h2>
                <div className="flex text-[11px] text-muted-foreground font-semibold mb-1.5">
                  <div style={{ width: `${tPct}%` }}>
                    SAFE <span className="font-normal block">0–{tPct}%</span>
                  </div>
                  <div style={{ width: `${highPct - tPct}%` }}>
                    WATCH <span className="font-normal block">{tPct}–{highPct}%</span>
                  </div>
                  <div style={{ width: `${100 - highPct}%` }}>
                    CRITICAL <span className="font-normal block">{highPct}–100%</span>
                  </div>
                </div>
                <div className="relative flex w-full h-2.5 rounded-full">
                  <div className="bg-emerald-500 h-full rounded-l-full" style={{ width: `${tPct}%` }} />
                  <div className="bg-amber-500 h-full" style={{ width: `${highPct - tPct}%` }} />
                  <div className="bg-red-500 h-full rounded-r-full" style={{ width: `${100 - highPct}%` }} />
                  <div
                    className="absolute -top-1.5 w-1.5 h-5 bg-foreground rounded-sm -translate-x-1/2 transition-all duration-300"
                    style={{ left: `${posPct}%` }}
                  />
                </div>
                <p className="text-xs text-muted-foreground mt-2.5">
                  Current position: <strong className="text-foreground">{formatPercent(prediction.risk)}</strong> · Status:{" "}
                  <strong className="text-foreground">{prediction.tier} Risk</strong>
                </p>
              </div>

              <div className="pt-4 border-t border-border">
                <h2 className="text-sm font-semibold mb-3">Multiclass Probability</h2>
                <div className="space-y-2.5">
                  {outcomes.map((o) => {
                    const isTop = o.label === topOutcome;
                    return (
                      <div key={o.label} className={isTop ? "opacity-100" : "opacity-75"}>
                        <div className="flex justify-between text-xs mb-1">
                          <span className={isTop ? "font-semibold" : "font-medium"}>{o.label}</span>
                          <span className={`font-mono ${isTop ? "font-semibold" : ""}`}>
                            {formatPercent(o.val)}
                          </span>
                        </div>
                        <div className="w-full h-2 bg-muted rounded-sm overflow-hidden">
                          <div
                            className={`h-full ${o.color} transition-all duration-300`}
                            style={{ width: `${Math.max(o.val * 100, 1.5)}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>

          <div className="border-t border-border pt-6 grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            {/* Advisor Action Plan */}
            <div className="lg:col-span-5 space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h2 className="text-base font-semibold">Recommended Advisor Action</h2>
                <span className={`px-2.5 py-0.5 rounded text-[11px] font-medium border ${colors.badge}`}>
                  {prediction.tier === "Low"
                    ? "No immediate intervention required"
                    : prediction.tier === "Medium"
                    ? "Targeted support recommended"
                    : "Priority outreach required"}
                </span>
              </div>

              <p className="text-xs text-muted-foreground">{prediction.guideline}</p>

              <div className="pt-2 space-y-2">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Recommended talking points
                </h3>
                <ul className="space-y-2 text-xs">
                  {prediction.talking_points.map((pt, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 shrink-0" />
                      <span>{pt}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* SHAP Explanation */}
            <div className="lg:col-span-7 space-y-3">
              <div>
                <h2 className="text-base font-semibold">Why is this prediction happening?</h2>
                <p className="text-xs text-muted-foreground">
                  Model explanation for this student&apos;s dropout risk.
                </p>
              </div>

              <div className="h-72 w-full">
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
                        borderRadius: "6px",
                        color: "#F8FAFC",
                      }}
                    />
                    <ReferenceLine x={0} stroke="#64748B" strokeWidth={1} />
                    <Bar dataKey="impact" radius={[0, 3, 3, 0]}>
                      {prediction.contributions.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={entry.impact > 0 ? "#EF4444" : "#2563EB"}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-border text-xs">
                <div>
                  <span className="font-semibold text-red-500 block mb-1">Factors increasing risk</span>
                  <span className="text-muted-foreground">
                    {upFactors.length > 0
                      ? upFactors.map((f) => `${f.display} (${f.impact > 0 ? "+" : ""}${f.impact.toFixed(2)})`).join(", ")
                      : "None"}
                  </span>
                </div>
                <div>
                  <span className="font-semibold text-blue-500 block mb-1">Factors reducing risk</span>
                  <span className="text-muted-foreground">
                    {downFactors.length > 0
                      ? downFactors.map((f) => `${f.display} (${f.impact.toFixed(2)})`).join(", ")
                      : "None"}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* Student Profile Studio (4 logical sections, 2-column layout) */
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="space-y-6">
            <div>
              <h2 className="text-sm font-semibold mb-3">Academic Performance</h2>
              <div className="space-y-3 text-xs">
                <div>
                  <div className="flex justify-between mb-1">
                    <span>Semester 1 enrolled units</span>
                    <span className="font-mono font-semibold">{enrolled1}</span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={26}
                    value={enrolled1}
                    onChange={(e) => updateField("Curricular units 1st sem (enrolled)", Number(e.target.value))}
                    className="w-full accent-blue-600 cursor-pointer"
                  />
                </div>
                <div>
                  <div className="flex justify-between mb-1">
                    <span>Semester 1 approved units</span>
                    <span className="font-mono font-semibold">{approved1}</span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={Math.max(enrolled1, 0)}
                    value={approved1}
                    onChange={(e) => updateField("Curricular units 1st sem (approved)", Number(e.target.value))}
                    className="w-full accent-blue-600 cursor-pointer"
                  />
                </div>
                <div>
                  <div className="flex justify-between mb-1">
                    <span>Grade average (0–20)</span>
                    <span className="font-mono font-semibold">{grade1.toFixed(1)}</span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={20}
                    step={0.5}
                    value={grade1}
                    onChange={(e) => updateField("Curricular units 1st sem (grade)", Number(e.target.value))}
                    className="w-full accent-blue-600 cursor-pointer"
                  />
                </div>
                <div className="grid grid-cols-3 gap-3 pt-1">
                  <div>
                    <label className="text-[11px] text-muted-foreground block mb-1">Evaluation moments</label>
                    <input
                      type="number"
                      min={approved1}
                      max={45}
                      value={evals1}
                      onChange={(e) => updateField("Curricular units 1st sem (evaluations)", Number(e.target.value))}
                      className="w-full px-2.5 py-1.5 rounded border border-border bg-background font-mono"
                    />
                  </div>
                  <div>
                    <label className="text-[11px] text-muted-foreground block mb-1">Credited units</label>
                    <input
                      type="number"
                      min={0}
                      max={20}
                      value={credited1}
                      onChange={(e) => updateField("Curricular units 1st sem (credited)", Number(e.target.value))}
                      className="w-full px-2.5 py-1.5 rounded border border-border bg-background font-mono"
                    />
                  </div>
                  <div>
                    <label className="text-[11px] text-muted-foreground block mb-1">Without evaluation</label>
                    <input
                      type="number"
                      min={0}
                      max={12}
                      value={withoutEval1}
                      onChange={(e) => updateField("Curricular units 1st sem (without evaluations)", Number(e.target.value))}
                      className="w-full px-2.5 py-1.5 rounded border border-border bg-background font-mono"
                    />
                  </div>
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-border">
              <h2 className="text-sm font-semibold mb-3">Financial &amp; Enrollment</h2>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="flex items-center justify-between p-2.5 rounded border border-border">
                  <span>Tuition status</span>
                  <button
                    onClick={() => updateField("Tuition fees up to date", tuitionPaid ? 0 : 1)}
                    className={`px-2.5 py-1 rounded text-[11px] font-medium ${
                      tuitionPaid ? "bg-emerald-500/10 text-emerald-500" : "bg-red-500/10 text-red-500"
                    }`}
                  >
                    {tuitionPaid ? "Up to date" : "Overdue"}
                  </button>
                </div>
                <div className="flex items-center justify-between p-2.5 rounded border border-border">
                  <span>Institutional debt</span>
                  <button
                    onClick={() => updateField("Debtor", debtor ? 0 : 1)}
                    className={`px-2.5 py-1 rounded text-[11px] font-medium ${
                      debtor ? "bg-red-500/10 text-red-500" : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {debtor ? "Yes" : "No"}
                  </button>
                </div>
                <div className="flex items-center justify-between p-2.5 rounded border border-border">
                  <span>Scholarship</span>
                  <button
                    onClick={() => updateField("Scholarship holder", scholarship ? 0 : 1)}
                    className={`px-2.5 py-1 rounded text-[11px] font-medium ${
                      scholarship ? "bg-blue-500/10 text-blue-500" : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {scholarship ? "Yes" : "No"}
                  </button>
                </div>
                <div className="flex items-center justify-between p-2.5 rounded border border-border">
                  <span>Attendance</span>
                  <button
                    onClick={() => updateField("Daytime/evening attendance", daytime ? 0 : 1)}
                    className="px-2.5 py-1 rounded text-[11px] font-medium bg-muted text-foreground"
                  >
                    {daytime ? "Daytime" : "Evening"}
                  </button>
                </div>
                <div className="flex items-center justify-between p-2.5 rounded border border-border col-span-2">
                  <span>Displacement status</span>
                  <button
                    onClick={() => updateField("Displaced", displaced ? 0 : 1)}
                    className="px-2.5 py-1 rounded text-[11px] font-medium bg-muted text-foreground"
                  >
                    {displaced ? "Displaced (Away from home)" : "Local"}
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <div>
              <h2 className="text-sm font-semibold mb-3">Student Background</h2>
              <div className="space-y-3 text-xs">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-[11px] text-muted-foreground block mb-1">Age at enrollment</label>
                    <input
                      type="number"
                      min={17}
                      max={70}
                      value={age}
                      onChange={(e) => updateField("Age at enrollment", Number(e.target.value))}
                      className="w-full px-2.5 py-1.5 rounded border border-border bg-background font-mono"
                    />
                  </div>
                  <div>
                    <label className="text-[11px] text-muted-foreground block mb-1">Gender</label>
                    <select
                      value={gender}
                      onChange={(e) => updateField("Gender", Number(e.target.value))}
                      className="w-full px-2.5 py-1.5 rounded border border-border bg-background"
                    >
                      <option value={0}>Female</option>
                      <option value={1}>Male</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="text-[11px] text-muted-foreground block mb-1">Degree</label>
                  <select
                    value={courseCode}
                    onChange={(e) => updateField("Course", Number(e.target.value))}
                    className="w-full px-2.5 py-1.5 rounded border border-border bg-background"
                  >
                    {courseOptions.map((c: number) => (
                      <option key={c} value={c}>
                        {courseMap[String(c)] || `Course ${c}`}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-[11px] text-muted-foreground block mb-1">Admission grade (0–200)</label>
                    <input
                      type="number"
                      min={0}
                      max={200}
                      step={0.5}
                      value={admGrade}
                      onChange={(e) => updateField("Admission grade", Number(e.target.value))}
                      className="w-full px-2.5 py-1.5 rounded border border-border bg-background font-mono"
                    />
                  </div>
                  <div>
                    <label className="text-[11px] text-muted-foreground block mb-1">Previous qualification grade</label>
                    <input
                      type="number"
                      min={0}
                      max={200}
                      step={0.5}
                      value={prevGrade}
                      onChange={(e) => updateField("Previous qualification (grade)", Number(e.target.value))}
                      className="w-full px-2.5 py-1.5 rounded border border-border bg-background font-mono"
                    />
                  </div>
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-border">
              <h2 className="text-sm font-semibold mb-3">Economic Context</h2>
              <div className="grid grid-cols-3 gap-3 text-xs">
                <div>
                  <label className="text-[11px] text-muted-foreground block mb-1">Unemployment (%)</label>
                  <input
                    type="number"
                    step={0.1}
                    value={unemp}
                    onChange={(e) => updateField("Unemployment rate", Number(e.target.value))}
                    className="w-full px-2.5 py-1.5 rounded border border-border bg-background font-mono"
                  />
                </div>
                <div>
                  <label className="text-[11px] text-muted-foreground block mb-1">Inflation (%)</label>
                  <input
                    type="number"
                    step={0.1}
                    value={infl}
                    onChange={(e) => updateField("Inflation rate", Number(e.target.value))}
                    className="w-full px-2.5 py-1.5 rounded border border-border bg-background font-mono"
                  />
                </div>
                <div>
                  <label className="text-[11px] text-muted-foreground block mb-1">GDP change (%)</label>
                  <input
                    type="number"
                    step={0.1}
                    value={gdp}
                    onChange={(e) => updateField("GDP", Number(e.target.value))}
                    className="w-full px-2.5 py-1.5 rounded border border-border bg-background font-mono"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </motion.div>
  );
}
