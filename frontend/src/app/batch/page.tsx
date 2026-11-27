"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { uploadBatchFile, fetchSampleBatch, BatchResponse } from "@/lib/api";
import { formatPercent } from "@/lib/utils";
import { useStudent } from "@/context/StudentContext";
import {
  UploadCloud,
  FileSpreadsheet,
  Download,
  AlertCircle,
  Sparkles,
  Search,
} from "lucide-react";

export default function BatchTriagePage() {
  const { tag } = useStudent();
  const [file, setFile] = useState<File | null>(null);
  const [batchResult, setBatchResult] = useState<BatchResponse | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [tierFilter, setTierFilter] = useState<"All" | "High" | "Medium" | "Low">("All");

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

  const handleDemoSample = async () => {
    setUploading(true);
    setError(null);
    try {
      const res = await fetchSampleBatch(tag, 50);
      setBatchResult(res);
      setUploading(false);
    } catch (err: any) {
      setError(err.message || "Failed to load holdout sample batch");
      setUploading(false);
    }
  };

  const handleExportCSV = () => {
    if (!batchResult) return;
    const headers = [
      "ID",
      "Risk",
      "Tier",
      "Flagged",
      "Course",
      "Age",
      "Tuition_Paid",
      "Approved_Sem1",
      "Enrolled_Sem1",
      "Grade_Sem1",
      "Actual_Outcome",
    ];
    const rows = batchResult.students.map((s) => [
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
      `"${s.actual_outcome}"`,
    ]);

    const csvContent =
      "data:text/csv;charset=utf-8," +
      [headers.join(","), ...rows.map((e) => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `prioritized_triage_students_${tag}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const filteredRows = (batchResult?.students || []).filter((s) => {
    const matchesTier = tierFilter === "All" || s.tier === tierFilter;
    const matchesSearch =
      searchTerm === "" ||
      s.course.toLowerCase().includes(searchTerm.toLowerCase()) ||
      String(s.id).includes(searchTerm);
    return matchesTier && matchesSearch;
  });

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="space-y-8"
    >
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Batch Student Triage & Upload</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Upload semester enrollment CSV files or score a real 50-student holdout sample to generate ranked outreach queues.
          </p>
        </div>
        <span className="text-xs font-mono text-muted-foreground">
          Pipeline: {tag === "early" ? "Semester 1 Early-Warning" : "Full Curriculum"}
        </span>
      </div>

      {/* Upload Zone */}
      <div className="p-6 sm:p-8 rounded-xl bg-card border border-border space-y-6">
        <div className="border-2 border-dashed border-border hover:border-blue-500/60 rounded-xl p-8 text-center transition-colors">
          <input
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            id="csv-upload"
            className="hidden"
          />
          <label
            htmlFor="csv-upload"
            className="cursor-pointer flex flex-col items-center justify-center space-y-3"
          >
            <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center text-blue-500">
              <UploadCloud className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm font-medium">
                {file ? file.name : "Click to select or drag and drop student enrollment CSV"}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                {file
                  ? `${(file.size / 1024).toFixed(1)} KB`
                  : "Supports semicolon- or comma-delimited CSVs matching UCI 697 schema"}
              </p>
            </div>
          </label>
        </div>

        {error && (
          <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-xs text-red-500 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div className="flex flex-wrap items-center justify-between gap-3">
          <button
            onClick={handleDemoSample}
            disabled={uploading}
            className="px-4 py-2 rounded-lg text-xs font-medium bg-muted hover:bg-muted/80 border border-border flex items-center gap-2 transition-colors"
          >
            <Sparkles className="w-3.5 h-3.5 text-blue-500" />
            Load 50 Holdout Students (Live Demo)
          </button>

          <button
            onClick={handleUpload}
            disabled={!file || uploading}
            className={`px-4 py-2 rounded-lg text-xs font-semibold text-white flex items-center gap-2 transition-colors ${
              !file || uploading
                ? "bg-muted text-muted-foreground cursor-not-allowed"
                : "bg-blue-600 hover:bg-blue-500 shadow-sm"
            }`}
          >
            {uploading ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Scoring Batch Cohort...
              </>
            ) : (
              <>
                <FileSpreadsheet className="w-4 h-4" />
                Score & Triage CSV
              </>
            )}
          </button>
        </div>
      </div>

      {/* Results View */}
      {batchResult && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-5 rounded-xl bg-card border border-border space-y-1">
              <span className="text-xs text-muted-foreground font-medium">Cohort Scored</span>
              <div className="text-2xl font-bold font-mono">{batchResult.total_students} Students</div>
            </div>

            <div className="p-5 rounded-xl bg-card border border-border space-y-1">
              <span className="text-xs text-muted-foreground font-medium">Flagged for Outreach</span>
              <div className="text-2xl font-bold font-mono text-red-500">
                {batchResult.flagged_count} ({formatPercent(batchResult.flagged_rate)})
              </div>
            </div>

            <div className="p-5 rounded-xl bg-card border border-border space-y-1">
              <span className="text-xs text-muted-foreground font-medium">High Risk (P ≥ 50%)</span>
              <div className="text-2xl font-bold font-mono text-red-500">
                {batchResult.high_risk_count} Students
              </div>
            </div>

            <div className="p-5 rounded-xl bg-card border border-border space-y-1">
              <span className="text-xs text-muted-foreground font-medium">Average Cohort Risk</span>
              <div className="text-2xl font-bold font-mono text-blue-500">
                {formatPercent(batchResult.average_risk)}
              </div>
            </div>
          </div>

          <div className="p-6 rounded-xl bg-card border border-border space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h2 className="text-base font-semibold">Prioritized Attrition Queue</h2>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Ranked descending by calibrated dropout risk
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
                  aria-label="Filter batch by tier"
                >
                  <option value="All">All Tiers</option>
                  <option value="High">High Risk</option>
                  <option value="Medium">Medium Risk</option>
                  <option value="Low">Low Risk</option>
                </select>

                <button
                  onClick={handleExportCSV}
                  className="px-3 py-1.5 text-xs font-semibold rounded-md bg-muted hover:bg-muted/80 border border-border flex items-center gap-1.5 transition-colors"
                >
                  <Download className="w-3.5 h-3.5" />
                  Export CSV
                </button>
              </div>
            </div>

            <div className="overflow-x-auto max-h-[500px]">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="sticky top-0 bg-card z-10">
                  <tr className="border-b border-border text-muted-foreground font-medium">
                    <th className="py-2.5 px-3">Rank</th>
                    <th className="py-2.5 px-3">Student ID</th>
                    <th className="py-2.5 px-3">Degree Course</th>
                    <th className="py-2.5 px-3">Age</th>
                    <th className="py-2.5 px-3">Tuition</th>
                    <th className="py-2.5 px-3">Sem 1 Performance</th>
                    <th className="py-2.5 px-3">Risk Score</th>
                    <th className="py-2.5 px-3">Tier</th>
                    <th className="py-2.5 px-3">Target</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {filteredRows.map((s, idx) => (
                    <tr key={s.id} className="hover:bg-muted/40 transition-colors">
                      <td className="py-2.5 px-3 font-mono text-muted-foreground">#{idx + 1}</td>
                      <td className="py-2.5 px-3 font-mono font-medium">ID-{s.id}</td>
                      <td className="py-2.5 px-3">{s.course}</td>
                      <td className="py-2.5 px-3">{s.age}</td>
                      <td className="py-2.5 px-3">
                        {s.tuition_paid ? (
                          <span className="text-emerald-500">Current</span>
                        ) : (
                          <span className="text-red-500 font-medium">Overdue</span>
                        )}
                      </td>
                      <td className="py-2.5 px-3 text-muted-foreground">
                        {s.approved_sem1}/{s.enrolled_sem1} approved • {s.grade_sem1.toFixed(1)}/20
                      </td>
                      <td className="py-2.5 px-3 font-mono font-semibold">{formatPercent(s.risk)}</td>
                      <td className="py-2.5 px-3">
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
                      <td className="py-2.5 px-3 text-muted-foreground">{s.actual_outcome}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </motion.div>
  );
}
