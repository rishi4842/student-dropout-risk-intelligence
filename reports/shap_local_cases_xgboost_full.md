# Local SHAP explanations - xgboost (full)

Typical test cases: for each group, the student whose risk is closest to the group's median. Positive = pushes towards Dropout.


## Caught dropout (High risk)

- Actual outcome: **Dropout**; calibrated dropout risk **95%**; tier **High**.
- Pushing risk UP: Tuition fees up to date = 0 (+1.17); Curricular units 2nd sem (approved) = 0 (+0.60); Curricular units 2nd sem (grade) = 0 (+0.30); Mother's qualification = 34 (+0.23)
- Pushing risk DOWN: Father's occupation = 99 (-0.76); Curricular units 2nd sem (enrolled) = 2 (-0.12); Unemployment rate = 7.6 (-0.07); Course = 9147 (-0.07)
- Interpretation: The model assigns a 95% dropout risk because the student exhibits acute financial distress (`Tuition fees up to date = 0`, SHAP +1.17) combined with zero approved units and zero grade in Semester 2 (+0.60 and +0.30). Although the student enrolled in 2 units and their father's occupation code pushed risk downward (-0.76), the model relies heavily on tuition arrears and complete second-semester academic failure to identify this student.

## MISSED dropout (flagged Low)

- Actual outcome: **Dropout**; calibrated dropout risk **12%**; tier **Low**.
- Pushing risk UP: Curricular units 2nd sem (approved) = 0 (+0.71); Curricular units 2nd sem (grade) = 0 (+0.27); Curricular units 1st sem (approved) = 0 (+0.13); Curricular units 2nd sem (evaluations) = 0 (+0.11)
- Pushing risk DOWN: Curricular units 2nd sem (enrolled) = 0 (-0.50); Curricular units 1st sem (enrolled) = 0 (-0.46); Admission grade = 146.3 (-0.37); Age at enrollment = 18 (-0.22)
- Interpretation: The model was misled because the student entered with strong credentials (admission grade 146.3, SHAP -0.37) and was a young direct entrant (age 18, -0.22). While zero units were approved in Semester 2 (+0.71), the student also had zero units enrolled in both semesters (-0.50 and -0.46), which the model interpreted as a non-standard or deferred study pattern rather than an academic failure, incorrectly suppressing the predicted risk to 12%.

## False alarm (not a dropout, flagged)

- Actual outcome: **Not a dropout**; calibrated dropout risk **33%**; tier **Medium**.
- Pushing risk UP: Curricular units 2nd sem (approved) = 0 (+0.70); Curricular units 2nd sem (grade) = 0 (+0.37); Admission grade = 133.3 (+0.15); Curricular units 1st sem (approved) = 0 (+0.11)
- Pushing risk DOWN: Curricular units 2nd sem (enrolled) = 0 (-0.42); Curricular units 1st sem (enrolled) = 0 (-0.28); Tuition fees up to date = 1 (-0.19); Course = 171 (-0.17)
- Interpretation: The model flags this persisting student as Medium risk (33% vs threshold 0.18) because zero units were approved and grades were zero in Semester 2 (+0.70 and +0.37). However, the student kept tuition payments fully current (`Tuition fees up to date = 1`, -0.19) and had zero enrolled units (-0.42), indicating a temporary administrative pause or gap semester rather than permanent departure.

## Correctly cleared (Low risk)

- Actual outcome: **Not a dropout**; calibrated dropout risk **6%**; tier **Low**.
- Pushing risk UP: Admission grade = 129.8 (+0.17); Curricular units 2nd sem (enrolled) = 8 (+0.08); Curricular units 1st sem (enrolled) = 7 (+0.06); Curricular units 1st sem (evaluations) = 8 (+0.05)
- Pushing risk DOWN: Curricular units 2nd sem (approved) = 7 (-0.87); Curricular units 1st sem (grade) = 14.4 (-0.28); Tuition fees up to date = 1 (-0.17); Age at enrollment = 20 (-0.16)
- Interpretation: The model assigns an exceptionally low risk of 6% because the student shows outstanding academic progress, approving 7 units in Semester 2 (SHAP -0.87) with a high first-semester grade of 14.4 (-0.28). Current tuition payments (-0.17) and traditional matriculation age (-0.16) further confirm strong retention signals.
