# Student Dropout Risk & Retention Intelligence System

Early-warning machine learning system that estimates a student's risk of dropping out and explains which factors drive that risk, so mentors can act early.

- **Course:** INT395 Supervised Learning (Project 29)
- **Author:** Rishikesh Boppa
- **Date:** November 19, 2026
- **Status:** In Progress (Phase 1 Complete)

---

## 1. Problem Definition

### Real-World Problem
Students who drop out of higher education are often identified too late for academic mentors or advisers to intervene effectively. Institutions require an early, interpretable, data-driven early-warning signal indicating which students may need support and what specific risk factors contribute to their situation.

### Target Users / Stakeholders
- **Mentors and Faculty Advisers:** Identify which students may need proactive academic or counselling support and understand the root drivers of their risk.
- **Academic Administrators:** Understand institutional and cohort-level trends linked to student dropout across academic degree programmes.
- **Students:** Indirect beneficiaries through timely, targeted academic support and guidance. The system serves as a support tool, not a judgement on any student's potential.

### Machine Learning Objective
Multiclass supervised classification. Predict each student's outcome at the end of the normal curriculum duration:
- `Dropout`
- `Enrolled`
- `Graduate`

The `Dropout` class is the primary focus; its predicted probability is used as a continuous risk score to prioritize interventions.

### Input Variables
The model uses 36 input features spanning demographic information, socio-economic background, application and enrolment details, academic performance across the first and second semesters (enrolled, approved, evaluated units, and grades), and macro-economic context indicators. Full details are documented in the data dictionary in [`data/README.md`](data/README.md).

### Expected Output
- Predicted academic outcome class and multiclass probabilities (`P(Dropout)`, `P(Enrolled)`, `P(Graduate)`).
- A dropout risk score (0.0 to 1.0) and triage risk band (`Low`, `Medium`, `High`).
- Per-student local explanations highlighting the top factors increasing or reducing risk using SHAP values.
- Suggested actionable follow-up recommendations for mentors.

---

## 2. Dataset & Limitations

- **Dataset Name:** Predict Students' Dropout and Academic Success
- **Source:** UCI Machine Learning Repository ([Dataset ID 697](https://archive.ics.uci.edu/dataset/697))
- **Creators:** Valentim Realinho, Mónica Vieira Martins, Jorge Machado, Luís Baptista (*Instituto Politécnico de Portalegre*, Portugal).
- **Size:** 4,424 student records, 36 input features, 1 target variable (`Target`), 3 classes (`Graduate`: 2,209, `Dropout`: 1,421, `Enrolled`: 794).
- **Data Quality:** Zero missing values reported in the source dataset (validated during data ingestion).
- **Licence:** Creative Commons Attribution 4.0 International ([CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)).
- **Limitations:**
  - **Institutional Context:** The data is gathered from a Portuguese polytechnic institute (*Instituto Politécnico de Portalegre*), not from LPU or an Indian educational framework; distributions, grading scales (0–20, 0–200), and policy dynamics may not directly transfer without recalibration.
  - **Class Imbalance:** Classes are naturally imbalanced (49.9% Graduate, 32.1% Dropout, 18.0% Enrolled), requiring balanced weighting or threshold tuning.
  - **Snapshot Nature:** The dataset represents a historical cohort cross-sectional snapshot rather than real-time longitudinal event streams.

---

## 3. Planned Pipeline

The planned project lifecycle follows a structured 10-step end-to-end supervised learning architecture:

```
Problem Definition
       │
       ▼
Data Ingestion & Validation
       │
       ▼
Exploratory Data Analysis (EDA)
       │
       ▼
Preprocessing & Pipeline Design
       │
       ▼
Feature Engineering
       │
       ▼
Baseline & Model Benchmarking
       │
       ▼
Hyperparameter Tuning & Error Analysis
       │
       ▼
Model Explainability (SHAP)
       │
       ▼
Streamlit Deployment (Interactive App)
       │
       ▼
Comprehensive Reporting & Documentation
```

---

## 4. Repository Structure

```
student-dropout-risk-intelligence/
├── README.md              # Project overview, problem definition, execution instructions
├── requirements.txt       # Frozen Python dependencies
├── .gitignore             # Git ignore patterns for venv, caches, and build artifacts
├── LICENSE                # MIT License
├── data/                  # Raw dataset and data documentation
│   ├── data.csv           # UCI 697 raw dataset (4,424 records)
│   └── README.md          # Comprehensive data dictionary
├── notebooks/             # Step-by-step Jupyter notebooks
│   ├── 01_eda.ipynb       # Exploratory Data Analysis & visual discovery
│   ├── 02_modelling.ipynb # Model experimentation, tuning & comparison
│   └── 03_shap.ipynb      # Global and local SHAP explainability
├── src/                   # Production modular Python code
│   ├── pipeline.py        # Leakage-free scikit-learn preprocessing pipelines
│   ├── train.py           # Model training and artifact serialization
│   └── evaluate.py        # Comprehensive evaluation metrics & reporting
├── models/                # Serialized trained model pipelines (.joblib)
├── app/                   # Interactive Streamlit web application
│   └── app.py             # Early-warning retention dashboard & single-student risk predictor
├── reports/               # EDA visuals, evaluation charts, and viva presentation summaries
└── tests/                 # Automated test suite with pytest
```

---

## 5. Environment Setup & Requirements

### System Requirements
- Python 3.10+ (tested on Python 3.11.16)
- macOS / Linux / Windows
- OpenMP runtime (for XGBoost and LightGBM native dylib acceleration)

### Virtual Environment Setup
```bash
# Clone the repository
git clone https://github.com/rishi4842/student-dropout-risk-intelligence.git
cd student-dropout-risk-intelligence

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# .\venv\Scripts\activate

# Install required dependencies
pip install -r requirements.txt
```

---

## 6. How to Run

### Step 1: Verify Environment & Data
```bash
python -c "import pandas as pd; df = pd.read_csv('data/data.csv', sep=';'); print('Records:', len(df))"
```

### Step 2: Run Exploratory Data Analysis (EDA)
```bash
jupyter notebook notebooks/
```

### Step 3: Run Automated Test Suite
```bash
pytest tests/
```

### Step 4: Launch Interactive Streamlit Early-Warning App
*(To be activated upon Phase 4 app deployment)*
```bash
streamlit run app/app.py
```

---

## 7. Evaluation & Success Criteria

Accuracy alone is misleading on imbalanced student outcome data. Success is defined across technical and domain-specific criteria:

1. **Macro-Averaged F1-Score:** The chosen model must convincingly outperform a naive majority-class baseline and a regularized Logistic Regression baseline on Macro-F1 across all 3 classes.
2. **Dropout Recall Prioritization:** Because the operational cost of missing an at-risk student (false negative) outweighs the cost of an unnecessary mentoring check-in (false positive), decision thresholds will be tuned to achieve a target **Recall ≥ 0.80** on the `Dropout` class while preserving acceptable precision (Precision ≥ 0.65).
3. **Strict Data Leakage Prevention:** All scalers, imputers, and encoders must be encapsulated strictly within a `scikit-learn Pipeline` and fitted exclusively on training folds during stratified cross-validation.
4. **Actionable Model Interpretability:** Every prediction must be accompanied by local SHAP (SHapley Additive exPlanations) values to provide transparent, defensible reasons for mentors.
5. **Deployment & Usability:** The final system must be delivered through an interactive, self-contained Streamlit application supporting both batch evaluation and single-student risk scoring.
6. **Empirical Quantitative Benchmarks (5-Fold Stratified CV on Training Part):**

#### Full Feature Set Comparison (36 Features):
| Model | Macro-F1 | Balanced Acc | Accuracy | Dropout Recall | Dropout Precision | ROC-AUC (OvR) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **XGBoost (untuned)** | **0.731 ± 0.017** | 0.732 ± 0.018 | 0.776 ± 0.015 | 0.759 ± 0.022 | 0.845 ± 0.022 | **0.898 ± 0.010** |
| **Stacking Classifier** | 0.728 ± 0.017 | **0.742 ± 0.019** | 0.761 ± 0.016 | 0.748 ± 0.015 | **0.854 ± 0.025** | 0.897 ± 0.011 |
| **LightGBM** | 0.720 ± 0.017 | 0.713 ± 0.016 | **0.777 ± 0.015** | **0.764 ± 0.021** | 0.831 ± 0.009 | 0.894 ± 0.009 |
| **Random Forest** | 0.719 ± 0.023 | 0.720 ± 0.025 | 0.765 ± 0.018 | 0.738 ± 0.025 | 0.846 ± 0.031 | 0.890 ± 0.012 |
| **HistGradientBoosting** | 0.711 ± 0.016 | 0.707 ± 0.015 | 0.769 ± 0.014 | 0.760 ± 0.015 | 0.816 ± 0.010 | 0.888 ± 0.008 |
| **Logistic Regression** | 0.709 ± 0.017 | 0.717 ± 0.018 | 0.750 ± 0.013 | 0.730 ± 0.028 | 0.826 ± 0.022 | 0.887 ± 0.009 |
| **Dummy Majority Baseline** | 0.222 ± 0.000 | 0.333 ± 0.000 | 0.499 ± 0.001 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.500 ± 0.000 |

*Tuning Results (Full Features):*
- **Tuned XGBoost:** Macro-F1 = **0.737** (`n_estimators=162`, `max_depth=5`, `learning_rate=0.080`, `subsample=0.63`, `colsample_bytree=0.57`, `min_child_weight=4`).
- **Tuned Random Forest:** Macro-F1 = **0.722** (`n_estimators=659`, `max_depth=20`, `max_features='sqrt'`, `min_samples_leaf=1`).

#### Early-Warning Feature Set Comparison (Semester 1 Only - 30 Features):
| Model | Macro-F1 | Balanced Acc | Accuracy | Dropout Recall | Dropout Precision | ROC-AUC (OvR) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **XGBoost (untuned)** | **0.703 ± 0.018** | 0.705 ± 0.019 | 0.748 ± 0.017 | 0.719 ± 0.025 | 0.833 ± 0.007 | **0.876 ± 0.013** |
| **Stacking Classifier** | 0.698 ± 0.015 | **0.710 ± 0.013** | 0.732 ± 0.016 | 0.706 ± 0.029 | **0.836 ± 0.019** | 0.876 ± 0.012 |
| **LightGBM** | 0.691 ± 0.029 | 0.687 ± 0.028 | **0.750 ± 0.024** | **0.745 ± 0.026** | 0.801 ± 0.024 | 0.871 ± 0.015 |
| **HistGradientBoosting** | 0.690 ± 0.016 | 0.686 ± 0.014 | 0.748 ± 0.017 | 0.737 ± 0.024 | 0.801 ± 0.015 | 0.865 ± 0.012 |
| **Random Forest** | 0.689 ± 0.021 | 0.689 ± 0.020 | 0.739 ± 0.019 | 0.717 ± 0.036 | 0.810 ± 0.026 | 0.868 ± 0.013 |
| **Logistic Regression** | 0.682 ± 0.020 | 0.689 ± 0.020 | 0.724 ± 0.020 | 0.705 ± 0.035 | 0.812 ± 0.027 | 0.861 ± 0.012 |
| **Dummy Majority Baseline** | 0.222 ± 0.000 | 0.333 ± 0.000 | 0.499 ± 0.001 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.500 ± 0.000 |

*Tuning Results (Early Warning):*
- **Tuned Early XGBoost:** Macro-F1 = **0.708** (`n_estimators=522`, `max_depth=5`, `learning_rate=0.025`, `subsample=0.84`, `colsample_bytree=0.72`, `min_child_weight=8`).

---

### Methodological & Ethical Considerations for Viva Defense

- **The "Enrolled" Class Dilemma:**
  - `Enrolled` students have neither graduated nor dropped out; they are actively persisting within normal duration.
  - Collapsing the task into binary (Dropout vs Rest) conflates successful graduates with delayed but persistent students.
  - Therefore, we retain the **3-class model** to respect cohort dynamics while explicitly tracking **Dropout recall** and using $P(\text{Dropout})$ as the primary risk score.
- **Timing Leakage Audit:**
  - In real institutional databases, features like `Debtor` and `Tuition fees up to date` may be recorded dynamically across semesters.
  - In our early-warning pipeline, all Semester 2 academic features are strictly omitted. In production, tuition status should be frozen at the close of Semester 1 billing.
- **Fairness & Decision Support:**
  - Demographic features (`Gender`, `Nacionality`, `International`, `Educational special needs`) reflect documented historical and systemic disparities.
  - The model is strictly an **advising decision-support tool** to direct resources and mentorship to students in need, NOT an automated gatekeeper or punitive instrument. Model error rates will be audited across demographic subgroups in Phase 5.

---

## 8. Acknowledgements & License

### Dataset Attribution
Realinho, V., Martins, M. V., Machado, J., & Baptista, L. (2021). *Predict Students' Dropout and Academic Success*. UCI Machine Learning Repository. [https://doi.org/10.24432/C5MC89](https://doi.org/10.24432/C5MC89).
Licensed under [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).

### Software License
The codebase and software implementation are licensed under the [MIT License](LICENSE).
