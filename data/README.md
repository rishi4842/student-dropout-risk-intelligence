# Data Dictionary: Predict Students' Dropout and Academic Success

This data dictionary documents the raw dataset used in the **Student Dropout Risk & Retention Intelligence System** (Course Project INT395: Supervised Learning, Project 29).

---

## 1. Dataset Overview

- **Dataset Name:** Predict Students' Dropout and Academic Success
- **UCI Repository ID:** 697
- **Source URL:** [https://archive.ics.uci.edu/dataset/697](https://archive.ics.uci.edu/dataset/697)
- **Creators:** Valentim Realinho, Mónica Vieira Martins, Jorge Machado, Luís Baptista (*Instituto Politécnico de Portalegre*, Portugal)
- **Publication Date:** 2021
- **Licence:** Creative Commons Attribution 4.0 International ([CC BY 4.0](https://creativecommons.org/licenses/by/4.0/))
- **File Format:** Semicolon-delimited CSV (`sep=';'`)
- **Dimensions:** 4,424 rows (students), 37 columns (36 predictive features + 1 target variable)
- **Missing Values:** 0 missing values reported in raw data (to be validated in EDA)

---

## 2. Target Variable

The target variable represents the student's academic status at the end of the normal curriculum duration.

- **Column Name:** `Target`
- **Data Type:** Multiclass Categorical (string)
- **Classes:**
  - `Graduate` (2,209 instances, 49.93%): Student completed their degree programme.
  - `Dropout` (1,421 instances, 32.12%): Student dropped out / abandoned the programme. This is the primary target class of interest for early warning risk prediction.
  - `Enrolled` (794 instances, 17.95%): Student is still matriculated and progressing.

---

## 3. Feature Groups Breakdown

The 36 input features are categorized into 6 thematic domains:

### A. Demographic Information (7 features)
- `Marital status`: Marital status of the student (single, married, widower, divorced, factoring union, legally separated).
- `Nacionality`: Nationality / country of origin of the student.
- `Displaced`: Whether the student lives displaced from home / hometown (1 = yes, 0 = no).
- `Educational special needs`: Whether the student has special educational needs (1 = yes, 0 = no).
- `Gender`: Gender of the student (1 = male, 0 = female).
- `Age at enrollment`: Age of the student at the time of matriculation.
- `International`: Whether the student is an international student (1 = yes, 0 = no).

### B. Socio-Economic Background (7 features)
- `Mother's qualification`: Level of education completed by the student's mother.
- `Father's qualification`: Level of education completed by the student's father.
- `Mother's occupation`: Professional occupation category of the mother.
- `Father's occupation`: Professional occupation category of the father.
- `Debtor`: Whether the student has overdue tuition or institutional debts (1 = yes, 0 = no).
- `Tuition fees up to date`: Whether the student's tuition fee payments are current (1 = yes, 0 = no).
- `Scholarship holder`: Whether the student holds an academic scholarship/grant (1 = yes, 0 = no).

### C. Admission & Enrolment Characteristics (7 features)
- `Application mode`: Route through which the student applied (general contingent, special access for over 23, international, transfer, etc.).
- `Application order`: Preference order of the chosen programme during application (1 = first choice, up to 9 = last choice).
- `Course`: Specific degree programme enrolled in (e.g., Agronomy, Design, Nursing, Management, Journalism, Informatics Engineering).
- `Daytime/evening attendance\t`: Schedule type (1 = daytime, 0 = evening; note raw header contains trailing tab).
- `Previous qualification`: Previous highest educational qualification completed prior to admission.
- `Previous qualification (grade)`: Normalized grade achieved in previous qualification (scale 0–200).
- `Admission grade`: Normalized entrance exam / admission evaluation grade (scale 0–200).

### D. Academic Performance — 1st Semester (6 features)
- `Curricular units 1st sem (credited)`: Number of course units recognized / credited from prior studies in semester 1.
- `Curricular units 1st sem (enrolled)`: Number of course units enrolled in semester 1.
- `Curricular units 1st sem (evaluations)`: Number of assessments/evaluations attended in semester 1.
- `Curricular units 1st sem (approved)`: Number of course units successfully passed in semester 1.
- `Curricular units 1st sem (grade)`: Average grade across approved units in semester 1 (scale 0–20).
- `Curricular units 1st sem (without evaluations)`: Number of enrolled units not evaluated in semester 1.

### E. Academic Performance — 2nd Semester (6 features)
- `Curricular units 2nd sem (credited)`: Number of course units credited from prior studies in semester 2.
- `Curricular units 2nd sem (enrolled)`: Number of course units enrolled in semester 2.
- `Curricular units 2nd sem (evaluations)`: Number of assessments/evaluations attended in semester 2.
- `Curricular units 2nd sem (approved)`: Number of course units successfully passed in semester 2.
- `Curricular units 2nd sem (grade)`: Average grade across approved units in semester 2 (scale 0–20).
- `Curricular units 2nd sem (without evaluations)`: Number of enrolled units not evaluated in semester 2.

### F. Macro-Economic Context (3 features)
- `Unemployment rate`: Regional unemployment rate at time of enrolment (%).
- `Inflation rate`: National annual inflation rate at time of enrolment (%).
- `GDP`: Percentage change in national Gross Domestic Product (GDP).

---

## 4. Comprehensive Feature Inventory Table

| # | Column Name in CSV | Feature Domain | Data Type | Value Range / Description |
|---|---|---|---|---|
| 1 | `Marital status` | Demographic | Categorical (int) | 1: Single, 2: Married, 3: Widower, 4: Divorced, 5: Facto union, 6: Legally separated |
| 2 | `Application mode` | Admission | Categorical (int) | Application pathway code (1 to 57) |
| 3 | `Application order` | Admission | Integer | Order of choice (0 to 9; 1 = 1st choice) |
| 4 | `Course` | Admission | Categorical (int) | Degree programme ID (code range 33 to 9991) |
| 5 | `Daytime/evening attendance\t` | Admission | Binary (int) | 1 = Daytime, 0 = Evening (strip `\t` during preprocessing) |
| 6 | `Previous qualification` | Admission | Categorical (int) | Previous educational level code (1 to 43) |
| 7 | `Previous qualification (grade)` | Admission | Continuous (float) | Grade in previous qualification (scale 0–200) |
| 8 | `Nacionality` | Demographic | Categorical (int) | Nationality country code (1 = Portuguese, etc.) |
| 9 | `Mother's qualification` | Socio-economic | Categorical (int) | Mother's education level code (1 to 44) |
| 10 | `Father's qualification` | Socio-economic | Categorical (int) | Father's education level code (1 to 44) |
| 11 | `Mother's occupation` | Socio-economic | Categorical (int) | Mother's ISCO occupation code (0 to 194) |
| 12 | `Father's occupation` | Socio-economic | Categorical (int) | Father's ISCO occupation code (0 to 195) |
| 13 | `Admission grade` | Admission | Continuous (float) | Higher education entrance grade (scale 0–200) |
| 14 | `Displaced` | Demographic | Binary (int) | 1 = Yes (living away from home), 0 = No |
| 15 | `Educational special needs` | Demographic | Binary (int) | 1 = Yes, 0 = No |
| 16 | `Debtor` | Socio-economic | Binary (int) | 1 = Yes (unpaid dues), 0 = No |
| 17 | `Tuition fees up to date` | Socio-economic | Binary (int) | 1 = Yes, 0 = No |
| 18 | `Gender` | Demographic | Binary (int) | 1 = Male, 0 = Female |
| 19 | `Scholarship holder` | Socio-economic | Binary (int) | 1 = Yes, 0 = No |
| 20 | `Age at enrollment` | Demographic | Integer | Student age at matriculation (17 to 70) |
| 21 | `International` | Demographic | Binary (int) | 1 = Yes, 0 = No |
| 22 | `Curricular units 1st sem (credited)` | Academic (1st sem) | Integer | Number of credited course units |
| 23 | `Curricular units 1st sem (enrolled)` | Academic (1st sem) | Integer | Number of enrolled course units |
| 24 | `Curricular units 1st sem (evaluations)` | Academic (1st sem) | Integer | Number of evaluation moments attended |
| 25 | `Curricular units 1st sem (approved)` | Academic (1st sem) | Integer | Number of approved course units |
| 26 | `Curricular units 1st sem (grade)` | Academic (1st sem) | Continuous (float) | Average grade in approved units (0–20 scale) |
| 27 | `Curricular units 1st sem (without evaluations)` | Academic (1st sem) | Integer | Number of units with no evaluation |
| 28 | `Curricular units 2nd sem (credited)` | Academic (2nd sem) | Integer | Number of credited course units |
| 29 | `Curricular units 2nd sem (enrolled)` | Academic (2nd sem) | Integer | Number of enrolled course units |
| 30 | `Curricular units 2nd sem (evaluations)` | Academic (2nd sem) | Integer | Number of evaluation moments attended |
| 31 | `Curricular units 2nd sem (approved)` | Academic (2nd sem) | Integer | Number of approved course units |
| 32 | `Curricular units 2nd sem (grade)` | Academic (2nd sem) | Continuous (float) | Average grade in approved units (0–20 scale) |
| 33 | `Curricular units 2nd sem (without evaluations)` | Academic (2nd sem) | Integer | Number of units with no evaluation |
| 34 | `Unemployment rate` | Macro-economic | Continuous (float) | National/regional unemployment rate (%) |
| 35 | `Inflation rate` | Macro-economic | Continuous (float) | National inflation rate (%) |
| 36 | `GDP` | Macro-economic | Continuous (float) | Gross Domestic Product change (%) |
| 37 | `Target` | Target | Categorical (string) | Outcome: `Dropout`, `Enrolled`, `Graduate` |

---

## 5. Known Institutional & Dataset Context

- **Institution:** The data originated from the *Instituto Politécnico de Portalegre* (IPP), Portugal, covering degree enrollments across technical and vocational higher education programs.
- **External Validity Limitation:** Because this dataset represents a single higher education institution in Portugal, conclusions and baseline distributions must be interpreted with caution when generalizing to other educational systems or institutions (such as Indian universities or non-polytechnic universities).
- **Temporal Nature:** The dataset records a fixed cohort snapshot at graduation/dropout evaluation time, rather than a continuous event-stream.
