"""Phase 4 - model comparison and tuning. Put this file in src/train.py.

Run from the repo root (cross-validation happens on the TRAINING part only;
the test set is not touched here - it is used once, in phase 5):

    python -m src.train compare --data data/data.csv
    python -m src.train tune --data data/data.csv --model random_forest
    python -m src.train tune --data data/data.csv --model random_forest --early

Needs scikit-learn >= 1.4. xgboost and lightgbm are optional: models whose
package is not installed are skipped with a message.
"""
import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy.stats import loguniform, randint, uniform
from sklearn.base import clone
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import (HistGradientBoostingClassifier,
                              RandomForestClassifier, StackingClassifier)
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import make_scorer, precision_score, recall_score
from sklearn.model_selection import (RandomizedSearchCV, StratifiedKFold,
                                     cross_val_predict, cross_validate)
from sklearn.utils.class_weight import compute_sample_weight

from src.pipeline import (RANDOM_STATE, build_model_pipeline, load_data,
                          make_split)

RS = RANDOM_STATE
REPORTS, MODELS = Path("reports"), Path("models")


# ---------------------------------------------------------------- metrics
# Class 0 = Dropout. Accuracy is reported but NOT used to choose models,
# because a model that always says "Graduate" already gets ~50% accuracy.
def _dropout_recall(y_true, y_pred):
    return recall_score(np.asarray(y_true) == 0, np.asarray(y_pred) == 0)


def _dropout_precision(y_true, y_pred):
    return precision_score(np.asarray(y_true) == 0, np.asarray(y_pred) == 0,
                           zero_division=0)


SCORING = {
    "f1_macro": "f1_macro",
    "balanced_accuracy": "balanced_accuracy",
    "accuracy": "accuracy",
    "dropout_recall": make_scorer(_dropout_recall),
    "dropout_precision": make_scorer(_dropout_precision),
    "roc_auc_ovr": "roc_auc_ovr",
}


# ----------------------------------------------------------------- models
def base_estimators():
    """Candidate models. Class imbalance is handled with balanced sample
    weights (passed at fit time), so no model uses class_weight here."""
    models = {
        "dummy_majority": DummyClassifier(strategy="prior"),
        "logreg": LogisticRegression(max_iter=3000),
        "random_forest": RandomForestClassifier(
            n_estimators=300, min_samples_leaf=2, random_state=RS, n_jobs=-1),
        "hist_gb": HistGradientBoostingClassifier(random_state=RS),
    }
    try:
        from xgboost import XGBClassifier
        models["xgboost"] = XGBClassifier(
            n_estimators=300, learning_rate=0.05, max_depth=5, subsample=0.8,
            colsample_bytree=0.8, eval_metric="mlogloss", random_state=RS,
            n_jobs=-1)
    except ImportError:
        print("[skip] xgboost not installed")
    try:
        from lightgbm import LGBMClassifier
        models["lightgbm"] = LGBMClassifier(
            n_estimators=300, learning_rate=0.05, num_leaves=31, subsample=0.8,
            subsample_freq=1, colsample_bytree=0.8, random_state=RS,
            n_jobs=-1, verbose=-1)
    except ImportError:
        print("[skip] lightgbm not installed")

    # Stacking: the base models' out-of-fold probabilities feed a logistic regression.
    stack_members = [(n, clone(m)) for n, m in models.items()
                     if n not in ("dummy_majority", "logreg")]
    models["stacking"] = StackingClassifier(
        estimators=[("logreg", LogisticRegression(max_iter=3000))] + stack_members,
        final_estimator=LogisticRegression(max_iter=3000),
        cv=5, stack_method="predict_proba")
    return models


SEARCH_SPACES = {
    "logreg": {"C": loguniform(1e-3, 1e2)},
    "random_forest": {
        "n_estimators": randint(200, 700), "max_depth": [None, 8, 12, 20],
        "min_samples_leaf": randint(1, 12), "max_features": ["sqrt", 0.3, 0.5]},
    "hist_gb": {
        "learning_rate": loguniform(0.02, 0.2), "max_iter": randint(150, 500),
        "max_leaf_nodes": randint(10, 64), "min_samples_leaf": randint(10, 60),
        "l2_regularization": loguniform(1e-3, 10)},
    "xgboost": {
        "n_estimators": randint(150, 600), "max_depth": randint(3, 9),
        "learning_rate": loguniform(0.02, 0.2), "subsample": uniform(0.6, 0.4),
        "colsample_bytree": uniform(0.5, 0.5), "min_child_weight": randint(1, 10)},
    "lightgbm": {
        "n_estimators": randint(150, 600), "num_leaves": randint(10, 64),
        "learning_rate": loguniform(0.02, 0.2), "subsample": uniform(0.6, 0.4),
        "colsample_bytree": uniform(0.5, 0.5), "min_child_samples": randint(10, 60),
        "reg_lambda": loguniform(1e-3, 10)},
}


# --------------------------------------------------------------- commands
def _setup(df, early):
    X_tr, _, y_tr, _ = make_split(df, early=early)  # test part is ignored here
    weights = compute_sample_weight("balanced", y_tr)
    return X_tr, y_tr, weights


def compare(df, early, cv=5):
    X_tr, y_tr, w = _setup(df, early)
    skf = StratifiedKFold(cv, shuffle=True, random_state=RS)
    rows = []
    for name, est in base_estimators().items():
        print(f"[{'early' if early else 'full'}] cross-validating {name} ...")
        # The dummy baseline is deliberately UNweighted so it really predicts
        # the majority class (Graduate), giving 0% Dropout recall.
        fit_params = {} if name == "dummy_majority" else {"model__sample_weight": w}
        res = cross_validate(build_model_pipeline(est, early), X_tr, y_tr,
                             cv=skf, scoring=SCORING,
                             params=fit_params, n_jobs=-1)
        row = {"model": name}
        for metric in SCORING:
            vals = res[f"test_{metric}"]
            row[metric] = f"{vals.mean():.3f} +/- {vals.std():.3f}"
            row[f"_{metric}"] = vals.mean()
        rows.append(row)
    table = pd.DataFrame(rows).sort_values("_f1_macro", ascending=False)
    REPORTS.mkdir(exist_ok=True)
    tag = "early" if early else "full"
    table.drop(columns=[c for c in table if c.startswith("_")]).to_csv(
        REPORTS / f"model_comparison_{tag}.csv", index=False)
    show = table.drop(columns=[c for c in table if c.startswith("_")])
    print("\n", show.to_string(index=False))
    return show


def tune(df, model_name, early, n_iter=25, cv=5):
    if model_name not in SEARCH_SPACES:
        raise SystemExit(f"No search space for {model_name!r}. "
                         f"Choose from {list(SEARCH_SPACES)}")
    estimators = base_estimators()
    if model_name not in estimators:
        raise SystemExit(f"{model_name!r} is not available (package missing?)")
    X_tr, y_tr, w = _setup(df, early)
    skf = StratifiedKFold(cv, shuffle=True, random_state=RS)
    pipe = build_model_pipeline(estimators[model_name], early)
    space = {f"model__{k}": v for k, v in SEARCH_SPACES[model_name].items()}
    search = RandomizedSearchCV(pipe, space, n_iter=n_iter, scoring="f1_macro",
                                cv=skf, random_state=RS, n_jobs=-1, refit=True)
    search.fit(X_tr, y_tr, model__sample_weight=w)
    tag = "early" if early else "full"
    print(f"best macro-F1 (CV): {search.best_score_:.3f}")
    print("best params:", search.best_params_)

    REPORTS.mkdir(exist_ok=True)
    MODELS.mkdir(exist_ok=True)
    joblib.dump(search.best_estimator_, MODELS / f"{model_name}_{tag}.joblib")
    with open(REPORTS / f"best_params_{model_name}_{tag}.json", "w") as f:
        json.dump({k: (v.item() if hasattr(v, "item") else v)
                   for k, v in search.best_params_.items()}, f, indent=2)
    pd.DataFrame(search.cv_results_).sort_values("rank_test_score").head(10)[
        ["rank_test_score", "mean_test_score", "std_test_score", "params"]
    ].to_csv(REPORTS / f"tuning_top10_{model_name}_{tag}.csv", index=False)

    # Out-of-fold probabilities on the training part: used in phase 5 for
    # threshold selection, calibration and error analysis (no test data used).
    oof = cross_val_predict(clone(search.best_estimator_), X_tr, y_tr, cv=skf,
                            method="predict_proba",
                            params={"model__sample_weight": w}, n_jobs=-1)
    out = pd.DataFrame(oof, index=X_tr.index,
                       columns=["p_dropout", "p_enrolled", "p_graduate"])
    out["y_true"] = y_tr.values
    out.to_csv(REPORTS / f"oof_{model_name}_{tag}.csv")
    return search


def main():
    p = argparse.ArgumentParser()
    p.add_argument("command", choices=["compare", "tune"])
    p.add_argument("--data", default="data/data.csv")
    p.add_argument("--model", default="random_forest")
    p.add_argument("--early", action="store_true",
                   help="tune: use only information available by end of semester 1")
    p.add_argument("--n-iter", type=int, default=25)
    p.add_argument("--cv", type=int, default=5)
    a = p.parse_args()
    df = load_data(a.data)
    if a.command == "compare":
        compare(df, early=False, cv=a.cv)
        compare(df, early=True, cv=a.cv)
    else:
        tune(df, a.model, a.early, a.n_iter, a.cv)


if __name__ == "__main__":
    main()
