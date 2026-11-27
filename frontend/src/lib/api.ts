const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export interface PredictResponse {
  risk: number;
  raw_p: number;
  tier: "High" | "Medium" | "Low";
  threshold: number;
  flagged: boolean;
  probs: {
    Dropout: number;
    Enrolled: number;
    Graduate: number;
  };
  contributions: Array<{
    feature: string;
    display: string;
    impact: number;
    direction: "Increases Risk" | "Reduces Risk";
  }>;
  talking_points: string[];
  review_window: string;
  guideline: string;
}

export interface SimulateResponse {
  baseline_risk: number;
  baseline_tier: "High" | "Medium" | "Low";
  simulated_risk: number;
  simulated_tier: "High" | "Medium" | "Low";
  risk_diff: number;
  validated_values: Record<string, any>;
}

export interface BatchResponse {
  total_students: number;
  flagged_count: number;
  flagged_rate: number;
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  average_risk: number;
  students: Array<{
    id: number;
    risk: number;
    tier: "High" | "Medium" | "Low";
    flagged: boolean;
    course: string;
    age: number;
    tuition_paid: boolean;
    approved_sem1: number;
    enrolled_sem1: number;
    grade_sem1: number;
    actual_outcome: string;
  }>;
}

export async function fetchMetadata() {
  const res = await fetch(`${API_BASE}/api/metadata`);
  if (!res.ok) throw new Error("Failed to load metadata");
  return res.json();
}

export async function fetchRandomStudent(tag: string = "early") {
  const res = await fetch(`${API_BASE}/api/random_student?tag=${tag}`);
  if (!res.ok) throw new Error("Failed to sample student");
  return res.json();
}

export async function predictStudent(tag: string, values: Record<string, any>): Promise<PredictResponse> {
  const res = await fetch(`${API_BASE}/api/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tag, values }),
  });
  if (!res.ok) throw new Error("Prediction request failed");
  return res.json();
}

export async function simulateIntervention(
  tag: string,
  baseline_values: Record<string, any>,
  tutoring_boost: number,
  grant_relief: boolean,
  grade_boost: number
): Promise<SimulateResponse> {
  const res = await fetch(`${API_BASE}/api/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      tag,
      baseline_values,
      tutoring_boost,
      grant_relief,
      grade_boost,
    }),
  });
  if (!res.ok) throw new Error("Simulation request failed");
  return res.json();
}

export async function uploadBatchFile(file: File, tag: string = "early"): Promise<BatchResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/api/batch?tag=${tag}`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Batch scoring failed");
  }
  return res.json();
}

export async function fetchGovernance() {
  const res = await fetch(`${API_BASE}/api/governance`);
  if (!res.ok) throw new Error("Failed to load governance metrics");
  return res.json();
}

export interface OverviewResponse {
  tag: "early" | "full";
  n_test: number;
  threshold: number;
  high_tier_cutoff: number;
  roc_auc: number;
  recall: number;
  precision: number;
  flagged_share: number;
  cost_reduction_nobody: string;
  cost_reduction_all: string;
  tier_counts: { High: number; Medium: number; Low: number };
  risk_distribution: Array<{ bucket: string; count: number; zone: "High" | "Medium" | "Low" }>;
  priority_students: Array<{
    id: number;
    course: string;
    age: number;
    enrolled: number;
    approved: number;
    grade: number;
    tuition: boolean;
    debt: boolean;
    risk: number;
    tier: "High" | "Medium" | "Low";
    actual_outcome: string;
    values: Record<string, any>;
  }>;
}

export async function fetchOverview(tag: "early" | "full" = "early"): Promise<OverviewResponse> {
  const res = await fetch(`${API_BASE}/api/overview?tag=${tag}`);
  if (!res.ok) throw new Error("Failed to load overview analytics");
  return res.json();
}

export async function fetchSampleBatch(tag: "early" | "full" = "early", n: number = 50): Promise<BatchResponse> {
  const res = await fetch(`${API_BASE}/api/sample_batch?tag=${tag}&n=${n}`);
  if (!res.ok) throw new Error("Failed to sample batch cohort");
  return res.json();
}
