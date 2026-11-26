"use client";

import React, { useState } from "react";
import { uploadBatchFile, BatchResponse } from "@/lib/api";
import { formatPercent } from "@/lib/utils";
import { 
  UploadCloud, 
  FileSpreadsheet, 
  Download, 
  CheckCircle2, 
  AlertCircle, 
  ArrowUpDown,
  Filter
} from "lucide-react";

export default function BatchTriagePage() {
  const [file, setFile] = useState<File | null>(null);
  const [tag, setTag] = useState<"early" | "full">("early");
  const [batchResult, setBatchResult] = useState<BatchResponse | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);

    try {
      const res = await uploadBatchFile(file, tag);
      setBatchResult(res);
      setUploading(false);
    } catch (err: any) {
      setError(err.message || "Failed to process batch CSV file");
      setUploading(false);
    }
  };

  const handleExportCSV = () => {
    if (!batchResult) return;
    const headers = ["ID", "Risk", "Tier", "Flagged", "Course", "Age", "Tuition_Paid", "Approved_Sem1", "Enrolled_Sem1", "Grade_Sem1", "Actual_Outcome"];
    const rows = batchResult.students.map(s => [
      s.id,
      s.risk,
      s.tier,
      s.flagged ? "YES" : "NO",
      `"${s.course}"`,
      s.age,
      s.tuition_paid ? "YES" : "NO",
      s.approved_sem1,
      s.enrolled_sem1,
      s.grade_sem1,
      `"${s.actual_outcome}"`
    ]);

    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `prioritized_triage_students_${tag}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-white">Batch Student Triage & Upload</h1>
        <p className="text-sm text-slate-400 mt-1">
          Upload semester enrollment CSV files to compute calibrated dropout risk scores and generate prioritized outreach queues.
        </p>
      </div>

      {/* Upload Zone */}
      <div className="p-8 rounded-xl bg-slate-900/60 border border-slate-800 space-y-6">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="text-xs font-medium text-slate-400">Scoring Pipeline:</span>
            <div className="flex p-0.5 rounded-lg bg-slate-800/80 border border-slate-700/80">
              <button
                onClick={() => setTag("early")}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                  tag === "early" ? "bg-blue-600 text-white shadow-sm" : "text-slate-400 hover:text-white"
                }`}
              >
                Early-Warning (Sem 1)
              </button>
              <button
                onClick={() => setTag("full")}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                  tag === "full" ? "bg-blue-600 text-white shadow-sm" : "text-slate-400 hover:text-white"
                }`}
              >
                Full Curriculum (Sem 1 & 2)
              </button>
            </div>
          </div>

          <div className="text-xs text-slate-400">
            Accepts semicolon- or comma-delimited CSVs matching UCI 697 schema.
          </div>
        </div>

        {/* Drag & Drop File Input */}
        <div className="border-2 border-dashed border-slate-700/80 hover:border-blue-500/60 rounded-xl p-8 text-center transition-colors">
          <input
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            id="csv-upload"
            className="hidden"
          />
          <label htmlFor="csv-upload" className="cursor-pointer flex flex-col items-center justify-center space-y-3">
            <div className="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center text-blue-400">
              <UploadCloud className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-200">
                {file ? file.name : "Click to select or drag and drop student enrollment CSV"}
              </p>
              <p className="text-xs text-slate-500 mt-1">
                {file ? `${(file.size / 1024).toFixed(1)} KB` : "Supports batch cohorts up to 5,000 students"}
              </p>
            </div>
          </label>
        </div>

        {error && (
          <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-xs text-red-400 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div className="flex items-center justify-end gap-3">
          <button
            onClick={handleUpload}
            disabled={!file || uploading}
            className={`px-4 py-2 rounded-lg text-xs font-semibold text-white flex items-center gap-2 transition-colors ${
              !file || uploading ? "bg-slate-800 text-slate-500 cursor-not-allowed" : "bg-blue-600 hover:bg-blue-500 shadow-sm"
            }`}
          >
            {uploading ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                Scoring Batch Cohort...
              </>
            ) : (
              <>
                <FileSpreadsheet className="w-4 h-4" />
                Score & Triage Batch
              </>
            )}
          </button>
        </div>
      </div>

      {/* Results View */}
      {batchResult && (
        <div className="space-y-6">
          {/* Cohort Summary Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
              <span className="text-xs text-slate-400 font-medium">Cohort Uploaded</span>
              <div className="text-2xl font-bold font-mono text-white">{batchResult.total_students} Students</div>
            </div>

            <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
              <span className="text-xs text-slate-400 font-medium">Flagged for Outreach</span>
              <div className="text-2xl font-bold font-mono text-red-400">
                {batchResult.flagged_count} ({formatPercent(batchResult.flagged_rate)})
              </div>
            </div>

            <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
              <span className="text-xs text-slate-400 font-medium">High Risk (P ≥ 50%)</span>
              <div className="text-2xl font-bold font-mono text-red-400">
                {batchResult.high_risk_count} Students
              </div>
            </div>

            <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
              <span className="text-xs text-slate-400 font-medium">Average Cohort Risk</span>
              <div className="text-2xl font-bold font-mono text-blue-400">
                {formatPercent(batchResult.average_risk)}
              </div>
            </div>
          </div>

          {/* Results Table */}
          <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-base font-semibold text-white">Prioritized Attrition Queue</h2>
                <p className="text-xs text-slate-400 mt-0.5">Ranked descending by predicted dropout risk</p>
              </div>

              <button
                onClick={handleExportCSV}
                className="px-3 py-1.5 text-xs font-semibold rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center gap-1.5 transition-colors"
              >
                <Download className="w-3.5 h-3.5" />
                Export Prioritized CSV
              </button>
            </div>

            <div className="overflow-x-auto max-h-[500px]">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="sticky top-0 bg-[#0B0F17] z-10">
                  <tr className="border-b border-slate-800 text-slate-400 font-medium">
                    <th className="py-2.5 px-3">Rank</th>
                    <th className="py-2.5 px-3">Student ID</th>
                    <th className="py-2.5 px-3">Degree Course</th>
                    <th className="py-2.5 px-3">Age</th>
                    <th className="py-2.5 px-3">Tuition Status</th>
                    <th className="py-2.5 px-3">Sem 1 Performance</th>
                    <th className="py-2.5 px-3">Risk Score</th>
                    <th className="py-2.5 px-3">Triage Tier</th>
                    <th className="py-2.5 px-3">Historical Target</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-200">
                  {batchResult.students.map((s, idx) => (
                    <tr key={s.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-2.5 px-3 font-mono text-slate-500 font-medium">#{idx + 1}</td>
                      <td className="py-2.5 px-3 font-mono font-medium text-slate-300">ID-{s.id}</td>
                      <td className="py-2.5 px-3">{s.course}</td>
                      <td className="py-2.5 px-3">{s.age}</td>
                      <td className="py-2.5 px-3">
                        {s.tuition_paid ? (
                          <span className="text-emerald-400">Current</span>
                        ) : (
                          <span className="text-red-400 font-medium">Overdue Debt</span>
                        )}
                      </td>
                      <td className="py-2.5 px-3 text-slate-300">
                        {s.approved_sem1}/{s.enrolled_sem1} approved • {s.grade_sem1.toFixed(1)}/20
                      </td>
                      <td className="py-2.5 px-3 font-mono font-semibold">
                        {formatPercent(s.risk)}
                      </td>
                      <td className="py-2.5 px-3">
                        {s.tier === "High" ? (
                          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-red-500/10 text-red-400 border border-red-500/30">
                            HIGH
                          </span>
                        ) : s.tier === "Medium" ? (
                          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
                            MEDIUM
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                            LOW
                          </span>
                        )}
                      </td>
                      <td className="py-2.5 px-3 text-slate-400">
                        {s.actual_outcome}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
