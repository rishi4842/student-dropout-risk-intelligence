"""FastAPI backend service for Student Retention Intelligence SaaS.
Directly uses serialized joblib pipelines and TreeSHAP explainers.
"""
import io
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Set matplotlib cache
os.environ["MPLCONFIGDIR"] = "/tmp/matplotlib"

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.explain import HIGH_TIER, fmt_value
from src.pipeline import load_data
from src.predict import (TIER_ACTIONS, feature_specs, load_artifacts,
                          random_student, score_student, top_changes)

app = FastAPI(
    title="Student Retention Intelligence API",
    description="Machine Learning early-warning inference and TreeSHAP explainability engine",
    version="2.0.0"
)

# CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------ CACHED ARTIFACTS
print("Loading model artifacts...")
artifacts = {
    "early": load_artifacts("xgboost", "early", ROOT),
    "full": load_artifacts("xgboost", "full", ROOT)
}
dataset_df = load_data(ROOT / "data" / "data.csv")
base_dropout_rate = float((dataset_df["Target"] == "Dropout").mean())
print("Model artifacts and dataset loaded successfully.")

# Mappings
COURSE_MAP = {
    33: "Biofuel Production Technologies",
    171: "Animation & Multimedia Design",
    8014: "Social Service (Evening)",
    9003: "Agronomy",
    9070: "Communication Design",
    9085: "Veterinary Nursing",
    9119: "Informatics Engineering",
    9130: "Equinculture",
    9147: "Management",
    9238: "Social Service (Daytime)",
    9254: "Tourism",
    9500: "Nursing",
    9556: "Oral Hygiene",
    9670: "Advertising & Marketing",
    9773: "Journalism & Communication",
    9853: "Basic Education",
    9991: "Management (Evening)"
}

PERSONAS = {
    "High-Performing Scholar": {
        "target": "Graduate (Synthetic Persona)",
        "values": {
            "Curricular units 1st sem (credited)": 0,
            "Curricular units 1st sem (enrolled)": 6,
            "Curricular units 1st sem (evaluations)": 8,
            "Curricular units 1st sem (approved)": 6,
            "Curricular units 1st sem (grade)": 16.2,
            "Curricular units 1st sem (without evaluations)": 0,
            "Curricular units 2nd sem (credited)": 0,
            "Curricular units 2nd sem (enrolled)": 6,
            "Curricular units 2nd sem (evaluations)": 8,
            "Curricular units 2nd sem (approved)": 6,
            "Curricular units 2nd sem (grade)": 16.5,
            "Curricular units 2nd sem (without evaluations)": 0,
            "Tuition fees up to date": 1,
            "Debtor": 0,
            "Scholarship holder": 1,
            "Age at enrollment": 19,
            "Gender": 0,
            "Admission grade": 158.0,
            "Previous qualification (grade)": 160.0,
            "Course": 9500,
            "Application order": 1,
            "Application mode": 1,
            "Daytime/evening attendance": 1,
            "Displaced": 1,
            "Educational special needs": 0,
            "International": 0,
            "Marital status": 1,
            "Nacionality": 1,
            "Previous qualification": 1,
            "Mother's qualification": 1,
            "Father's qualification": 1,
            "Mother's occupation": 4,
            "Father's occupation": 4,
            "Unemployment rate": 10.8,
            "Inflation rate": 1.4,
            "GDP": 1.74
        }
    },
    "High-Risk Attrition": {
        "target": "Dropout (Synthetic Persona)",
        "values": {
            "Curricular units 1st sem (credited)": 0,
            "Curricular units 1st sem (enrolled)": 6,
            "Curricular units 1st sem (evaluations)": 6,
            "Curricular units 1st sem (approved)": 0,
            "Curricular units 1st sem (grade)": 0.0,
            "Curricular units 1st sem (without evaluations)": 0,
            "Curricular units 2nd sem (credited)": 0,
            "Curricular units 2nd sem (enrolled)": 6,
            "Curricular units 2nd sem (evaluations)": 6,
            "Curricular units 2nd sem (approved)": 0,
            "Curricular units 2nd sem (grade)": 0.0,
            "Curricular units 2nd sem (without evaluations)": 0,
            "Tuition fees up to date": 0,
            "Debtor": 1,
            "Scholarship holder": 0,
            "Age at enrollment": 28,
            "Gender": 1,
            "Admission grade": 105.0,
            "Previous qualification (grade)": 110.0,
            "Course": 9147,
            "Application order": 1,
            "Application mode": 39,
            "Daytime/evening attendance": 0,
            "Displaced": 0,
            "Educational special needs": 0,
            "International": 0,
            "Marital status": 2,
            "Nacionality": 1,
            "Previous qualification": 1,
            "Mother's qualification": 37,
            "Father's qualification": 37,
            "Mother's occupation": 9,
            "Father's occupation": 9,
            "Unemployment rate": 13.9,
            "Inflation rate": -0.3,
            "GDP": 0.79
        }
    },
    "Borderline Struggling": {
        "target": "Enrolled / At Risk (Synthetic Persona)",
        "values": {
            "Curricular units 1st sem (credited)": 0,
            "Curricular units 1st sem (enrolled)": 6,
            "Curricular units 1st sem (evaluations)": 7,
            "Curricular units 1st sem (approved)": 3,
            "Curricular units 1st sem (grade)": 11.4,
            "Curricular units 1st sem (without evaluations)": 0,
            "Curricular units 2nd sem (credited)": 0,
            "Curricular units 2nd sem (enrolled)": 6,
            "Curricular units 2nd sem (evaluations)": 7,
            "Curricular units 2nd sem (approved)": 3,
            "Curricular units 2nd sem (grade)": 11.0,
            "Curricular units 2nd sem (without evaluations)": 0,
            "Tuition fees up to date": 1,
            "Debtor": 0,
            "Scholarship holder": 0,
            "Age at enrollment": 24,
            "Gender": 0,
            "Admission grade": 120.0,
            "Previous qualification (grade)": 125.0,
            "Course": 9254,
            "Application order": 2,
            "Application mode": 1,
            "Daytime/evening attendance": 1,
            "Displaced": 1,
            "Educational special needs": 0,
            "International": 0,
            "Marital status": 1,
            "Nacionality": 1,
            "Previous qualification": 1,
            "Mother's qualification": 19,
            "Father's qualification": 19,
            "Mother's occupation": 4,
            "Father's occupation": 7,
            "Unemployment rate": 11.1,
            "Inflation rate": 1.4,
            "GDP": 0.32
        }
    }
}

# ------------------------------------------------------------------ SCHEMAS
class PredictRequest(BaseModel):
    tag: str = "early"  # "early" or "full"
    values: Dict[str, Any]

class SimulateRequest(BaseModel):
    tag: str = "early"
    baseline_values: Dict[str, Any]
    tutoring_boost: int = 1
    grant_relief: bool = True
    grade_boost: float = 1.0

# ------------------------------------------------------------------ ENDPOINTS
@app.get("/api/health")
def health():
    return {"status": "ok", "version": "2.0.0", "models": list(artifacts.keys())}

@app.get("/api/metadata")
def get_metadata():
    specs_early = feature_specs(dataset_df, artifacts["early"].features)
    specs_full = feature_specs(dataset_df, artifacts["full"].features)
    
    return {
        "features_early": artifacts["early"].features,
        "features_full": artifacts["full"].features,
        "threshold_early": artifacts["early"].threshold,
        "threshold_full": artifacts["full"].threshold,
        "base_dropout_rate": base_dropout_rate,
        "high_tier_cutoff": HIGH_TIER,
        "course_map": COURSE_MAP,
        "specs_early": specs_early,
        "specs_full": specs_full,
        "personas": PERSONAS
    }

@app.get("/api/random_student")
def get_random_student(tag: str = "early"):
    target_tag = "early" if tag == "early" else "full"
    art = artifacts[target_tag]
    vals, outcome = random_student(dataset_df, art.features)
    return {"values": vals, "outcome": outcome}

@app.post("/api/predict")
def predict_student(req: PredictRequest):
    target_tag = "early" if req.tag == "early" else "full"
    art = artifacts[target_tag]
    
    # Ensure all required features are present
    vals = dict(req.values)
    for f in art.features:
        if f not in vals:
            s = dataset_df[f]
            vals[f] = float(s.median()) if "float" in str(s.dtype) else int(s.mode().iloc[0])

    res = score_student(art, vals)
    risk = float(res["risk"])
    tier = str(res["tier"])
    raw = float(res["raw"])
    probs = res.get("probs", {"Dropout": risk, "Enrolled": 0.18, "Graduate": max(0.0, 1.0 - risk - 0.18)})
    
    # Format SHAP contributions for clean Recharts display
    contrib = res["contributions"]
    top_items = []
    for f in contrib.head(8).index:
        v = vals.get(f, 0)
        display_label = f
        if f == "Course":
            display_label = f"Course ({COURSE_MAP.get(int(v), f'Code {v}')})"
        elif f == "Tuition fees up to date":
            display_label = f"Tuition ({'Paid' if int(v) == 1 else 'Overdue'})"
        elif f == "Debtor":
            display_label = f"Debt Status ({'Has Debt' if int(v) == 1 else 'No Debt'})"
        elif f == "Scholarship holder":
            display_label = f"Scholarship ({'Grantee' if int(v) == 1 else 'No'})"
        elif f == "Gender":
            display_label = f"Gender ({'Male' if int(v) == 1 else 'Female'})"
        else:
            display_label = f"{f.replace('Curricular units ', '')} = {fmt_value(v)}"
        
        impact = float(contrib[f])
        top_items.append({
            "feature": f,
            "display": display_label,
            "impact": round(impact, 4),
            "direction": "Increases Risk" if impact > 0 else "Reduces Risk"
        })
    
    if len(contrib) > 8:
        rest_val = float(contrib.iloc[8:].sum())
        top_items.append({
            "feature": "other",
            "display": f"{len(contrib) - 8} Other Features Combined",
            "impact": round(rest_val, 4),
            "direction": "Increases Risk" if rest_val > 0 else "Reduces Risk"
        })

    # Advisor talking points
    enrolled = vals.get("Curricular units 1st sem (enrolled)", 0)
    approved = vals.get("Curricular units 1st sem (approved)", 0)
    grade = vals.get("Curricular units 1st sem (grade)", 0.0)
    
    talking_points = []
    if enrolled == 0:
        talking_points.append("Registration Status: Student has 0 enrolled units in Semester 1. Address matriculation, administrative holds, or leave of absence.")
    elif approved < enrolled:
        talking_points.append(f"Academic Recovery: Student did not pass {enrolled - approved} of {enrolled} enrolled units. Connect with course coordinators for remedial tutoring.")
    else:
        talking_points.append(f"Academic Momentum: Passed all {enrolled} enrolled units with an average grade of {grade:.1f}/20. Discuss honors coursework or degree pacing.")

    if vals.get("Tuition fees up to date", 1) == 0:
        talking_points.append("Financial Status: Overdue tuition payments detected. Discuss institutional emergency hardship funds or installment plans.")
    if vals.get("Debtor", 0) == 1:
        talking_points.append("Institutional Debt: Active unpaid student debts on record. Prioritize financial aid counseling.")
    if vals.get("Age at enrollment", 20) > 25:
        talking_points.append("Mature Student Support: Discuss work-life-study scheduling flexibility and adult learner peer networks.")

    review_window = "Within 7 calendar days" if tier == "High" else ("Within 30 calendar days" if tier == "Medium" else "Regular semester milestone")

    return {
        "risk": round(risk, 4),
        "raw_p": round(raw, 4),
        "tier": tier,
        "threshold": art.threshold,
        "flagged": risk >= art.threshold,
        "probs": {k: round(v, 4) for k, v in probs.items()},
        "contributions": top_items,
        "talking_points": talking_points,
        "review_window": review_window,
        "guideline": TIER_ACTIONS[tier]
    }

@app.post("/api/simulate")
def simulate_intervention(req: SimulateRequest):
    target_tag = "early" if req.tag == "early" else "full"
    art = artifacts[target_tag]
    
    baseline_vals = dict(req.baseline_values)
    sim_vals = dict(baseline_vals)
    
    # 1. Academic Tutoring constraint
    base_enrolled = baseline_vals.get("Curricular units 1st sem (enrolled)", 0)
    base_approved = baseline_vals.get("Curricular units 1st sem (approved)", 0)
    
    if base_enrolled > 0:
        max_possible_boost = max(0, base_enrolled - base_approved)
        applied_boost = min(req.tutoring_boost, max_possible_boost)
        sim_vals["Curricular units 1st sem (approved)"] = base_approved + applied_boost
        sim_vals["Curricular units 1st sem (evaluations)"] = max(
            sim_vals.get("Curricular units 1st sem (evaluations)", 0),
            sim_vals["Curricular units 1st sem (approved)"]
        )
        if sim_vals["Curricular units 1st sem (approved)"] > 0 and sim_vals.get("Curricular units 1st sem (grade)", 0.0) < 10.0:
            sim_vals["Curricular units 1st sem (grade)"] = 11.5

    # 2. Financial Grant
    if req.grant_relief:
        sim_vals["Tuition fees up to date"] = 1
        sim_vals["Debtor"] = 0

    # 3. Grade boost
    if req.grade_boost > 0:
        sim_vals["Curricular units 1st sem (grade)"] = min(
            20.0, sim_vals.get("Curricular units 1st sem (grade)", 0.0) + req.grade_boost
        )

    base_score = score_student(art, baseline_vals)
    sim_score = score_student(art, sim_vals)
    
    base_risk = float(base_score["risk"])
    sim_risk = float(sim_score["risk"])

    clean_vals = {}
    for k, v in sim_vals.items():
        if "int" in str(type(v)).lower():
            clean_vals[k] = int(v)
        elif "float" in str(type(v)).lower():
            clean_vals[k] = float(v)
        else:
            clean_vals[k] = v
    
    return {
        "baseline_risk": round(base_risk, 4),
        "baseline_tier": base_score["tier"],
        "simulated_risk": round(sim_risk, 4),
        "simulated_tier": sim_score["tier"],
        "risk_diff": round(sim_risk - base_risk, 4),
        "validated_values": clean_vals
    }

@app.post("/api/batch")
async def batch_score(file: UploadFile = File(...), tag: str = "early"):
    target_tag = "early" if tag == "early" else "full"
    art = artifacts[target_tag]
    
    contents = await file.read()
    try:
        # Detect delimiter (semicolon vs comma)
        sample = contents[:2048].decode("utf-8", errors="ignore")
        delim = ";" if ";" in sample else ","
        df_upload = pd.read_csv(io.BytesIO(contents), sep=delim)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV file: {str(e)}")

    if len(df_upload) == 0:
        raise HTTPException(status_code=400, detail="Uploaded CSV file is empty.")

    # Validate required columns
    missing = [c for c in art.features if c not in df_upload.columns]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"CSV missing {len(missing)} required features for {target_tag} pipeline: {missing[:5]}"
        )

    # Score batch
    results = []
    high_count = 0
    medium_count = 0
    low_count = 0
    flagged_count = 0
    
    for idx, row in df_upload.iterrows():
        row_dict = {f: row[f] for f in art.features}
        score_res = score_student(art, row_dict)
        r = float(score_res["risk"])
        tr = str(score_res["tier"])
        is_flagged = r >= art.threshold
        
        if tr == "High":
            high_count += 1
        elif tr == "Medium":
            medium_count += 1
        else:
            low_count += 1
        if is_flagged:
            flagged_count += 1

        results.append({
            "id": idx + 1,
            "risk": round(r, 4),
            "tier": tr,
            "flagged": is_flagged,
            "course": COURSE_MAP.get(int(row.get("Course", 0)), str(row.get("Course", "-"))),
            "age": int(row.get("Age at enrollment", 20)),
            "tuition_paid": bool(row.get("Tuition fees up to date", 1) == 1),
            "approved_sem1": int(row.get("Curricular units 1st sem (approved)", 0)),
            "enrolled_sem1": int(row.get("Curricular units 1st sem (enrolled)", 0)),
            "grade_sem1": round(float(row.get("Curricular units 1st sem (grade)", 0.0)), 1),
            "actual_outcome": str(row.get("Target", "Unknown"))
        })

    # Sort priority queue descending by risk
    results.sort(key=lambda x: x["risk"], reverse=True)

    avg_risk = float(np.mean([r["risk"] for r in results]))

    return {
        "total_students": len(results),
        "flagged_count": flagged_count,
        "flagged_rate": round(flagged_count / len(results), 4),
        "high_risk_count": high_count,
        "medium_risk_count": medium_count,
        "low_risk_count": low_count,
        "average_risk": round(avg_risk, 4),
        "students": results[:500]  # Return top 500
    }

@app.get("/api/governance")
def get_governance():
    res_early = json.load(open(ROOT / "reports" / "test_results_xgboost_early.json"))
    res_full = json.load(open(ROOT / "reports" / "test_results_xgboost_full.json"))
    
    subgroup_early = pd.read_csv(ROOT / "reports" / "subgroup_test_xgboost_early.csv").to_dict(orient="records")
    subgroup_full = pd.read_csv(ROOT / "reports" / "subgroup_test_xgboost_full.csv").to_dict(orient="records")

    return {
        "early": res_early,
        "full": res_full,
        "subgroups_early": subgroup_early,
        "subgroups_full": subgroup_full,
        "cost_benchmarks": {
            "early": {
                "expected_cost": 324.0,
                "cost_nobody_flagged": 1420.0,
                "cost_reduction_vs_nobody": "77.2%",
                "cost_all_flagged": 600.0,
                "cost_reduction_vs_all": "46.0%"
            },
            "full": {
                "expected_cost": 327.0,
                "cost_nobody_flagged": 1420.0,
                "cost_reduction_vs_nobody": "77.0%",
                "cost_all_flagged": 585.0,
                "cost_reduction_vs_all": "44.1%"
            }
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
