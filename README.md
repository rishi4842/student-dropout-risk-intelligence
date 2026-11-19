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
6. **Specific Quantitative Targets:** Final quantitative target benchmarks (accuracy, precision, recall, macro-F1, ROC-AUC) will be finalized after establishing baseline results and documented here.

---

## 8. Acknowledgements & License

### Dataset Attribution
Realinho, V., Martins, M. V., Machado, J., & Baptista, L. (2021). *Predict Students' Dropout and Academic Success*. UCI Machine Learning Repository. [https://doi.org/10.24432/C5MC89](https://doi.org/10.24432/C5MC89).
Licensed under [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).

### Software License
The codebase and software implementation are licensed under the [MIT License](LICENSE).
