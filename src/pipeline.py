"""Data loading, feature groups and preprocessing for the dropout-risk project.

Put this file in src/pipeline.py. Everything that learns from data (scaling,
one-hot categories) lives inside the sklearn Pipeline, so it is fitted on
training folds only and cannot leak information from validation/test rows.
"""
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

TARGET = "Target"
CLASS_ORDER = ["Dropout", "Enrolled", "Graduate"]
CLASS_TO_INT = {c: i for i, c in enumerate(CLASS_ORDER)}  # Dropout = 0
RANDOM_STATE = 42

# Column groups, taken from the EDA partition (checked against the UCI dictionary).
BINARY = [
    "Daytime/evening attendance", "Displaced", "Educational special needs",
    "Debtor", "Tuition fees up to date", "Gender", "Scholarship holder",
    "International",
]
NOMINAL = [
    "Marital status", "Application mode", "Course", "Previous qualification",
    "Nacionality", "Mother's qualification", "Father's qualification",
    "Mother's occupation", "Father's occupation",
]
NUMERIC = [
    "Application order",  # ordered preference 0-9, treated as a number
    "Previous qualification (grade)", "Admission grade", "Age at enrollment",
    "Curricular units 1st sem (credited)", "Curricular units 1st sem (enrolled)",
    "Curricular units 1st sem (evaluations)", "Curricular units 1st sem (approved)",
    "Curricular units 1st sem (grade)", "Curricular units 1st sem (without evaluations)",
    "Curricular units 2nd sem (credited)", "Curricular units 2nd sem (enrolled)",
    "Curricular units 2nd sem (evaluations)", "Curricular units 2nd sem (approved)",
    "Curricular units 2nd sem (grade)", "Curricular units 2nd sem (without evaluations)",
    "Unemployment rate", "Inflation rate", "GDP",
]


def _keep(cols, early):
    """Early-warning model = only information available by the end of semester 1."""
    return [c for c in cols if not (early and "2nd sem" in c)]


def feature_columns(early=False):
    return _keep(BINARY + NOMINAL + NUMERIC, early)


def load_data(path):
    df = pd.read_csv(path, sep=";")
    df.columns = df.columns.str.strip()  # one column name has a stray tab
    unknown = set(df[TARGET].unique()) - set(CLASS_ORDER)
    if unknown:
        raise ValueError(f"Unexpected target labels: {unknown}")
    return df


def build_preprocessor(early=False):
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), _keep(NUMERIC, early)),
            ("nom", OneHotEncoder(handle_unknown="infrequent_if_exist",
                                  min_frequency=20, sparse_output=False),
             _keep(NOMINAL, early)),
            ("bin", "passthrough", BINARY),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    ).set_output(transform="pandas")


def build_model_pipeline(model, early=False):
    return Pipeline([("prep", build_preprocessor(early)), ("model", model)])


def make_split(df, early=False, test_size=0.2):
    """Stratified train/test split. The test set is used ONCE, at the very end.
    Use cross-validation on the training part for model selection and tuning."""
    X = df[feature_columns(early)]
    y = df[TARGET].map(CLASS_TO_INT)
    return train_test_split(X, y, test_size=test_size, stratify=y,
                            random_state=RANDOM_STATE)
