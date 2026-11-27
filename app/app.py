"""Retention Intelligence — University Student Success & Early-Warning Platform.

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
    initial_sidebar_state="expanded",
)

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
    195: "Food Preparation Assistants",
}

PERSONAS = {
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

# ------------------------------------------------------------------ SIDEBAR
with st.sidebar:
    st.markdown("### :material/school: Retention Intelligence")
    st.caption("Student Success Analytics")

    nav_page = st.radio(
        "Navigation",
        options=[
            "Risk Assessment",
            "Student Profile",
            "What-If Lab",
            "Governance & Fairness",
        ],
        label_visibility="collapsed",
    )

    st.divider()

    st.markdown("**Model Mode**")
    tag_choice = st.segmented_control(
        "Model mode",
        options=["Early Warning", "Full Curriculum"],
        default="Early Warning",
        label_visibility="collapsed",
        width="stretch",
    )
    selected_tag = "early" if tag_choice != "Full Curriculum" else "full"
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

    st.session_state.setdefault("_outcome", None)
    st.session_state.setdefault("_active_persona", "Custom Input")

    st.markdown("**Student Profiles**")
    preset_names = list(PERSONAS.keys()) + ["Custom Input"]
    current_idx = (
        preset_names.index(st.session_state["_active_persona"])
        if st.session_state["_active_persona"] in preset_names
        else len(preset_names) - 1
    )
    selected_preset = st.radio(
        "Student profiles",
        options=preset_names,
        index=current_idx,
        label_visibility="collapsed",
    )

    if selected_preset in PERSONAS:
        st.caption(PERSONAS[selected_preset]["desc"])
    else:
        st.caption("Active profile with custom or sampled student parameters.")

    if selected_preset != st.session_state["_active_persona"] and selected_preset in PERSONAS:
        st.session_state["_active_persona"] = selected_preset
        p_data = PERSONAS[selected_preset]
        for f, val in p_data["values"].items():
            if f in specs:
                tv = typed(specs[f], val)
                st.session_state["student_profile"][f] = tv
                st.session_state[f"inp_{f}"] = tv
        st.session_state["_outcome"] = p_data["target"]
        st.rerun()

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Sample Random", icon=":material/shuffle:", width="stretch"):
            vals, outcome = random_student(df, features)
            for f in features:
                tv = typed(specs[f], vals[f])
                st.session_state["student_profile"][f] = tv
                st.session_state[f"inp_{f}"] = tv
            st.session_state["_outcome"] = outcome
            st.session_state["_active_persona"] = "Custom Input"
            st.rerun()
    with c2:
        if st.button("Reset Median", icon=":material/restart_alt:", width="stretch"):
            for f in features:
                tv = typed(specs[f], specs[f]["default"])
                st.session_state["student_profile"][f] = tv
                st.session_state[f"inp_{f}"] = tv
            st.session_state["_outcome"] = None
            st.session_state["_active_persona"] = "Custom Input"
            st.rerun()

    if st.session_state.get("_outcome"):
        st.caption(f"Recorded target: **{st.session_state['_outcome']}**")

    st.divider()
    st.markdown("**Model Information**")
    res_path = ROOT / "reports" / f"test_results_xgboost_{selected_tag}.json"
    if res_path.exists():
        res_data = json.load(open(res_path))
        st.markdown(
            f"""
| Metric | Value |
| :--- | ---: |
| Holdout cohort | {res_data['n_test']} |
| ROC-AUC | {res_data['dropout_roc_auc']:.3f} |
| Recall | {res_data['at_chosen_threshold']['recall']:.1%} |
| Threshold | {art.threshold:.0%} |
"""
        )

# ------------------------------------------------------------------ SCORE CURRENT STUDENT
current_values = {f: st.session_state["student_profile"][f] for f in features}
result = score_student(art, current_values)
risk = float(result["risk"])
tier_name = str(result["tier"])
probs = result.get(
    "probs",
    {"Dropout": risk, "Enrolled": 0.18, "Graduate": max(0.0, 1.0 - risk - 0.18)},
)
t = float(art.threshold)

# Normalize multiclass probabilities for clean bar visualization
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

# ------------------------------------------------------------------ TOP HEADER
hdr_left, hdr_right = st.columns([3, 1], vertical_alignment="center")
with hdr_left:
    st.caption("Retention Intelligence")
    st.markdown("#### Student Retention & Early-Warning Intelligence")
    mode_badge = ":blue-badge[Early Warning]" if selected_tag == "early" else ":blue-badge[Full Curriculum]"
    st.markdown(f"{mode_badge} :gray-badge[Supervised Learning] :gray-badge[Model v1.0]")
with hdr_right:
    st.markdown(
        "<div style='text-align:right; font-size:12px; color:#94A3B8;'>"
        "<strong style='color:#10B981;'>Model Status: Active</strong><br/>"
        "Holdout cohort: 885 students"
        "</div>",
        unsafe_allow_html=True,
    )

st.divider()

# ==============================================================================
# PAGE 1: RISK ASSESSMENT
# ==============================================================================
if nav_page == "Risk Assessment":
    st.title("Risk Assessment")
    st.caption("Identify early signs of student attrition and understand the factors driving the prediction.")

    course_name = map_label(COURSE_MAP, current_values.get("Course", 9500), "Course")
    age_val = int(current_values.get("Age at enrollment", 20))
    sem_label = "Semester 1" if selected_tag == "early" else "Semesters 1 & 2"
    st.markdown(
        f"**Student Profile:** `{st.session_state['_active_persona']}` &nbsp;·&nbsp; "
        f"{course_name} &nbsp;·&nbsp; Age {age_val} &nbsp;·&nbsp; {sem_label}"
    )

    st.space("small")

    # Primary Risk KPI + Risk Spectrum + Multiclass Probability
    col_kpi, col_spec = st.columns([5, 7], gap="large")

    with col_kpi:
        with st.container(border=True):
            st.caption("ATTRITION RISK")
            tier_color = "#EF4444" if tier_name == "High" else ("#F59E0B" if tier_name == "Medium" else "#10B981")
            badge_md = (
                ":red-badge[HIGH RISK]"
                if tier_name == "High"
                else (":orange-badge[MEDIUM RISK]" if tier_name == "Medium" else ":green-badge[LOW RISK]")
            )
            st.markdown(
                f"<div style='font-size:48px; font-weight:700; line-height:1.1; color:{tier_color}; margin:4px 0 8px 0;'>"
                f"{risk:.1%}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(badge_md)
            if risk >= t:
                st.write("Student is currently above the intervention threshold.")
            else:
                st.write("Student is currently below the intervention threshold.")

            gap_pp = (risk - t) * 100.0
            m1, m2 = st.columns(2)
            with m1:
                st.caption("Operational threshold")
                st.markdown(f"**{t:.0%}**")
            with m2:
                st.caption("Risk gap")
                st.markdown(f"**{gap_pp:+.1f} percentage points**")

    with col_spec:
        # Segmented Risk Scale (SAFE 0-16% | WATCH 16-50% | CRITICAL 50-100%)
        st.markdown("**Risk Spectrum**")
        pos_pct = min(max(risk * 100.0, 0.0), 100.0)
        t_pct = int(round(t * 100))
        high_pct = int(round(HIGH_TIER * 100))

        spectrum_html = f"""
        <div style="margin: 8px 0 18px 0;">
          <div style="display:flex; width:100%; font-size:11px; color:#94A3B8; margin-bottom:6px; font-weight:600;">
            <div style="width:{t_pct}%;">SAFE<br/><span style="font-weight:400;">0–{t_pct}%</span></div>
            <div style="width:{high_pct - t_pct}%;">WATCH<br/><span style="font-weight:400;">{t_pct}–{high_pct}%</span></div>
            <div style="width:{100 - high_pct}%;">CRITICAL<br/><span style="font-weight:400;">{high_pct}–100%</span></div>
          </div>
          <div style="position:relative; display:flex; width:100%; height:10px; border-radius:5px; overflow:visible;">
            <div style="width:{t_pct}%; background:#10B981; border-radius:5px 0 0 5px;"></div>
            <div style="width:{high_pct - t_pct}%; background:#F59E0B;"></div>
            <div style="width:{100 - high_pct}%; background:#EF4444; border-radius:0 5px 5px 0;"></div>
            <div style="position:absolute; left:{pos_pct:.1f}%; top:-5px; transform:translateX(-50%); width:4px; height:20px; background:#F8FAFC; border:1px solid #0F172A; border-radius:2px;"></div>
          </div>
          <div style="margin-top:10px; font-size:12px; color:#94A3B8;">
            Current position: <strong style="color:#F8FAFC;">{risk:.1%}</strong> &nbsp;·&nbsp; Status: <strong style="color:#F8FAFC;">{tier_name} Risk</strong>
          </div>
        </div>
        """
        st.html(spectrum_html)

        st.markdown("**Multiclass Probability**")
        outcomes = [
            ("Graduate", p_grad_norm, "#10B981"),
            ("Persist", p_enr_norm, "#3B82F6"),
            ("Dropout", p_drop_norm, "#EF4444"),
        ]
        top_outcome = max(outcomes, key=lambda x: x[1])[0]
        bars_html = "<div style='display:flex; flex-direction:column; gap:10px; margin-top:6px;'>"
        for name, val, col in outcomes:
            is_top = name == top_outcome
            weight = "700" if is_top else "500"
            opacity = "1.0" if is_top else "0.7"
            w_pct = max(val * 100.0, 1.5)
            bars_html += f"""
            <div style="opacity:{opacity};">
              <div style="display:flex; justify-content:space-between; font-size:13px; font-weight:{weight}; margin-bottom:4px;">
                <span>{name}</span>
                <span style="font-family:monospace;">{val:.1%}</span>
              </div>
              <div style="width:100%; height:8px; background:rgba(148,163,184,0.18); border-radius:4px; overflow:hidden;">
                <div style="width:{w_pct:.1f}%; height:100%; background:{col}; border-radius:4px;"></div>
              </div>
            </div>
            """
        bars_html += "</div>"
        st.html(bars_html)

    st.divider()

    # Advisor Action Plan + SHAP Explanation
    col_adv, col_shap = st.columns([5, 7], gap="large")

    with col_adv:
        st.subheader("Recommended Advisor Action")
        if tier_name == "High":
            st.markdown(":red-badge[Priority 1-on-1 outreach required]")
        elif tier_name == "Medium":
            st.markdown(":orange-badge[Targeted support recommended]")
        else:
            st.markdown(":green-badge[No immediate intervention required]")

        st.write(TIER_ACTIONS[tier_name])

        enrolled_u = int(current_values.get("Curricular units 1st sem (enrolled)", 0))
        approved_u = int(current_values.get("Curricular units 1st sem (approved)", 0))
        grade_u = float(current_values.get("Curricular units 1st sem (grade)", 0.0))

        st.markdown("**Recommended talking points**")
        if enrolled_u == 0:
            st.markdown("- **Registration & enrollment:** 0 units enrolled in Semester 1. Verify administrative holds or leave status.")
        elif approved_u < enrolled_u:
            st.markdown(f"- **Academic recovery:** {enrolled_u - approved_u} of {enrolled_u} enrolled units not passed. Refer to course tutoring and office hours.")
        else:
            st.markdown(f"- **Academic progress:** Passed all {enrolled_u} enrolled units (average {grade_u:.1f}/20). Maintain current study plan.")

        if int(current_values.get("Tuition fees up to date", 1)) == 0:
            st.markdown("- **Financial support:** Overdue tuition detected. Review emergency hardship aid or installment options.")
        if int(current_values.get("Debtor", 0)) == 1:
            st.markdown("- **Account balance:** Institutional debt recorded. Coordinate with student finance office.")
        if int(current_values.get("Daytime/evening attendance", 1)) == 0 or age_val > 25:
            st.markdown("- **Attendance & schedule:** Review evening/work-study balance and flexible advising hours.")

    with col_shap:
        st.subheader("Why is this prediction happening?")
        st.caption("Model explanation for this student's dropout risk.")

        contrib = result["contributions"]
        top_k = contrib.head(8)
        rest_sum = float(contrib.iloc[8:].sum())

        plot_items = []
        for f in top_k.index:
            val = current_values.get(f, 0)
            plot_items.append({
                "Feature": friendly_feature_label(f, val),
                "Impact": float(top_k[f]),
                "Direction": "Increasing risk" if top_k[f] > 0 else "Reducing risk",
            })
        if len(contrib) > 8:
            plot_items.append({
                "Feature": f"{len(contrib) - 8} other features",
                "Impact": rest_sum,
                "Direction": "Increasing risk" if rest_sum > 0 else "Reducing risk",
            })

        df_shap = pd.DataFrame(plot_items)
        chart = (
            alt.Chart(df_shap)
            .mark_bar(cornerRadiusEnd=3)
            .encode(
                x=alt.X("Impact:Q", title="SHAP contribution (log-odds toward Dropout)"),
                y=alt.Y(
                    "Feature:N",
                    sort=None,
                    title=None,
                    axis=alt.Axis(labelLimit=320, labelFontSize=12),
                ),
                color=alt.Color(
                    "Direction:N",
                    scale=alt.Scale(
                        domain=["Increasing risk", "Reducing risk"],
                        range=["#EF4444", "#2563EB"],
                    ),
                    legend=alt.Legend(orient="top", title=None),
                ),
                tooltip=[
                    alt.Tooltip("Feature:N", title="Feature"),
                    alt.Tooltip("Impact:Q", title="SHAP impact", format="+.3f"),
                    alt.Tooltip("Direction:N", title="Effect"),
                ],
            )
            .properties(height=310)
        )
        st.altair_chart(chart, width="stretch")

        up_changes, down_changes = top_changes(contrib, current_values)
        f_up, f_down = st.columns(2)
        with f_up:
            st.caption("Factors increasing risk")
            st.write(", ".join(up_changes) if up_changes else "None")
        with f_down:
            st.caption("Factors reducing risk")
            st.write(", ".join(down_changes) if down_changes else "None")

# ==============================================================================
# PAGE 2: STUDENT PROFILE STUDIO
# ==============================================================================
elif nav_page == "Student Profile":
    st.title("Student Profile")
    st.caption("Update academic, financial, demographic, and economic inputs. Predictions recalculate automatically.")

    def mark_custom():
        st.session_state["_active_persona"] = "Custom Input"
        st.session_state["_outcome"] = None

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.subheader("Academic Performance")
        enr1 = st.slider(
            "Semester 1 enrolled units", 0, 26,
            value=int(st.session_state["student_profile"].get("Curricular units 1st sem (enrolled)", 6)),
            key="inp_Curricular units 1st sem (enrolled)",
            on_change=mark_custom,
        )
        st.session_state["student_profile"]["Curricular units 1st sem (enrolled)"] = enr1

        cur_app1 = min(int(st.session_state["student_profile"].get("Curricular units 1st sem (approved)", 5)), enr1)
        app1 = st.slider(
            "Semester 1 approved units", 0, max(enr1, 1) if enr1 > 0 else 0,
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
            st.divider()
            st.markdown("**Semester 2 Academic Record**")
            enr2 = st.slider(
                "Semester 2 enrolled units", 0, 26,
                value=int(st.session_state["student_profile"].get("Curricular units 2nd sem (enrolled)", 6)),
                key="inp_Curricular units 2nd sem (enrolled)",
                on_change=mark_custom,
            )
            st.session_state["student_profile"]["Curricular units 2nd sem (enrolled)"] = enr2

            cur_app2 = min(int(st.session_state["student_profile"].get("Curricular units 2nd sem (approved)", 5)), enr2)
            app2 = st.slider(
                "Semester 2 approved units", 0, max(enr2, 1) if enr2 > 0 else 0,
                value=cur_app2,
                key="inp_Curricular units 2nd sem (approved)",
                on_change=mark_custom,
            )
            st.session_state["student_profile"]["Curricular units 2nd sem (approved)"] = app2

            gr2 = st.slider(
                "Semester 2 grade average (0–20)", 0.0, 20.0,
                value=float(st.session_state["student_profile"].get("Curricular units 2nd sem (grade)", 12.5)),
                step=0.1,
                key="inp_Curricular units 2nd sem (grade)",
                on_change=mark_custom,
            )
            st.session_state["student_profile"]["Curricular units 2nd sem (grade)"] = gr2

        st.divider()
        st.subheader("Financial & Enrollment")
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
        st.subheader("Student Background")
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
            "Degree",
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

        st.divider()
        st.subheader("Economic Context")
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
# PAGE 3: WHAT-IF LAB
# ==============================================================================
elif nav_page == "What-If Lab":
    st.title("What-If Intervention Lab")
    st.caption("Simulate targeted interventions and estimate their potential impact.")

    sim_values = dict(current_values)
    base_enrolled = int(sim_values.get("Curricular units 1st sem (enrolled)", 0))
    base_approved = int(sim_values.get("Curricular units 1st sem (approved)", 0))

    col_ctrl, col_impact = st.columns(2, gap="large")

    with col_ctrl:
        st.subheader("Intervention Controls")
        if base_enrolled == 0:
            st.info("Baseline enrolled units is 0. Enroll the student in curricular units on Student Profile to simulate tutoring.")
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
            "Hardship grant: bring tuition up to date and clear debt",
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
            st.subheader("Prediction Impact")
            arrow_html = f"""
            <div style="display:flex; align-items:center; gap:20px; margin:12px 0;">
              <div>
                <div style="font-size:12px; color:#94A3B8; text-transform:uppercase;">Before</div>
                <div style="font-size:32px; font-weight:700; font-family:monospace;">{risk:.1%}</div>
                <div style="font-size:12px; color:#94A3B8;">{tier_name} Risk</div>
              </div>
              <div style="font-size:28px; color:#64748B;">&rarr;</div>
              <div>
                <div style="font-size:12px; color:#94A3B8; text-transform:uppercase;">After</div>
                <div style="font-size:32px; font-weight:700; font-family:monospace; color:#2563EB;">{sim_risk:.1%}</div>
                <div style="font-size:12px; color:#94A3B8;">{sim_tier} Risk</div>
              </div>
            </div>
            """
            st.html(arrow_html)

            if reduction_pp > 0:
                st.markdown(f":green-badge[Risk reduction: {reduction_pp:.1f} percentage points]")
            elif reduction_pp < 0:
                st.markdown(f":red-badge[Risk change: {reduction_pp:+.1f} percentage points]")
            else:
                st.markdown(":gray-badge[No change in predicted risk]")

            st.caption("Simulations reflect model sensitivity to modified inputs, not guaranteed causal outcomes.")

# ==============================================================================
# PAGE 4: GOVERNANCE & FAIRNESS
# ==============================================================================
elif nav_page == "Governance & Fairness":
    st.title("Model Governance & Fairness")
    st.caption("Holdout performance, subgroup diagnostics, and responsible-use safeguards.")

    st.subheader("Holdout Performance")
    perf_df = pd.DataFrame([
        {"Metric": "Holdout cohort (N)", "Early Warning (Sem 1)": "885 students", "Full Curriculum (Sem 1 & 2)": "885 students"},
        {"Metric": "Dropout ROC-AUC", "Early Warning (Sem 1)": "0.893", "Full Curriculum (Sem 1 & 2)": "0.915"},
        {"Metric": "Dropout PR-AUC", "Early Warning (Sem 1)": "0.844", "Full Curriculum (Sem 1 & 2)": "0.872"},
        {"Metric": "Dropout Recall @ Cutoff", "Early Warning (Sem 1)": "89.4% (254/284)", "Full Curriculum (Sem 1 & 2)": "86.6% (246/284)"},
        {"Metric": "Dropout Precision @ Cutoff", "Early Warning (Sem 1)": "59.3%", "Full Curriculum (Sem 1 & 2)": "64.2%"},
        {"Metric": "Cost reduction vs flag nobody", "Early Warning (Sem 1)": "77.2%", "Full Curriculum (Sem 1 & 2)": "77.0%"},
        {"Metric": "Cost reduction vs flag all", "Early Warning (Sem 1)": "~46.0%", "Full Curriculum (Sem 1 & 2)": "~44.0%"},
    ])
    st.dataframe(perf_df, hide_index=True, width="stretch", alt="Holdout test performance comparison")

    st.divider()
    st.subheader("Fairness Audit")
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
        c_title, c_obs, c_int = st.columns([2, 3, 5])
        with c_title:
            st.markdown(f"**{title}**")
            st.caption(metric)
        with c_obs:
            st.markdown(f"`{observed}`")
        with c_int:
            st.write(interp)
        st.divider()

    st.subheader("Ethical Decision Support")
    principles = [
        ("1", "Supportive, Not Punitive", "The system allocates advising, tutoring, and financial support and is never used to deny enrollment or penalize students."),
        ("2", "Human in the Loop", "Model scores serve strictly as diagnostic signals; a human academic advisor always makes the final mentoring decision."),
        ("3", "Unobserved External Factors", "Students leaving with strong grades and paid tuition often depart for personal, health, or relocation reasons absent from the database."),
        ("4", "Attribution", "Built on the UCI 697 dataset created by Instituto Politécnico de Portalegre (Realinho et al., 2021) under CC BY 4.0."),
    ]
    p_cols = st.columns(2, gap="medium")
    for idx, (num, p_title, p_desc) in enumerate(principles):
        with p_cols[idx % 2]:
            st.markdown(f"**{num}. {p_title}**")
            st.caption(p_desc)
