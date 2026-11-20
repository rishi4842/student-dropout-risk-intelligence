"""tests/test_pipeline.py - runs on synthetic data, so it needs no dataset file.
Run from the repo root with:  pytest -q   (src/ must be importable, see note in README)
"""
import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score

from src.pipeline import (BINARY, NOMINAL, NUMERIC, TARGET, CLASS_ORDER,
                          build_model_pipeline, feature_columns, make_split)


def fake_df(n=400, seed=0):
    rng = np.random.default_rng(seed)
    d = {c: rng.integers(0, 2, n) for c in BINARY}
    d.update({c: rng.integers(1, 8, n) for c in NOMINAL})
    d.update({c: rng.normal(10, 3, n) for c in NUMERIC})
    d[TARGET] = rng.choice(CLASS_ORDER, n, p=[0.32, 0.18, 0.50])
    return pd.DataFrame(d)


def test_early_set_has_no_second_semester_columns():
    assert not any("2nd sem" in c for c in feature_columns(early=True))
    assert any("2nd sem" in c for c in feature_columns(early=False))


def test_split_is_stratified_and_disjoint():
    X_tr, X_te, y_tr, y_te = make_split(fake_df())
    assert set(X_tr.index).isdisjoint(X_te.index)
    assert abs(y_tr.value_counts(normalize=True)[0]
               - y_te.value_counts(normalize=True)[0]) < 0.03


def test_pipeline_fits_and_predicts_probabilities():
    X_tr, X_te, y_tr, _ = make_split(fake_df())
    pipe = build_model_pipeline(LogisticRegression(max_iter=500))
    pipe.fit(X_tr, y_tr)
    proba = pipe.predict_proba(X_te)
    assert proba.shape == (len(X_te), 3)
    assert np.allclose(proba.sum(axis=1), 1.0)


def test_unseen_category_does_not_crash():
    X_tr, X_te, y_tr, _ = make_split(fake_df())
    pipe = build_model_pipeline(LogisticRegression(max_iter=500)).fit(X_tr, y_tr)
    X_new = X_te.copy()
    X_new["Course"] = 99999  # category never seen in training
    pipe.predict(X_new)


def test_cross_validation_runs_with_early_features():
    X_tr, _, y_tr, _ = make_split(fake_df(), early=True)
    pipe = build_model_pipeline(LogisticRegression(max_iter=500), early=True)
    scores = cross_val_score(pipe, X_tr, y_tr, cv=3, scoring="f1_macro")
    assert len(scores) == 3
