"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { fetchGovernance } from "@/lib/api";
import { formatPercent } from "@/lib/utils";
import { useStudent } from "@/context/StudentContext";
import {
  ShieldAlert,
  Scale,
  TrendingDown,
  BookOpen,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

const SUBGROUP_LABELS: Record<string, Record<string, string>> = {
  Gender: { "0": "Female", "1": "Male" },
  "Scholarship holder": { "0": "Non-Scholar", "1": "Scholarship" },
  "Age group": { "<=20": "Age ≤ 20", "21-25": "Age 21–25", ">25": "Age > 25" },
};

export default function GovernancePage() {
  const { tag } = useStudent();
  const [gov, setGov] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchGovernance()
      .then((data) => {
        setGov(data);
        setLoading(false);
      })
      .catch((e) => {
        console.error("Governance load error:", e);
        setLoading(false);
      });
  }, []);

  if (loading || !gov) {
    return (
      <div className="flex items-center justify-center min-h-[420px]">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const early = gov.early;
  const full = gov.full;
  const rawSubgroups = tag === "early" ? gov.subgroups_early : gov.subgroups_full;

  const chartData = (rawSubgroups || [])
    .filter((row: any) => ["Gender", "Scholarship holder", "Age group"].includes(row.feature))
    .map((row: any) => {
      const labelMap = SUBGROUP_LABELS[row.feature] || {};
      const friendly = labelMap[String(row.value)] || `${row.feature}=${row.value}`;
      return {
        group: `${friendly} (n=${row.n})`,
        Recall: Number((row.recall_on_dropouts * 100).toFixed(1)),
        "False Alarm": Number((row.false_alarm_rate * 100).toFixed(1)),
      };
    });

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="space-y-8"
    >
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Model Governance, Evaluation & Fairness</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Empirical evaluation on 885 holdout test students, cost-curve benchmarks, and demographic subgroup parity audits.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="p-6 rounded-xl bg-card border border-border space-y-4">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-blue-500" />
            <h2 className="text-base font-semibold">Holdout Test Set Benchmarks (N=885)</h2>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-border text-muted-foreground font-medium">
                  <th className="py-2.5 px-3">Evaluation Metric</th>
                  <th className="py-2.5 px-3 text-right">Early Model (Sem 1)</th>
                  <th className="py-2.5 px-3 text-right">Full Model (Sem 1 & 2)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                <tr>
                  <td className="py-2.5 px-3 font-medium">Dropout ROC-AUC</td>
                  <td className="py-2.5 px-3 text-right font-mono text-blue-500 font-bold">
                    {early.dropout_roc_auc.toFixed(3)}
                  </td>
                  <td className="py-2.5 px-3 text-right font-mono text-emerald-500 font-bold">
                    {full.dropout_roc_auc.toFixed(3)}
                  </td>
                </tr>
                <tr>
                  <td className="py-2.5 px-3 font-medium">Average Precision (PR-AUC)</td>
                  <td className="py-2.5 px-3 text-right font-mono">{early.dropout_avg_precision.toFixed(3)}</td>
                  <td className="py-2.5 px-3 text-right font-mono">{full.dropout_avg_precision.toFixed(3)}</td>
                </tr>
                <tr>
                  <td className="py-2.5 px-3 font-medium">Cost-Optimal Cutoff (t)</td>
                  <td className="py-2.5 px-3 text-right font-mono">0.16</td>
                  <td className="py-2.5 px-3 text-right font-mono">0.18</td>
                </tr>
                <tr>
                  <td className="py-2.5 px-3 font-medium">Dropout Recall @ Cutoff</td>
                  <td className="py-2.5 px-3 text-right font-mono text-emerald-500 font-semibold">
                    {formatPercent(early.at_chosen_threshold.recall)}
                  </td>
                  <td className="py-2.5 px-3 text-right font-mono text-emerald-500 font-semibold">
                    {formatPercent(full.at_chosen_threshold.recall)}
                  </td>
                </tr>
                <tr>
                  <td className="py-2.5 px-3 font-medium">Dropout Precision @ Cutoff</td>
                  <td className="py-2.5 px-3 text-right font-mono">
                    {formatPercent(early.at_chosen_threshold.precision)}
                  </td>
                  <td className="py-2.5 px-3 text-right font-mono">
                    {formatPercent(full.at_chosen_threshold.precision)}
                  </td>
                </tr>
                <tr>
                  <td className="py-2.5 px-3 font-medium">Cohort Flagged Share</td>
                  <td className="py-2.5 px-3 text-right font-mono">
                    {formatPercent(early.at_chosen_threshold.flagged_share)}
                  </td>
                  <td className="py-2.5 px-3 text-right font-mono">
                    {formatPercent(full.at_chosen_threshold.flagged_share)}
                  </td>
                </tr>
                <tr>
                  <td className="py-2.5 px-3 font-medium">3-Class Macro-F1</td>
                  <td className="py-2.5 px-3 text-right font-mono">{early.three_class_macro_f1.toFixed(3)}</td>
                  <td className="py-2.5 px-3 text-right font-mono">{full.three_class_macro_f1.toFixed(3)}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p className="text-[11px] text-muted-foreground">
            Evaluated strictly once on the unseen holdout partition. Zero post-hoc tuning on test data.
          </p>
        </div>

        <div className="p-6 rounded-xl bg-card border border-border space-y-4">
          <div className="flex items-center gap-2">
            <TrendingDown className="w-5 h-5 text-violet-500" />
            <h2 className="text-base font-semibold">Cost-Curve Decision Analysis (5:1 Penalty)</h2>
          </div>

          <div className="space-y-4 text-xs">
            <div className="p-4 rounded-lg bg-muted/40 border border-border space-y-1.5">
              <div className="flex items-center justify-between font-medium">
                <span>Cost Reduction vs Flag Nobody</span>
                <span className="font-mono text-emerald-500 font-bold text-sm">77.2% Reduction</span>
              </div>
              <p className="text-muted-foreground text-[11px]">
                Flagging nobody accrues an error cost of 1,420 (284 missed dropouts &times; 5). At the 0.16 cutoff, expected cost drops to 324.0.
              </p>
            </div>

            <div className="p-4 rounded-lg bg-muted/40 border border-border space-y-1.5">
              <div className="flex items-center justify-between font-medium">
                <span>Cost Reduction vs Flag Everyone</span>
                <span className="font-mono text-blue-500 font-bold text-sm">~46.0% Reduction</span>
              </div>
              <p className="text-muted-foreground text-[11px]">
                Flagging all 885 students incurs 601 false alarms (cost = 601). The Early model cuts that burden nearly in half.
              </p>
            </div>

            <div className="p-3.5 rounded-lg bg-muted/20 border border-border text-[11px] text-muted-foreground">
              <strong>5:1 Cost Ratio:</strong> Missing a student who drops out costs the institution 5&times; more than an unneeded 15-minute advising check-in.
            </div>
          </div>
        </div>
      </div>

      {/* Subgroup Fairness Chart */}
      <div className="p-6 rounded-xl bg-card border border-border space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Scale className="w-5 h-5 text-amber-500" />
            <div>
              <h2 className="text-base font-semibold">
                Subgroup Fairness Diagnostics ({tag === "early" ? "Early Model" : "Full Model"})
              </h2>
              <p className="text-xs text-muted-foreground">
                Dropout recall vs. false alarm rate across demographic subgroups on the 885-student test set
              </p>
            </div>
          </div>
        </div>

        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 20 }}>
              <XAxis dataKey="group" stroke="#94A3B8" fontSize={11} />
              <YAxis domain={[0, 100]} unit="%" stroke="#94A3B8" fontSize={11} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#0F172A",
                  borderColor: "#334155",
                  borderRadius: "8px",
                  fontSize: "12px",
                  color: "#F8FAFC",
                }}
              />
              <Legend wrapperStyle={{ fontSize: "12px" }} />
              <Bar dataKey="Recall" fill="#3B82F6" radius={[4, 4, 0, 0]} />
              <Bar dataKey="False Alarm" fill="#F59E0B" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs pt-2">
          <div className="p-4 rounded-lg bg-muted/40 border border-border space-y-1.5">
            <span className="font-semibold block">Scholarship Disparity</span>
            <p className="text-muted-foreground text-[11px]">
              Scholarship holders have a low base dropout rate (9.3% vs 39.0%), lowering recall (63.2% vs 91.3%). Mentors should not rely solely on automated flags for scholarship holders.
            </p>
          </div>
          <div className="p-4 rounded-lg bg-muted/40 border border-border space-y-1.5">
            <span className="font-semibold block">Gender Disparity</span>
            <p className="text-muted-foreground text-[11px]">
              Male students experience roughly double the false-alarm rate of females (42.4% vs 23.7%). Outreach must remain supportive, never punitive.
            </p>
          </div>
          <div className="p-4 rounded-lg bg-muted/40 border border-border space-y-1.5">
            <span className="font-semibold block">Small Sample Caveats</span>
            <p className="text-muted-foreground text-[11px]">
              International (N=24) and Special Needs (N=10) subgroups in the test set are too small for statistically reliable parity claims.
            </p>
          </div>
        </div>
      </div>

      {/* Ethical Charter */}
      <div className="p-6 rounded-xl bg-card border border-border space-y-3">
        <div className="flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-blue-500" />
          <h2 className="text-base font-semibold">Ethical Decision-Support Charter</h2>
        </div>
        <ul className="space-y-2 text-xs text-muted-foreground">
          <li className="flex items-start gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 shrink-0" />
            <span>
              <strong className="text-foreground">Decision-Support Only:</strong> The model never makes autonomous punitive or enrollment decisions. It surfaces advisory cues for human mentors.
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 shrink-0" />
            <span>
              <strong className="text-foreground">Unobserved External Factors:</strong> Students who leave in good academic standing depart for personal, relocation, or health reasons not captured in administrative records.
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 shrink-0" />
            <span>
              <strong className="text-foreground">Attribution:</strong> UCI 697 dataset created by Valentim Realinho, Mónica Vieira Martins, Jorge Machado, and Luís Baptista (Instituto Politécnico de Portalegre, Portugal) under CC BY 4.0.
            </span>
          </li>
        </ul>
      </div>
    </motion.div>
  );
}
