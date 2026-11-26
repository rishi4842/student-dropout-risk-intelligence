"use client";

import React, { useEffect, useState } from "react";
import { 
  fetchMetadata, 
  fetchRandomStudent, 
  predictStudent, 
  PredictResponse 
} from "@/lib/api";
import { formatPercent, getTierColor } from "@/lib/utils";
import { 
  AlertCircle, 
  CheckCircle, 
  HelpCircle, 
  RefreshCw, 
  Sparkles, 
  Clock, 
  Check, 
  ChevronRight,
  TrendingUp,
  TrendingDown
} from "lucide-react";
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer, 
  Cell, 
  ReferenceLine 
} from "recharts";

export default function StudentDeepDivePage() {
  const [tag, setTag] = useState<"early" | "full">("early");
  const [metadata, setMetadata] = useState<any>(null);
  const [studentValues, setStudentValues] = useState<Record<string, any>>({});
  const [prediction, setPrediction] = useState<PredictResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [targetLabel, setTargetLabel] = useState<string | null>(null);
  const [selectedPersona, setSelectedPersona] = useState<string>("High-Risk Attrition");

  // Load initial metadata and default persona
  useEffect(() => {
    fetchMetadata()
      .then((meta) => {
        setMetadata(meta);
        const personaData = meta.personas["High-Risk Attrition"];
        setStudentValues(personaData.values);
        setTargetLabel(personaData.target);
        return predictStudent("early", personaData.values);
      })
      .then((pred) => {
        setPrediction(pred);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Initialization error:", err);
        setLoading(false);
      });
  }, []);

  // Re-run prediction when values or tag changes
  const updatePrediction = async (newValues: Record<string, any>, newTag: "early" | "full") => {
    try {
      const pred = await predictStudent(newTag, newValues);
      setPrediction(pred);
    } catch (e) {
      console.error("Prediction error:", e);
    }
  };

  const handlePersonaChange = (pName: string) => {
    if (!metadata) return;
    setSelectedPersona(pName);
    if (metadata.personas[pName]) {
      const p = metadata.personas[pName];
      setStudentValues(p.values);
      setTargetLabel(p.target);
      updatePrediction(p.values, tag);
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
      updatePrediction(data.values, tag);
    } catch (e) {
      console.error("Sampling error:", e);
    }
  };

  const handleTagToggle = (newTag: "early" | "full") => {
    setTag(newTag);
    updatePrediction(studentValues, newTag);
  };

  if (loading || !prediction) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center space-y-3">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-xs text-slate-400">Loading student inference engine...</p>
        </div>
      </div>
    );
  }

  const colors = getTierColor(prediction.tier);

  return (
    <div className="space-y-8">
      {/* Top Controls Bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-xl bg-slate-900/60 border border-slate-800">
        <div className="flex items-center gap-3">
          <span className="text-xs font-medium text-slate-400">Pipeline Mode:</span>
          <div className="flex p-0.5 rounded-lg bg-slate-800/80 border border-slate-700/80">
            <button
              onClick={() => handleTagToggle("early")}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                tag === "early" ? "bg-blue-600 text-white shadow-sm" : "text-slate-400 hover:text-white"
              }`}
            >
              Early-Warning (Sem 1)
            </button>
            <button
              onClick={() => handleTagToggle("full")}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                tag === "full" ? "bg-blue-600 text-white shadow-sm" : "text-slate-400 hover:text-white"
              }`}
            >
              Full Curriculum (Sem 1 & 2)
            </button>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs font-medium text-slate-400">Persona:</span>
          <select
            value={selectedPersona}
            onChange={(e) => handlePersonaChange(e.target.value)}
            className="px-3 py-1.5 text-xs rounded-md bg-slate-800 border border-slate-700 text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="High-Risk Attrition">🚨 High-Risk Attrition</option>
            <option value="High-Performing Scholar">⭐ High-Performing Scholar</option>
            <option value="Borderline Struggling">⚖️ Borderline Struggling</option>
            <option value="Custom Input">Custom Input</option>
          </select>

          <button
            onClick={handleSampleRandom}
            className="px-3 py-1.5 text-xs rounded-md font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center gap-1.5 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5 text-slate-400" />
            Sample Random
          </button>
        </div>
      </div>

      {targetLabel && (
        <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20 text-xs text-blue-300 flex items-center justify-between">
          <span>Historical Ground Truth Label: <strong>{targetLabel}</strong></span>
          <span className="text-blue-400 font-mono text-[11px]">Recorded outcome in dataset</span>
        </div>
      )}

      {/* Main Score & Action Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Animated Gauge & Probabilities */}
        <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-6 lg:col-span-1 flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium uppercase tracking-wider text-slate-400">Dropout Risk Score</span>
              <span className={`px-2.5 py-0.5 rounded text-[11px] font-semibold border ${colors.badge}`}>
                {colors.label}
              </span>
            </div>

            {/* Circular Gauge */}
            <div className="flex flex-col items-center justify-center py-4">
              <div className="relative w-44 h-44 flex items-center justify-center">
                <svg className="w-full h-full transform -rotate-90">
                  <circle
                    cx="88"
                    cy="88"
                    r="72"
                    stroke="#1E293B"
                    strokeWidth="12"
                    fill="transparent"
                  />
                  <circle
                    cx="88"
                    cy="88"
                    r="72"
                    stroke={prediction.tier === "High" ? "#EF4444" : prediction.tier === "Medium" ? "#F59E0B" : "#10B981"}
                    strokeWidth="12"
                    strokeDasharray={452}
                    strokeDashoffset={452 - (452 * prediction.risk)}
                    strokeLinecap="round"
                    fill="transparent"
                    className="transition-all duration-1000 ease-out"
                  />
                </svg>
                <div className="absolute flex flex-col items-center justify-center text-center">
                  <span className="text-3xl font-bold font-mono tracking-tight text-white">
                    {formatPercent(prediction.risk)}
                  </span>
                  <span className="text-[11px] text-slate-400 mt-0.5 font-medium">Calibrated P(Dropout)</span>
                </div>
              </div>
            </div>

            {/* Decision Threshold Callout */}
            <div className="p-3.5 rounded-lg bg-slate-800/40 border border-slate-700/60 text-xs space-y-1">
              <div className="flex items-center justify-between text-slate-300 font-medium">
                <span>Cost-Optimal Cutoff (t)</span>
                <span className="font-mono text-slate-200">{formatPercent(prediction.threshold)}</span>
              </div>
              <p className="text-[11px] text-slate-400">
                {prediction.flagged ? (
                  <span className="text-red-400 font-medium">Flagged for active advisor intervention (Risk ≥ Cutoff).</span>
                ) : (
                  <span className="text-emerald-400 font-medium">Within safe cohort retention bounds (Risk &lt; Cutoff).</span>
                )}
              </p>
            </div>
          </div>

          {/* Multiclass Breakdown */}
          <div className="pt-4 border-t border-slate-800/80 space-y-2">
            <span className="text-xs font-medium text-slate-400 block">Class Probabilities</span>
            <div className="space-y-1.5 text-xs">
              <div className="flex items-center justify-between text-slate-300">
                <span>P(Graduate)</span>
                <span className="font-mono font-medium text-emerald-400">{formatPercent(prediction.probs.Graduate)}</span>
              </div>
              <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                <div className="bg-emerald-500 h-full rounded-full" style={{ width: `${prediction.probs.Graduate * 100}%` }}></div>
              </div>

              <div className="flex items-center justify-between text-slate-300 pt-1">
                <span>P(Enrolled / Persist)</span>
                <span className="font-mono font-medium text-amber-400">{formatPercent(prediction.probs.Enrolled)}</span>
              </div>
              <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                <div className="bg-amber-500 h-full rounded-full" style={{ width: `${prediction.probs.Enrolled * 100}%` }}></div>
              </div>

              <div className="flex items-center justify-between text-slate-300 pt-1">
                <span>P(Dropout)</span>
                <span className="font-mono font-medium text-red-400">{formatPercent(prediction.probs.Dropout)}</span>
              </div>
              <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                <div className="bg-red-500 h-full rounded-full" style={{ width: `${prediction.probs.Dropout * 100}%` }}></div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Prescriptive Advisor & SHAP Waterfall */}
        <div className="space-y-6 lg:col-span-2">
          {/* Action Plan Card */}
          <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-base font-semibold text-white">Prescriptive Mentoring Advisor</h2>
                <p className="text-xs text-slate-400 mt-0.5">{prediction.guideline}</p>
              </div>
              <div className="flex items-center gap-1.5 px-3 py-1 rounded-md bg-slate-800 text-xs text-slate-300 border border-slate-700">
                <Clock className="w-3.5 h-3.5 text-blue-400" />
                <span>Review: {prediction.review_window}</span>
              </div>
            </div>

            <div className="space-y-2 pt-2 border-t border-slate-800">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 block">
                Evidence-Based Talking Points:
              </span>
              <ul className="space-y-2 text-xs text-slate-300">
                {prediction.talking_points.map((pt, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 shrink-0"></span>
                    <span>{pt}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* TreeSHAP Feature Attribution Chart */}
          <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-semibold text-white">TreeSHAP Feature Attribution</h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Exact log-odds contribution pushing prediction toward or away from dropout
                </p>
              </div>
              <div className="flex items-center gap-3 text-xs">
                <span className="flex items-center gap-1 text-red-400">
                  <span className="w-2.5 h-2.5 rounded-sm bg-red-500"></span> Increases Risk
                </span>
                <span className="flex items-center gap-1 text-blue-400">
                  <span className="w-2.5 h-2.5 rounded-sm bg-blue-500"></span> Reduces Risk
                </span>
              </div>
            </div>

            <div className="h-72 w-full pt-2">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={prediction.contributions}
                  layout="vertical"
                  margin={{ top: 5, right: 30, left: 140, bottom: 5 }}
                >
                  <XAxis type="number" stroke="#64748B" fontSize={11} />
                  <YAxis
                    dataKey="display"
                    type="category"
                    stroke="#CBD5E1"
                    fontSize={11}
                    width={130}
                    tick={{ fill: "#CBD5E1" }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#0F172A",
                      borderColor: "#334155",
                      fontSize: "12px",
                      borderRadius: "6px"
                    }}
                    itemStyle={{ color: "#F1F5F9" }}
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

            <p className="text-[11px] text-slate-500 text-center">
              *TreeSHAP explains model reliance on this cohort, not real-world causation.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
