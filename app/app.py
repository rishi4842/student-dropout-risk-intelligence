"""Retention Intelligence — AI Student Success Platform.

Run locally:
    streamlit run app/app.py
"""
import json
import os
import sys
from pathlib import Path

os.environ["MPLCONFIGDIR"] = "/tmp/matplotlib"

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import altair as alt
import pandas as pd
import streamlit as st

from src.explain import HIGH_TIER, fmt_value
from src.pipeline import load_data
from src.predict import (TIER_ACTIONS, feature_specs, load_artifacts,
                         random_student, score_student, top_changes)

# ------------------------------------------------------------------ PAGE CONFIG
st.set_page_config(
    page_title="Retention Intelligence • Student Success Analytics",
    page_icon=":material/school:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ------------------------------------------------------------------ GLOBAL CSS
st.html("""
<style>
/* Hide default sidebar hamburger */
[data-testid="stSidebarCollapsedControl"] { display: none !important; }

/* Tighten main content padding */
.block-container { padding-top: 1rem !important; padding-bottom: 2rem !important; max-width: 1200px !important; }

/* Brand bar styling */
.ri-brand { display: flex; align-items: center; gap: 10px; }
.ri-brand-icon { width: 32px; height: 32px; border-radius: 8px; background: linear-gradient(135deg, #2563EB, #1D4ED8); display: flex; align-items: center; justify-content: center; color: white; font-size: 16px; font-weight: 700; flex-shrink: 0; }
.ri-brand-text { line-height: 1.25; }
.ri-brand-name { font-size: 15px; font-weight: 700; color: #0F172A; letter-spacing: -0.01em; }
.ri-brand-sub { font-size: 11px; color: #64748B; font-weight: 500; }
.ri-status { text-align: right; font-size: 12px; color: #64748B; line-height: 1.4; }
.ri-status-dot { color: #16A34A; font-weight: 600; }

/* Risk hero */
.ri-risk-hero { margin: 4px 0 12px 0; }
.ri-risk-value { font-size: 56px; font-weight: 800; line-height: 1.0; letter-spacing: -0.02em; font-variant-numeric: tabular-nums; }
.ri-risk-low { color: #16A34A; }
.ri-risk-med { color: #D97706; }
.ri-risk-high { color: #DC2626; }

/* Impact comparison */
.ri-impact { display: flex; align-items: center; gap: 24px; margin: 12px 0; }
.ri-impact-block label { font-size: 11px; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600; display: block; margin-bottom: 2px; }
.ri-impact-val { font-size: 36px; font-weight: 700; font-variant-numeric: tabular-nums; line-height: 1.1; }
.ri-impact-tier { font-size: 12px; color: #64748B; margin-top: 2px; }
.ri-arrow { font-size: 28px; color: #94A3B8; }

/* Spectrum bar */
.ri-spectrum { margin: 8px 0 20px 0; }
.ri-spectrum-labels { display: flex; width: 100%; font-size: 11px; color: #64748B; margin-bottom: 6px; font-weight: 600; }
.ri-spectrum-labels span { font-weight: 400; }
.ri-spectrum-bar { position: relative; display: flex; width: 100%; height: 8px; border-radius: 4px; }
.ri-spectrum-safe { background: #16A34A; border-radius: 4px 0 0 4px; }
.ri-spectrum-watch { background: #D97706; }
.ri-spectrum-crit { background: #DC2626; border-radius: 0 4px 4px 0; }
.ri-spectrum-pin { position: absolute; top: -6px; transform: translateX(-50%); width: 4px; height: 20px; background: #0F172A; border: 2px solid #FFFFFF; border-radius: 2px; box-shadow: 0 1px 3px rgba(0,0,0,0.2); }
.ri-spectrum-pos { margin-top: 8px; font-size: 12px; color: #64748B; }

/* Probability bars */
.ri-prob-row { opacity: 0.72; margin-bottom: 10px; }
.ri-prob-row.top { opacity: 1.0; }
.ri-prob-header { display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px; }
.ri-prob-name { font-weight: 500; }
.ri-prob-name.top { font-weight: 700; }
.ri-prob-val { font-family: 'JetBrains Mono', monospace; font-size: 12px; }
.ri-prob-track { width: 100%; height: 7px; background: rgba(100,116,139,0.12); border-radius: 4px; overflow: hidden; }
.ri-prob-fill { height: 100%; border-radius: 4px; }

/* Section headers */
.ri-section-label { font-size: 11px; font-weight: 600; color: #64748B; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px; }

/* Student context strip */
.ri-context { font-size: 13px; color: #475569; margin: 2px 0 8px 0; }
.ri-context strong { color: #0F172A; font-weight: 600; }
.ri-context .sep { color: #CBD5E1; margin: 0 6px; }

/* Fairness card */
.ri-fairness { padding: 12px 16px; border-left: 3px solid #E2E8F0; margin-bottom: 12px; }
.ri-fairness-title { font-weight: 600; font-size: 14px; color: #0F172A; }
.ri-fairness-metric { font-size: 12px; color: #64748B; margin-top: 2px; }
.ri-fairness-obs { font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #334155; margin-top: 6px; }
.ri-fairness-interp { font-size: 13px; color: #475569; margin-top: 4px; line-height: 1.5; }

/* Principle cards */
.ri-principle { padding: 16px; border: 1px solid #E2E8F0; border-radius: 8px; margin-bottom: 12px; }
.ri-principle-num { font-size: 20px; font-weight: 700; color: #2563EB; margin-bottom: 4px; }
.ri-principle-title { font-size: 14px; font-weight: 600; color: #0F172A; margin-bottom: 6px; }
.ri-principle-desc { font-size: 13px; color: #475569; line-height: 1.5; }

/* Performance strip */
.ri-perf { font-size: 12px; color: #64748B; padding: 8px 0; }
.ri-perf strong { color: #334155; font-weight: 600; }

/* Dark mode overrides */
@media (prefers-color-scheme: dark) {
    .ri-brand-name { color: #F8FAFC; }
    .ri-brand-icon { background: linear-gradient(135deg, #3B82F6, #2563EB); }
    .ri-risk-low { color: #10B981; }
    .ri-risk-med { color: #F59E0B; }
    .ri-risk-high { color: #EF4444; }
    .ri-context { color: #94A3B8; }
    .ri-context strong { color: #F8FAFC; }
    .ri-context .sep { color: #334155; }
    .ri-fairness { border-left-color: #334155; }
    .ri-fairness-title { color: #F8FAFC; }
    .ri-fairness-obs { color: #E2E8F0; }
    .ri-fairness-interp { color: #94A3B8; }
    .ri-principle { border-color: #1E293B; }
    .ri-principle-title { color: #F8FAFC; }
    .ri-principle-desc { color: #94A3B8; }
    .ri-spectrum-pin { background: #F8FAFC; border-color: #0F172A; }
}
</style>
""")

# ------------------------------------------------------------------ DOMAIN MAPS
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
    9991: "Management (Evening)",
}

APPLICATION_MODE_MAP = {
    1: "1st Phase - General Contingent",
    2: "Ordinance No. 612/93",
    5: "1st Phase - Azores",
    7: "Holders of Other Higher Courses",
    10: "Ordinance No. 854-B/99",
    15: "International Student",
    16: "1st Phase - Madeira",
    17: "2nd Phase - General Contingent",
    18: "3rd Phase - General Contingent",
    26: "Ordinance No. 533-A/99 - Plan b2",
    27: "Ordinance No. 533-A/99 - Plan b3",
    39: "Over 23 Years Old",
    42: "Transfer",
    43: "Change of Course",
    44: "Technological Specialization Diploma",
    51: "Change of Institution/Course",
    53: "Short Cycle Diploma",
    57: "Change of Institution/Course (Intl)",
}

PARENT_QUAL_MAP = {
    1: "Secondary Education (12th Year)",
    2: "Higher Education - Bachelor's",
    3: "Higher Education - Degree",
    4: "Higher Education - Master's",
    5: "Higher Education - Doctorate",
    6: "Frequency of Higher Education",
    9: "12th Year (Incomplete)",
    10: "11th Year (Incomplete)",
    11: "7th Year (Old System)",
    12: "Other - 11th Year",
    14: "10th Year",
    18: "General Commerce Course",
    19: "Basic Education 3rd Cycle (9th-11th)",
    22: "Technical-Professional Course",
    26: "7th Year of Schooling",
    27: "2nd Cycle General High School",
    29: "9th Year of Schooling",
    30: "8th Year of Schooling",
    34: "Unknown",
    35: "Cannot Read or Write",
    36: "Can Read Without 4th Year",
    37: "Basic Education 1st Cycle (4th Year)",
    38: "Basic Education 2nd Cycle (6th Year)",
    39: "Technological Specialization Course",
    40: "Higher Education Degree (1st Cycle)",
    41: "Specialized Higher Studies (ESE)",
    42: "Professional Higher Technical Course",
    43: "Higher Education Master (2nd Cycle)",
    44: "Higher Education Doctorate (3rd Cycle)",
}

PERSONAS = {
    "Custom Input": {
        "desc": "Active profile with custom or sampled student parameters.",
        "target": None,
        "values": None,
    },
    "High-Risk Attrition": {
        "desc": "Student profile with elevated academic and financial risk.",
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
            "GDP": 0.79,
        },
    },
    "High-Performing Scholar": {
        "desc": "Strong academic standing, scholarship, tuition current.",
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
            "GDP": 1.74,
        },
    },
    "Borderline Struggling": {
        "desc": "Mixed unit pass rate with moderate retention risk.",
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
            "GDP": 0.32,
        },
    },
}


def map_label(mapping, key, fallback_prefix="Code"):
    try:
        return mapping.get(int(key), f"{fallback_prefix} {key}")
    except (ValueError, TypeError):
        return f"{fallback_prefix} {key}"


def friendly_feature_label(feature, val):
    if feature == "Course":
        return f"Course: {COURSE_MAP.get(int(val), f'Code {val}')}"
    if feature == "Tuition fees up to date":
        return f"Tuition: {'Current' if int(val) == 1 else 'Overdue'}"
    if feature == "Debtor":
        return f"Debt: {'Yes' if int(val) == 1 else 'None'}"
    if feature == "Scholarship holder":
        return f"Scholarship: {'Yes' if int(val) == 1 else 'No'}"
    if feature == "Gender":
        return f"Gender: {'Male' if int(val) == 1 else 'Female'}"
    if feature == "Age at enrollment":
        return f"Age at enrollment: {int(val)}"
    if feature == "Daytime/evening attendance":
        return f"Schedule: {'Daytime' if int(val) == 1 else 'Evening'}"
    if feature == "Displaced":
        return f"Displaced: {'Yes' if int(val) == 1 else 'No'}"
    clean = (
        feature.replace("Curricular units ", "")
        .replace("1st sem ", "Sem 1 ")
        .replace("2nd sem ", "Sem 2 ")
    )
    return f"{clean}: {fmt_value(val)}"


# ------------------------------------------------------------------ CACHED DATA
@st.cache_resource
def get_artifacts(model="xgboost", tag="early"):
    return load_artifacts(model, tag, ROOT)


@st.cache_data
def get_data():
    return load_data(ROOT / "data" / "data.csv")


df = get_data()

# ------------------------------------------------------------------ SESSION STATE
st.session_state.setdefault("_model_tag", "early")
st.session_state.setdefault("_outcome", None)
st.session_state.setdefault("_active_persona", "Custom Input")

# ------------------------------------------------------------------ HEADER BAR
hdr_left, hdr_right = st.columns([7, 5], vertical_alignment="center")
with hdr_left:
    st.html(
        '<div class="ri-brand">'
        '<div class="ri-brand-icon">RI</div>'
        '<div class="ri-brand-text">'
        '<div class="ri-brand-name">Retention Intelligence</div>'
        '<div class="ri-brand-sub">Student Success Analytics</div>'
        '</div></div>'
    )
with hdr_right:
    st.html(
        '<div class="ri-status">'
        '<span class="ri-status-dot">&#9679; Model Active</span> · v1.0<br/>'
        'Holdout: 885 students'
        '</div>'
    )

# ------------------------------------------------------------------ LOAD ARTIFACTS
selected_tag = st.session_state["_model_tag"]
art = get_artifacts("xgboost", selected_tag)
features = art.features
specs = feature_specs(df, features)


def typed(spec, v):
    return int(v) if spec["kind"] in ("binary", "nominal", "int") else float(v)


if "student_profile" not in st.session_state:
    st.session_state["student_profile"] = {
        f: typed(specs[f], specs[f]["default"]) for f in features
    }
else:
    for f in features:
        if f not in st.session_state["student_profile"]:
            st.session_state["student_profile"][f] = typed(specs[f], specs[f]["default"])

current_values = {f: st.session_state["student_profile"][f] for f in features}
result = score_student(art, current_values)
risk = float(result["risk"])
tier_name = str(result["tier"])
probs = result.get(
    "probs",
    {"Dropout": risk, "Enrolled": 0.18, "Graduate": max(0.0, 1.0 - risk - 0.18)},
)
t = float(art.threshold)

p_drop = float(probs.get("Dropout", risk))
p_enr = float(probs.get("Enrolled", 0.0))
p_grad = float(probs.get("Graduate", 0.0))
prob_sum = p_drop + p_enr + p_grad
if prob_sum > 0:
    p_drop_norm = p_drop / prob_sum
    p_enr_norm = p_enr / prob_sum
    p_grad_norm = p_grad / prob_sum
else:
    p_drop_norm, p_enr_norm, p_grad_norm = risk, 0.0, max(0.0, 1.0 - risk)

res_path = ROOT / "reports" / f"test_results_xgboost_{selected_tag}.json"
res_data = json.load(open(res_path)) if res_path.exists() else {}


# ------------------------------------------------------------------ CONTEXT CONTROLS
def render_context_controls():
    """Compact controls: model scope, student preset, actions."""
    c_scope, c_profile, c_actions = st.columns([4, 5, 2], vertical_alignment="bottom")
    with c_scope:
        st.caption("MODEL SCOPE")
        scope_choice = st.segmented_control(
            "Model scope",
            options=["Early Warning", "Full Curriculum"],
            default="Early Warning" if selected_tag == "early" else "Full Curriculum",
            label_visibility="collapsed",
            width="stretch",
            key="ctx_scope_control",
        )
        new_tag = "early" if scope_choice != "Full Curriculum" else "full"
        if new_tag != st.session_state["_model_tag"]:
            st.session_state["_model_tag"] = new_tag
            st.rerun()

    with c_profile:
        st.caption("STUDENT PROFILE")
        preset_names = list(PERSONAS.keys())
        cur_p = st.session_state["_active_persona"]
        idx = preset_names.index(cur_p) if cur_p in preset_names else 0
        chosen_preset = st.selectbox(
            "Student profile preset",
            options=preset_names,
            index=idx,
            label_visibility="collapsed",
            key="ctx_preset_select",
        )
        if chosen_preset != cur_p:
            st.session_state["_active_persona"] = chosen_preset
            p_data = PERSONAS[chosen_preset]
            if p_data["values"] is not None:
                for f, val in p_data["values"].items():
                    if f in specs:
                        tv = typed(specs[f], val)
                        st.session_state["student_profile"][f] = tv
                        st.session_state[f"inp_{f}"] = tv
                st.session_state["_outcome"] = p_data["target"]
            st.rerun()

    with c_actions:
        with st.popover(":material/more_horiz: Actions"):
            if st.button("Sample random student", icon=":material/shuffle:", use_container_width=True):
                vals, outcome = random_student(df, features)
                for f in features:
                    tv = typed(specs[f], vals[f])
                    st.session_state["student_profile"][f] = tv
                    st.session_state[f"inp_{f}"] = tv
                st.session_state["_outcome"] = outcome
                st.session_state["_active_persona"] = "Custom Input"
                st.rerun()
            if st.button("Reset to defaults", icon=":material/restart_alt:", use_container_width=True):
                for f in features:
                    tv = typed(specs[f], specs[f]["default"])
                    st.session_state["student_profile"][f] = tv
                    st.session_state[f"inp_{f}"] = tv
                st.session_state["_outcome"] = None
                st.session_state["_active_persona"] = "Custom Input"
                st.rerun()


def render_student_context():
    """Show current student context strip."""
    course_name = map_label(COURSE_MAP, current_values.get("Course", 9500), "Course")
    age_val = int(current_values.get("Age at enrollment", 20))
    sem_label = "Semester 1 only" if selected_tag == "early" else "Semesters 1 & 2"
    outcome_str = f'<span class="sep">·</span><em>{st.session_state["_outcome"]}</em>' if st.session_state.get("_outcome") else ""
    st.html(
        f'<div class="ri-context">'
        f'<strong>{st.session_state["_active_persona"]}</strong>'
        f'<span class="sep">·</span>{course_name}'
        f'<span class="sep">·</span>Age {age_val}'
        f'<span class="sep">·</span>{sem_label}'
        f'{outcome_str}'
        f'</div>'
    )


# ==============================================================================
# TABBED NAVIGATION
# ==============================================================================
tab_risk, tab_profile, tab_whatif, tab_gov = st.tabs([
    ":material/monitoring: Risk Assessment",
    ":material/person: Student Profile",
    ":material/science: What-If Lab",
    ":material/verified_user: Governance",
])

# ==============================================================================
# TAB 1: RISK ASSESSMENT
# ==============================================================================
with tab_risk:
    render_student_context()
    render_context_controls()

    st.markdown("---")

    # ---- Primary Risk KPI + Risk Spectrum ----
    col_kpi, col_profile = st.columns([5, 7], gap="large")

    with col_kpi:
        with st.container(border=True):
            st.html('<div class="ri-section-label">ATTRITION RISK</div>')
            tier_css = "ri-risk-high" if tier_name == "High" else ("ri-risk-med" if tier_name == "Medium" else "ri-risk-low")
            st.html(
                f'<div class="ri-risk-hero">'
                f'<div class="ri-risk-value {tier_css}">{risk:.1%}</div>'
                f'</div>'
            )
            badge_md = (
                ":red-badge[HIGH RISK]"
                if tier_name == "High"
                else (":orange-badge[MEDIUM RISK]" if tier_name == "Medium" else ":green-badge[LOW RISK]")
            )
            st.markdown(badge_md)
            st.write(
                "Student is currently **above** the intervention threshold."
                if risk >= t
                else "Student is currently **below** the intervention threshold."
            )

            m1, m2 = st.columns(2)
            with m1:
                st.metric("Operational threshold", f"{t:.0%}")
            with m2:
                gap_pp = (risk - t) * 100.0
                st.metric("Risk gap", f"{gap_pp:+.1f} pp")

    with col_profile:
        st.html('<div class="ri-section-label">RISK PROFILE</div>')
        pos_pct = min(max(risk * 100.0, 0.0), 100.0)
        t_pct = int(round(t * 100))
        high_pct = int(round(HIGH_TIER * 100))

        st.html(f"""
        <div class="ri-spectrum">
          <div class="ri-spectrum-labels">
            <div style="width:{t_pct}%;">SAFE<br/><span>0–{t_pct}%</span></div>
            <div style="width:{high_pct - t_pct}%;">WATCH<br/><span>{t_pct}–{high_pct}%</span></div>
            <div style="width:{100 - high_pct}%;">CRITICAL<br/><span>{high_pct}–100%</span></div>
          </div>
          <div class="ri-spectrum-bar">
            <div class="ri-spectrum-safe" style="width:{t_pct}%;"></div>
            <div class="ri-spectrum-watch" style="width:{high_pct - t_pct}%;"></div>
            <div class="ri-spectrum-crit" style="width:{100 - high_pct}%;"></div>
            <div class="ri-spectrum-pin" style="left:{pos_pct:.1f}%;"></div>
          </div>
          <div class="ri-spectrum-pos">
            &#9679; Student position: <strong>{risk:.1%}</strong> &nbsp;·&nbsp; Status: <strong>{tier_name} Risk</strong>
          </div>
        </div>
        """)

        st.html('<div class="ri-section-label">MULTICLASS PROBABILITY</div>')
        outcomes = [
            ("Graduate", p_grad_norm, "#16A34A"),
            ("Persist", p_enr_norm, "#2563EB"),
            ("Dropout", p_drop_norm, "#DC2626"),
        ]
        top_outcome = max(outcomes, key=lambda x: x[1])[0]
        bars_html = ""
        for name, val, col in outcomes:
            is_top = name == top_outcome
            top_cls = " top" if is_top else ""
            w_pct = max(val * 100.0, 1.5)
            bars_html += f"""
            <div class="ri-prob-row{top_cls}">
              <div class="ri-prob-header">
                <span class="ri-prob-name{top_cls}">{name}</span>
                <span class="ri-prob-val">{val:.1%}</span>
              </div>
              <div class="ri-prob-track">
                <div class="ri-prob-fill" style="width:{w_pct:.1f}%; background:{col};"></div>
              </div>
            </div>
            """
        st.html(bars_html)

    st.markdown("---")

    # ---- Explanation + Advisor Action ----
    col_adv, col_shap = st.columns([5, 7], gap="large")

    with col_adv:
        st.html('<div class="ri-section-label">RECOMMENDED ADVISOR ACTION</div>')
        if tier_name == "High":
            st.markdown("#### Priority 1-on-1 outreach required")
        elif tier_name == "Medium":
            st.markdown("#### Targeted academic & peer support")
        else:
            st.markdown("#### No immediate intervention required")

        st.caption("Why?")
        st.write(TIER_ACTIONS[tier_name])

        enrolled_u = int(current_values.get("Curricular units 1st sem (enrolled)", 0))
        approved_u = int(current_values.get("Curricular units 1st sem (approved)", 0))
        grade_u = float(current_values.get("Curricular units 1st sem (grade)", 0.0))

        st.html('<div class="ri-section-label" style="margin-top:16px;">RECOMMENDED TALKING POINTS</div>')
        if enrolled_u == 0:
            st.markdown("**Registration status**  \n0 of 0 units enrolled in Semester 1. Verify administrative holds or leave status.")
        elif approved_u < enrolled_u:
            st.markdown(f"**Academic recovery**  \n{enrolled_u - approved_u} of {enrolled_u} enrolled units not passed. Refer to course tutoring and office hours.")
        else:
            st.markdown(f"**Academic progress**  \nPassed all {enrolled_u} enrolled units (average {grade_u:.1f}/20). Maintain current study plan.")

        if int(current_values.get("Tuition fees up to date", 1)) == 0:
            st.markdown("**Financial support**  \nOverdue tuition detected. Review emergency hardship aid or installment options.")
        if int(current_values.get("Debtor", 0)) == 1:
            st.markdown("**Account balance**  \nInstitutional debt recorded. Coordinate with student finance office.")
        if int(current_values.get("Daytime/evening attendance", 1)) == 0 or int(current_values.get("Age at enrollment", 20)) > 25:
            st.markdown("**Attendance & schedule**  \nReview evening or work-study balance and flexible advising hours.")

    with col_shap:
        st.html('<div class="ri-section-label">WHY THIS PREDICTION?</div>')
        st.caption("How individual features influenced the model's dropout score.")

        contrib = result["contributions"]
        top_k = contrib.head(8)
        rest_sum = float(contrib.iloc[8:].sum())

        plot_items = []
        for f in top_k.index:
            val = current_values.get(f, 0)
            plot_items.append({
                "Feature": friendly_feature_label(f, val),
                "Impact": float(top_k[f]),
                "Direction": "Increases risk" if top_k[f] > 0 else "Reduces risk",
            })
        if len(contrib) > 8:
            plot_items.append({
                "Feature": f"{len(contrib) - 8} other features",
                "Impact": rest_sum,
                "Direction": "Increases risk" if rest_sum > 0 else "Reduces risk",
            })

        df_shap = pd.DataFrame(plot_items)
        chart = (
            alt.Chart(df_shap)
            .mark_bar(cornerRadiusEnd=3)
            .encode(
                x=alt.X("Impact:Q", title="Effect on dropout log-odds"),
                y=alt.Y(
                    "Feature:N",
                    sort=None,
                    title=None,
                    axis=alt.Axis(labelLimit=320, labelFontSize=12),
                ),
                color=alt.Color(
                    "Direction:N",
                    scale=alt.Scale(
                        domain=["Increases risk", "Reduces risk"],
                        range=["#DC2626", "#2563EB"],
                    ),
                    legend=alt.Legend(orient="top", title=None),
                ),
                tooltip=[
                    alt.Tooltip("Feature:N", title="Feature"),
                    alt.Tooltip("Impact:Q", title="SHAP impact", format="+.3f"),
                    alt.Tooltip("Direction:N", title="Effect"),
                ],
            )
            .properties(height=300)
        )
        st.altair_chart(chart, use_container_width=True)

        st.caption("Associations in the data, not causal effects.")

        up_changes, down_changes = top_changes(contrib, current_values)
        f_up, f_down = st.columns(2)
        with f_up:
            st.caption("Factors increasing risk")
            st.write(", ".join(up_changes) if up_changes else "None")
        with f_down:
            st.caption("Factors reducing risk")
            st.write(", ".join(down_changes) if down_changes else "None")

    # ---- Performance strip ----
    if res_data:
        st.markdown("---")
        st.html(
            f'<div class="ri-perf">'
            f'MODEL PERFORMANCE &nbsp;·&nbsp; '
            f'ROC-AUC <strong>{res_data["dropout_roc_auc"]:.3f}</strong> &nbsp;|&nbsp; '
            f'Recall <strong>{res_data["at_chosen_threshold"]["recall"]:.1%}</strong> &nbsp;|&nbsp; '
            f'Threshold <strong>{t:.0%}</strong> &nbsp;|&nbsp; '
            f'Holdout <strong>{res_data["n_test"]}</strong>'
            f'</div>'
        )

# ==============================================================================
# TAB 2: STUDENT PROFILE
# ==============================================================================
with tab_profile:
    render_student_context()
    render_context_controls()

    st.markdown("---")

    def mark_custom():
        st.session_state["_active_persona"] = "Custom Input"
        st.session_state["_outcome"] = None

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.html('<div class="ri-section-label">ACADEMIC RECORD — SEMESTER 1</div>')
        enr1 = st.slider(
            "Enrolled units", 0, 26,
            value=int(st.session_state["student_profile"].get("Curricular units 1st sem (enrolled)", 6)),
            key="inp_Curricular units 1st sem (enrolled)",
            on_change=mark_custom,
        )
        st.session_state["student_profile"]["Curricular units 1st sem (enrolled)"] = enr1

        cur_app1 = min(int(st.session_state["student_profile"].get("Curricular units 1st sem (approved)", 5)), enr1)
        app1 = st.slider(
            "Approved units", 0, max(enr1, 1) if enr1 > 0 else 0,
            value=cur_app1,
            key="inp_Curricular units 1st sem (approved)",
            on_change=mark_custom,
        )
        st.session_state["student_profile"]["Curricular units 1st sem (approved)"] = app1

        ev1 = st.number_input(
            "Evaluation moments", min_value=app1, max_value=45,
            value=max(int(st.session_state["student_profile"].get("Curricular units 1st sem (evaluations)", 8)), app1),
            key="inp_Curricular units 1st sem (evaluations)",
            on_change=mark_custom,
        )
        st.session_state["student_profile"]["Curricular units 1st sem (evaluations)"] = ev1

        gr1 = st.slider(
            "Grade average (0–20)", 0.0, 20.0,
            value=float(st.session_state["student_profile"].get("Curricular units 1st sem (grade)", 12.5)),
            step=0.1,
            key="inp_Curricular units 1st sem (grade)",
            on_change=mark_custom,
        )
        st.session_state["student_profile"]["Curricular units 1st sem (grade)"] = gr1

        c_a, c_b = st.columns(2)
        with c_a:
            cr1 = st.number_input(
                "Credited units", 0, 20,
                value=int(st.session_state["student_profile"].get("Curricular units 1st sem (credited)", 0)),
                key="inp_Curricular units 1st sem (credited)",
                on_change=mark_custom,
            )
            st.session_state["student_profile"]["Curricular units 1st sem (credited)"] = cr1
        with c_b:
            wo1 = st.number_input(
                "Units without evaluation", 0, 12,
                value=int(st.session_state["student_profile"].get("Curricular units 1st sem (without evaluations)", 0)),
                key="inp_Curricular units 1st sem (without evaluations)",
                on_change=mark_custom,
            )
            st.session_state["student_profile"]["Curricular units 1st sem (without evaluations)"] = wo1

        if selected_tag == "full":
            st.markdown("---")
            st.html('<div class="ri-section-label">ACADEMIC RECORD — SEMESTER 2</div>')
            enr2 = st.slider(
                "Enrolled units (Sem 2)", 0, 26,
                value=int(st.session_state["student_profile"].get("Curricular units 2nd sem (enrolled)", 6)),
                key="inp_Curricular units 2nd sem (enrolled)",
                on_change=mark_custom,
            )
            st.session_state["student_profile"]["Curricular units 2nd sem (enrolled)"] = enr2

            cur_app2 = min(int(st.session_state["student_profile"].get("Curricular units 2nd sem (approved)", 5)), enr2)
            app2 = st.slider(
                "Approved units (Sem 2)", 0, max(enr2, 1) if enr2 > 0 else 0,
                value=cur_app2,
                key="inp_Curricular units 2nd sem (approved)",
                on_change=mark_custom,
            )
            st.session_state["student_profile"]["Curricular units 2nd sem (approved)"] = app2

            gr2 = st.slider(
                "Grade average Sem 2 (0–20)", 0.0, 20.0,
                value=float(st.session_state["student_profile"].get("Curricular units 2nd sem (grade)", 12.5)),
                step=0.1,
                key="inp_Curricular units 2nd sem (grade)",
                on_change=mark_custom,
            )
            st.session_state["student_profile"]["Curricular units 2nd sem (grade)"] = gr2

        st.markdown("---")
        st.html('<div class="ri-section-label">FINANCIAL & ENROLLMENT</div>')
        f1, f2 = st.columns(2)
        with f1:
            tuition_opt = st.segmented_control(
                "Tuition status",
                options=["Up to date", "Overdue"],
                default="Up to date" if int(st.session_state["student_profile"].get("Tuition fees up to date", 1)) == 1 else "Overdue",
                key="seg_tuition",
                on_change=mark_custom,
            )
            st.session_state["student_profile"]["Tuition fees up to date"] = 1 if tuition_opt == "Up to date" else 0

            debtor_opt = st.segmented_control(
                "Institutional debt",
                options=["No", "Yes"],
                default="Yes" if int(st.session_state["student_profile"].get("Debtor", 0)) == 1 else "No",
                key="seg_debtor",
                on_change=mark_custom,
            )
            st.session_state["student_profile"]["Debtor"] = 1 if debtor_opt == "Yes" else 0

            schol_opt = st.segmented_control(
                "Scholarship",
                options=["No", "Yes"],
                default="Yes" if int(st.session_state["student_profile"].get("Scholarship holder", 0)) == 1 else "No",
                key="seg_scholarship",
                on_change=mark_custom,
            )
            st.session_state["student_profile"]["Scholarship holder"] = 1 if schol_opt == "Yes" else 0
        with f2:
            att_opt = st.segmented_control(
                "Attendance schedule",
                options=["Daytime", "Evening"],
                default="Daytime" if int(st.session_state["student_profile"].get("Daytime/evening attendance", 1)) == 1 else "Evening",
                key="seg_attend",
                on_change=mark_custom,
            )
            st.session_state["student_profile"]["Daytime/evening attendance"] = 1 if att_opt == "Daytime" else 0

            disp_opt = st.segmented_control(
                "Displacement status",
                options=["Local", "Displaced"],
                default="Displaced" if int(st.session_state["student_profile"].get("Displaced", 1)) == 1 else "Local",
                key="seg_displaced",
                on_change=mark_custom,
            )
            st.session_state["student_profile"]["Displaced"] = 1 if disp_opt == "Displaced" else 0

    with col2:
        st.html('<div class="ri-section-label">DEMOGRAPHICS & PROGRAM</div>')
        age_inp = st.slider(
            "Age at enrollment", 17, 70,
            value=int(st.session_state["student_profile"].get("Age at enrollment", 20)),
            key="inp_Age at enrollment",
            on_change=mark_custom,
        )
        st.session_state["student_profile"]["Age at enrollment"] = age_inp

        g_opt = st.segmented_control(
            "Gender",
            options=["Female", "Male"],
            default="Female" if int(st.session_state["student_profile"].get("Gender", 0)) == 0 else "Male",
            key="seg_gender",
            on_change=mark_custom,
        )
        st.session_state["student_profile"]["Gender"] = 1 if g_opt == "Male" else 0

        course_opts = specs["Course"]["options"]
        cur_c = int(st.session_state["student_profile"].get("Course", course_opts[0]))
        c_sel = st.selectbox(
            "Degree program",
            options=course_opts,
            index=course_opts.index(cur_c) if cur_c in course_opts else 0,
            format_func=lambda c: map_label(COURSE_MAP, c, "Course"),
            key="inp_Course",
            on_change=mark_custom,
        )
        st.session_state["student_profile"]["Course"] = c_sel

        adm_gr = st.slider(
            "Admission grade (0–200)", 0.0, 200.0,
            value=float(st.session_state["student_profile"].get("Admission grade", 125.0)),
            step=0.5,
            key="inp_Admission grade",
            on_change=mark_custom,
        )
        st.session_state["student_profile"]["Admission grade"] = adm_gr

        prev_gr = st.slider(
            "Previous qualification grade (0–200)", 0.0, 200.0,
            value=float(st.session_state["student_profile"].get("Previous qualification (grade)", 130.0)),
            step=0.5,
            key="inp_Previous qualification (grade)",
            on_change=mark_custom,
        )
        st.session_state["student_profile"]["Previous qualification (grade)"] = prev_gr

        with st.expander("Application & family qualifications"):
            app_opts = specs["Application mode"]["options"]
            cur_am = int(st.session_state["student_profile"].get("Application mode", app_opts[0]))
            st.session_state["student_profile"]["Application mode"] = st.selectbox(
                "Application mode",
                options=app_opts,
                index=app_opts.index(cur_am) if cur_am in app_opts else 0,
                format_func=lambda a: map_label(APPLICATION_MODE_MAP, a, "Mode"),
                key="inp_Application mode",
                on_change=mark_custom,
            )
            mq_opts = specs["Mother's qualification"]["options"]
            cur_mq = int(st.session_state["student_profile"].get("Mother's qualification", mq_opts[0]))
            st.session_state["student_profile"]["Mother's qualification"] = st.selectbox(
                "Mother's qualification",
                options=mq_opts,
                index=mq_opts.index(cur_mq) if cur_mq in mq_opts else 0,
                format_func=lambda q: map_label(PARENT_QUAL_MAP, q, "Qual"),
                key="inp_Mothers qualification",
                on_change=mark_custom,
            )
            fq_opts = specs["Father's qualification"]["options"]
            cur_fq = int(st.session_state["student_profile"].get("Father's qualification", fq_opts[0]))
            st.session_state["student_profile"]["Father's qualification"] = st.selectbox(
                "Father's qualification",
                options=fq_opts,
                index=fq_opts.index(cur_fq) if cur_fq in fq_opts else 0,
                format_func=lambda q: map_label(PARENT_QUAL_MAP, q, "Qual"),
                key="inp_Fathers qualification",
                on_change=mark_custom,
            )

        st.markdown("---")
        st.html('<div class="ri-section-label">ECONOMIC CONTEXT</div>')
        e1, e2, e3 = st.columns(3)
        with e1:
            st.session_state["student_profile"]["Unemployment rate"] = st.number_input(
                "Unemployment (%)", 0.0, 30.0,
                value=float(st.session_state["student_profile"].get("Unemployment rate", 10.8)),
                step=0.1, key="inp_Unemployment rate", on_change=mark_custom,
            )
        with e2:
            st.session_state["student_profile"]["Inflation rate"] = st.number_input(
                "Inflation (%)", -5.0, 10.0,
                value=float(st.session_state["student_profile"].get("Inflation rate", 1.4)),
                step=0.1, key="inp_Inflation rate", on_change=mark_custom,
            )
        with e3:
            st.session_state["student_profile"]["GDP"] = st.number_input(
                "GDP change (%)", -10.0, 10.0,
                value=float(st.session_state["student_profile"].get("GDP", 1.74)),
                step=0.1, key="inp_GDP", on_change=mark_custom,
            )

# ==============================================================================
# TAB 3: WHAT-IF LAB
# ==============================================================================
with tab_whatif:
    render_student_context()
    render_context_controls()

    st.markdown("---")

    sim_values = dict(current_values)
    base_enrolled = int(sim_values.get("Curricular units 1st sem (enrolled)", 0))
    base_approved = int(sim_values.get("Curricular units 1st sem (approved)", 0))

    col_ctrl, col_impact = st.columns(2, gap="large")

    with col_ctrl:
        st.html('<div class="ri-section-label">INTERVENTION SCENARIO</div>')
        if base_enrolled == 0:
            st.info("Baseline enrolled units is 0. Enroll the student in units on the Student Profile tab to simulate tutoring.")
            tutoring_boost = 0
        else:
            max_boost = max(0, base_enrolled - base_approved)
            if max_boost == 0:
                st.caption(f"All {base_enrolled} enrolled units are already approved.")
                tutoring_boost = 0
            else:
                tutoring_boost = st.slider(
                    f"Tutoring: additional approved units (max {max_boost})",
                    0, max_boost, value=min(1, max_boost),
                )

        sim_values["Curricular units 1st sem (approved)"] = base_approved + tutoring_boost
        sim_values["Curricular units 1st sem (evaluations)"] = max(
            int(sim_values.get("Curricular units 1st sem (evaluations)", 0)),
            int(sim_values["Curricular units 1st sem (approved)"]),
        )
        if sim_values["Curricular units 1st sem (approved)"] > 0 and float(sim_values.get("Curricular units 1st sem (grade)", 0.0)) < 10.0:
            sim_values["Curricular units 1st sem (grade)"] = 11.5

        grant_relief = st.toggle(
            "Emergency hardship grant: bring tuition up to date and clear debt",
            value=(int(sim_values.get("Tuition fees up to date", 1)) == 0 or int(sim_values.get("Debtor", 0)) == 1),
        )
        if grant_relief:
            sim_values["Tuition fees up to date"] = 1
            sim_values["Debtor"] = 0

        grade_boost = st.slider(
            "Study workshop: grade improvement (+ points on 0–20 scale)",
            0.0, 4.0, value=1.0, step=0.5,
        )
        sim_values["Curricular units 1st sem (grade)"] = min(
            20.0, float(sim_values.get("Curricular units 1st sem (grade)", 0.0)) + grade_boost
        )

        st.caption(
            f"Validated constraints: Approved ({sim_values['Curricular units 1st sem (approved)']}) "
            f"≤ Evaluations ({sim_values['Curricular units 1st sem (evaluations)']}) "
            f"≤ Enrolled ({sim_values['Curricular units 1st sem (enrolled)']})"
        )

    sim_result = score_student(art, sim_values)
    sim_risk = float(sim_result["risk"])
    sim_tier = str(sim_result["tier"])
    reduction_pp = (risk - sim_risk) * 100.0

    with col_impact:
        with st.container(border=True):
            st.html('<div class="ri-section-label">PREDICTED IMPACT</div>')

            sim_tier_css = "ri-risk-high" if sim_tier == "High" else ("ri-risk-med" if sim_tier == "Medium" else "ri-risk-low")
            base_tier_css = "ri-risk-high" if tier_name == "High" else ("ri-risk-med" if tier_name == "Medium" else "ri-risk-low")

            st.html(f"""
            <div class="ri-impact">
              <div class="ri-impact-block">
                <label>Baseline</label>
                <div class="ri-impact-val {base_tier_css}">{risk:.1%}</div>
                <div class="ri-impact-tier">{tier_name} Risk</div>
              </div>
              <div class="ri-arrow">&rarr;</div>
              <div class="ri-impact-block">
                <label>Projected</label>
                <div class="ri-impact-val {sim_tier_css}">{sim_risk:.1%}</div>
                <div class="ri-impact-tier">{sim_tier} Risk</div>
              </div>
            </div>
            """)

            st.caption("Risk reduction")
            if reduction_pp > 0:
                st.markdown(f":green-badge[▼ {reduction_pp:.1f} percentage points]")
            elif reduction_pp < 0:
                st.markdown(f":red-badge[▲ {abs(reduction_pp):.1f} percentage points]")
            else:
                st.markdown(":gray-badge[0.0 percentage points]")

            st.caption("Simulations reflect model sensitivity to modified inputs, not guaranteed causal outcomes.")

# ==============================================================================
# TAB 4: GOVERNANCE
# ==============================================================================
with tab_gov:
    st.markdown("---")

    st.html('<div class="ri-section-label">MODEL PERFORMANCE</div>')
    perf_df = pd.DataFrame([
        {"Metric": "Holdout cohort (N)", "Early Warning (Sem 1)": "885 students", "Full Curriculum (Sem 1 & 2)": "885 students"},
        {"Metric": "Dropout ROC-AUC", "Early Warning (Sem 1)": "0.893", "Full Curriculum (Sem 1 & 2)": "0.915"},
        {"Metric": "Dropout PR-AUC", "Early Warning (Sem 1)": "0.844", "Full Curriculum (Sem 1 & 2)": "0.872"},
        {"Metric": "Dropout Recall @ Cutoff", "Early Warning (Sem 1)": "89.4% (254/284)", "Full Curriculum (Sem 1 & 2)": "86.6% (246/284)"},
        {"Metric": "Dropout Precision @ Cutoff", "Early Warning (Sem 1)": "59.3%", "Full Curriculum (Sem 1 & 2)": "64.2%"},
        {"Metric": "Cost reduction vs flag nobody", "Early Warning (Sem 1)": "77.2%", "Full Curriculum (Sem 1 & 2)": "77.0%"},
        {"Metric": "Cost reduction vs flag all", "Early Warning (Sem 1)": "~46.0%", "Full Curriculum (Sem 1 & 2)": "~44.0%"},
    ])
    st.dataframe(perf_df, hide_index=True, use_container_width=True)

    st.markdown("---")
    st.html('<div class="ri-section-label">FAIRNESS AUDIT</div>')
    fairness_rows = [
        (
            "Scholarship disparity",
            "Dropout recall",
            "63.2% (scholarship) vs 91.3% (non-scholarship)",
            "Scholarship holders have a lower base dropout rate (9.3% vs 39.0%); advisors should not rely solely on automated flags for scholarship recipients.",
        ),
        (
            "Gender disparity",
            "False alarm rate",
            "42.4% (male) vs 23.7% (female)",
            "Male students are flagged more often (66.3% vs 38.4%); outreach must stay supportive and avoid stigma.",
        ),
        (
            "Age disparity",
            "Dropout recall",
            "84.1% (age ≤ 20) vs 94.1% (age > 25)",
            "Older students carry stronger financial and attendance signals; International (N=24) and Special Needs (N=10) samples are too small for parity conclusions.",
        ),
    ]
    for title, metric, observed, interp in fairness_rows:
        st.html(f"""
        <div class="ri-fairness">
          <div class="ri-fairness-title">{title}</div>
          <div class="ri-fairness-metric">{metric}</div>
          <div class="ri-fairness-obs">{observed}</div>
          <div class="ri-fairness-interp">{interp}</div>
        </div>
        """)

    st.markdown("---")
    st.html('<div class="ri-section-label">RESPONSIBLE USE PRINCIPLES</div>')
    principles = [
        ("1", "Supportive, Not Punitive", "The system allocates advising, tutoring, and financial support and is never used to deny enrollment or penalize students."),
        ("2", "Human in the Loop", "Model scores serve strictly as diagnostic signals; a human academic advisor always makes the final mentoring decision."),
        ("3", "Unobserved External Factors", "Students leaving with strong grades and paid tuition often depart for personal, health, or relocation reasons absent from the database."),
        ("4", "Attribution", "Built on the UCI 697 dataset created by Instituto Polit&eacute;cnico de Portalegre (Realinho et al., 2021) under CC BY 4.0."),
    ]
    p_cols = st.columns(2, gap="medium")
    for idx, (num, p_title, p_desc) in enumerate(principles):
        with p_cols[idx % 2]:
            st.html(f"""
            <div class="ri-principle">
              <div class="ri-principle-num">{num}</div>
              <div class="ri-principle-title">{p_title}</div>
              <div class="ri-principle-desc">{p_desc}</div>
            </div>
            """)
