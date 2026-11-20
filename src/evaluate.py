"""Phase 5 - error analysis, decision threshold, calibration, final test. Put in src/evaluate.py.

Step A (uses ONLY training data, via the out-of-fold probabilities saved by `src.train tune`):

    python -m src.evaluate analyze --model xgboost --tag full  --cost-ratio 5
    python -m src.evaluate analyze --model xgboost --tag early --cost-ratio 5

Step B (uses the TEST set - run once per model, after every decision is final):

    python -m src.evaluate final --model xgboost --tag full  --yes
    python -m src.evaluate final --model xgboost --tag early --yes

cost-ratio = how many times worse it is to MISS a dropout than to raise a false
alarm (e.g. 5 means one missed dropout costs as much as five unnecessary
mentor check-ins). This is an assumption you must state and defend.
"""
import argparse
import json
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, brier_score_loss,
                             classification_report, confusion_matrix,
                             f1_score, precision_recall_curve, roc_auc_score)
from sklearn.model_selection import StratifiedKFold

from src.pipeline import (BINARY, CLASS_ORDER, NUMERIC, RANDOM_STATE,
                          load_data, make_split)

RS = RANDOM_STATE
REPORTS, MODELS = Path("reports"), Path("models")
FIGS = REPORTS / "figures"
PROBA_COLS = ["p_dropout", "p_enrolled", "p_graduate"]


# ------------------------------------------------------------- helpers
def _logit(p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def ece(y, p, bins=10):
    """Expected calibration error: average gap between predicted risk and
    the real dropout rate, over probability bins."""
    idx = np.clip(np.digitize(p, np.linspace(0, 1, bins + 1)[1:-1]), 0, bins - 1)
    return float(sum((idx == b).mean() * abs(y[idx == b].mean() - p[idx == b].mean())
                     for b in range(bins) if (idx == b).any()))


def fit_calibrator(p, y, method):
    if method == "platt":
        return LogisticRegression(C=1e6, max_iter=1000).fit(_logit(p).reshape(-1, 1), y)
    if method == "isotonic":
        return IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1).fit(p, y)
    raise ValueError(method)


def apply_calibrator(method, cal, p):
    if method == "raw":
        return np.asarray(p, dtype=float)
    if method == "platt":
        return cal.predict_proba(_logit(p).reshape(-1, 1))[:, 1]
    return cal.predict(p)


def cv_calibrated(p, y, method, cv=5):
    """Calibrated probabilities obtained WITHOUT letting a row calibrate itself."""
    if method == "raw":
        return np.asarray(p, dtype=float)
    out = np.zeros(len(p))
    for tr, te in StratifiedKFold(cv, shuffle=True, random_state=RS).split(p, y):
        out[te] = apply_calibrator(method, fit_calibrator(p[tr], y[tr], method), p[te])
    return out


def threshold_table(y, p, cost_ratio):
    rows = []
    for t in np.round(np.linspace(0.02, 0.98, 97), 2):
        flag = p >= t
        tp, fp = int((flag & y).sum()), int((flag & ~y).sum())
        fn = int((~flag & y).sum())
        rows.append({"threshold": t, "tp": tp, "fp": fp, "fn": fn,
                     "recall": tp / max(tp + fn, 1), "precision": tp / max(tp + fp, 1),
                     "cost": cost_ratio * fn + fp})
    return pd.DataFrame(rows)


def at_threshold(y, p, t):
    flag = p >= t
    tp, fp, fn = int((flag & y).sum()), int((flag & ~y).sum()), int((~flag & y).sum())
    prec, rec = tp / max(tp + fp, 1), tp / max(tp + fn, 1)
    return {"threshold": float(t), "recall": rec, "precision": prec,
            "f1": 2 * prec * rec / max(prec + rec, 1e-9),
            "flagged_share": float(flag.mean()), "tp": tp, "fp": fp, "fn": fn}


def compare_groups(frame, a, b):
    """Standardised difference in feature means between two groups of students."""
    cols = [c for c in BINARY + NUMERIC if c in frame.columns]
    sd = frame[cols].std().replace(0, np.nan)
    out = pd.DataFrame({"mean_group_a": frame.loc[a, cols].mean(),
                        "mean_group_b": frame.loc[b, cols].mean()})
    out["std_diff"] = (out.mean_group_a - out.mean_group_b) / sd
    return out.reindex(out.std_diff.abs().sort_values(ascending=False).index)


def subgroup_table(frame, y, flag):
    groups = {c: frame[c] for c in ["Gender", "International", "Educational special needs",
                                    "Scholarship holder", "Daytime/evening attendance",
                                    "Debtor"] if c in frame.columns}
    if "Age at enrollment" in frame.columns:
        groups["Age group"] = pd.cut(frame["Age at enrollment"], [0, 20, 25, 200],
                                     labels=["<=20", "21-25", ">25"]).astype(object)
    rows = []
    for name, s in groups.items():
        for val in sorted(pd.unique(s.dropna()), key=str):
            m = (s == val).to_numpy()
            pos, neg = y[m], ~y[m]
            rows.append({"feature": name, "value": val, "n": int(m.sum()),
                         "dropout_rate": float(pos.mean()),
                         "recall_on_dropouts": float(flag[m][pos].mean()) if pos.any() else np.nan,
                         "false_alarm_rate": float(flag[m][neg].mean()) if neg.any() else np.nan,
                         "flagged_share": float(flag[m].mean())})
    return pd.DataFrame(rows)


def _calibration_plot(ax, y, p, label):
    frac, mean_p = calibration_curve(y, p, n_bins=10, strategy="quantile")
    ax.plot(mean_p, frac, "o-", label=label)


# ------------------------------------------------------------- step A
def analyze(model, tag, cost_ratio, data, cv=5):
    early = tag == "early"
    FIGS.mkdir(parents=True, exist_ok=True)
    MODELS.mkdir(exist_ok=True)
    oof = pd.read_csv(REPORTS / f"oof_{model}_{tag}.csv", index_col=0)
    y = (oof["y_true"].to_numpy() == 0)          # True = Dropout
    p_raw = oof["p_dropout"].to_numpy()

    # 1) three-class view
    pred = oof[PROBA_COLS].to_numpy().argmax(1)
    report = classification_report(oof["y_true"], pred, target_names=CLASS_ORDER, digits=3)
    cm = confusion_matrix(oof["y_true"], pred)
    print("3-class report (out-of-fold, training data only):\n", report)
    print("confusion matrix (rows = true, cols = predicted):\n", cm)

    # 2) calibration. The model was trained with balanced class weights, so its
    #    raw p_dropout over-states risk. Compare raw vs Platt vs isotonic.
    scores = {}
    for m in ["raw", "platt", "isotonic"]:
        p = cv_calibrated(p_raw, y, m, cv)
        scores[m] = {"brier": float(brier_score_loss(y, p)), "ece": ece(y, p)}
    print("\ncalibration (lower is better):")
    print(pd.DataFrame(scores).T.round(4))
    method = min(scores, key=lambda m: scores[m]["brier"])
    p_cal = cv_calibrated(p_raw, y, method, cv)
    cal_obj = None if method == "raw" else fit_calibrator(p_raw, y, method)
    joblib.dump({"method": method, "calibrator": cal_obj},
                MODELS / f"calibrator_{model}_{tag}.joblib")
    print("chosen calibration method:", method)

    # 3) cost-based threshold on the calibrated dropout probability
    table = threshold_table(y, p_cal, cost_ratio)
    best = table.loc[table["cost"].idxmin()]
    t = float(best["threshold"])
    theory = 1 / (1 + cost_ratio)
    table.to_csv(REPORTS / f"threshold_table_{model}_{tag}.csv", index=False)
    sens = {r: float(threshold_table(y, p_cal, r).pipe(lambda d: d.loc[d["cost"].idxmin(), "threshold"]))
            for r in [2, 3, 5, 10]}
    chosen, default = at_threshold(y, p_cal, t), at_threshold(y, p_cal, 0.5)
    print(f"\ncost ratio {cost_ratio}:1 -> threshold {t:.2f} "
          f"(textbook value for perfectly calibrated risk: {theory:.2f})")
    print("at chosen threshold:", {k: round(v, 3) for k, v in chosen.items()})
    print("at default 0.50    :", {k: round(v, 3) for k, v in default.items()})
    print("best threshold for other cost ratios:", sens)

    decision = {"model": model, "tag": tag, "cost_ratio": cost_ratio,
                "calibration_method": method, "calibration_scores": scores,
                "threshold": t, "textbook_threshold": theory,
                "threshold_by_cost_ratio": sens,
                "oof_at_threshold": chosen, "oof_at_0.5": default,
                "oof_dropout_roc_auc": float(roc_auc_score(y, p_cal)),
                "oof_dropout_avg_precision": float(average_precision_score(y, p_cal))}
    with open(MODELS / f"decision_{model}_{tag}.json", "w") as f:
        json.dump(decision, f, indent=2, default=float)
    (REPORTS / f"classification_report_oof_{model}_{tag}.txt").write_text(report)

    # 4) error analysis on the training data (which students are missed / wrongly flagged)
    df = load_data(data)
    X_tr, _, _, _ = make_split(df, early=early)
    frame = X_tr.loc[oof.index]
    flag = p_cal >= t
    fn_vs_tp = compare_groups(frame, (~flag & y), (flag & y))
    fp_vs_tn = compare_groups(frame, (flag & ~y), (~flag & ~y))
    fn_vs_tp.to_csv(REPORTS / f"errors_missed_vs_caught_{model}_{tag}.csv")
    fp_vs_tn.to_csv(REPORTS / f"errors_false_alarm_vs_correct_{model}_{tag}.csv")
    print(f"\nmissed dropouts: {int((~flag & y).sum())}  |  false alarms: {int((flag & ~y).sum())}")
    print("\nMissed dropouts vs caught dropouts - biggest differences:\n",
          fn_vs_tp.head(8).round(3))
    print("\nFalse alarms vs correctly-cleared students - biggest differences:\n",
          fp_vs_tn.head(8).round(3))
    sub = subgroup_table(frame, y, flag)
    sub.to_csv(REPORTS / f"subgroup_oof_{model}_{tag}.csv", index=False)
    print("\nsubgroup performance at the chosen threshold:\n", sub.round(3).to_string(index=False))

    # 5) figures
    fig, axes = plt.subplots(2, 2, figsize=(11, 9))
    axes[0, 0].imshow(cm, cmap="Blues")
    axes[0, 0].set_xticks(range(3), CLASS_ORDER); axes[0, 0].set_yticks(range(3), CLASS_ORDER)
    for i in range(3):
        for j in range(3):
            axes[0, 0].text(j, i, cm[i, j], ha="center", va="center")
    axes[0, 0].set(title="3-class confusion matrix (out-of-fold)", xlabel="Predicted", ylabel="True")
    prec, rec, _ = precision_recall_curve(y, p_cal)
    axes[0, 1].plot(rec, prec)
    axes[0, 1].plot(chosen["recall"], chosen["precision"], "ro", label=f"threshold {t:.2f}")
    axes[0, 1].set(title="Dropout precision-recall", xlabel="Recall", ylabel="Precision")
    axes[0, 1].legend()
    axes[1, 0].plot(table["threshold"], table["cost"])
    axes[1, 0].axvline(t, color="r", ls="--")
    axes[1, 0].set(title=f"Expected cost vs threshold (miss = {cost_ratio} x false alarm)",
                   xlabel="Threshold on dropout probability", ylabel="Cost")
    _calibration_plot(axes[1, 1], y, p_raw, "raw model output")
    if method != "raw":
        _calibration_plot(axes[1, 1], y, p_cal, f"calibrated ({method})")
    axes[1, 1].plot([0, 1], [0, 1], "k:", label="perfect")
    axes[1, 1].set(title="Calibration (out-of-fold)", xlabel="Predicted dropout probability",
                   ylabel="Observed dropout rate")
    axes[1, 1].legend()
    fig.tight_layout()
    fig.savefig(FIGS / f"phase5_{model}_{tag}.png", dpi=150)
    print(f"\nsaved figure reports/figures/phase5_{model}_{tag}.png and decision file "
          f"models/decision_{model}_{tag}.json")


# ------------------------------------------------------------- step B
def final(model, tag, data):
    early = tag == "early"
    FIGS.mkdir(parents=True, exist_ok=True)
    decision = json.load(open(MODELS / f"decision_{model}_{tag}.json"))
    saved = joblib.load(MODELS / f"calibrator_{model}_{tag}.joblib")
    pipe = joblib.load(MODELS / f"{model}_{tag}.joblib")
    df = load_data(data)
    _, X_te, _, y_te = make_split(df, early=early)

    proba = pipe.predict_proba(X_te)
    y = (y_te.to_numpy() == 0)
    p_raw = proba[:, 0]
    p_cal = apply_calibrator(saved["method"], saved["calibrator"], p_raw)
    t, cr = decision["threshold"], decision["cost_ratio"]
    pred = proba.argmax(1)

    res = {"model": model, "tag": tag, "n_test": int(len(y)),
           "three_class_macro_f1": float(f1_score(y_te, pred, average="macro")),
           "three_class_accuracy": float((pred == y_te.to_numpy()).mean()),
           "dropout_roc_auc": float(roc_auc_score(y, p_cal)),
           "dropout_avg_precision": float(average_precision_score(y, p_cal)),
           "brier_raw": float(brier_score_loss(y, p_raw)),
           "brier_calibrated": float(brier_score_loss(y, p_cal)),
           "ece_raw": ece(y, p_raw), "ece_calibrated": ece(y, p_cal),
           "at_chosen_threshold": at_threshold(y, p_cal, t),
           "at_0.5": at_threshold(y, p_cal, 0.5)}
    c = res["at_chosen_threshold"]
    res["expected_cost_at_threshold"] = cr * c["fn"] + c["fp"]
    res["cost_if_nobody_flagged"] = cr * int(y.sum())
    cm = confusion_matrix(y_te, pred)
    print("TEST RESULTS (used once):")
    print(json.dumps(res, indent=2, default=float))
    print("\n3-class report:\n", classification_report(y_te, pred, target_names=CLASS_ORDER, digits=3))
    print("confusion matrix:\n", cm)
    sub = subgroup_table(X_te, y, p_cal >= t)
    sub.to_csv(REPORTS / f"subgroup_test_{model}_{tag}.csv", index=False)
    print("\nsubgroup performance on test:\n", sub.round(3).to_string(index=False))
    with open(REPORTS / f"test_results_{model}_{tag}.json", "w") as f:
        json.dump(res, f, indent=2, default=float)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    axes[0].imshow(cm, cmap="Blues")
    axes[0].set_xticks(range(3), CLASS_ORDER); axes[0].set_yticks(range(3), CLASS_ORDER)
    for i in range(3):
        for j in range(3):
            axes[0].text(j, i, cm[i, j], ha="center", va="center")
    axes[0].set(title="Test confusion matrix", xlabel="Predicted", ylabel="True")
    _calibration_plot(axes[1], y, p_raw, "raw")
    _calibration_plot(axes[1], y, p_cal, "calibrated")
    axes[1].plot([0, 1], [0, 1], "k:")
    axes[1].set(title="Test calibration", xlabel="Predicted dropout probability",
                ylabel="Observed dropout rate")
    axes[1].legend()
    fig.tight_layout()
    fig.savefig(FIGS / f"test_{model}_{tag}.png", dpi=150)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("command", choices=["analyze", "final"])
    p.add_argument("--model", default="xgboost")
    p.add_argument("--tag", choices=["full", "early"], default="full")
    p.add_argument("--data", default="data/data.csv")
    p.add_argument("--cost-ratio", type=float, default=5.0)
    p.add_argument("--yes", action="store_true",
                   help="final: confirm you want to use the test set")
    a = p.parse_args()
    if a.command == "analyze":
        analyze(a.model, a.tag, a.cost_ratio, a.data)
    else:
        if not a.yes:
            raise SystemExit("`final` uses the test set. Re-run with --yes when all "
                             "decisions (model, cost ratio, threshold) are final.")
        final(a.model, a.tag, a.data)


if __name__ == "__main__":
    main()
