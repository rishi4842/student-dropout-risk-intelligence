# Student Dropout Risk & Retention Intelligence System

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)
[![pytest](https://img.shields.io/badge/tests-5%20passed-brightgreen.svg)](tests/test_pipeline.py)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

An end-to-end early-warning machine learning system designed to predict higher education student dropout risk (`Dropout`, `Enrolled`, `Graduate`) using the UCI 697 dataset (*Instituto Politécnico de Portalegre*, 4,424 students). The system prioritizes **Dropout recall**, incorporates **cost-sensitive decision thresholding**, audits **subgroup fairness**, and provides **local TreeSHAP explainability** via an interactive Streamlit retention dashboard.

- **Course:** INT395 Supervised Learning (Project 29)
- **Author:** Rishikesh Boppa
- **Status:** **Completed** (Phases 1 through 8 finalized)
- **Primary Model:** Tuned XGBoost Classifier with Early-Warning Pipeline (Semester 1 only) and Full Curriculum Pipeline (Semesters 1 & 2).

---

## Table of Contents
1. [Executive Summary & Problem Definition](#1-executive-summary--problem-definition)
2. [Dataset & Data Governance](#2-dataset--data-governance)
3. [Pipeline Architecture & Anti-Leakage Strategy](#3-pipeline-architecture--anti-leakage-strategy)
4. [Cross-Validation Model Benchmarks](#4-cross-validation-model-benchmarks)
5. [Final Holdout Test Evaluation (885 Students)](#5-final-holdout-test-evaluation-885-students)
6. [Critical Empirical Findings & Limitations](#6-critical-empirical-findings--limitations)
7. [Explainability via TreeSHAP](#7-explainability-via-treeshap)
8. [Interactive Streamlit Web Dashboard](#8-interactive-streamlit-web-dashboard)
9. [How to Run & Reproduce Locally](#9-how-to-run--reproduce-locally)
10. [Streamlit Cloud Deployment Guide](#10-streamlit-cloud-deployment-guide)
11. [Comprehensive Viva Voce Defense Guide](#11-comprehensive-viva-voce-defense-guide)
12. [Repository Structure & License](#12-repository-structure--license)

---

## 1. Executive Summary & Problem Definition

### The Real-World Challenge
In higher education institutions, student dropout typically manifests late in the academic cycle—frequently after consecutive course failures, unpaid tuition fees, or unobserved personal disengagement. Academic advisors and mentors are often notified only after the student has formally departed, preventing timely mentorship, financial aid restructuring, or academic tutoring.

### Machine Learning Objective
Multiclass supervised classification predicting student outcomes at the conclusion of normal curriculum duration:
1. `Dropout` (Primary target of interest)
2. `Enrolled` (Persisting students within normal duration)
3. `Graduate` (Students who completed their degree)

Rather than treating the problem as generic multi-class accuracy, the system calculates $P(\text{Dropout})$ as a continuous risk metric and applies **cost-sensitive decision thresholding** calibrated to a **5:1 penalty ratio** (missing an at-risk student is 5 times more detrimental to institutional outcomes than initiating a preemptive advisory check-in).

```
   ┌────────────────────────────────────────────────────────┐
   │             Student Ingestion (36 Features)            │
   └───────────────────────────┬────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
     [Full Curriculum Model]       [Early-Warning Model]
     (Semesters 1 & 2 Data)        (Semester 1 Data Only)
               │                               │
               ▼                               ▼
    P(Dropout) Score [0.0 - 1.0]   P(Dropout) Score [0.0 - 1.0]
               │                               │
               ▼                               ▼
    Threshold Cutoff (t = 0.18)    Threshold Cutoff (t = 0.16)
               │                               │
               └───────────────┬───────────────┘
                               │
                               ▼
            ┌──────────────────────────────────────┐
            │        Three-Tier Triage System      │
            ├──────────────────────────────────────┤
            │  🔴 High Risk (P ≥ 0.50):            │
            │     Immediate 1-on-1 Advisor Session │
            │  🟡 Medium Risk (0.16 ≤ P < 0.50):   │
            │     Tutoring Referral & Auto-Nudge   │
            │  🟢 Low Risk (P < 0.16):             │
            │     Standard Academic Advising       │
            └──────────────────────────────────────┘
```

---

## 2. Dataset & Data Governance

- **Repository:** UCI Machine Learning Repository ([Dataset ID 697](https://archive.ics.uci.edu/dataset/697))
- **Origin:** *Instituto Politécnico de Portalegre*, Portugal (Valentim Realinho, Mónica Vieira Martins, Jorge Machado, Luís Baptista, 2021).
- **License:** Creative Commons Attribution 4.0 International ([CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)).
- **Volume:** 4,424 student records, 36 feature columns, 1 target column (`Target`).
- **Class Breakdown:**
  - `Graduate`: 2,209 students (49.9%)
  - `Dropout`: 1,421 students (32.1%)
  - `Enrolled`: 794 students (18.0%)
- **Data Quality:** 0 missing values across all 4,424 records; 0 duplicate rows. Semicolon-separated (`sep=';'`).
- **Key Feature Categories:**
  - *Demographic & Social:* Age at enrollment, Gender, Nationality, Marital status, Displaced, Educational special needs, Debtor, Tuition fees up to date, Scholarship holder.
  - *Socioeconomic Background:* Mother's/Father's qualification and occupation.
  - *Academic History:* Previous qualification grade, Admission grade, Application mode, Course.
  - *Curricular Units (Sem 1 & Sem 2):* Credited, enrolled, evaluations, approved, grade, without evaluations.
  - *Macroeconomic Context:* Unemployment rate, Inflation rate, GDP change.

---

## 3. Pipeline Architecture & Anti-Leakage Strategy

To prevent target leakage and data snooping, all data transformations are encapsulated inside an immutable scikit-learn `ColumnTransformer` and pipeline fitted strictly on training partitions:

```python
# Partition of 36 input features
NUMERIC_FEATURES = [
    "Previous qualification (grade)", "Admission grade", "Age at enrollment",
    "Curricular units 1st sem (credited)", "Curricular units 1st sem (enrolled)",
    "Curricular units 1st sem (evaluations)", "Curricular units 1st sem (approved)",
    "Curricular units 1st sem (grade)", "Curricular units 1st sem (without evaluations)",
    "Curricular units 2nd sem (credited)", "Curricular units 2nd sem (enrolled)",
    "Curricular units 2nd sem (evaluations)", "Curricular units 2nd sem (approved)",
    "Curricular units 2nd sem (grade)", "Curricular units 2nd sem (without evaluations)",
    "Unemployment rate", "Inflation rate", "GDP"
]  # StandardScaler()

NOMINAL_FEATURES = [
    "Marital status", "Application mode", "Application order", "Course",
    "Previous qualification", "Nacionality", "Mother's qualification",
    "Father's qualification", "Mother's occupation", "Father's occupation"
]  # OneHotEncoder(min_frequency=20, handle_unknown="infrequent_if_exist")

BINARY_FEATURES = [
    "Daytime/evening attendance", "Displaced", "Educational special needs",
    "Debtor", "Tuition fees up to date", "Gender", "Scholarship holder", "International"
]  # Passthrough
```

### Early-Warning Pipeline (`early=True`)
To evaluate whether risk can be reliably predicted before Semester 2 results are posted, the pipeline features an early-warning mode that drops all 6 second-semester curricular features (`enrolled`, `evaluations`, `approved`, `grade`, `credited`, `without evaluations`). This leaves 30 features collected at or before the completion of Semester 1.

### Train/Test Split
A single stratified 80/20 train/test split was established using `random_state=42`:
- **Training Set:** 3,539 students (used exclusively for cross-validation and hyperparameter tuning).
- **Holdout Test Set:** 885 students (evaluated once at the conclusion of Phase 5; completely untouched during tuning).

---

## 4. Cross-Validation Model Benchmarks

Seven candidate algorithms were benchmarked on the 3,539-student training partition using **5-Fold Stratified Cross-Validation**.

### Full Feature Set Comparison (36 Features)
| Model | Macro-F1 | Balanced Acc | Accuracy | Dropout Recall | Dropout Precision | ROC-AUC (OvR) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **XGBoost (untuned)** | **0.731 ± 0.017** | 0.732 ± 0.018 | 0.776 ± 0.015 | 0.759 ± 0.022 | 0.845 ± 0.022 | **0.898 ± 0.010** |
| **Stacking Classifier** | 0.728 ± 0.017 | **0.742 ± 0.019** | 0.761 ± 0.016 | 0.748 ± 0.015 | **0.854 ± 0.025** | 0.897 ± 0.011 |
| **LightGBM** | 0.720 ± 0.017 | 0.713 ± 0.016 | **0.777 ± 0.015** | **0.764 ± 0.021** | 0.831 ± 0.009 | 0.894 ± 0.009 |
| **Random Forest** | 0.719 ± 0.023 | 0.720 ± 0.025 | 0.765 ± 0.018 | 0.738 ± 0.025 | 0.846 ± 0.031 | 0.890 ± 0.012 |
| **HistGradientBoosting** | 0.711 ± 0.016 | 0.707 ± 0.015 | 0.769 ± 0.014 | 0.760 ± 0.015 | 0.816 ± 0.010 | 0.888 ± 0.008 |
| **Logistic Regression (L2)**| 0.709 ± 0.017 | 0.717 ± 0.018 | 0.750 ± 0.013 | 0.730 ± 0.028 | 0.826 ± 0.022 | 0.887 ± 0.009 |
| **Dummy Majority Baseline** | 0.222 ± 0.000 | 0.333 ± 0.000 | 0.499 ± 0.001 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.500 ± 0.000 |

### Early-Warning Feature Set Comparison (Semester 1 Only - 30 Features)
| Model | Macro-F1 | Balanced Acc | Accuracy | Dropout Recall | Dropout Precision | ROC-AUC (OvR) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **XGBoost (untuned)** | **0.703 ± 0.018** | 0.705 ± 0.019 | 0.748 ± 0.017 | 0.719 ± 0.025 | 0.833 ± 0.007 | **0.876 ± 0.013** |
| **Stacking Classifier** | 0.698 ± 0.015 | **0.710 ± 0.013** | 0.732 ± 0.016 | 0.706 ± 0.029 | **0.836 ± 0.019** | 0.876 ± 0.012 |
| **LightGBM** | 0.691 ± 0.029 | 0.687 ± 0.028 | **0.750 ± 0.024** | **0.745 ± 0.026** | 0.801 ± 0.024 | 0.871 ± 0.015 |
| **HistGradientBoosting** | 0.690 ± 0.016 | 0.686 ± 0.014 | 0.748 ± 0.017 | 0.737 ± 0.024 | 0.801 ± 0.015 | 0.865 ± 0.012 |
| **Random Forest** | 0.689 ± 0.021 | 0.689 ± 0.020 | 0.739 ± 0.019 | 0.717 ± 0.036 | 0.810 ± 0.026 | 0.868 ± 0.013 |
| **Logistic Regression (L2)**| 0.682 ± 0.020 | 0.689 ± 0.020 | 0.724 ± 0.020 | 0.705 ± 0.035 | 0.812 ± 0.027 | 0.861 ± 0.012 |
| **Dummy Majority Baseline** | 0.222 ± 0.000 | 0.333 ± 0.000 | 0.499 ± 0.001 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.500 ± 0.000 |

### Hyperparameter Tuning Results
`RandomizedSearchCV` (25 iterations, 5-fold CV) yielded:
- **Tuned XGBoost Full (Macro-F1 = 0.737):** `n_estimators=162`, `max_depth=5`, `learning_rate=0.0804`, `subsample=0.6308`, `colsample_bytree=0.5697`, `min_child_weight=4`.
- **Tuned XGBoost Early (Macro-F1 = 0.708):** `n_estimators=522`, `max_depth=5`, `learning_rate=0.0252`, `subsample=0.8404`, `colsample_bytree=0.7229`, `min_child_weight=8`.

---

## 5. Final Holdout Test Evaluation (885 Students)

The holdout test partition ($N=885$, containing 284 Dropouts, 159 Enrolled, and 442 Graduates) was evaluated strictly **once** following threshold and calibration selection. 

### Holdout Test Performance Summary
| Metric | Full Features Model | Early-Warning Model (Sem 1 Only) | Baseline / Unflagged |
| :--- | :---: | :---: | :---: |
| **Features Used** | 36 features | 30 features | N/A |
| **Selected Threshold** | **$t = 0.18$** | **$t = 0.16$** | $t = 0.50$ (standard) |
| **Dropout ROC-AUC** | **0.915** | **0.893** | 0.500 |
| **Dropout Average Precision (PR-AUC)** | **0.872** | **0.844** | 0.321 |
| **Dropout Recall** | **86.6%** (246 / 284) | **89.4%** (254 / 284) | 0.0% |
| **Dropout Precision** | **64.2%** | **59.3%** | 0.0% |
| **Dropout F1-Score** | **0.738** | **0.713** | 0.000 |
| **3-Class Macro-F1** | 0.690 | 0.672 | 0.222 |
| **3-Class Accuracy** | 73.2% | 71.4% | 49.9% |
| **Total Cohort Flagged** | 43.3% (383 students) | 48.4% (428 students) | 0.0% |
| **Cost at 5:1 Penalty** | **327.0** | **324.0** | 1,420.0 |
| **Cost Reduction vs Baseline** | **-77.0%** | **-77.2%** | 0.0% |

### Why Did Test Macro-F1 Drop from CV?
In cross-validation, Tuned XGBoost achieved 0.737 (Full) and 0.708 (Early), whereas on the holdout test set it achieved 0.690 and 0.672. This minor drop is expected and statistically sound:
1. Hyperparameter tuning selected configurations at the peak of the training folds.
2. The `Enrolled` class (159 students in test) represents an inherently noisy, fluid boundary between persisting and departing students, lowering the unweighted 3-class macro average.
3. Crucially, the **Dropout ROC-AUC on the test set remained exceptionally strong at 0.915 (Full) and 0.893 (Early)**, proving that the early-warning signal is robust and generalizes without overfitting.

---

## 6. Critical Empirical Findings & Limitations

### 1. Calibration Reality & Platt Scaling
Raw XGBoost probabilities were already well-calibrated out of the box (Raw Brier score: 0.0920 vs Platt calibrated: 0.0919; Expected Calibration Error $< 1\%$). Because dropouts constitute ~32.1% (roughly one-third) of the cohort, balanced sample weighting did not introduce severe probability distortions. Platt scaling made negligible difference, which explains why the empirically selected threshold ($0.18$) aligned closely with the theoretical Bayesian cutoff ($1 / (1 + 5) \approx 0.167$).

### 2. Characterizing Missed Dropouts (False Negatives)
An audit of the 38 missed dropouts in the full model revealed a distinct institutional profile:
- They are younger (mean age 21.1 vs 26.7 for caught dropouts).
- 100% had paid their tuition fees up to date.
- They achieved solid academic marks in Semester 1 (average grade ~12.4 / 20).
- **Core Insight:** Their departure is driven by unobserved factors (mental health challenges, relocation, personal/family emergencies, transfer to another institution) that are fundamentally absent from the administrative dataset. **Machine learning cannot predict what the database does not measure.** Institutional exit interviews are required to address this group.

### 3. Subgroup Fairness & Disparities
An audit of demographic subgroups on the holdout test set revealed critical equity implications:
- **Scholarship Holders:** In the early-warning model, dropout recall for scholarship holders was only **63.2%** (12/19 caught) compared to **91.3%** (242/265 caught) for non-scholarship students. Because scholarship holders drop out at a much lower base rate (9.3% vs 39.0%), their risk probabilities are systematically lower. Mentors must not rely solely on automated flags for scholarship recipients.
- **Age Disparities:** Students aged $\le 20$ exhibited an 84.1% dropout recall, while older students ($>25$) exhibited 94.1% recall with a 50.0% false alarm rate.
- **Gender Disparities:** Male students experienced double the false alarm rate of female students (42.4% vs 23.7%), leading to 66.3% of males being flagged for outreach.
- **Small Sample Caveat:** Subgroup counts for `International` ($n=24$ in test) and `Educational special needs` ($n=10$ in test) are too small to draw statistically reliable parity conclusions.

### 4. Timing Leakage Audit
In administrative systems, `Tuition fees up to date` and `Debtor` might be updated continuously throughout the academic year. When both financial indicators were completely removed from the early-warning model, it achieved a 5-fold Macro-F1 of **0.676 ± 0.020** and ROC-AUC of **0.856 ± 0.012** (a drop of only 0.032). This confirms that the early-warning capacity **mostly survives** on academic and demographic indicators alone even in the absence of financial billing data.

### 5. Multi-Tier Triage to Prevent Mentor Alert Fatigue
At the cost-optimal cutoff ($t = 0.16$), the system flags ~48.4% of the cohort. If every flag prompted an urgent mandatory meeting, academic advisors would experience acute alert fatigue. The production deployment implements a **Three-Tier Operational Strategy**:
- **High Risk ($P \ge 0.50$):** ~25.6% of the student body. High precision (80.6%). Mandates immediate 1-on-1 advisor outreach, academic probation counseling, and financial aid review.
- **Medium Risk ($0.16 \le P < 0.50$):** ~22.7% of the cohort. Moderate precision. Routes students into low-overhead automated nudges, study skills workshops, and peer tutoring referrals.
- **Low Risk ($P < 0.16$):** ~51.6% of students. Standard academic monitoring.

### 6. Macroeconomic Feature Proxying
`Unemployment rate` emerged as the 8th most influential feature in the early TreeSHAP ranking. However, because there are only 10 unique values across the dataset corresponding to calendar years, it acts partly as a proxy for the student's admission intake cohort rather than pure macroeconomic sensitivity.

---

## 7. Explainability via TreeSHAP

Model interpretability is implemented through **TreeSHAP** (SHapley Additive exPlanations) directly on tree ensembles. Additivity checks confirmed exact mathematical consistency ($|\sum \text{SHAP} - (\text{margin} - \text{base})| < 10^{-6}$).

### Top Risk Factors in Early-Warning Model (Semester 1)
| Rank | Feature | Mean \|SHAP\| | Direction / Impact |
| :---: | :--- | :---: | :--- |
| **1** | `Curricular units 1st sem (approved)` | 0.632 (23.3%) | Lower approved units dramatically spikes dropout risk. |
| **2** | `Tuition fees up to date` | 0.350 (12.9%) | Unpaid tuition is the strongest non-academic risk driver. |
| **3** | `Age at enrollment` | 0.206 (7.6%) | Mature students (>25 years) carry significantly higher risk. |
| **4** | `Curricular units 1st sem (enrolled)` | 0.162 (6.0%) | High enrollment without corresponding approvals signals distress. |
| **5** | `Curricular units 1st sem (grade)` | 0.158 (5.8%) | Lower grade averages push predictions toward dropout. |
| **6** | `Course` | 0.133 (4.9%) | Degree programme baseline variance. |
| **7** | `Gender` | 0.128 (4.7%) | Male students exhibit higher dropout likelihood in this cohort. |
| **8** | `Unemployment rate` | 0.124 (4.6%) | Economic context / admission cohort identifier. |

> **Viva Note:** SHAP values measure **model feature reliance**, not real-world causation. For example, a positive SHAP value on `Age at enrollment` indicates that the tree ensemble relies on older age to assign higher risk; it does not imply that aging causes a student to drop out.

---

## 8. Interactive Streamlit Web Dashboard

The deployment layer provides an interactive faculty dashboard located at [`app/app.py`](app/app.py) powered by [`src/predict.py`](src/predict.py).

### Core Features
1. **Model Toggle:** Switch dynamically between the *Full Curriculum Model* and the *Early-Warning Model (Semester 1 Only)*.
2. **Student Presets:** Instantly load synthetic student personas (e.g., High-Risk Student, Low-Risk Student, Borderline Student) or sample random students from the holdout dataset.
3. **Interactive Control Panels:** Adjust academic performance, demographic indicators, and financial standing via structured sliders and dropdowns.
4. **Risk Gauge & Triage Recommendation:** Displays $P(\text{Dropout})$, $P(\text{Enrolled})$, $P(\text{Graduate})$, visual risk badges (`HIGH RISK`, `MEDIUM RISK`, `LOW RISK`), and specific action recommendations for mentors.
5. **Real-Time Local SHAP Waterfall Plot:** Dynamically visualizes the exact top factors increasing or reducing risk for that specific student.
6. **Model Audit Expander:** Transparently presents confusion matrices, threshold trade-offs, and subgroup performance to ensure faculty understand model boundaries.

---

## 9. How to Run & Reproduce Locally

### Step 1: Clone Repository & Set Up Environment
```bash
git clone https://github.com/rishi4842/student-dropout-risk-intelligence.git
cd student-dropout-risk-intelligence

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install frozen dependencies
pip install -r requirements.txt
```

### Step 2: Run the Automated Unit Test Suite
Verify pipeline integrity and data transformation guarantees:
```bash
pytest -q
# Expected output: 5 passed in < 5s
```

### Step 3: Launch the Streamlit Web Application
```bash
streamlit run app/app.py
```
Open your browser to `http://localhost:8501`.

### Step 4: Re-run Full Pipeline (Optional)
If you wish to re-train the models or re-generate SHAP explanations from scratch:
```bash
# Model training and hyperparameter search
python src/train.py

# Out-of-fold calibration and holdout test evaluation
python src/evaluate.py

# TreeSHAP global and local attribution generation
python src/explain.py
```

---

## 10. Streamlit Cloud Deployment Guide

To deploy the interactive web app to Streamlit Community Cloud:

1. **Push to GitHub:** Ensure your repository `rishi4842/student-dropout-risk-intelligence` is up to date on branch `main`.
2. **Sign In to Streamlit:** Visit [share.streamlit.io](https://share.streamlit.io) and sign in using your GitHub account.
3. **Create New App:**
   - **Repository:** `rishi4842/student-dropout-risk-intelligence`
   - **Branch:** `main`
   - **Main file path:** `app/app.py`
4. **Deploy:** Click **Deploy**. Streamlit Cloud will automatically detect `requirements.txt`, install dependencies, load the serialized model artifacts from `models/`, and provide a public HTTPS URL.

---

## 11. Comprehensive Viva Voce Defense Guide

Be prepared to defend your methodological, mathematical, and ethical decisions during your project defense:

#### Q1: Why did you frame this as a 3-class problem instead of binary classification (Dropout vs Non-Dropout)?
> **Defense:** Collapsing the task into a binary "Dropout vs Rest" classification conflates students who successfully graduate with students who are actively persisting (`Enrolled`). Persisting students have different academic profiles, progress speeds, and credit loads. Treating them as graduates creates label noise; treating them as dropouts creates severe false alarm distortions. By keeping all 3 classes, the model accurately maps the cohort dynamics, while we extract $P(\text{Dropout})$ as our primary risk metric for student retention triage.

#### Q2: Why is Macro-F1 and Dropout Recall preferred over standard classification accuracy?
> **Defense:** The dataset exhibits class imbalance (49.9% Graduate, 32.1% Dropout, 18.0% Enrolled). A trivial dummy baseline that always predicts `Graduate` achieves nearly 50% accuracy while having **0% recall** on dropouts. Macro-F1 weights all three classes equally, preventing the dominant `Graduate` class from masking poor performance on minority classes. Furthermore, in educational retention, the cost of a False Negative (missing a student who drops out) far exceeds a False Positive (an unneeded advisor check-in), making Dropout Recall our paramount clinical metric.

#### Q3: How did you select the decision threshold of 0.16 / 0.18 instead of the default 0.50?
> **Defense:** We formalized threshold selection through an expected cost objective function: $\text{Cost} = 5 \times FN + 1 \times FP$. In higher education, missing an at-risk student costs the institution tuition revenue and damages the student's career, whereas a false alarm only costs 15 minutes of mentor advising time (a 5:1 cost ratio). By evaluating out-of-fold cost curves across thresholds from 0.01 to 0.99, the minimum expected cost occurred at $t = 0.18$ for the full model and $t = 0.16$ for the early model, cutting total institutional error costs by **77%** compared to unflagged baselines.

#### Q4: How did you ensure there was no data leakage in your pipeline?
> **Defense:** Strict anti-leakage hygiene was enforced:
> 1. A single 80/20 stratified split separated the test set before any exploratory analysis, imputation, or scaling.
> 2. All preprocessing transformations (`StandardScaler`, `OneHotEncoder`) were wrapped in an immutable scikit-learn `Pipeline` fitted strictly on the training folds during 5-fold cross-validation.
> 3. For the early-warning model, all 6 Semester 2 curricular features were stripped upstream to eliminate temporal lookahead leakage.
> 4. Automated unit tests in `tests/test_pipeline.py` assert that test data transforms without refitting parameters.

#### Q5: Can SHAP explanations be interpreted as causal reasons for why a student drops out?
> **Defense:** Absolutely not. SHAP values calculate feature attribution based on cooperative game theory (Shapley values), quantifying how much each feature moves the model's log-odds prediction away from the base value. They measure **model reliance**, not real-world causality. For instance, high tuition debt is correlated with dropout risk in the model, but paying off the debt may not prevent dropout if the underlying cause is academic failure or family relocation. SHAP indicates *where to look*, not *what caused it*.

#### Q6: How does the system address algorithmic fairness and demographic bias?
> **Defense:** We audited the model across demographic subgroups (Gender, Scholarship Status, Age, Nationality). We found that scholarship holders have lower dropout recall (63.2%) due to low base departure rates, and male students have higher false alarm rates. Rather than using the model to make punitive or automated decisions (such as withholding financial aid or denying enrollment), our system operates strictly as a **decision-support tool** to direct supportive mentoring resources. Tiers ensure students who need assistance receive human advisor oversight.

---

## 12. Repository Structure & License

```
student-dropout-risk-intelligence/
├── README.md                                  # Comprehensive project documentation & viva guide
├── requirements.txt                           # Pinned dependencies for reproduction & deployment
├── pytest.ini                                 # pytest configuration
├── LICENSE                                    # MIT License
├── data/
│   ├── data.csv                               # UCI 697 raw dataset (4,424 records)
│   └── README.md                              # Complete feature dictionary & metadata
├── notebooks/
│   ├── 01_eda.ipynb                           # Exploratory data analysis & statistical findings
│   ├── 02_modelling.ipynb                     # Cross-validation benchmarking & tuning
│   └── 03_shap.ipynb                          # TreeSHAP global and local analysis
├── src/
│   ├── __init__.py                            # Package initialization
│   ├── pipeline.py                            # ColumnTransformer & anti-leakage pipeline
│   ├── train.py                               # 7-model CV benchmark & hyperparameter search
│   ├── evaluate.py                            # Calibration, cost thresholding & test run
│   ├── explain.py                             # TreeSHAP computation & figure generation
│   └── predict.py                             # Decoupled inference engine for deployment
├── models/
│   ├── xgboost_full.joblib                    # Tuned Full Model (36 features)
│   ├── xgboost_early.joblib                   # Tuned Early-Warning Model (30 features)
│   └── random_forest_full.joblib              # Tuned Random Forest benchmark
├── app/
│   └── app.py                                 # Streamlit retention dashboard application
├── reports/
│   ├── model_comparison_full.csv              # Full CV metrics across 7 models
│   ├── model_comparison_early.csv             # Early CV metrics across 7 models
│   ├── test_results_xgboost_full.json         # Single-pass holdout test metrics (Full)
│   ├── test_results_xgboost_early.json        # Single-pass holdout test metrics (Early)
│   ├── shap_importance_xgboost_full.csv       # TreeSHAP global feature rankings (Full)
│   ├── shap_importance_xgboost_early.csv      # TreeSHAP global feature rankings (Early)
│   ├── shap_local_cases_xgboost_full.md       # Prototypical case studies (Full)
│   ├── shap_local_cases_xgboost_early.md      # Prototypical case studies (Early)
│   └── figures/                               # ROC curves, confusion matrices, SHAP plots
└── tests/
    └── test_pipeline.py                       # Automated test suite (5 passing unit tests)
```

### Dataset Attribution
Realinho, V., Martins, M. V., Machado, J., & Baptista, L. (2021). *Predict Students' Dropout and Academic Success*. UCI Machine Learning Repository. [https://doi.org/10.24432/C5MC89](https://doi.org/10.24432/C5MC89).  
Licensed under [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).

### Software License
The software and analysis codebase are licensed under the [MIT License](LICENSE).
