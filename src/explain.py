"""Phase 6 - SHAP explanations. Put this file in src/explain.py.

    python -m src.explain --model xgboost --tag full
    python -m src.explain --model xgboost --tag early

Explains the saved model on the TEST students (this changes no decision; it only
describes the model). SHAP values are computed on the one-hot-expanded features
and then SUMMED back to the original columns (e.g. all "Course_..." columns ->
"Course"), so the plots show 36 readable features instead of 150+ dummies.

Sign convention: a positive SHAP value pushes the student TOWARDS Dropout.
Units: log-odds of the model's raw Dropout score (before calibration).

Outputs (reports/ and reports/figures/):
    shap_importance_<model>_<tag>.csv, shap_global_bar_*.png, shap_summary_*.png,
    shap_dependence_*.png, shap_local_cases_*.png, shap_local_cases_*.md
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
import shap

from src.evaluate import apply_calibrator
from src.pipeline import BINARY, NOMINAL, NUMERIC, load_data, make_split

REPORTS, MODELS = Path("reports"), Path("models")
FIGS = REPORTS / "figures"
HIGH_TIER = 0.50   # risk >= 0.50 -> High; between the cost threshold and 0.50 -> Medium


def owner_map(transformed_cols):
    """Map each model input column back to the original feature it came from."""
    owners = {}
    for col in transformed_cols:
        if col in NUMERIC or col in BINARY:
            owners[col] = col
        else:
            owners[col] = next((c for c in NOMINAL if col.startswith(c + "_")), col)
    return owners


def shap_all_classes(model, X_t):
    """Return SHAP values shaped (n_rows, n_features, n_classes) and the base values."""
    explainer = shap.TreeExplainer(model)
    sv = explainer.shap_values(X_t)
    if isinstance(sv, list):                 # older shap versions: list of per-class arrays
        sv = np.stack(sv, axis=-1)
    sv = np.asarray(sv)
    if sv.ndim != 3:
        raise SystemExit(f"Unexpected SHAP output shape {sv.shape}; expected "
                         "(rows, features, classes). Paste this error to the assistant.")
    return sv, np.atleast_1d(explainer.expected_value)


def check_additivity(sv, base, proba):
    """Base value + sum of SHAP values must rebuild the model's own prediction."""
    margin = base + sv.sum(axis=1)
    soft = np.exp(margin - margin.max(1, keepdims=True))
    soft /= soft.sum(1, keepdims=True)
    err_logodds = np.abs(soft - proba).max()
    err_prob = np.abs(margin - proba).max()
    if err_logodds < 1e-3:
        print(f"additivity check passed (log-odds units, max error {err_logodds:.1e})")
        return "log-odds"
    if err_prob < 1e-3:
        print(f"additivity check passed (probability units, max error {err_prob:.1e})")
        return "probability"
    print(f"WARNING: additivity check failed (errors {err_logodds:.3f} / {err_prob:.3f}). "
          "Do not trust the plots until this is understood.")
    return "log-odds"


def fmt_value(v):
    return f"{v:g}" if float(v).is_integer() else f"{v:.1f}"


def tier(p, t):
    return "High" if p >= HIGH_TIER else ("Medium" if p >= t else "Low")


def pick_typical(mask, p):
    """Index (position) of the case whose risk is closest to the group's median."""
    idx = np.flatnonzero(mask)
    if len(idx) == 0:
        return None
    return int(idx[np.argmin(np.abs(p[idx] - np.median(p[idx])))])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="xgboost")
    ap.add_argument("--tag", choices=["full", "early"], default="full")
    ap.add_argument("--data", default="data/data.csv")
    a = ap.parse_args()
    FIGS.mkdir(parents=True, exist_ok=True)
    early = a.tag == "early"
    name = f"{a.model}_{a.tag}"

    decision = json.load(open(MODELS / f"decision_{name}.json"))
    saved = joblib.load(MODELS / f"calibrator_{name}.joblib")
    pipe = joblib.load(MODELS / f"{name}.joblib")
    t = decision["threshold"]

    df = load_data(a.data)
    _, X_te, _, y_te = make_split(df, early=early)
    y_drop = (y_te.to_numpy() == 0)
    proba = pipe.predict_proba(X_te)
    p_cal = apply_calibrator(saved["method"], saved["calibrator"], proba[:, 0])

    X_t = pipe.named_steps["prep"].transform(X_te)
    sv, base = shap_all_classes(pipe.named_steps["model"], X_t)
    units = check_additivity(sv, base, proba)

    # ---- sum one-hot columns back to the original features (class 0 = Dropout)
    owners = owner_map(list(X_t.columns))
    feats = list(dict.fromkeys(owners.values()))
    pos = {f: [i for i, c in enumerate(X_t.columns) if owners[c] == f] for f in feats}
    G = np.column_stack([sv[:, pos[f], 0].sum(axis=1) for f in feats])
    base0 = float(base[0])
    Xo = X_te[feats]                              # original values, for display

    # ---- global importance + direction
    imp = pd.DataFrame({"feature": feats, "mean_abs_shap": np.abs(G).mean(0)})
    imp["share_of_total"] = imp["mean_abs_shap"] / imp["mean_abs_shap"].sum()
    dirs = []
    for j, f in enumerate(feats):
        x = Xo[f].to_numpy(dtype=float)
        if f in NOMINAL or x.std() == 0 or G[:, j].std() == 0:
            dirs.append("n/a (category codes)" if f in NOMINAL else "n/a")
        else:
            dirs.append("higher value -> higher risk" if np.corrcoef(x, G[:, j])[0, 1] > 0
                        else "higher value -> lower risk")
    imp["direction"] = dirs
    imp = imp.sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)
    imp.to_csv(REPORTS / f"shap_importance_{name}.csv", index=False)
    print("\nTop 12 features by mean |SHAP|:\n", imp.head(12).round(3).to_string(index=False))

    top = imp.head(15)
    plt.figure(figsize=(8, 6))
    plt.barh(top["feature"][::-1], top["mean_abs_shap"][::-1], color="#1F3864")
    plt.xlabel(f"Mean |SHAP value| ({units}, Dropout class)")
    plt.title(f"Global feature importance ({a.model}, {a.tag})")
    plt.tight_layout(); plt.savefig(FIGS / f"shap_global_bar_{name}.png", dpi=150); plt.close()

    order = [feats.index(f) for f in top["feature"]]
    plt.figure()
    shap.summary_plot(G[:, order], Xo[top["feature"].tolist()].to_numpy(dtype=float),
                      feature_names=top["feature"].tolist(), max_display=15, show=False)
    plt.tight_layout(); plt.savefig(FIGS / f"shap_summary_{name}.png", dpi=150); plt.close()

    # ---- dependence plots for the top 4 non-category features
    dep = [f for f in imp["feature"] if f not in NOMINAL][:4]
    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    rng = np.random.default_rng(0)
    for ax, f in zip(axes.ravel(), dep):
        x = Xo[f].to_numpy(dtype=float)
        if len(np.unique(x)) <= 3:
            x = x + rng.normal(0, 0.03, len(x))
        ax.scatter(x, G[:, feats.index(f)], s=6, alpha=0.5)
        ax.axhline(0, color="k", lw=0.8)
        ax.set(title=f, xlabel="feature value", ylabel="SHAP (towards Dropout)")
    fig.tight_layout(); fig.savefig(FIGS / f"shap_dependence_{name}.png", dpi=150); plt.close(fig)

    # ---- four typical local cases from the test set
    cases = [
        ("Caught dropout (High risk)", pick_typical(y_drop & (p_cal >= HIGH_TIER), p_cal)),
        ("MISSED dropout (flagged Low)", pick_typical(y_drop & (p_cal < t), p_cal)),
        ("False alarm (not a dropout, flagged)", pick_typical(~y_drop & (p_cal >= t), p_cal)),
        ("Correctly cleared (Low risk)", pick_typical(~y_drop & (p_cal < t), p_cal)),
    ]
    md = [f"# Local SHAP explanations - {a.model} ({a.tag})\n",
          "Typical test cases: for each group, the student whose risk is closest to the "
          "group's median. Positive = pushes towards Dropout.\n"]
    fig, axes = plt.subplots(2, 2, figsize=(14, 8))
    for ax, (label, i) in zip(axes.ravel(), cases):
        if i is None:
            ax.set_title(f"{label}\n(no such student in the test set)"); ax.axis("off")
            continue
        contrib = pd.Series(G[i], index=feats)
        order_i = contrib.abs().sort_values(ascending=False).index
        shown, rest = order_i[:8], order_i[8:]
        vals = list(contrib[shown]) + [contrib[rest].sum()]
        labels = [f"{f} = {fmt_value(Xo[f].iloc[i])}" for f in shown] + [f"{len(rest)} other features"]
        ax.barh(labels[::-1], vals[::-1], color=["#C0392B" if v > 0 else "#2E86C1" for v in vals[::-1]])
        ax.axvline(0, color="k", lw=0.8)
        ax.set_title(f"{label}\nactual: {'Dropout' if y_drop[i] else 'Not dropout'} | "
                     f"risk {p_cal[i]:.0%} ({tier(p_cal[i], t)})", fontsize=10)
        ax.set_xlabel(f"SHAP ({units})")
        up = [(f, contrib[f]) for f in order_i if contrib[f] > 0][:4]
        down = [(f, contrib[f]) for f in order_i if contrib[f] < 0][:4]
        md += [f"\n## {label}\n",
               f"- Actual outcome: **{'Dropout' if y_drop[i] else 'Not a dropout'}**; "
               f"calibrated dropout risk **{p_cal[i]:.0%}**; tier **{tier(p_cal[i], t)}**.",
               "- Pushing risk UP: " + ("; ".join(f"{f} = {fmt_value(Xo[f].iloc[i])} ({v:+.2f})" for f, v in up) or "none"),
               "- Pushing risk DOWN: " + ("; ".join(f"{f} = {fmt_value(Xo[f].iloc[i])} ({v:+.2f})" for f, v in down) or "none"),
               "- Interpretation (write this in your own words): _TODO_"]
    fig.tight_layout(); fig.savefig(FIGS / f"shap_local_cases_{name}.png", dpi=150); plt.close(fig)
    (REPORTS / f"shap_local_cases_{name}.md").write_text("\n".join(md) + "\n")
    print("\n" + "\n".join(md))
    print(f"\nsaved figures to reports/figures/ (shap_*_{name}.png) and "
          f"reports/shap_local_cases_{name}.md, reports/shap_importance_{name}.csv")


if __name__ == "__main__":
    main()
