"use client";

import React, { useEffect, useState } from "react";
import { fetchGovernance } from "@/lib/api";
import { formatPercent } from "@/lib/utils";
import { 
  ShieldAlert, 
  Scale, 
  TrendingDown, 
  CheckCircle2, 
  AlertTriangle,
  BookOpen
} from "lucide-react";

export default function GovernancePage() {
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
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  const early = gov.early;
  const full = gov.full;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-white">Model Governance, Evaluation & Fairness</h1>
        <p className="text-sm text-slate-400 mt-1">
          Empirical evaluation on 885 holdout test students, cost-curve optimizations, and demographic subgroup parity audits.
        </p>
      </div>

      {/* Benchmarks Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Holdout Performance Table */}
        <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-blue-400" />
            <h2 className="text-base font-semibold text-white">Holdout Test Set Benchmarks (N=885)</h2>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 font-medium">
                  <th className="py-2.5 px-3">Evaluation Metric</th>
                  <th className="py-2.5 px-3 text-right">Early Model (Sem 1)</th>
                  <th className="py-2.5 px-3 text-right">Full Model (Sem 1 & 2)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-200">
                <tr>
                  <td className="py-2.5 px-3 font-medium">Dropout ROC-AUC</td>
                  <td className="py-2.5 px-3 text-right font-mono text-blue-400 font-bold">{early.dropout_roc_auc.toFixed(3)}</td>
                  <td className="py-2.5 px-3 text-right font-mono text-emerald-400 font-bold">{full.dropout_roc_auc.toFixed(3)}</td>
                </tr>
                <tr>
                  <td className="py-2.5 px-3 font-medium">Average Precision (PR-AUC)</td>
                  <td className="py-2.5 px-3 text-right font-mono text-slate-300">{early.dropout_avg_precision.toFixed(3)}</td>
                  <td className="py-2.5 px-3 text-right font-mono text-slate-300">{full.dropout_avg_precision.toFixed(3)}</td>
                </tr>
                <tr>
                  <td className="py-2.5 px-3 font-medium">Cost-Optimal Cutoff (t)</td>
                  <td className="py-2.5 px-3 text-right font-mono text-slate-300">0.16</td>
                  <td className="py-2.5 px-3 text-right font-mono text-slate-300">0.18</td>
                </tr>
                <tr>
                  <td className="py-2.5 px-3 font-medium">Dropout Recall @ Cutoff</td>
                  <td className="py-2.5 px-3 text-right font-mono text-emerald-400 font-semibold">{formatPercent(early.at_chosen_threshold.recall)}</td>
                  <td className="py-2.5 px-3 text-right font-mono text-emerald-400 font-semibold">{formatPercent(full.at_chosen_threshold.recall)}</td>
                </tr>
                <tr>
                  <td className="py-2.5 px-3 font-medium">Dropout Precision @ Cutoff</td>
                  <td className="py-2.5 px-3 text-right font-mono text-slate-300">{formatPercent(early.at_chosen_threshold.precision)}</td>
                  <td className="py-2.5 px-3 text-right font-mono text-slate-300">{formatPercent(full.at_chosen_threshold.precision)}</td>
                </tr>
                <tr>
                  <td className="py-2.5 px-3 font-medium">Cohort Flagged Share</td>
                  <td className="py-2.5 px-3 text-right font-mono text-slate-300">{formatPercent(early.at_chosen_threshold.flagged_share)}</td>
                  <td className="py-2.5 px-3 text-right font-mono text-slate-300">{formatPercent(full.at_chosen_threshold.flagged_share)}</td>
                </tr>
                <tr>
                  <td className="py-2.5 px-3 font-medium">3-Class Macro-F1</td>
                  <td className="py-2.5 px-3 text-right font-mono text-slate-300">{early.three_class_macro_f1.toFixed(3)}</td>
                  <td className="py-2.5 px-3 text-right font-mono text-slate-300">{full.three_class_macro_f1.toFixed(3)}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p className="text-[11px] text-slate-500">
            *Evaluated strictly once on unseen test partition. No post-hoc tuning on test data.
          </p>
        </div>

        {/* Cost Reduction Analysis */}
        <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
          <div className="flex items-center gap-2">
            <TrendingDown className="w-5 h-5 text-purple-400" />
            <h2 className="text-base font-semibold text-white">Cost-Curve Decision Analysis (5:1 Penalty)</h2>
          </div>

          <div className="space-y-4 text-xs text-slate-300">
            <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/60 space-y-2">
              <div className="flex items-center justify-between text-white font-medium">
                <span>Cost Reduction vs Flag Nobody</span>
                <span className="font-mono text-emerald-400 font-bold text-sm">77.2% Reduction</span>
              </div>
              <p className="text-slate-400 text-[11px]">
                Flagging nobody accrues an error cost of 1,420 (284 missed dropouts &times; 5). At the 0.16 cutoff, expected cost plummets to 324.0.
              </p>
            </div>

            <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/60 space-y-2">
              <div className="flex items-center justify-between text-white font-medium">
                <span>Cost Reduction vs Flag Everyone</span>
                <span className="font-mono text-blue-400 font-bold text-sm">~46.0% Reduction</span>
              </div>
              <p className="text-slate-400 text-[11px]">
                Flagging all 885 students incurs 601 false alarms (cost = 601). The Early model cuts that cost by nearly half by isolating high-probability at-risk candidates.
              </p>
            </div>

            <div className="p-3.5 rounded-lg bg-slate-800/20 border border-slate-800 text-[11px] text-slate-400">
              <strong>Viva Voce Note:</strong> The cost ratio $5:1$ formalizes institutional economics: missing a student who drops out costs the university tuition revenue and career potential, whereas an unneeded 15-minute advising session costs minimal faculty overhead.
            </div>
          </div>
        </div>
      </div>

      {/* Subgroup Fairness Diagnostics */}
      <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
        <div className="flex items-center gap-2">
          <Scale className="w-5 h-5 text-amber-400" />
          <h2 className="text-base font-semibold text-white">Subgroup Fairness Audit (Early Model on Holdout Set)</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/60 space-y-2">
            <span className="font-semibold text-slate-200 block">Scholarship Disparity</span>
            <p className="text-slate-400 text-[11px]">
              Scholarship holders have lower base dropout rates (9.3% vs 39.0%), which causes their recall to be lower (<strong>63.2%</strong> vs <strong>91.3%</strong>).
            </p>
            <div className="pt-2 text-amber-400 text-[11px] font-medium">
              Policy: Mentors should not rely solely on automated flags for scholarship holders.
            </div>
          </div>

          <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/60 space-y-2">
            <span className="font-semibold text-slate-200 block">Gender Parity</span>
            <p className="text-slate-400 text-[11px]">
              Male students experience double the false alarm rate of females (<strong>42.4%</strong> vs <strong>23.7%</strong>), with 66.3% of males flagged vs 38.4% of females.
            </p>
            <div className="pt-2 text-blue-400 text-[11px] font-medium">
              Policy: Ensure male student outreach focuses on academic encouragement, not stigma.
            </div>
          </div>

          <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/60 space-y-2">
            <span className="font-semibold text-slate-200 block">Age Disparity & Sample Caveats</span>
            <p className="text-slate-400 text-[11px]">
              Mature students (&gt;25) have higher recall (<strong>94.1%</strong> vs <strong>84.1%</strong> for &le;20) due to financial/family pressures.
            </p>
            <div className="pt-2 text-slate-400 text-[11px]">
              Sample Warning: International (N=24) and Special Needs (N=10) are too small to draw statistical parity conclusions.
            </div>
          </div>
        </div>
      </div>

      {/* Ethical Charter */}
      <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
        <div className="flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-blue-400" />
          <h2 className="text-base font-semibold text-white">Ethical Decision-Support Charter</h2>
        </div>
        <ul className="space-y-2 text-xs text-slate-300">
          <li className="flex items-start gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 shrink-0"></span>
            <span><strong>Decision-Support Tool Only:</strong> The model never makes autonomous punitive or enrollment decisions. It provides advisory triage cues for professional mentors.</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 shrink-0"></span>
            <span><strong>Unobserved External Reasons:</strong> Students who leave in good standing depart due to personal, relocation, or health factors unmeasured by the database. Exit interviews remain indispensable.</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 shrink-0"></span>
            <span><strong>Attribution:</strong> Developed on the UCI 697 dataset created by Valentim Realinho, Mónica Vieira Martins, Jorge Machado, and Luís Baptista (*Instituto Politécnico de Portalegre*, Portugal) under CC BY 4.0.</span>
          </li>
        </ul>
      </div>
    </div>
  );
}
