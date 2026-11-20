"""Streamlit app: student dropout early-warning. Put this file in app/app.py.

Run locally from the repo root:   streamlit run app/app.py
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))          # so `from src...` works when run as app/app.py

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import streamlit as st

from src.explain import HIGH_TIER, fmt_value
from src.pipeline import load_data
from src.predict import (TIER_ACTIONS, feature_specs, load_artifacts,
                         random_student, score_student, top_changes)

MODEL = os.environ.get("DROPOUT_MODEL", "xgboost")
TAG = os.environ.get("DROPOUT_TAG", "early")

st.set_page_config(page_title="Student Dropout Early-Warning", layout="wide")


@st.cache_resource
def get_artifacts():
    return load_artifacts(MODEL, TAG, ROOT)


@st.cache_data
def get_data():
    return load_data(ROOT / "data" / "data.csv")


art, df = get_artifacts(), get_data()
features = art.features
specs = feature_specs(df, features)
base_rate = float((df["Target"] == "Dropout").mean())

BINARY_LABELS = {"Gender": {0: "Female", 1: "Male"},
                 "Daytime/evening attendance": {0: "Evening", 1: "Daytime"}}
SECTIONS = {
    "Semester 1 academic record": [f for f in features if "1st sem" in f],
    "Admission and personal details": [
        "Age at enrollment", "Gender", "Admission grade", "Previous qualification (grade)",
        "Application order", "Application mode", "Course", "Daytime/evening attendance",
        "Previous qualification", "International", "Educational special needs",
        "Displaced", "Marital status"],
    "Financial situation": ["Tuition fees up to date", "Debtor", "Scholarship holder"],
    "Family background (advanced)": [
        "Nacionality", "Mother's qualification", "Father's qualification",
        "Mother's occupation", "Father's occupation"],
    "Economic context (advanced)": ["Unemployment rate", "Inflation rate", "GDP"],
}
placed = {f for fs in SECTIONS.values() for f in fs}
leftover = [f for f in features if f not in placed]
if leftover:
    SECTIONS["Other"] = leftover


def typed(spec, v):
    return int(v) if spec["kind"] in ("binary", "nominal", "int") else float(v)


for f in features:
    st.session_state.setdefault(f, typed(specs[f], specs[f]["default"]))
st.session_state.setdefault("_outcome", None)


def load_random():
    values, outcome = random_student(df, features)
    for f in features:
        st.session_state[f] = typed(specs[f], values[f])
    st.session_state["_outcome"] = outcome


def reset_typical():
    for f in features:
        st.session_state[f] = typed(specs[f], specs[f]["default"])
    st.session_state["_outcome"] = None


def widget(f):
    s = specs[f]
    if s["kind"] == "binary":
        labels = BINARY_LABELS.get(f, {0: "No", 1: "Yes"})
        return st.selectbox(f, s["options"], key=f, format_func=lambda v, m=labels: m[v])
    if s["kind"] == "nominal":
        return st.selectbox(f, s["options"], key=f,
                            help="Category code from the UCI dataset (see data/README.md).")
    if s["kind"] == "int":
        return st.number_input(f, min_value=s["min"], max_value=s["max"], step=1, key=f,
                               help="Range seen in the training data.")
    return st.number_input(f, min_value=s["min"], max_value=s["max"], step=0.1,
                           format="%.2f", key=f, help="Range seen in the training data.")


# ------------------------------------------------------------------ layout
st.title("Student Dropout Early-Warning")
st.caption("Research prototype for a university course. It supports a mentor's judgement; "
           "it does not make decisions about students.")

with st.sidebar:
    st.header("Demo tools")
    st.button("Load a random student from the dataset", on_click=load_random)
    st.button("Reset to a typical student", on_click=reset_typical)
    if st.session_state["_outcome"]:
        st.info(f"Recorded outcome in the dataset: {st.session_state['_outcome']} "
                "(the inputs may have been edited since).")
    st.markdown(f"**Model:** {MODEL}, {'semester 1 information only' if TAG == 'early' else 'all features'}.")

col_out, col_in = st.columns([2, 3])

values = {}
with col_in:
    st.subheader("Student details")
    for title, fs in SECTIONS.items():
        fs = [f for f in fs if f in specs]
        if not fs:
            continue
        if "advanced" in title:
            with st.expander(title):
                for f in fs:
                    values[f] = widget(f)
        else:
            st.markdown(f"**{title}**")
            for f in fs:
                values[f] = widget(f)

result = score_student(art, values)
risk, tier_name, t = result["risk"], result["tier"], art.threshold

with col_out:
    st.subheader("Estimated dropout risk")
    st.metric("Calibrated probability of dropout", f"{risk:.0%}")
    st.progress(min(max(risk, 0.0), 1.0))
    message = f"{tier_name} risk"
    {"High": st.error, "Medium": st.warning, "Low": st.success}[tier_name](message)
    st.caption(f"Tiers: Medium from {t:.0%}, High from {HIGH_TIER:.0%}. "
               f"Dropout rate in the training data overall: {base_rate:.0%}.")
    st.markdown(f"**Suggested next step:** {TIER_ACTIONS[tier_name]}")

    st.subheader("Why this score")
    contrib = result["contributions"]
    shown = contrib.head(8)
    rest = contrib.iloc[8:].sum()
    labels = [f"{f} = {fmt_value(values[f])}" for f in shown.index] + [f"{len(contrib) - 8} other features"]
    vals = list(shown.values) + [rest]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.barh(labels[::-1], vals[::-1], color=["#C0392B" if v > 0 else "#2E86C1" for v in vals[::-1]])
    ax.axvline(0, color="k", lw=0.8)
    ax.set_xlabel("Effect on the model's score (red = towards dropout)")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)
    up, down = top_changes(contrib, values)
    st.markdown("**Raising risk:** " + ("; ".join(up) or "none"))
    st.markdown("**Lowering risk:** " + ("; ".join(down) or "none"))
    st.caption("These describe what the model relies on, not what causes a student to leave.")

    with st.expander("About this tool and its limits"):
        res_file = ROOT / "reports" / f"test_results_{MODEL}_{TAG}.json"
        if res_file.exists():
            res = json.load(open(res_file))
            at = res["at_chosen_threshold"]
            st.write(f"On {res['n_test']} held-out students: dropout ROC-AUC "
                     f"{res['dropout_roc_auc']:.2f}. At the {t:.0%} cut-off the model caught "
                     f"{at['recall']:.0%} of dropouts with {at['precision']:.0%} precision, "
                     f"and flagged {at['flagged_share']:.0%} of students.")
        st.markdown(
            "- Trained on data from one Portuguese polytechnic institute, not validated at any "
            "other institution.\n"
            "- The cut-off assumes a missed dropout is about five times worse than a false alarm. "
            "That is an assumption, not a measured cost.\n"
            "- Performance is uneven across groups in the training data. For example, dropouts "
            "among scholarship holders and among students aged 20 or under are caught less often, "
            "and male students are flagged more often.\n"
            "- The model uses gender, nationality and other sensitive fields, so a score should "
            "never be used on its own for any decision about a student.\n"
            "- Economic indicators are the same for a whole intake year, so they act partly as a "
            "stand-in for the cohort and may not carry over to other years.\n"
            "- Explanations show associations in the data, not causes.")
