"""Parity tests verifying that FastAPI backend endpoints match the original
scikit-learn pipeline and TreeSHAP calculations within numerical tolerance.
"""
import pytest
from fastapi.testclient import TestClient

from backend.main import app, artifacts, dataset_df
from src.predict import score_student

client = TestClient(app)


def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "early" in data["models"]
    assert "full" in data["models"]


def test_api_metadata():
    res = client.get("/api/metadata")
    assert res.status_code == 200
    data = res.json()
    assert len(data["features_early"]) == 30
    assert len(data["features_full"]) == 36
    assert abs(data["threshold_early"] - 0.16) < 1e-4
    assert abs(data["threshold_full"] - 0.18) < 1e-4
    assert len(data["personas"]) == 3


def test_api_predict_parity():
    # Test random row from dataset
    row = dataset_df.iloc[10]
    art_early = artifacts["early"]
    vals = {}
    for f in art_early.features:
        v = row[f]
        vals[f] = int(v) if "int" in str(type(v)).lower() else float(v)

    # Reference prediction from original src.predict
    ref = score_student(art_early, vals)

    # API prediction
    res = client.post("/api/predict", json={"tag": "early", "values": vals})
    assert res.status_code == 200
    data = res.json()

    # Assert exact numerical parity
    assert abs(data["risk"] - float(ref["risk"])) < 1e-4
    assert abs(data["raw_p"] - float(ref["raw"])) < 1e-4
    assert data["tier"] == ref["tier"]
    assert len(data["contributions"]) > 0


def test_api_simulate_constraints():
    # Test that simulate enforces approved <= evaluations <= enrolled
    vals = {}
    for f in artifacts["early"].features:
        v = dataset_df.iloc[0][f]
        vals[f] = int(v) if "int" in str(type(v)).lower() else float(v)
    vals["Curricular units 1st sem (enrolled)"] = 5
    vals["Curricular units 1st sem (approved)"] = 2
    vals["Curricular units 1st sem (evaluations)"] = 3

    res = client.post("/api/simulate", json={
        "tag": "early",
        "baseline_values": vals,
        "tutoring_boost": 2,
        "grant_relief": True,
        "grade_boost": 1.5
    })
    assert res.status_code == 200
    data = res.json()
    assert data["simulated_risk"] <= data["baseline_risk"]
    v = data["validated_values"]
    assert v["Curricular units 1st sem (approved)"] <= v["Curricular units 1st sem (enrolled)"]
    assert v["Curricular units 1st sem (approved)"] <= v["Curricular units 1st sem (evaluations)"]


def test_api_governance_metrics():
    res = client.get("/api/governance")
    assert res.status_code == 200
    data = res.json()
    assert abs(data["early"]["dropout_roc_auc"] - 0.8929) < 1e-3
    assert abs(data["full"]["dropout_roc_auc"] - 0.9147) < 1e-3
    assert data["early"]["at_chosen_threshold"]["recall"] > 0.89
    assert data["cost_benchmarks"]["early"]["cost_reduction_vs_nobody"] == "77.2%"


def test_api_overview_real_holdout():
    res = client.get("/api/overview?tag=early")
    assert res.status_code == 200
    data = res.json()
    assert data["n_test"] == 885
    assert len(data["risk_distribution"]) == 10
    assert sum(b["count"] for b in data["risk_distribution"]) == 885
    assert len(data["priority_students"]) >= 10


def test_api_sample_batch():
    res = client.get("/api/sample_batch?tag=early&n=25")
    assert res.status_code == 200
    data = res.json()
    assert data["total_students"] == 25
    assert len(data["students"]) == 25
    risks = [s["risk"] for s in data["students"]]
    assert risks == sorted(risks, reverse=True)
