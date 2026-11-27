"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { fetchGovernance } from "@/lib/api";
import { formatPercent } from "@/lib/utils";
import { useStudent } from "@/context/StudentContext";
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

const ETHICAL_PRINCIPLES = [
  {
    num: "01",
    title: "Supportive, Not Punitive",
    desc: "This system allocates mentoring, tutoring, and financial support and is never used to penalize students or deny enrollment.",
  },
  {
    num: "02",
    title: "Human in the Loop",
    desc: "Model probabilities act strictly as diagnostic cues; a human academic advisor always makes the final mentoring decision.",
  },
  {
    num: "03",
    title: "Unobserved External Factors",
    desc: "Students leaving in good academic standing often depart for personal, health, or relocation reasons absent from the database.",
  },
  {
    num: "04",
    title: "Attribution",
    desc: "Built on the UCI 697 dataset created by Instituto Politécnico de Portalegre (Realinho et al., 2021) under CC BY 4.0.",
  },
];

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
        <div className="w-7 h-7 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
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
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className="space-y-8"
    >
      <div className="pb-4 border-b border-border">
        <h1 className="text-2xl font-semibold tracking-tight">Model Governance &amp; Fairness</h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          Holdout performance, subgroup diagnostics, and responsible-use safeguards.
        </p>
      </div>

      {/* Holdout Performance */}
      <section className="space-y-3">
        <h2 className="text-base font-semibold">Holdout Performance (885 Students)</h2>
        <div className="overflow-x-auto rounded-lg border border-border bg-card">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-border text-muted-foreground bg-muted/30">
                <th className="py-3 px-4 font-medium">Metric</th>
                <th className="py-3 px-4 text-right font-medium">Early Warning (Sem 1)</th>
                <th className="py-3 px-4 text-right font-medium">Full Curriculum (Sem 1 &amp; 2)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              <tr>
                <td className="py-3 px-4 font-medium">Dropout ROC-AUC</td>
                <td className="py-3 px-4 text-right font-mono font-semibold text-blue-500">
                  {early.dropout_roc_auc.toFixed(3)}
                </td>
                <td className="py-3 px-4 text-right font-mono font-semibold text-emerald-500">
                  {full.dropout_roc_auc.toFixed(3)}
                </td>
              </tr>
              <tr>
                <td className="py-3 px-4 font-medium">Dropout PR-AUC</td>
                <td className="py-3 px-4 text-right font-mono">{early.dropout_avg_precision.toFixed(3)}</td>
                <td className="py-3 px-4 text-right font-mono">{full.dropout_avg_precision.toFixed(3)}</td>
              </tr>
              <tr>
                <td className="py-3 px-4 font-medium">Operational Threshold</td>
                <td className="py-3 px-4 text-right font-mono">16%</td>
                <td className="py-3 px-4 text-right font-mono">18%</td>
              </tr>
              <tr>
                <td className="py-3 px-4 font-medium">Dropout Recall @ Cutoff</td>
                <td className="py-3 px-4 text-right font-mono font-semibold text-emerald-500">
                  {formatPercent(early.at_chosen_threshold.recall)}
                </td>
                <td className="py-3 px-4 text-right font-mono font-semibold text-emerald-500">
                  {formatPercent(full.at_chosen_threshold.recall)}
                </td>
              </tr>
              <tr>
                <td className="py-3 px-4 font-medium">Dropout Precision @ Cutoff</td>
                <td className="py-3 px-4 text-right font-mono">
                  {formatPercent(early.at_chosen_threshold.precision)}
                </td>
                <td className="py-3 px-4 text-right font-mono">
                  {formatPercent(full.at_chosen_threshold.precision)}
                </td>
              </tr>
              <tr>
                <td className="py-3 px-4 font-medium">Cost Reduction vs Flag Nobody</td>
                <td className="py-3 px-4 text-right font-mono font-semibold">77.2%</td>
                <td className="py-3 px-4 text-right font-mono font-semibold">77.0%</td>
              </tr>
              <tr>
                <td className="py-3 px-4 font-medium">Cost Reduction vs Flag Everyone</td>
                <td className="py-3 px-4 text-right font-mono">~46.0%</td>
                <td className="py-3 px-4 text-right font-mono">~44.1%</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* Fairness Audit */}
      <section className="space-y-4 pt-2">
        <div>
          <h2 className="text-base font-semibold">
            Fairness Audit ({tag === "early" ? "Early Model" : "Full Model"})
          </h2>
          <p className="text-xs text-muted-foreground">
            Subgroup diagnostic rows and recall vs. false alarm comparison across demographic cohorts.
          </p>
        </div>

        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 10 }}>
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
              <Bar dataKey="Recall" fill="#2563EB" radius={[4, 4, 0, 0]} />
              <Bar dataKey="False Alarm" fill="#F59E0B" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="divide-y divide-border border-y border-border text-xs">
          <div className="py-3.5 grid grid-cols-1 md:grid-cols-12 gap-3">
            <div className="md:col-span-3">
              <span className="font-semibold block">Scholarship disparity</span>
              <span className="text-muted-foreground">Metric: Dropout recall</span>
            </div>
            <div className="md:col-span-3 font-mono text-amber-500">
              63.2% (scholarship) vs 91.3% (other)
            </div>
            <div className="md:col-span-6 text-muted-foreground">
              Scholarship holders have a low base dropout rate (9.3% vs 39.0%). Advisors should not rely solely on automated alerts for scholarship recipients.
            </div>
          </div>

          <div className="py-3.5 grid grid-cols-1 md:grid-cols-12 gap-3">
            <div className="md:col-span-3">
              <span className="font-semibold block">Gender disparity</span>
              <span className="text-muted-foreground">Metric: False alarm rate</span>
            </div>
            <div className="md:col-span-3 font-mono text-blue-500">
              42.4% (male) vs 23.7% (female)
            </div>
            <div className="md:col-span-6 text-muted-foreground">
              Male students are flagged more frequently (66.3% vs 38.4%). Outreach must remain supportive and encouraging.
            </div>
          </div>

          <div className="py-3.5 grid grid-cols-1 md:grid-cols-12 gap-3">
            <div className="md:col-span-3">
              <span className="font-semibold block">Age disparity</span>
              <span className="text-muted-foreground">Metric: Dropout recall</span>
            </div>
            <div className="md:col-span-3 font-mono">
              84.1% (age ≤ 20) vs 94.1% (age &gt; 25)
            </div>
            <div className="md:col-span-6 text-muted-foreground">
              Mature students carry stronger financial/attendance risk signals. International (N=24) and Special Needs (N=10) groups are too small for parity conclusions.
            </div>
          </div>
        </div>
      </section>

      {/* Ethical Decision Support */}
      <section className="space-y-3 pt-2">
        <h2 className="text-base font-semibold">Ethical Decision Support</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {ETHICAL_PRINCIPLES.map((p) => (
            <div key={p.num} className="p-4 rounded-lg border border-border bg-card/50 flex gap-3">
              <span className="font-mono text-xs font-semibold text-blue-500 pt-0.5">{p.num}</span>
              <div>
                <h3 className="text-sm font-semibold">{p.title}</h3>
                <p className="text-xs text-muted-foreground mt-1">{p.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>
    </motion.div>
  );
}
