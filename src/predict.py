"""Scoring helpers for the Streamlit app. Put this file in src/predict.py.

Kept separate from the UI so the logic can be tested without Streamlit.
"""
import json
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import shap

from src.evaluate import apply_calibrator
from src.explain import fmt_value, owner_map, tier
from src.pipeline import BINARY, NOMINAL, feature_columns

# Suggestions for a mentor, not decisions about a student.
TIER_ACTIONS = {
    "High": "Priority outreach: a mentor or adviser contacts the student soon to "
            "discuss their situation and the support available.",
    "Medium": "Light-touch support: an automated check-in, a peer-tutoring or "
              "study-workshop referral, and a look at progress next month.",
    "Low": "Standard advising schedule. No extra action suggested by the model.",
}


@dataclass
class Artifacts:
    pipe: object
    method: str
    calibrator: object
    threshold: float
    decision: dict
    explainer: object
    features: list


def load_artifacts(model="xgboost", tag="early", root="."):
    root, name = Path(root), f"{model}_{tag}"
    decision = json.load(open(root / "models" / f"decision_{name}.json"))
    saved = joblib.load(root / "models" / f"calibrator_{name}.joblib")
    pipe = joblib.load(root / "models" / f"{name}.joblib")
    return Artifacts(pipe=pipe, method=saved["method"], calibrator=saved["calibrator"],
                     threshold=float(decision["threshold"]), decision=decision,
                     explainer=shap.TreeExplainer(pipe.named_steps["model"]),
                     features=feature_columns(early=(tag == "early")))


def feature_specs(df, features):
    """Input widget settings per feature, taken from the training data."""
    specs = {}
    for f in features:
        s = df[f]
        if f in BINARY:
            specs[f] = {"kind": "binary", "options": [0, 1], "default": int(s.mode().iloc[0])}
        elif f in NOMINAL:
            specs[f] = {"kind": "nominal", "options": sorted(int(v) for v in s.unique()),
                        "default": int(s.mode().iloc[0])}
        elif np.allclose(s, s.round()):
            specs[f] = {"kind": "int", "min": int(s.min()), "max": int(s.max()),
                        "default": int(round(s.median()))}
        else:
            specs[f] = {"kind": "float", "min": float(s.min()), "max": float(s.max()),
                        "default": float(s.median())}
    return specs


def random_student(df, features):
    """A random row from the public dataset, for demos. Returns (values, recorded outcome)."""
    row = df.sample(1).iloc[0]
    return {f: row[f] for f in features}, str(row["Target"])


def score_student(art, values):
    """Dropout risk, tier and SHAP contributions for one student (dict of feature -> value)."""
    X = pd.DataFrame([values])[art.features]
    probs = art.pipe.predict_proba(X)[0]
    p_raw = float(probs[0])
    risk = float(apply_calibrator(art.method, art.calibrator, np.array([p_raw]))[0])

    X_t = art.pipe.named_steps["prep"].transform(X)
    sv = art.explainer.shap_values(X_t)
    if isinstance(sv, list):
        sv = np.stack(sv, axis=-1)
    sv = np.asarray(sv)                       # (1, model inputs, classes); class 0 = Dropout
    owners = owner_map(list(X_t.columns))
    contrib = {}
    for i, col in enumerate(X_t.columns):
        contrib[owners[col]] = contrib.get(owners[col], 0.0) + float(sv[0, i, 0])
    contrib = pd.Series(contrib)
    contrib = contrib.reindex(contrib.abs().sort_values(ascending=False).index)
    return {
        "risk": risk,
        "raw": p_raw,
        "probs": {
            "Dropout": risk,
            "Enrolled": float(probs[1]),
            "Graduate": float(probs[2])
        },
        "tier": tier(risk, art.threshold),
        "contributions": contrib
    }


def top_changes(contrib, values, k=3):
    """Plain-text lists of the biggest risk-raising and risk-lowering inputs."""
    def line(f, v):
        return f"{f} = {fmt_value(values[f])} ({v:+.2f})"
    up = [line(f, v) for f, v in contrib.items() if v > 0][:k]
    down = [line(f, v) for f, v in contrib.items() if v < 0][:k]
    return up, down
