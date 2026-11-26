"""Student Dropout Risk & Retention Intelligence System.
Streamlit Faculty Advising Dashboard.

Run locally:
    streamlit run app/app.py
"""
import os
import sys
from pathlib import Path

# Ensure writable matplotlib cache directory
os.environ["MPLCONFIGDIR"] = "/tmp/matplotlib"

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import altair as alt
import json
import numpy as np
import pandas as pd
import streamlit as st

from src.explain import HIGH_TIER, fmt_value
from src.pipeline import load_data
from src.predict import (TIER_ACTIONS, feature_specs, load_artifacts,
                          random_student, score_student, top_changes)

# ------------------------------------------------------------------ PAGE CONFIG
st.set_page_config(
    page_title="Student Dropout Risk Intelligence",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------------ HUMAN-FRIENDLY MAPPINGS
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

MARITAL_STATUS_MAP = {
    1: "Single",
    2: "Married",
    3: "Widower",
    4: "Divorced",
    5: "Facto Union",
    6: "Legally Separated"
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
    57: "Change of Institution/Course (Intl)"
}

PREVIOUS_QUAL_MAP = {
    1: "Secondary Education (12th Year)",
    2: "Higher Education - Bachelor's",
    3: "Higher Education - Degree",
    4: "Higher Education - Master's",
    5: "Higher Education - Doctorate",
    6: "Frequency of Higher Education",
    9: "12th Year (Incomplete)",
    10: "11th Year (Incomplete)",
    12: "Other - 11th Year",
    14: "10th Year of Schooling",
    15: "10th Year (Incomplete)",
    19: "Basic Education 3rd Cycle (9th-11th)",
    38: "Basic Education 2nd Cycle (6th-8th)",
    39: "Technological Specialization",
    40: "Higher Education Degree (1st Cycle)",
    42: "Professional Higher Technical",
    43: "Higher Education Master (2nd Cycle)"
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
    44: "Higher Education Doctorate (3rd Cycle)"
}

PARENT_OCC_MAP = {
    0: "Student",
    1: "Legislative & Executive Representatives",
    2: "Specialists in Intellectual & Scientific Fields",
    3: "Intermediate Level Technicians",
    4: "Administrative Staff",
    5: "Personal, Protection & Security Services",
    6: "Farmers & Skilled Agricultural Workers",
    7: "Skilled Metallurgy & Construction Workers",
    8: "Plant & Machine Operators & Assembly",
    9: "Unskilled Workers",
    10: "Armed Forces Occupations",
    90: "Other Situations",
    99: "Armed Forces Officers",
    122: "Health Professionals",
    123: "Teachers & Professors",
    125: "ICT Specialists",
    131: "Engineering & Science Technicians",
    132: "Health Technicians",
    134: "Legal & Social Technicians",
    141: "Office Clerks & Secretaries",
    143: "Data & Finance Clerks",
    144: "Other Admin Support",
    151: "Personal Service Workers",
    152: "Sales & Store Staff",
    153: "Personal Care Workers",
    154: "Security Personnel",
    171: "Construction Trades",
    173: "Woodworkers & Cabinet Makers",
    175: "Textile & Garment Workers",
    191: "Cleaners & Helpers",
    192: "Agricultural & Fishery Laborers",
    193: "Mining & Construction Laborers",
    194: "Manufacturing Laborers",
    195: "Food Preparation Assistants"
}

def map_label(mapping, key, fallback_prefix="Code"):
    try:
        k = int(key)
        return mapping.get(k, f"{fallback_prefix} {key}")
    except (ValueError, TypeError):
        return f"{fallback_prefix} {key}"

# ------------------------------------------------------------------ DATA & ARTIFACTS
@st.cache_resource
def get_artifacts(model="xgboost", tag="early"):
    return load_artifacts(model, tag, ROOT)

@st.cache_data
def get_data():
    return load_data(ROOT / "data" / "data.csv")

df = get_data()
base_rate = float((df["Target"] == "Dropout").mean())

# ------------------------------------------------------------------ SIDEBAR CONTROLS
with st.sidebar:
    st.markdown("### 🎓 Retention Intelligence")
    st.caption("Course Project INT395 • Supervised Learning")

    st.markdown("#### Model & Pipeline Mode")
    tag_choice = st.segmented_control(
        "Prediction Pipeline",
        options=["⚡ Early-Warning (Sem 1)", "📚 Full Curriculum (Sem 1 & 2)"],
        default="⚡ Early-Warning (Sem 1)",
        label_visibility="collapsed"
    )
    selected_tag = "early" if "Early" in tag_choice else "full"
    art = get_artifacts("xgboost", selected_tag)
    features = art.features
    specs = feature_specs(df, features)

    st.markdown("#### Student Presets")
    preset_choice = st.selectbox(
        "Choose Persona or Load Student",
        [
            "Custom Input (Live Sliders)",
            "🚨 Persona: High-Risk Attrition",
            "⭐ Persona: High-Performing Scholar",
            "⚖️ Persona: Borderline Struggling",
        ],
        index=0,
    )

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        load_random_clicked = st.button("🎲 Sample Random", use_container_width=True)
    with col_btn2:
        reset_clicked = st.button("🔄 Reset Baseline", use_container_width=True)

    # State management for features
    def typed(spec, v):
        return int(v) if spec["kind"] in ("binary", "nominal", "int") else float(v)

    # Initialize session state if missing
    for f in features:
        st.session_state.setdefault(f, typed(specs[f], specs[f]["default"]))
    st.session_state.setdefault("_outcome", None)
    st.session_state.setdefault("_preset_name", "Custom")

    # Handle preset clicks
    if load_random_clicked:
        vals, outcome = random_student(df, features)
        for f in features:
            st.session_state[f] = typed(specs[f], vals[f])
        st.session_state["_outcome"] = outcome
        st.session_state["_preset_name"] = "Random Dataset Student"
        st.toast(f"Loaded random student record (Actual: {outcome})", icon="🎲")

    elif reset_clicked:
        for f in features:
            st.session_state[f] = typed(specs[f], specs[f]["default"])
        st.session_state["_outcome"] = None
        st.session_state["_preset_name"] = "Baseline"
        st.toast("Reset student profile to cohort medians.", icon="🔄")

    elif preset_choice == "🚨 Persona: High-Risk Attrition" and st.session_state.get("_preset_name") != "High-Risk":
        st.session_state["Curricular units 1st sem (approved)"] = 0
        st.session_state["Curricular units 1st sem (enrolled)"] = 6
        st.session_state["Curricular units 1st sem (grade)"] = 0.0
        st.session_state["Tuition fees up to date"] = 0
        st.session_state["Debtor"] = 1
        st.session_state["Scholarship holder"] = 0
        st.session_state["Age at enrollment"] = 28
        st.session_state["Admission grade"] = 105.0
        st.session_state["Course"] = 9147  # Management
        if "Curricular units 2nd sem (approved)" in features:
            st.session_state["Curricular units 2nd sem (approved)"] = 0
            st.session_state["Curricular units 2nd sem (grade)"] = 0.0
        st.session_state["_outcome"] = "Dropout (Synthetic Persona)"
        st.session_state["_preset_name"] = "High-Risk"

    elif preset_choice == "⭐ Persona: High-Performing Scholar" and st.session_state.get("_preset_name") != "Scholar":
        st.session_state["Curricular units 1st sem (approved)"] = 6
        st.session_state["Curricular units 1st sem (enrolled)"] = 6
        st.session_state["Curricular units 1st sem (grade)"] = 16.2
        st.session_state["Tuition fees up to date"] = 1
        st.session_state["Debtor"] = 0
        st.session_state["Scholarship holder"] = 1
        st.session_state["Age at enrollment"] = 19
        st.session_state["Admission grade"] = 158.0
        st.session_state["Course"] = 9500  # Nursing
        if "Curricular units 2nd sem (approved)" in features:
            st.session_state["Curricular units 2nd sem (approved)"] = 6
            st.session_state["Curricular units 2nd sem (grade)"] = 16.5
        st.session_state["_outcome"] = "Graduate (Synthetic Persona)"
        st.session_state["_preset_name"] = "Scholar"

    elif preset_choice == "⚖️ Persona: Borderline Struggling" and st.session_state.get("_preset_name") != "Borderline":
        st.session_state["Curricular units 1st sem (approved)"] = 3
        st.session_state["Curricular units 1st sem (enrolled)"] = 6
        st.session_state["Curricular units 1st sem (grade)"] = 11.4
        st.session_state["Tuition fees up to date"] = 1
        st.session_state["Debtor"] = 0
        st.session_state["Scholarship holder"] = 0
        st.session_state["Age at enrollment"] = 24
        st.session_state["Admission grade"] = 120.0
        st.session_state["Course"] = 9254  # Tourism
        if "Curricular units 2nd sem (approved)" in features:
            st.session_state["Curricular units 2nd sem (approved)"] = 3
            st.session_state["Curricular units 2nd sem (grade)"] = 11.0
        st.session_state["_outcome"] = "Enrolled / At Risk"
        st.session_state["_preset_name"] = "Borderline"

    if st.session_state.get("_outcome"):
        st.info(f"Target Record: **{st.session_state['_outcome']}**")

    st.markdown("---")
    st.markdown("#### Model Telemetry")
    res_path = ROOT / "reports" / f"test_results_xgboost_{selected_tag}.json"
    if res_path.exists():
        res_data = json.load(open(res_path))
        st.caption(f"**Evaluated on:** {res_data['n_test']} Holdout Students")
        st.caption(f"• **Dropout ROC-AUC:** `{res_data['dropout_roc_auc']:.3f}`")
        st.caption(f"• **Dropout Recall:** `{res_data['at_chosen_threshold']['recall']:.1%}`")
        st.caption(f"• **Cost Reduction:** `77%` vs Unflagged")
        st.caption(f"• **Triage Cutoff ($t$):** `{art.threshold:.2f}` (5:1 penalty)")

# ------------------------------------------------------------------ HEADER SECTION
st.title("Student Retention & Early-Warning Intelligence")
st.markdown(
    ":blue-badge[INT395 Supervised Learning] "
    ":green-badge[Verified Single-Pass Holdout (N=885)] "
    ":orange-badge[TreeSHAP Interpretable] "
    f":gray-badge[Active: {'Early-Warning (Sem 1)' if selected_tag == 'early' else 'Full Curriculum'}]"
)
st.caption(
    "Decision-support system for academic advisors to identify early student attrition risk, "
    "diagnose personalized contributing factors, and guide targeted clinical retention interventions."
)

# ------------------------------------------------------------------ TABS
tab_overview, tab_studio, tab_simulator, tab_audit = st.tabs([
    "🎯 Risk Assessment & AI Advisor",
    "📝 Student Profile Studio",
    "🧪 What-If Intervention Lab",
    "🛡️ Model Governance & Fairness"
])

# Gather current values from session state
current_values = {f: st.session_state[f] for f in features}
result = score_student(art, current_values)
risk = result["risk"]
tier_name = result["tier"]
raw_p = result["raw"]
probs = result.get("probs", {"Dropout": risk, "Enrolled": 0.18, "Graduate": 1 - risk - 0.18})
t = art.threshold

# ==============================================================================
# TAB 1: RISK ASSESSMENT & AI ADVISOR
# ==============================================================================
with tab_overview:
    # Top KPI Cards
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)

    with col_kpi1:
        with st.container(border=True):
            if tier_name == "High":
                st.markdown("#### 🔴 Dropout Risk: **High**")
                st.metric("P(Dropout)", f"{risk:.1%}", delta=f"{risk - base_rate:+.1%} vs cohort avg", delta_color="inverse")
                st.error("Priority 1-on-1 advisor outreach mandated within 7 days.")
            elif tier_name == "Medium":
                st.markdown("#### 🟡 Dropout Risk: **Medium**")
                st.metric("P(Dropout)", f"{risk:.1%}", delta=f"{risk - base_rate:+.1%} vs cohort avg", delta_color="inverse")
                st.warning("Automated check-in & peer tutoring referral suggested.")
            else:
                st.markdown("#### 🟢 Dropout Risk: **Low**")
                st.metric("P(Dropout)", f"{risk:.1%}", delta=f"{risk - base_rate:+.1%} vs cohort avg", delta_color="inverse")
                st.success("Standard academic advising schedule. On track.")

    with col_kpi2:
        with st.container(border=True):
            st.markdown("#### ⚖️ Decision Threshold")
            st.metric("Cost-Optimal Cutoff (t)", f"{t:.0%}", f"Cost penalty ratio 5:1")
            if risk >= t:
                st.markdown(f"**Flagged for Intervention:** Student risk (`{risk:.1%}`) exceeds operational threshold (`{t:.0%}`).")
            else:
                st.markdown(f"**Below Flagging Threshold:** Student risk (`{risk:.1%}`) is under the operational trigger (`{t:.0%}`).")

    with col_kpi3:
        with st.container(border=True):
            st.markdown("#### 📊 Outcome Probabilities")
            p_drop = probs.get("Dropout", risk)
            p_enr = probs.get("Enrolled", 0.18)
            p_grad = max(0.0, 1.0 - p_drop - p_enr)
            st.markdown(f"• **Graduate:** `{p_grad:.1%}`")
            st.markdown(f"• **Persist (Enrolled):** `{p_enr:.1%}`")
            st.markdown(f"• **Dropout:** `{p_drop:.1%}`")

    # Visual Risk Spectrum Gauge
    with st.container(border=True):
        st.markdown("**Visual Risk Spectrum & Triage Cutoff**")
        gauge_percent = min(max(int(risk * 100), 0), 100)
        t_percent = int(t * 100)
        high_percent = int(HIGH_TIER * 100)

        gauge_html = f"""
        <div style="margin: 10px 0 20px 0;">
            <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 5px; color: #94A3B8;">
                <span>🟢 Safe (0%)</span>
                <span>Cutoff: {t_percent}% (5:1 min cost)</span>
                <span>High Alert: {high_percent}%</span>
                <span>🔴 Critical (100%)</span>
            </div>
            <div style="position: relative; width: 100%; height: 20px; background: linear-gradient(to right, #10B981 0%, #10B981 {t_percent}%, #F59E0B {t_percent}%, #F59E0B {high_percent}%, #EF4444 {high_percent}%, #DC2626 100%); border-radius: 10px;">
                <div style="position: absolute; left: {gauge_percent}%; top: -6px; transform: translateX(-50%); width: 12px; height: 32px; background-color: #FFFFFF; border: 2px solid #0F172A; border-radius: 6px; box-shadow: 0 0 10px rgba(0,0,0,0.5);"></div>
            </div>
            <div style="text-align: center; margin-top: 8px; font-weight: 600; font-size: 14px;">
                Current Position: {risk:.1%} ({tier_name} Risk Zone)
            </div>
        </div>
        """
        st.html(gauge_html)

    # Detailed Analysis: Action Plan & TreeSHAP
    col_plan, col_shap = st.columns([1, 1])

    with col_plan:
        with st.container(border=True):
            st.markdown("### 📋 Prescriptive Advisor Action Plan")
            st.markdown(f"**Primary Guidance:** {TIER_ACTIONS[tier_name]}")

            contrib = result["contributions"]
            up_factors = [f for f, v in contrib.items() if v > 0]
            down_factors = [f for f, v in contrib.items() if v < 0]

            st.markdown("#### 💬 Recommended Talking Points")
            talking_points = []
            if "Tuition fees up to date" in up_factors:
                talking_points.append("💸 **Tuition Payment Status:** Discuss emergency student hardship funds, installment schedules, or student union grants.")
            if any("approved" in f for f in up_factors):
                talking_points.append("📚 **Academic Recovery:** Investigate dropped/failed units and connect with faculty office hours and peer tutoring.")
            if "Age at enrollment" in up_factors:
                talking_points.append("⏰ **Work-Life Balance:** Explore flexible evening course alternatives or part-time matriculation tracks for mature students.")
            if not talking_points:
                talking_points.append("✅ **Positive Reinforcement:** Affirm current academic momentum and ensure continuity for the upcoming semester.")

            for tp in talking_points:
                st.markdown(f"• {tp}")

            st.markdown("#### ⏱️ Recommended Follow-Up Window")
            if tier_name == "High":
                st.error("🚨 **Urgent:** Schedule personal meeting within **7 calendar days**.")
            elif tier_name == "Medium":
                st.warning("⚠️ **Moderate:** Review progress within **30 calendar days**.")
            else:
                st.success("🟢 **Routine:** Follow standard semester advising milestones.")

    with col_shap:
        with st.container(border=True):
            st.markdown("### 🔍 TreeSHAP Feature Attribution")
            st.caption("How specific factors push this student's risk up or down (Class 0: Dropout)")

            top_k = contrib.head(8)
            rest_sum = contrib.iloc[8:].sum()

            plot_items = []
            for f in top_k.index:
                val = current_values.get(f, 0)
                formatted_val = fmt_value(val)
                # Shorten long feature names for clean display
                clean_name = f.replace("Curricular units ", "").replace("1st sem ", "Sem1 ").replace("2nd sem ", "Sem2 ")
                plot_items.append({
                    "Feature": f"{clean_name} = {formatted_val}",
                    "SHAP Impact": float(top_k[f]),
                    "Direction": "Increases Risk" if top_k[f] > 0 else "Reduces Risk"
                })

            if len(contrib) > 8:
                plot_items.append({
                    "Feature": f"{len(contrib) - 8} Other Features Combined",
                    "SHAP Impact": float(rest_sum),
                    "Direction": "Increases Risk" if rest_sum > 0 else "Reduces Risk"
                })

            df_shap = pd.DataFrame(plot_items)

            # Modern Altair horizontal bar chart
            chart = alt.Chart(df_shap).mark_bar(cornerRadiusEnd=4).encode(
                x=alt.X("SHAP Impact:Q", title="Log-Odds Contribution (Red = Toward Dropout)"),
                y=alt.Y("Feature:N", sort=None, title=None),
                color=alt.Color(
                    "Direction:N",
                    scale=alt.Scale(domain=["Increases Risk", "Reduces Risk"], range=["#EF4444", "#3B82F6"]),
                    legend=alt.Legend(orient="bottom", title=None)
                ),
                tooltip=["Feature", "SHAP Impact", "Direction"]
            ).properties(height=320)

            st.altair_chart(chart, use_container_width=True)

            up_changes, down_changes = top_changes(contrib, current_values)
            st.markdown(f":red-badge[Top Risk Factors:] {', '.join(up_changes) if up_changes else 'None'}")
            st.markdown(f":blue-badge[Top Protective Factors:] {', '.join(down_changes) if down_changes else 'None'}")
            st.caption("⚠️ *TreeSHAP quantifies model feature reliance, not real-world causation.*")

# ==============================================================================
# TAB 2: STUDENT PROFILE STUDIO
# ==============================================================================
with tab_studio:
    st.markdown("### 📝 Student Data & Parameters Studio")
    st.caption("Adjust student academic, socioeconomic, and demographic records below. Changes update the risk model in real-time.")

    col_acad, col_socio, col_demo = st.columns(3)

    with col_acad:
        with st.container(border=True):
            st.markdown("#### 📚 Academic Record (Sem 1 & 2)")

            st.session_state["Curricular units 1st sem (approved)"] = st.slider(
                "Sem 1 Approved Units", 0, 26,
                value=int(st.session_state.get("Curricular units 1st sem (approved)", 5)),
                help="Units successfully passed in Semester 1."
            )
            st.session_state["Curricular units 1st sem (enrolled)"] = st.slider(
                "Sem 1 Enrolled Units", 0, 26,
                value=int(st.session_state.get("Curricular units 1st sem (enrolled)", 6)),
                help="Total units matriculated in Semester 1."
            )
            st.session_state["Curricular units 1st sem (evaluations)"] = st.number_input(
                "Sem 1 Evaluation Moments", 0, 45,
                value=int(st.session_state.get("Curricular units 1st sem (evaluations)", 8)),
                help="Assessments or exam sittings attended."
            )
            st.session_state["Curricular units 1st sem (grade)"] = st.slider(
                "Sem 1 Grade Average (0–20 Scale)", 0.0, 20.0,
                value=float(st.session_state.get("Curricular units 1st sem (grade)", 12.5)),
                step=0.1
            )
            st.session_state["Curricular units 1st sem (credited)"] = st.number_input(
                "Sem 1 Credited Units", 0, 20,
                value=int(st.session_state.get("Curricular units 1st sem (credited)", 0))
            )
            st.session_state["Curricular units 1st sem (without evaluations)"] = st.number_input(
                "Sem 1 Without Evaluations", 0, 12,
                value=int(st.session_state.get("Curricular units 1st sem (without evaluations)", 0))
            )

            if "Curricular units 2nd sem (approved)" in features:
                st.markdown("---")
                st.markdown("**Semester 2 Record (Full Model Only)**")
                st.session_state["Curricular units 2nd sem (approved)"] = st.slider(
                    "Sem 2 Approved Units", 0, 26,
                    value=int(st.session_state.get("Curricular units 2nd sem (approved)", 5))
                )
                st.session_state["Curricular units 2nd sem (enrolled)"] = st.slider(
                    "Sem 2 Enrolled Units", 0, 26,
                    value=int(st.session_state.get("Curricular units 2nd sem (enrolled)", 6))
                )
                st.session_state["Curricular units 2nd sem (grade)"] = st.slider(
                    "Sem 2 Grade Average (0–20 Scale)", 0.0, 20.0,
                    value=float(st.session_state.get("Curricular units 2nd sem (grade)", 12.5)),
                    step=0.1
                )
            else:
                st.info("🔒 Semester 2 features excluded in Early-Warning mode to eliminate lookahead leakage.")

    with col_socio:
        with st.container(border=True):
            st.markdown("#### 💳 Socioeconomic & Financial")

            tuition_val = st.segmented_control(
                "Tuition Fees Current?",
                options=["Yes (Up to Date)", "No (Overdue)"],
                default="Yes (Up to Date)" if st.session_state.get("Tuition fees up to date", 1) == 1 else "No (Overdue)"
            )
            st.session_state["Tuition fees up to date"] = 1 if "Yes" in tuition_val else 0

            debtor_val = st.segmented_control(
                "Institutional Debts?",
                options=["No Debt", "Has Unpaid Debt"],
                default="No Debt" if st.session_state.get("Debtor", 0) == 0 else "Has Unpaid Debt"
            )
            st.session_state["Debtor"] = 1 if "Has" in debtor_val else 0

            scholarship_val = st.segmented_control(
                "Scholarship Grantee?",
                options=["No", "Yes (Grantee)"],
                default="Yes (Grantee)" if st.session_state.get("Scholarship holder", 0) == 1 else "No"
            )
            st.session_state["Scholarship holder"] = 1 if "Yes" in scholarship_val else 0

            attend_val = st.segmented_control(
                "Attendance Schedule",
                options=["Daytime", "Evening"],
                default="Daytime" if st.session_state.get("Daytime/evening attendance", 1) == 1 else "Evening"
            )
            st.session_state["Daytime/evening attendance"] = 1 if attend_val == "Daytime" else 0

            displaced_val = st.segmented_control(
                "Displaced Student?",
                options=["Local", "Living Away From Home"],
                default="Living Away From Home" if st.session_state.get("Displaced", 1) == 1 else "Local"
            )
            st.session_state["Displaced"] = 1 if "Away" in displaced_val else 0

            st.markdown("---")
            st.markdown("**Macroeconomic Indicators**")
            st.session_state["Unemployment rate"] = st.number_input(
                "Unemployment Rate (%)", 0.0, 30.0,
                value=float(st.session_state.get("Unemployment rate", 10.8)), step=0.1
            )
            st.session_state["Inflation rate"] = st.number_input(
                "Inflation Rate (%)", -5.0, 10.0,
                value=float(st.session_state.get("Inflation rate", 1.4)), step=0.1
            )
            st.session_state["GDP"] = st.number_input(
                "GDP Change (%)", -10.0, 10.0,
                value=float(st.session_state.get("GDP", 1.74)), step=0.1
            )

    with col_demo:
        with st.container(border=True):
            st.markdown("#### 👤 Demographics & Program")

            st.session_state["Age at enrollment"] = st.slider(
                "Age at Enrollment", 17, 70,
                value=int(st.session_state.get("Age at enrollment", 20))
            )

            gender_val = st.segmented_control(
                "Gender",
                options=["Female", "Male"],
                default="Female" if st.session_state.get("Gender", 0) == 0 else "Male"
            )
            st.session_state["Gender"] = 1 if gender_val == "Male" else 0

            course_options = specs["Course"]["options"]
            current_course = int(st.session_state.get("Course", course_options[0]))
            st.session_state["Course"] = st.selectbox(
                "Degree Programme",
                options=course_options,
                index=course_options.index(current_course) if current_course in course_options else 0,
                format_func=lambda c: map_label(COURSE_MAP, c, "Course Code")
            )

            st.session_state["Admission grade"] = st.slider(
                "Admission Grade (0–200)", 0.0, 200.0,
                value=float(st.session_state.get("Admission grade", 125.0)), step=0.5
            )

            st.session_state["Previous qualification (grade)"] = st.slider(
                "Previous Qualification Grade (0–200)", 0.0, 200.0,
                value=float(st.session_state.get("Previous qualification (grade)", 130.0)), step=0.5
            )

            with st.expander("Family Qualifications & Background"):
                app_options = specs["Application mode"]["options"]
                cur_app = int(st.session_state.get("Application mode", app_options[0]))
                st.session_state["Application mode"] = st.selectbox(
                    "Application Mode",
                    options=app_options,
                    index=app_options.index(cur_app) if cur_app in app_options else 0,
                    format_func=lambda a: map_label(APPLICATION_MODE_MAP, a, "Mode")
                )

                mq_options = specs["Mother's qualification"]["options"]
                cur_mq = int(st.session_state.get("Mother's qualification", mq_options[0]))
                st.session_state["Mother's qualification"] = st.selectbox(
                    "Mother's Qualification",
                    options=mq_options,
                    index=mq_options.index(cur_mq) if cur_mq in mq_options else 0,
                    format_func=lambda q: map_label(PARENT_QUAL_MAP, q, "Qual")
                )

                fq_options = specs["Father's qualification"]["options"]
                cur_fq = int(st.session_state.get("Father's qualification", fq_options[0]))
                st.session_state["Father's qualification"] = st.selectbox(
                    "Father's Qualification",
                    options=fq_options,
                    index=fq_options.index(cur_fq) if cur_fq in fq_options else 0,
                    format_func=lambda q: map_label(PARENT_QUAL_MAP, q, "Qual")
                )

                mo_options = specs["Mother's occupation"]["options"]
                cur_mo = int(st.session_state.get("Mother's occupation", mo_options[0]))
                st.session_state["Mother's occupation"] = st.selectbox(
                    "Mother's Occupation",
                    options=mo_options,
                    index=mo_options.index(cur_mo) if cur_mo in mo_options else 0,
                    format_func=lambda o: map_label(PARENT_OCC_MAP, o, "Occ")
                )

# ==============================================================================
# TAB 3: WHAT-IF INTERVENTION LAB
# ==============================================================================
with tab_simulator:
    st.markdown("### 🧪 What-If Counterfactual Intervention Lab")
    st.caption("Simulate hypothetical mentorship interventions to evaluate their predicted risk reduction before deploying institutional resources.")

    sim_values = dict(current_values)

    col_sim_controls, col_sim_results = st.columns([1, 1])

    with col_sim_controls:
        with st.container(border=True):
            st.markdown("#### 🛠️ Configure Intervention Package")

            tutoring_boost = st.slider(
                "Tutoring Impact: Additional Approved Units",
                0, 4, value=1,
                help="Simulate the student passing extra curricular units due to academic mentoring."
            )
            sim_values["Curricular units 1st sem (approved)"] = min(
                26, sim_values.get("Curricular units 1st sem (approved)", 0) + tutoring_boost
            )

            grant_relief = st.toggle(
                "Emergency Hardship Grant: Settle Overdue Tuition & Debt",
                value=(sim_values.get("Tuition fees up to date", 1) == 0 or sim_values.get("Debtor", 0) == 1),
                help="Simulate clearing institutional debts and bringing tuition payments up to date."
            )
            if grant_relief:
                sim_values["Tuition fees up to date"] = 1
                sim_values["Debtor"] = 0

            grade_boost = st.slider(
                "Study Workshop: GPA Improvement (Points)",
                0.0, 4.0, value=1.5, step=0.5,
                help="Simulate an increase in academic grade average."
            )
            sim_values["Curricular units 1st sem (grade)"] = min(
                20.0, sim_values.get("Curricular units 1st sem (grade)", 0.0) + grade_boost
            )

    # Score simulated student
    sim_result = score_student(art, sim_values)
    sim_risk = sim_result["risk"]
    sim_tier = sim_result["tier"]
    risk_diff = sim_risk - risk

    with col_sim_results:
        with st.container(border=True):
            st.markdown("#### 📈 Predicted Intervention Impact")

            col_before, col_after = st.columns(2)
            with col_before:
                st.metric("Baseline Risk", f"{risk:.1%}", tier_name)
            with col_after:
                st.metric(
                    "Post-Intervention Risk",
                    f"{sim_risk:.1%}",
                    delta=f"{risk_diff:+.1%}",
                    delta_color="inverse"
                )

            if risk_diff < -0.05:
                st.success(
                    f"🎉 **Positive Trajectory:** Intervention reduces attrition probability by **{abs(risk_diff):.1%}**, "
                    f"shifting student from **{tier_name} Risk** to **{sim_tier} Risk**!"
                )
            elif risk_diff >= 0:
                st.info("ℹ️ Configured parameters produced no significant risk reduction.")
            else:
                st.warning(f"Modest risk reduction of {abs(risk_diff):.1%}. Additional support required.")

# ==============================================================================
# TAB 4: MODEL GOVERNANCE & FAIRNESS AUDIT
# ==============================================================================
with tab_audit:
    st.markdown("### 🛡️ Algorithmic Governance, Fairness & Holdout Test Audit")
    st.caption("Rigorous single-pass test set evaluation on 885 completely unobserved students, with subgroup fairness diagnostics.")

    col_gov1, col_gov2 = st.columns(2)

    with col_gov1:
        with st.container(border=True):
            st.markdown("#### 📊 Empirical Holdout Test Benchmarks")
            st.markdown(
                """
                | Metric | Early-Warning (Sem 1) | Full Curriculum |
                | :--- | :---: | :---: |
                | **Holdout Cohort (N)** | **885 students** | **885 students** |
                | **Dropout ROC-AUC** | **0.893** | **0.915** |
                | **Dropout PR-AUC** | **0.844** | **0.872** |
                | **Dropout Recall** | **89.4%** (254/284) | **86.6%** (246/284) |
                | **Dropout Precision** | **59.3%** | **64.2%** |
                | **Cost Reduction vs Unflagged** | **77.2%** | **77.0%** |
                """
            )
            st.caption("Evaluated strictly once at Phase 5 conclusion. No post-hoc tuning on test data.")

    with col_gov2:
        with st.container(border=True):
            st.markdown("#### ⚖️ Subgroup Fairness Audit (Early Model)")
            st.markdown(
                """
                - **Scholarship Disparity:** Scholarship holders have lower base dropout rates (9.3% vs 39.0%), resulting in lower recall (**63.2%** vs **91.3%**). Mentors should not rely solely on automated alerts for scholarship recipients.
                - **Gender Disparity:** Male students experience double the false-alarm rate (42.4% vs 23.7%), with 66.3% of males flagged vs 38.4% of females.
                - **Age Disparity:** Students aged $\le 20$ have an 84.1% recall, while mature students ($>25$) have a 94.1% recall.
                - **Sample Size Warning:** International ($N=24$) and Special Needs ($N=10$) cohorts are too small for statistically valid conclusions.
                """
            )

    with st.container(border=True):
        st.markdown("#### 📜 Ethical Decision-Support Charter")
        st.markdown(
            """
            1. **Supportive, Not Punitive:** This tool exists exclusively to allocate support, tutoring, and counseling—never to disqualify, dismiss, or deny enrollment.
            2. **Human in the Loop:** Automated scores never constitute decisions; they serve as diagnostic signals for experienced human faculty advisors.
            3. **Unobserved External Factors:** Students who leave with good grades and paid tuition depart due to personal, family, or health reasons not present in institutional databases.
            4. **Attribution:** Dataset created by *Instituto Politécnico de Portalegre* (Realinho et al., 2021) under CC BY 4.0.
            """
        )
