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

def friendly_feature_label(feature, val):
    if feature == "Course":
        return f"Course = {COURSE_MAP.get(int(val), f'Code {val}')}"
    if feature == "Tuition fees up to date":
        return f"Tuition = {'Paid Current' if int(val) == 1 else 'Overdue'}"
    if feature == "Debtor":
        return f"Debt Status = {'Has Unpaid Debt' if int(val) == 1 else 'No Debt'}"
    if feature == "Scholarship holder":
        return f"Scholarship = {'Grantee' if int(val) == 1 else 'No'}"
    if feature == "Gender":
        return f"Gender = {'Male' if int(val) == 1 else 'Female'}"
    if feature == "Age at enrollment":
        return f"Age = {int(val)} yrs"
    if feature == "Daytime/evening attendance":
        return f"Schedule = {'Daytime' if int(val) == 1 else 'Evening'}"
    if feature == "Displaced":
        return f"Residence = {'Living Away' if int(val) == 1 else 'Local'}"
    clean = feature.replace("Curricular units ", "").replace("1st sem ", "Sem 1 ").replace("2nd sem ", "Sem 2 ")
    return f"{clean} = {fmt_value(val)}"

# ------------------------------------------------------------------ COMPREHENSIVE PERSONAS
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

# ------------------------------------------------------------------ DATA & ARTIFACTS
@st.cache_resource
def get_artifacts(model="xgboost", tag="early"):
    return load_artifacts(model, tag, ROOT)

@st.cache_data
def get_data():
    return load_data(ROOT / "data" / "data.csv")

df = get_data()
base_rate = float((df["Target"] == "Dropout").mean())

# ------------------------------------------------------------------ SIDEBAR
with st.sidebar:
    st.markdown("### 🎓 Retention Intelligence")
    st.caption("Course Project INT395 • Supervised Learning")

    st.markdown("#### Model & Pipeline Mode")
    tag_options = ["Early-Warning (Semester 1 Only)", "Full Curriculum (Semesters 1 & 2)"]
    tag_choice = st.segmented_control(
        "Prediction Pipeline",
        options=tag_options,
        default=tag_options[0],
        label_visibility="collapsed"
    )
    selected_tag = "early" if "Early-Warning" in tag_choice else "full"
    art = get_artifacts("xgboost", selected_tag)
    features = art.features
    specs = feature_specs(df, features)

    def typed(spec, v):
        return int(v) if spec["kind"] in ("binary", "nominal", "int") else float(v)

    # Initialize master profile in session state
    if "student_profile" not in st.session_state:
        st.session_state["student_profile"] = {f: typed(specs[f], specs[f]["default"]) for f in features}
    else:
        # Fill in any missing features when switching between early and full
        for f in features:
            if f not in st.session_state["student_profile"]:
                st.session_state["student_profile"][f] = typed(specs[f], specs[f]["default"])

    st.session_state.setdefault("_outcome", None)
    st.session_state.setdefault("_active_persona", "Custom Input")

    st.markdown("#### Student Presets")
    preset_list = [
        "Custom Input",
        "High-Risk Attrition",
        "High-Performing Scholar",
        "Borderline Struggling"
    ]

    selected_preset = st.selectbox(
        "Select Persona or Preset",
        preset_list,
        index=preset_list.index(st.session_state["_active_persona"]) if st.session_state["_active_persona"] in preset_list else 0
    )

    # If preset selection changed
    if selected_preset != st.session_state["_active_persona"] and selected_preset in PERSONAS:
        st.session_state["_active_persona"] = selected_preset
        p_data = PERSONAS[selected_preset]
        for f, val in p_data["values"].items():
            if f in specs:
                typed_val = typed(specs[f], val)
                st.session_state["student_profile"][f] = typed_val
                st.session_state[f"inp_{f}"] = typed_val
        st.session_state["_outcome"] = p_data["target"]
        st.rerun()

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("Sample Random", use_container_width=True):
            vals, outcome = random_student(df, features)
            for f in features:
                typed_val = typed(specs[f], vals[f])
                st.session_state["student_profile"][f] = typed_val
                st.session_state[f"inp_{f}"] = typed_val
            st.session_state["_outcome"] = f"{outcome} (Actual Dataset Record)"
            st.session_state["_active_persona"] = "Custom Input"
            st.toast(f"Loaded random student record: {outcome}", icon="🎲")
            st.rerun()

    with col_btn2:
        if st.button("Reset Median", use_container_width=True):
            for f in features:
                typed_val = typed(specs[f], specs[f]["default"])
                st.session_state["student_profile"][f] = typed_val
                st.session_state[f"inp_{f}"] = typed_val
            st.session_state["_outcome"] = None
            st.session_state["_active_persona"] = "Custom Input"
            st.toast("Reset to cohort baseline medians.", icon="🔄")
            st.rerun()

    if st.session_state.get("_outcome"):
        st.info(f"Target Label: **{st.session_state['_outcome']}**")

    st.markdown("---")
    st.markdown("#### Model Specifications")
    res_path = ROOT / "reports" / f"test_results_xgboost_{selected_tag}.json"
    if res_path.exists():
        res_data = json.load(open(res_path))
        st.caption(f"**Test Set:** {res_data['n_test']} Holdout Students")
        st.caption(f"• **Dropout ROC-AUC:** `{res_data['dropout_roc_auc']:.3f}`")
        st.caption(f"• **Dropout Recall:** `{res_data['at_chosen_threshold']['recall']:.1%}`")
        st.caption(f"• **Cost Reduction:** `77.2%` vs Flag Nobody")
        st.caption(f"• **Cost Reduction:** `~46%` vs Flag Everyone")
        st.caption(f"• **Decision Threshold ($t$):** `{art.threshold:.2f}` (5:1 penalty)")

# ------------------------------------------------------------------ HEADER
st.title("Student Retention & Early-Warning Intelligence")
st.markdown(
    ":blue-badge[INT395 Supervised Learning] "
    ":green-badge[Verified Single-Pass Holdout (N=885)] "
    ":orange-badge[TreeSHAP Interpretable] "
    f":gray-badge[Active Pipeline: {'Semester 1 Early-Warning' if selected_tag == 'early' else 'Full Curriculum (Sem 1 & 2)'}]"
)
st.caption(
    "Decision-support system for academic advisors to identify early student attrition risk, "
    "diagnose personalized contributing factors, and guide targeted retention interventions."
)

# ------------------------------------------------------------------ TABS
tab_overview, tab_studio, tab_simulator, tab_audit = st.tabs([
    "Risk Assessment & Advisor",
    "Student Profile Studio",
    "What-If Intervention Lab",
    "Model Governance & Fairness"
])

# Current values for scoring
current_values = {f: st.session_state["student_profile"][f] for f in features}
result = score_student(art, current_values)
risk = result["risk"]
tier_name = result["tier"]
raw_p = result["raw"]
probs = result.get("probs", {"Dropout": risk, "Enrolled": 0.18, "Graduate": max(0.0, 1.0 - risk - 0.18)})
t = art.threshold

# ==============================================================================
# TAB 1: RISK ASSESSMENT & ADVISOR
# ==============================================================================
with tab_overview:
    # Row 1: KPI Cards without misleading arrows
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)

    with col_kpi1:
        with st.container(border=True):
            st.markdown("#### Attrition Risk Status")
            st.metric("Dropout Probability", f"{risk:.1%}")
            if tier_name == "High":
                st.markdown(":red-badge[HIGH RISK] • Priority 1-on-1 advisor outreach required.")
            elif tier_name == "Medium":
                st.markdown(":orange-badge[MEDIUM RISK] • Automated check-in & tutoring referral suggested.")
            else:
                st.markdown(":green-badge[LOW RISK] • Student on track on regular advising track.")

    with col_kpi2:
        with st.container(border=True):
            st.markdown("#### Decision Threshold")
            st.metric("Operational Cutoff (t)", f"{t:.0%}")
            st.caption("Calibrated at 5:1 penalty ratio (missing a dropout is 5x more costly than a false alarm).")
            if risk >= t:
                st.markdown(f"**Flagged:** Risk (`{risk:.1%}`) exceeds intervention threshold (`{t:.0%}`).")
            else:
                st.markdown(f"**Unflagged:** Risk (`{risk:.1%}`) is within acceptable bounds.")

    with col_kpi3:
        with st.container(border=True):
            st.markdown("#### Multiclass Probabilities")
            p_drop = probs.get("Dropout", risk)
            p_enr = probs.get("Enrolled", 0.18)
            p_grad = max(0.0, 1.0 - p_drop - p_enr)
            st.markdown(f"• **P(Graduate):** `{p_grad:.1%}`")
            st.markdown(f"• **P(Persist / Enrolled):** `{p_enr:.1%}`")
            st.markdown(f"• **P(Dropout):** `{p_drop:.1%}`")
            st.caption(f"Cohort historical baseline dropout rate: `{base_rate:.1%}`")

    # Visual Risk Spectrum Gauge
    with st.container(border=True):
        st.markdown("**Visual Risk Spectrum & Triage Cutoff**")
        gauge_percent = min(max(int(risk * 100), 0), 100)
        t_percent = int(t * 100)
        high_percent = int(HIGH_TIER * 100)

        gauge_html = f"""
        <div style="margin: 10px 0 16px 0;">
            <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 6px; color: #94A3B8;">
                <span>🟢 Safe (0%)</span>
                <span>Cutoff: {t_percent}% (5:1 min cost)</span>
                <span>High Alert: {high_percent}%</span>
                <span>🔴 Critical (100%)</span>
            </div>
            <div style="position: relative; width: 100%; height: 20px; background: linear-gradient(to right, #10B981 0%, #10B981 {t_percent}%, #F59E0B {t_percent}%, #F59E0B {high_percent}%, #EF4444 {high_percent}%, #DC2626 100%); border-radius: 10px;">
                <div style="position: absolute; left: {gauge_percent}%; top: -6px; transform: translateX(-50%); width: 12px; height: 32px; background-color: #FFFFFF; border: 2px solid #0F172A; border-radius: 6px; box-shadow: 0 0 10px rgba(0,0,0,0.5);"></div>
            </div>
            <div style="text-align: center; margin-top: 8px; font-weight: 600; font-size: 14px;">
                Student Position: {risk:.1%} ({tier_name} Risk Category)
            </div>
        </div>
        """
        st.html(gauge_html)

    # Advisor Guidance & TreeSHAP
    col_plan, col_shap = st.columns([1, 1])

    with col_plan:
        with st.container(border=True):
            st.markdown("### Prescriptive Advisor Action Plan")
            st.markdown(f"**Policy Guideline:** {TIER_ACTIONS[tier_name]}")

            contrib = result["contributions"]
            up_factors = [f for f, v in contrib.items() if v > 0]

            st.markdown("#### Recommended Talking Points")
            talking_points = []
            
            # Check enrolled & approved accurately
            enrolled_units = current_values.get("Curricular units 1st sem (enrolled)", 0)
            approved_units = current_values.get("Curricular units 1st sem (approved)", 0)
            grade_sem1 = current_values.get("Curricular units 1st sem (grade)", 0.0)

            if enrolled_units == 0:
                talking_points.append("Registration Status: Student has 0 enrolled units in Semester 1. Inquire about administrative matriculation holds, program transfer, or formal leave of absence.")
            elif approved_units < enrolled_units:
                failed_count = enrolled_units - approved_units
                talking_points.append(f"Academic Recovery: Student did not pass {failed_count} of {enrolled_units} enrolled units. Connect with course coordinators for remedial tutoring and faculty office hours.")
            else:
                talking_points.append(f"Academic Momentum: Passed all {enrolled_units} enrolled units with an average grade of {grade_sem1:.1f}/20. Discuss honors coursework or degree pacing.")

            if current_values.get("Tuition fees up to date", 1) == 0:
                talking_points.append("Financial Status: Overdue tuition payments detected. Discuss institutional emergency hardship funds, installment plans, or bursar deferrals.")

            if current_values.get("Debtor", 0) == 1:
                talking_points.append("Institutional Debt: Active unpaid student debts on record. Prioritize financial aid counseling to prevent registration cancellation.")

            if current_values.get("Age at enrollment", 20) > 25:
                talking_points.append("Mature Student Support: Discuss work-life-study scheduling flexibility, evening session options, and adult learner peer networks.")

            for tp in talking_points:
                st.markdown(f"• {tp}")

            st.markdown("#### Recommended Review Window")
            if tier_name == "High":
                st.error("Priority: Schedule in-person or virtual advising conference within 7 calendar days.")
            elif tier_name == "Medium":
                st.warning("Moderate: Check academic progress and tutoring engagement within 30 calendar days.")
            else:
                st.success("Standard: Follow standard semester advising milestones.")

    with col_shap:
        with st.container(border=True):
            st.markdown("### TreeSHAP Feature Attribution")
            st.caption("Impact of individual factors pushing this student's risk toward or away from dropout (Class 0: Dropout)")

            top_k = contrib.head(8)
            rest_sum = contrib.iloc[8:].sum()

            plot_items = []
            for f in top_k.index:
                val = current_values.get(f, 0)
                label_str = friendly_feature_label(f, val)
                plot_items.append({
                    "Feature": label_str,
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

            # Altair bar chart with expanded label limit so text is never cut off
            chart = alt.Chart(df_shap).mark_bar(cornerRadiusEnd=4).encode(
                x=alt.X("SHAP Impact:Q", title="Log-Odds Contribution to Dropout Score"),
                y=alt.Y(
                    "Feature:N",
                    sort=None,
                    title=None,
                    axis=alt.Axis(labelLimit=320, labelFontSize=12, labelColor="#E2E8F0")
                ),
                color=alt.Color(
                    "Direction:N",
                    scale=alt.Scale(domain=["Increases Risk", "Reduces Risk"], range=["#EF4444", "#3B82F6"]),
                    legend=alt.Legend(orient="bottom", title=None)
                ),
                tooltip=["Feature", "SHAP Impact", "Direction"]
            ).properties(height=340)

            st.altair_chart(chart, use_container_width=True)

            up_changes, down_changes = top_changes(contrib, current_values)
            st.markdown(f":red-badge[Primary Risk Drivers:] {', '.join(up_changes) if up_changes else 'None'}")
            st.markdown(f":blue-badge[Primary Protective Factors:] {', '.join(down_changes) if down_changes else 'None'}")
            st.caption("TreeSHAP quantifies model feature reliance, not real-world causality.")

# ==============================================================================
# TAB 2: STUDENT PROFILE STUDIO
# ==============================================================================
with tab_studio:
    st.markdown("### Student Profile Studio")
    st.caption("Adjust student academic, financial, and demographic parameters. The model re-scores immediately.")

    col_acad, col_socio, col_demo = st.columns(3)

    with col_acad:
        with st.container(border=True):
            if selected_tag == "early":
                st.markdown("#### Academic Record (Semester 1 Early-Warning)")
            else:
                st.markdown("#### Academic Record (Semesters 1 & 2 Full Curriculum)")

            # Use unique persistent widget keys bound to student_profile
            cur_enrolled_1 = int(st.session_state["student_profile"].get("Curricular units 1st sem (enrolled)", 6))
            new_enrolled_1 = st.slider(
                "Sem 1 Enrolled Units", 0, 26,
                value=cur_enrolled_1,
                key="inp_Curricular units 1st sem (enrolled)"
            )
            st.session_state["student_profile"]["Curricular units 1st sem (enrolled)"] = new_enrolled_1

            cur_approved_1 = min(int(st.session_state["student_profile"].get("Curricular units 1st sem (approved)", 5)), new_enrolled_1)
            new_approved_1 = st.slider(
                "Sem 1 Approved Units", 0, max(new_enrolled_1, 1) if new_enrolled_1 > 0 else 0,
                value=cur_approved_1,
                key="inp_Curricular units 1st sem (approved)",
                help="Approved units cannot exceed enrolled units."
            )
            st.session_state["student_profile"]["Curricular units 1st sem (approved)"] = new_approved_1

            cur_eval_1 = max(int(st.session_state["student_profile"].get("Curricular units 1st sem (evaluations)", 8)), new_approved_1)
            new_eval_1 = st.number_input(
                "Sem 1 Evaluation Moments", min_value=new_approved_1, max_value=45,
                value=cur_eval_1,
                key="inp_Curricular units 1st sem (evaluations)",
                help="Evaluations cannot be less than approved units."
            )
            st.session_state["student_profile"]["Curricular units 1st sem (evaluations)"] = new_eval_1

            cur_grade_1 = float(st.session_state["student_profile"].get("Curricular units 1st sem (grade)", 12.5))
            new_grade_1 = st.slider(
                "Sem 1 Grade Average (0–20 Scale)", 0.0, 20.0,
                value=cur_grade_1, step=0.1,
                key="inp_Curricular units 1st sem (grade)"
            )
            st.session_state["student_profile"]["Curricular units 1st sem (grade)"] = new_grade_1

            st.session_state["student_profile"]["Curricular units 1st sem (credited)"] = st.number_input(
                "Sem 1 Credited Units", 0, 20,
                value=int(st.session_state["student_profile"].get("Curricular units 1st sem (credited)", 0)),
                key="inp_Curricular units 1st sem (credited)"
            )
            st.session_state["student_profile"]["Curricular units 1st sem (without evaluations)"] = st.number_input(
                "Sem 1 Without Evaluations", 0, 12,
                value=int(st.session_state["student_profile"].get("Curricular units 1st sem (without evaluations)", 0)),
                key="inp_Curricular units 1st sem (without evaluations)"
            )

            if "Curricular units 2nd sem (approved)" in features:
                st.markdown("---")
                st.markdown("**Semester 2 Record (Full Model)**")

                cur_enrolled_2 = int(st.session_state["student_profile"].get("Curricular units 2nd sem (enrolled)", 6))
                new_enrolled_2 = st.slider(
                    "Sem 2 Enrolled Units", 0, 26,
                    value=cur_enrolled_2,
                    key="inp_Curricular units 2nd sem (enrolled)"
                )
                st.session_state["student_profile"]["Curricular units 2nd sem (enrolled)"] = new_enrolled_2

                cur_approved_2 = min(int(st.session_state["student_profile"].get("Curricular units 2nd sem (approved)", 5)), new_enrolled_2)
                new_approved_2 = st.slider(
                    "Sem 2 Approved Units", 0, max(new_enrolled_2, 1) if new_enrolled_2 > 0 else 0,
                    value=cur_approved_2,
                    key="inp_Curricular units 2nd sem (approved)"
                )
                st.session_state["student_profile"]["Curricular units 2nd sem (approved)"] = new_approved_2

                cur_eval_2 = max(int(st.session_state["student_profile"].get("Curricular units 2nd sem (evaluations)", 8)), new_approved_2)
                new_eval_2 = st.number_input(
                    "Sem 2 Evaluation Moments", min_value=new_approved_2, max_value=45,
                    value=cur_eval_2,
                    key="inp_Curricular units 2nd sem (evaluations)"
                )
                st.session_state["student_profile"]["Curricular units 2nd sem (evaluations)"] = new_eval_2

                new_grade_2 = st.slider(
                    "Sem 2 Grade Average (0–20 Scale)", 0.0, 20.0,
                    value=float(st.session_state["student_profile"].get("Curricular units 2nd sem (grade)", 12.5)), step=0.1,
                    key="inp_Curricular units 2nd sem (grade)"
                )
                st.session_state["student_profile"]["Curricular units 2nd sem (grade)"] = new_grade_2
            else:
                st.info("🔒 Semester 2 features excluded in Early-Warning mode to eliminate lookahead leakage.")

    with col_socio:
        with st.container(border=True):
            st.markdown("#### Financial & Enrollment Status")

            tuition_current = int(st.session_state["student_profile"].get("Tuition fees up to date", 1))
            tuition_choice = st.segmented_control(
                "Tuition Fees Current?",
                options=["Yes (Up to Date)", "No (Overdue)"],
                default="Yes (Up to Date)" if tuition_current == 1 else "No (Overdue)",
                key="seg_tuition"
            )
            st.session_state["student_profile"]["Tuition fees up to date"] = 1 if "Yes" in (tuition_choice or "Yes") else 0

            debtor_current = int(st.session_state["student_profile"].get("Debtor", 0))
            debtor_choice = st.segmented_control(
                "Institutional Debts?",
                options=["No Debt", "Has Unpaid Debt"],
                default="No Debt" if debtor_current == 0 else "Has Unpaid Debt",
                key="seg_debtor"
            )
            st.session_state["student_profile"]["Debtor"] = 1 if "Has" in (debtor_choice or "No") else 0

            scholarship_current = int(st.session_state["student_profile"].get("Scholarship holder", 0))
            scholarship_choice = st.segmented_control(
                "Scholarship Grantee?",
                options=["No", "Yes (Grantee)"],
                default="Yes (Grantee)" if scholarship_current == 1 else "No",
                key="seg_scholarship"
            )
            st.session_state["student_profile"]["Scholarship holder"] = 1 if "Yes" in (scholarship_choice or "No") else 0

            attend_current = int(st.session_state["student_profile"].get("Daytime/evening attendance", 1))
            attend_choice = st.segmented_control(
                "Attendance Schedule",
                options=["Daytime", "Evening"],
                default="Daytime" if attend_current == 1 else "Evening",
                key="seg_attend"
            )
            st.session_state["student_profile"]["Daytime/evening attendance"] = 1 if attend_choice == "Daytime" else 0

            displaced_current = int(st.session_state["student_profile"].get("Displaced", 1))
            displaced_choice = st.segmented_control(
                "Displaced Student?",
                options=["Local", "Living Away From Home"],
                default="Living Away From Home" if displaced_current == 1 else "Local",
                key="seg_displaced"
            )
            st.session_state["student_profile"]["Displaced"] = 1 if "Away" in (displaced_choice or "Local") else 0

            st.markdown("---")
            st.markdown("**Macroeconomic Indicators**")
            st.session_state["student_profile"]["Unemployment rate"] = st.number_input(
                "Unemployment Rate (%)", 0.0, 30.0,
                value=float(st.session_state["student_profile"].get("Unemployment rate", 10.8)), step=0.1,
                key="inp_Unemployment rate"
            )
            st.session_state["student_profile"]["Inflation rate"] = st.number_input(
                "Inflation Rate (%)", -5.0, 10.0,
                value=float(st.session_state["student_profile"].get("Inflation rate", 1.4)), step=0.1,
                key="inp_Inflation rate"
            )
            st.session_state["student_profile"]["GDP"] = st.number_input(
                "GDP Change (%)", -10.0, 10.0,
                value=float(st.session_state["student_profile"].get("GDP", 1.74)), step=0.1,
                key="inp_GDP"
            )

    with col_demo:
        with st.container(border=True):
            st.markdown("#### Demographics & Program")

            st.session_state["student_profile"]["Age at enrollment"] = st.slider(
                "Age at Enrollment", 17, 70,
                value=int(st.session_state["student_profile"].get("Age at enrollment", 20)),
                key="inp_Age at enrollment"
            )

            gender_current = int(st.session_state["student_profile"].get("Gender", 0))
            gender_choice = st.segmented_control(
                "Gender",
                options=["Female", "Male"],
                default="Female" if gender_current == 0 else "Male",
                key="seg_gender"
            )
            st.session_state["student_profile"]["Gender"] = 1 if gender_choice == "Male" else 0

            course_options = specs["Course"]["options"]
            cur_course = int(st.session_state["student_profile"].get("Course", course_options[0]))
            st.session_state["student_profile"]["Course"] = st.selectbox(
                "Degree Programme",
                options=course_options,
                index=course_options.index(cur_course) if cur_course in course_options else 0,
                format_func=lambda c: map_label(COURSE_MAP, c, "Course"),
                key="inp_Course"
            )

            st.session_state["student_profile"]["Admission grade"] = st.slider(
                "Admission Grade (0–200)", 0.0, 200.0,
                value=float(st.session_state["student_profile"].get("Admission grade", 125.0)), step=0.5,
                key="inp_Admission grade"
            )
            st.session_state["student_profile"]["Previous qualification (grade)"] = st.slider(
                "Previous Qualification Grade (0–200)", 0.0, 200.0,
                value=float(st.session_state["student_profile"].get("Previous qualification (grade)", 130.0)), step=0.5,
                key="inp_Previous qualification (grade)"
            )

            with st.expander("Family & Background Details"):
                app_options = specs["Application mode"]["options"]
                cur_app = int(st.session_state["student_profile"].get("Application mode", app_options[0]))
                st.session_state["student_profile"]["Application mode"] = st.selectbox(
                    "Application Mode",
                    options=app_options,
                    index=app_options.index(cur_app) if cur_app in app_options else 0,
                    format_func=lambda a: map_label(APPLICATION_MODE_MAP, a, "Mode"),
                    key="inp_Application mode"
                )

                mq_options = specs["Mother's qualification"]["options"]
                cur_mq = int(st.session_state["student_profile"].get("Mother's qualification", mq_options[0]))
                st.session_state["student_profile"]["Mother's qualification"] = st.selectbox(
                    "Mother's Qualification",
                    options=mq_options,
                    index=mq_options.index(cur_mq) if cur_mq in mq_options else 0,
                    format_func=lambda q: map_label(PARENT_QUAL_MAP, q, "Qual"),
                    key="inp_Mothers qualification"
                )

                fq_options = specs["Father's qualification"]["options"]
                cur_fq = int(st.session_state["student_profile"].get("Father's qualification", fq_options[0]))
                st.session_state["student_profile"]["Father's qualification"] = st.selectbox(
                    "Father's Qualification",
                    options=fq_options,
                    index=fq_options.index(cur_fq) if cur_fq in fq_options else 0,
                    format_func=lambda q: map_label(PARENT_QUAL_MAP, q, "Qual"),
                    key="inp_Fathers qualification"
                )

# ==============================================================================
# TAB 3: WHAT-IF INTERVENTION LAB
# ==============================================================================
with tab_simulator:
    st.markdown("### What-If Intervention Lab")
    st.caption("Simulate hypothetical mentoring interventions. The system enforces logical academic constraints.")

    sim_values = dict(current_values)
    base_enrolled = sim_values.get("Curricular units 1st sem (enrolled)", 0)
    base_approved = sim_values.get("Curricular units 1st sem (approved)", 0)

    col_sim_controls, col_sim_results = st.columns([1, 1])

    with col_sim_controls:
        with st.container(border=True):
            st.markdown("#### Configure Interventions")

            if base_enrolled == 0:
                st.warning("⚠️ Baseline enrolled units is 0. Student must be matriculated in units to simulate tutoring.")
                tutoring_boost = 0
            else:
                max_possible_boost = max(0, base_enrolled - base_approved)
                if max_possible_boost == 0:
                    st.info(f"Student has already passed all {base_enrolled} enrolled units.")
                    tutoring_boost = 0
                else:
                    tutoring_boost = st.slider(
                        f"Tutoring: Convert Failed Units to Passed (Max: {max_possible_boost})",
                        0, max_possible_boost, value=min(1, max_possible_boost),
                        help="Converts unapproved enrolled units into approved units."
                    )
            
            sim_values["Curricular units 1st sem (approved)"] = base_approved + tutoring_boost
            # Enforce evaluations >= approved
            sim_values["Curricular units 1st sem (evaluations)"] = max(
                sim_values.get("Curricular units 1st sem (evaluations)", 0),
                sim_values["Curricular units 1st sem (approved)"]
            )
            # If approved units increased from 0, assign at least passing grade (10.0)
            if sim_values["Curricular units 1st sem (approved)"] > 0 and sim_values.get("Curricular units 1st sem (grade)", 0.0) < 10.0:
                sim_values["Curricular units 1st sem (grade)"] = 11.5

            grant_relief = st.toggle(
                "Emergency Hardship Grant: Clear Unpaid Tuition & Debts",
                value=(sim_values.get("Tuition fees up to date", 1) == 0 or sim_values.get("Debtor", 0) == 1),
                help="Simulates settling outstanding tuition and clearing institutional debts."
            )
            if grant_relief:
                sim_values["Tuition fees up to date"] = 1
                sim_values["Debtor"] = 0

            grade_boost = st.slider(
                "Study Workshop: GPA Improvement (Points on 0–20 Scale)",
                0.0, 4.0, value=1.0, step=0.5,
                help="Simulates grade improvement through study skills mentorship."
            )
            sim_values["Curricular units 1st sem (grade)"] = min(
                20.0, sim_values.get("Curricular units 1st sem (grade)", 0.0) + grade_boost
            )

            st.caption(
                f"Validation guarantee: Approved ({sim_values['Curricular units 1st sem (approved)']}) "
                f"≤ Evaluations ({sim_values['Curricular units 1st sem (evaluations)']}) "
                f"≤ Enrolled ({sim_values['Curricular units 1st sem (enrolled)']})"
            )

    # Score simulated student
    sim_result = score_student(art, sim_values)
    sim_risk = sim_result["risk"]
    sim_tier = sim_result["tier"]
    risk_diff = sim_risk - risk

    with col_sim_results:
        with st.container(border=True):
            st.markdown("#### Predicted Intervention Impact")

            col_before, col_after = st.columns(2)
            with col_before:
                st.metric("Baseline Risk", f"{risk:.1%}")
                st.markdown(f"Status: **{tier_name} Risk**")
            with col_after:
                st.metric("Post-Intervention Risk", f"{sim_risk:.1%}")
                st.markdown(f"New Status: **{sim_tier} Risk**")

            st.markdown("---")
            if risk_diff < -0.05:
                st.success(
                    f"Intervention reduces predicted dropout risk by **{abs(risk_diff):.1%}** "
                    f"(from {risk:.1%} down to {sim_risk:.1%})."
                )
            elif risk_diff >= 0:
                st.info("No significant risk reduction with current intervention parameters.")
            else:
                st.warning(f"Modest risk reduction of {abs(risk_diff):.1%}.")

# ==============================================================================
# TAB 4: MODEL GOVERNANCE & FAIRNESS AUDIT
# ==============================================================================
with tab_audit:
    st.markdown("### Algorithmic Governance, Fairness & Holdout Test Audit")
    st.caption("Rigorous single-pass test set evaluation on 885 completely unobserved students, with subgroup fairness diagnostics.")

    col_gov1, col_gov2 = st.columns(2)

    with col_gov1:
        with st.container(border=True):
            st.markdown("#### Holdout Test Benchmarks (885 Students)")
            st.markdown(
                """
                | Metric | Early-Warning (Sem 1) | Full Curriculum |
                | :--- | :---: | :---: |
                | **Holdout Cohort (N)** | **885 students** | **885 students** |
                | **Dropout ROC-AUC** | **0.893** | **0.915** |
                | **Dropout PR-AUC** | **0.844** | **0.872** |
                | **Dropout Recall** | **89.4%** (254/284) | **86.6%** (246/284) |
                | **Dropout Precision** | **59.3%** | **64.2%** |
                | **Cost Reduction vs Flag Nobody** | **77.2%** | **77.0%** |
                | **Cost Reduction vs Flag All** | **~46.0%** | **~44.0%** |
                """
            )
            st.caption("Evaluated strictly once at Phase 5 conclusion. Zero post-hoc tuning on test data.")

    with col_gov2:
        with st.container(border=True):
            st.markdown("#### Subgroup Fairness Audit (Early Model)")
            st.markdown(
                """
                - **Scholarship Disparity:** Scholarship holders have lower base dropout rates (9.3% vs 39.0%), resulting in lower recall (**63.2%** vs **91.3%**). Mentors should not rely solely on automated alerts for scholarship recipients.
                - **Gender Disparity:** Male students experience double the false-alarm rate (42.4% vs 23.7%), with 66.3% of males flagged vs 38.4% of females.
                - **Age Disparity:** Students aged $\le 20$ have an 84.1% recall, while mature students ($>25$) have a 94.1% recall.
                - **Sample Size Warning:** International ($N=24$) and Special Needs ($N=10$) cohorts are too small for statistically valid conclusions.
                """
            )

    with st.container(border=True):
        st.markdown("#### Ethical Decision-Support Charter")
        st.markdown(
            """
            1. **Supportive, Not Punitive:** This tool exists exclusively to allocate support, tutoring, and counseling—never to disqualify, dismiss, or deny enrollment.
            2. **Human in the Loop:** Automated scores never constitute decisions; they serve as diagnostic signals for experienced human faculty advisors.
            3. **Unobserved External Factors:** Students who leave with good grades and paid tuition depart due to personal, family, or health reasons not present in institutional databases.
            4. **Attribution:** Dataset created by *Instituto Politécnico de Portalegre* (Realinho et al., 2021) under CC BY 4.0.
            """
        )
