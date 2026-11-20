# Local SHAP explanations - xgboost (early)

Typical test cases: for each group, the student whose risk is closest to the group's median. Positive = pushes towards Dropout.


## Caught dropout (High risk)

- Actual outcome: **Dropout**; calibrated dropout risk **94%**; tier **High**.
- Pushing risk UP: Tuition fees up to date = 0 (+1.58); Father's occupation = 90 (+0.37); Age at enrollment = 59 (+0.36); Curricular units 1st sem (credited) = 10 (+0.24)
- Pushing risk DOWN: Curricular units 1st sem (approved) = 12 (-0.71); Curricular units 1st sem (grade) = 13.3 (-0.20); Gender = 0 (-0.10); Debtor = 0 (-0.04)
- Interpretation: The early-warning model flags this student at 94% risk primarily because of unpaid tuition (`Tuition fees up to date = 0`, SHAP +1.58) and older matriculation age (age 59, SHAP +0.36). Even though the student approved 12 curricular units in semester 1 (-0.71) and had 10 credited units from prior studies (+0.24), the model heavily weights the unpaid tuition and older age profile to assign a High risk score.

## MISSED dropout (flagged Low)

- Actual outcome: **Dropout**; calibrated dropout risk **7%**; tier **Low**.
- Pushing risk UP: Curricular units 1st sem (enrolled) = 7 (+0.10); Application order = 5 (+0.07); Curricular units 1st sem (credited) = 2 (+0.06); Displaced = 1 (+0.06)
- Pushing risk DOWN: Curricular units 1st sem (approved) = 6 (-0.66); Tuition fees up to date = 1 (-0.23); Curricular units 1st sem (grade) = 13.3 (-0.20); Age at enrollment = 20 (-0.16)
- Interpretation: The model failed to detect this dropout because the student's observable semester-1 record showed no signs of academic or financial distress: the student approved 6 of 7 enrolled units (SHAP -0.66) with a 13.3 grade (-0.20), had fees fully paid (-0.23), and was a young entrant (age 20, -0.16). The dataset contains no exit survey or post-semester information to explain why the student subsequently left.

## False alarm (not a dropout, flagged)

- Actual outcome: **Not a dropout**; calibrated dropout risk **31%**; tier **Medium**.
- Pushing risk UP: Curricular units 1st sem (approved) = 0 (+0.85); Curricular units 1st sem (evaluations) = 0 (+0.28); Admission grade = 131.4 (+0.24); Curricular units 1st sem (grade) = 0 (+0.22)
- Pushing risk DOWN: Curricular units 1st sem (enrolled) = 0 (-0.47); Course = 171 (-0.33); Age at enrollment = 20 (-0.27); Tuition fees up to date = 1 (-0.25)
- Interpretation: The model places this persisting student in Medium risk (31% vs threshold 0.16) because of complete first-semester non-evaluation: 0 approved units, 0 evaluations attended, and a 0.0 grade (+0.85, +0.28, +0.22). However, because enrolled units were also 0 (-0.47) and tuition was fully paid (-0.25), this pattern resembles an inactive semester, though the data cannot verify the administrative reason.

## Correctly cleared (Low risk)

- Actual outcome: **Not a dropout**; calibrated dropout risk **6%**; tier **Low**.
- Pushing risk UP: Unemployment rate = 12.7 (+0.16); Curricular units 1st sem (enrolled) = 8 (+0.12); Displaced = 1 (+0.06); Application order = 4 (+0.06)
- Pushing risk DOWN: Curricular units 1st sem (approved) = 7 (-0.71); Tuition fees up to date = 1 (-0.23); Age at enrollment = 19 (-0.15); Course = 9500 (-0.11)
- Interpretation: The model comfortably clears this student at 6% risk due to strong Semester 1 momentum, approving 7 units (-0.71), maintaining current tuition status (-0.23), and being a young direct entrant (age 19, -0.15). Slight upward risk contributions from macro unemployment (+0.16) and credit load (+0.12) are completely offset by solid academic achievement.
