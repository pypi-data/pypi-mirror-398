# humanlens/core.py
# =====================================================
# HumanLens core engine (Binary + Multi-Class + Regression)
# =====================================================

import sys
import os
import json
import time
import random
from datetime import datetime

import pandas as pd
from IPython.display import display, Markdown

from sklearn.metrics import (
    confusion_matrix,
    precision_recall_fscore_support,
    accuracy_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)


# =====================================================
# Safe Display for Both Terminal + Jupyter
# =====================================================
def _safe_display(obj):
    from pandas.io.formats.style import Styler

    if "ipykernel" in sys.modules:
        display(obj)
        return

    if isinstance(obj, Styler):
        df = obj.data
        print("\n" + df.to_string(index=False))
        return

    if isinstance(obj, pd.DataFrame):
        print("\n" + obj.to_string(index=False))
        return

    if isinstance(obj, Markdown):
        text = obj.data.replace("<br>", "\n").replace("<strong>", "").replace("</strong>", "")
        print("\n" + text)
        return

    print(obj)


# =====================================================
# MODEL CATALOG + PROJECT MODEL TYPE STORAGE
# =====================================================
_MODEL_CATALOG = {
    1: {
        "name": "Binary Classification",
        "desc": "Two-class prediction (approve/reject, pass/fail)",
        "use_cases": "Hiring, loan approval, fraud detection",
        "required": ["ground_truth", "predictions", "demographics"],
    },
    2: {
        "name": "Multi-Class Classification",
        "desc": "Prediction with 3+ categories",
        "use_cases": "Job role classification, risk tiers",
        "required": ["ground_truth", "predictions", "demographics"],
    },
    3: {
        "name": "Regression",
        "desc": "Continuous value prediction",
        "use_cases": "Credit scoring, salary prediction",
        "required": ["ground_truth", "predictions", "demographics"],
    },
    4: {
        "name": "RAG-Based LLM",
        "desc": "Retrieval-Augmented Generation",
        "use_cases": "Chatbots, Q&A systems",
        "required": ["questions", "answers", "contexts"],
    },
}

_PROJECT_MODEL_TYPES = {}  # project → model type mapping


def show_model_catalog():
    """Display the model catalog and return selected model type dict (includes 'id')."""
    border = "═" * 66
    print(f"\n╔{border}╗")
    print(f"║{'HumanLens Model Type Catalog'.center(66)}║")
    print(f"╠{border}╣")

    for mid, info in _MODEL_CATALOG.items():
        print(f"║  {mid}. {info['name']:<58}║")
        print(f"║     • {info['desc']:<58}║")
        print(f"║     • Use cases : {info['use_cases']:<46}║")
        print(f"║     • Required  : {', '.join(info['required']):<40}║")
        print(f"║{'':66}║")

    print(f"╚{border}╝\n")

    try:
        choice = int(input("Select model type (1–4): ").strip())
    except Exception:
        print("⚠️ Invalid input.")
        return None

    if choice not in _MODEL_CATALOG:
        print("⚠️ Invalid choice.")
        return None

    selected = dict(_MODEL_CATALOG[choice])
    selected["id"] = choice

    print(f"\n✅ Selected Model Type: {selected['name']}")
    print("ℹ Required:", ", ".join(selected["required"]))

    _PROJECT_MODEL_TYPES["__last_selected__"] = selected
    return selected


def set_model_type(project_name, model_type_id):
    """Set model type programmatically for a project."""
    if model_type_id not in _MODEL_CATALOG:
        raise ValueError("Invalid model_type_id. Must be one of 1–4.")

    m = dict(_MODEL_CATALOG[model_type_id])
    m["id"] = model_type_id
    _PROJECT_MODEL_TYPES[project_name] = m
    print(f"✅ Model type for '{project_name}' set to: {m['name']}")
    return m


# =====================================================
# HELPERS: Identify model type
# =====================================================
def _is_binary(model_type):
    return bool(model_type and (model_type.get("id") == 1 or model_type.get("name") == "Binary Classification"))


def _is_multiclass(model_type):
    return bool(model_type and (model_type.get("id") == 2 or model_type.get("name") == "Multi-Class Classification"))


def _is_regression(model_type):
    return bool(model_type and (model_type.get("id") == 3 or model_type.get("name") == "Regression"))


# =====================================================
# BINARY GROUP METRICS / DISPARITY
# =====================================================
def _calculate_group_metrics_binary(df, group_col, y_true_col, y_pred_col):
    rows = []
    for group, subset in df.groupby(group_col):
        y_true = subset[y_true_col]
        y_pred = subset[y_pred_col]

        tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
        total = len(subset)

        sr = tp / total if total else 0
        fpr = fp / (fp + tn) if (fp + tn) else 0
        fnr = fn / (fn + tp) if (fn + tp) else 0

        rows.append({
            group_col: group,
            "Count": total,
            "TP": tp,
            "FN": fn,
            "FP": fp,
            "TN": tn,
            "SR (Selection Rate)": round(sr, 3),
            "FPR": round(fpr, 3),
            "FNR": round(fnr, 3),
        })
    return pd.DataFrame(rows)


def _disparity_summary_binary(df_metrics):
    sr_min = df_metrics["SR (Selection Rate)"].min()
    sr_max = df_metrics["SR (Selection Rate)"].max()
    di_ratio = sr_min / sr_max if sr_max > 0 else 0

    return {
        "Selection Ratio (DI)": di_ratio,
        "FPR Max Difference": df_metrics["FPR"].max() - df_metrics["FPR"].min(),
        "FNR Max Difference": df_metrics["FNR"].max() - df_metrics["FNR"].min(),
        "Fail 4/5 Rule": di_ratio < 0.8,
        "High FNR Risk": (df_metrics["FNR"].max() - df_metrics["FNR"].min()) > 0.10,
    }


def print_group_table(feature_name, group_df):
    """Pretty-print a binary-style group table."""
    print("\n" + "=" * 110)
    print(f"{feature_name.upper():^110}")
    print("=" * 110)

    print("{:<18} {:>7} {:>6} {:>6} {:>6} {:>6} {:>10} {:>8} {:>8}".format(
        feature_name, "Count", "TP", "FN", "FP", "TN", "SR", "FPR", "FNR"
    ))
    print("-" * 110)

    for _, row in group_df.iterrows():
        print("{:<18} {:>7} {:>6} {:>6} {:>6} {:>6} {:>10.3f} {:>8.3f} {:>8.3f}".format(
            str(row[feature_name]),
            int(row["Count"]),
            int(row["TP"]),
            int(row["FN"]),
            int(row["FP"]),
            int(row["TN"]),
            float(row["SR (Selection Rate)"]),
            float(row["FPR"]),
            float(row["FNR"])
        ))

    print("=" * 110 + "\n")


# ✅ PUBLIC: binary
def get_group_metrics(df, feature, y_true_col, y_pred_col):
    return _calculate_group_metrics_binary(df, feature, y_true_col, y_pred_col)


# =====================================================
# MULTICLASS GROUP METRICS (OVR) + DISPARITY
# =====================================================
def _calculate_group_metrics_multiclass_ovr(df, group_col, y_true_col, y_pred_col):
    rows = []
    y_true_all = df[y_true_col].astype(str)
    y_pred_all = df[y_pred_col].astype(str)
    labels = sorted(set(y_true_all.unique()).union(set(y_pred_all.unique())))

    for c in labels:
        y_true_bin = (y_true_all == c).astype(int)
        y_pred_bin = (y_pred_all == c).astype(int)

        tmp = df[[group_col]].copy()
        tmp["_yt"] = y_true_bin.values
        tmp["_yp"] = y_pred_bin.values

        for group, subset in tmp.groupby(group_col):
            yt = subset["_yt"]
            yp = subset["_yp"]

            tn, fp, fn, tp = confusion_matrix(yt, yp, labels=[0, 1]).ravel()
            total = len(subset)

            sr = tp / total if total else 0
            tpr = tp / (tp + fn) if (tp + fn) else 0
            fpr = fp / (fp + tn) if (fp + tn) else 0
            fnr = fn / (fn + tp) if (fn + tp) else 0

            rows.append({
                group_col: group,
                "Class": c,
                "Count": total,
                "TP": tp,
                "FN": fn,
                "FP": fp,
                "TN": tn,
                "SR (Selection Rate)": round(sr, 3),
                "TPR": round(tpr, 3),
                "FPR": round(fpr, 3),
                "FNR": round(fnr, 3),
            })

    return pd.DataFrame(rows)


def _disparity_summary_multiclass(one_class_df):
    sr_min = one_class_df["SR (Selection Rate)"].min()
    sr_max = one_class_df["SR (Selection Rate)"].max()
    di_ratio = sr_min / sr_max if sr_max > 0 else 0

    return {
        "Selection Ratio (DI)": di_ratio,
        "TPR Max Difference": one_class_df["TPR"].max() - one_class_df["TPR"].min(),
        "FPR Max Difference": one_class_df["FPR"].max() - one_class_df["FPR"].min(),
        "FNR Max Difference": one_class_df["FNR"].max() - one_class_df["FNR"].min(),
        "Fail 4/5 Rule": di_ratio < 0.8,
        "High FNR Risk": (one_class_df["FNR"].max() - one_class_df["FNR"].min()) > 0.10,
    }


# ✅ PUBLIC: multiclass OVR
def get_group_metrics_multiclass_ovr(df, feature, y_true_col, y_pred_col):
    return _calculate_group_metrics_multiclass_ovr(df, feature, y_true_col, y_pred_col)


# =====================================================
# REGRESSION GROUP METRICS + DISPARITY
# =====================================================
def _calculate_group_metrics_regression(df, group_col, y_true_col, y_pred_col):
    rows = []
    for group, subset in df.groupby(group_col):
        y_true = pd.to_numeric(subset[y_true_col], errors="coerce")
        y_pred = pd.to_numeric(subset[y_pred_col], errors="coerce")

        m = pd.DataFrame({"y_true": y_true, "y_pred": y_pred}).dropna()
        yt = m["y_true"]
        yp = m["y_pred"]

        if len(m) == 0:
            rows.append({
                group_col: group,
                "Count": 0,
                "Mean y_true": None,
                "Mean y_pred": None,
                "Mean Error (pred-true)": None,
                "MAE": None,
                "RMSE": None,
            })
            continue

        err = (yp - yt)
        mae = float(mean_absolute_error(yt, yp))
        rmse = float(mean_squared_error(yt, yp) ** 0.5)

        rows.append({
            group_col: group,
            "Count": int(len(m)),
            "Mean y_true": float(yt.mean()),
            "Mean y_pred": float(yp.mean()),
            "Mean Error (pred-true)": float(err.mean()),
            "MAE": round(mae, 6),
            "RMSE": round(rmse, 6),
        })

    return pd.DataFrame(rows)


def _disparity_summary_regression(group_df):
    def _spread(col):
        s = pd.to_numeric(group_df[col], errors="coerce").dropna()
        return float(s.max() - s.min()) if len(s) else 0.0

    bias_spread = _spread("Mean Error (pred-true)")

    return {
        "MAE Max Difference": _spread("MAE"),
        "RMSE Max Difference": _spread("RMSE"),
        "Mean Error Max Difference": bias_spread,
        "High MAE Spread": _spread("MAE") > 0.10,
        "High Bias Spread": abs(bias_spread) > 0.10,
    }


# ✅ PUBLIC: regression per-group tables (THIS fixes your ImportError)
def get_group_metrics_regression(df, feature, y_true_col, y_pred_col):
    return _calculate_group_metrics_regression(df, feature, y_true_col, y_pred_col)


# =====================================================
# MAIN FAIRNESS AUDIT (Binary vs Multiclass vs Regression)
# =====================================================
def run_fairness_audit(df, y_true_col, y_pred_col, sensitive_features, suppress_display=False, model_type=None):
    summary_rows = []

    is_bin = _is_binary(model_type)
    is_mc = _is_multiclass(model_type)
    is_reg = _is_regression(model_type)

    for feature in sensitive_features:
        if is_bin:
            metrics = _calculate_group_metrics_binary(df, feature, y_true_col, y_pred_col)
            disp = _disparity_summary_binary(metrics)

            if not suppress_display:
                _safe_display(metrics.style.set_caption(f"📊 {feature} Disparity Metrics (Binary)"))

            summary_rows.append({
                "Feature": feature,
                "Model Type": "Binary",
                "Class": None,
                "DI Ratio": round(disp["Selection Ratio (DI)"], 3),
                "FPR Diff": round(disp["FPR Max Difference"], 3),
                "FNR Diff": round(disp["FNR Max Difference"], 3),
                "TPR Diff": None,
                "MAE Diff": None,
                "RMSE Diff": None,
                "Bias Diff": None,
                "Fail/Pass 4/5": "Fail" if disp["Fail 4/5 Rule"] else "Pass",
                "High Risk Flag": "High" if disp["High FNR Risk"] else "Low",
            })

        elif is_mc:
            metrics_all = _calculate_group_metrics_multiclass_ovr(df, feature, y_true_col, y_pred_col)

            if not suppress_display:
                _safe_display(metrics_all.style.set_caption(f"📊 {feature} Disparity Metrics (Multi-class OVR)"))

            for c in sorted(metrics_all["Class"].unique()):
                one_class = metrics_all[metrics_all["Class"] == c].copy()
                disp = _disparity_summary_multiclass(one_class)

                summary_rows.append({
                    "Feature": feature,
                    "Model Type": "Multi-Class",
                    "Class": c,
                    "DI Ratio": round(disp["Selection Ratio (DI)"], 3),
                    "FPR Diff": round(disp["FPR Max Difference"], 3),
                    "FNR Diff": round(disp["FNR Max Difference"], 3),
                    "TPR Diff": round(disp["TPR Max Difference"], 3),
                    "MAE Diff": None,
                    "RMSE Diff": None,
                    "Bias Diff": None,
                    "Fail/Pass 4/5": "Fail" if disp["Fail 4/5 Rule"] else "Pass",
                    "High Risk Flag": "High" if disp["High FNR Risk"] else "Low",
                })

        elif is_reg:
            metrics = _calculate_group_metrics_regression(df, feature, y_true_col, y_pred_col)
            disp = _disparity_summary_regression(metrics)

            if not suppress_display:
                _safe_display(metrics.style.set_caption(f"📊 {feature} Error Metrics (Regression)"))

            summary_rows.append({
                "Feature": feature,
                "Model Type": "Regression",
                "Class": None,
                "DI Ratio": None,
                "FPR Diff": None,
                "FNR Diff": None,
                "TPR Diff": None,
                "MAE Diff": round(disp["MAE Max Difference"], 6),
                "RMSE Diff": round(disp["RMSE Max Difference"], 6),
                "Bias Diff": round(disp["Mean Error Max Difference"], 6),
                "Fail/Pass 4/5": None,
                "High Risk Flag": "High" if (disp["High MAE Spread"] or disp["High Bias Spread"]) else "Low",
            })

        else:
            # default to binary-style
            metrics = _calculate_group_metrics_binary(df, feature, y_true_col, y_pred_col)
            disp = _disparity_summary_binary(metrics)
            summary_rows.append({
                "Feature": feature,
                "Model Type": "Unknown",
                "Class": None,
                "DI Ratio": round(disp["Selection Ratio (DI)"], 3),
                "FPR Diff": round(disp["FPR Max Difference"], 3),
                "FNR Diff": round(disp["FNR Max Difference"], 3),
                "TPR Diff": None,
                "MAE Diff": None,
                "RMSE Diff": None,
                "Bias Diff": None,
                "Fail/Pass 4/5": "Fail" if disp["Fail 4/5 Rule"] else "Pass",
                "High Risk Flag": "High" if disp["High FNR Risk"] else "Low",
            })

    return pd.DataFrame(summary_rows).to_dict(orient="records")


# =====================================================
# MULTICLASS PERFORMANCE PRINTING (optional)
# =====================================================
def _print_multiclass_performance(df, y_true_col, y_pred_col, labels=None):
    y_true = df[y_true_col].astype(str)
    y_pred = df[y_pred_col].astype(str)

    if labels is None:
        labels = sorted(set(y_true.unique()).union(set(y_pred.unique())))

    cm = confusion_matrix(y_true, y_pred, labels=labels)
    cm_df = pd.DataFrame(cm, index=[f"true:{l}" for l in labels], columns=[f"pred:{l}" for l in labels])

    p, r, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, average=None, zero_division=0
    )
    per_class = pd.DataFrame({"Class": labels, "Precision": p, "Recall": r, "F1": f1, "Support": support})

    macro = precision_recall_fscore_support(y_true, y_pred, average="macro", zero_division=0)
    weighted = precision_recall_fscore_support(y_true, y_pred, average="weighted", zero_division=0)

    overall = {
        "Accuracy": float(round(accuracy_score(y_true, y_pred), 4)),
        "Precision (macro)": float(round(macro[0], 4)),
        "Recall (macro)": float(round(macro[1], 4)),
        "F1 (macro)": float(round(macro[2], 4)),
        "Precision (weighted)": float(round(weighted[0], 4)),
        "Recall (weighted)": float(round(weighted[1], 4)),
        "F1 (weighted)": float(round(weighted[2], 4)),
    }

    print("\n# ===============================")
    print("# Multiclass Confusion Matrix")
    print("# ===============================")
    _safe_display(cm_df)

    print("\n# ===============================")
    print("# Per-Class Precision / Recall / F1")
    print("# ===============================")
    _safe_display(per_class)

    print("\n# ===============================")
    print("# Overall (Macro / Weighted)")
    print("# ===============================")
    _safe_display(pd.DataFrame([overall]))


def _print_regression_performance(df, y_true_col, y_pred_col):
    y_true = pd.to_numeric(df[y_true_col], errors="coerce")
    y_pred = pd.to_numeric(df[y_pred_col], errors="coerce")
    m = pd.DataFrame({"y_true": y_true, "y_pred": y_pred}).dropna()
    if len(m) == 0:
        print("\n# ===============================")
        print("# Regression Metrics")
        print("# ===============================")
        print("⚠️ No valid numeric pairs found for regression metrics.")
        return

    yt = m["y_true"]
    yp = m["y_pred"]

    mae = float(mean_absolute_error(yt, yp))
    rmse = float(mean_squared_error(yt, yp) ** 0.5)
    r2 = float(r2_score(yt, yp))

    overall = {
        "MAE": round(mae, 6),
        "RMSE": round(rmse, 6),
        "R^2": round(r2, 6),
        "N": int(len(m)),
    }

    print("\n# ===============================")
    print("# Regression Metrics")
    print("# ===============================")
    _safe_display(pd.DataFrame([overall]))


# =====================================================
# TEST() — Main Wrapper
# =====================================================
def test(model=None, eval_data=None, y_true_col=None, y_pred_col=None,
         sensitive_features=None, model_type=None, suppress_display=False):

    if isinstance(eval_data, str):
        df = pd.read_csv(eval_data)
        dataset_source = eval_data
    else:
        df = eval_data
        dataset_source = getattr(df, "name", "in-memory dataframe")

    # Auto-predict if a model is passed and y_pred_col is None
    if model is not None and y_pred_col is None:
        preds = model.predict(df.drop(columns=[y_true_col]))
        df["__model_pred"] = preds
        y_pred_col = "__model_pred"

    mtype = model_type if model_type else _PROJECT_MODEL_TYPES.get("__last_selected__", None)

    result = {
        "total_records": len(df),
        "_dataset_source": dataset_source,
        "_eval_data": df,
        "_y_true_col": y_true_col,
        "_y_pred_col": y_pred_col,
        "_sensitive_features": sensitive_features,
        "_model_type": mtype["name"] if mtype else None,
    }

    # Performance metrics by type
    if _is_regression(mtype):
        if not suppress_display:
            _print_regression_performance(df, y_true_col, y_pred_col)

        y_true = pd.to_numeric(df[y_true_col], errors="coerce")
        y_pred = pd.to_numeric(df[y_pred_col], errors="coerce")
        m = pd.DataFrame({"y_true": y_true, "y_pred": y_pred}).dropna()
        if len(m) == 0:
            result["regression"] = {"mae": None, "rmse": None, "r2": None, "n": 0}
        else:
            yt = m["y_true"]
            yp = m["y_pred"]
            result["regression"] = {
                "mae": float(round(mean_absolute_error(yt, yp), 6)),
                "rmse": float(round(mean_squared_error(yt, yp) ** 0.5, 6)),
                "r2": float(round(r2_score(yt, yp), 6)),
                "n": int(len(m)),
            }

    else:
        acc = (df[y_true_col].astype(str) == df[y_pred_col].astype(str)).mean()
        result["accuracy"] = float(round(acc, 4))

        if (not suppress_display) and _is_multiclass(mtype):
            _print_multiclass_performance(df, y_true_col, y_pred_col)

    # Fairness audit
    if sensitive_features:
        result["fairness"] = run_fairness_audit(
            df,
            y_true_col,
            y_pred_col,
            sensitive_features,
            suppress_display=suppress_display,
            model_type=mtype,
        )

    return result


# =====================================================
# SAVE RESULTS
# =====================================================
def save_results(results, path_prefix="audit"):
    metadata = {
        "dataset_source": results.get("_dataset_source"),
        "model_type": results.get("_model_type"),
        "total_records": results.get("total_records", 0),
        "overall_accuracy": results.get("accuracy", None),
        "regression": results.get("regression", None),
    }

    fairness = []
    for f in results.get("fairness", []):
        fairness.append({
            "feature": f.get("Feature"),
            "model_type": f.get("Model Type"),
            "class": f.get("Class"),
            "di_ratio": f.get("DI Ratio"),
            "tpr_diff": f.get("TPR Diff"),
            "fpr_diff": f.get("FPR Diff"),
            "fnr_diff": f.get("FNR Diff"),
            "mae_diff": f.get("MAE Diff"),
            "rmse_diff": f.get("RMSE Diff"),
            "bias_diff": f.get("Bias Diff"),
            "fail_4_5": (f.get("Fail/Pass 4/5") == "Fail") if f.get("Fail/Pass 4/5") is not None else None,
            "risk_flag": f.get("High Risk Flag"),
        })

    disparity = []
    df = results["_eval_data"]
    y_true = results["_y_true_col"]
    y_pred = results["_y_pred_col"]

    model_type_name = results.get("_model_type")
    is_mc = (model_type_name == "Multi-Class Classification")
    is_reg = (model_type_name == "Regression")

    for feature in results.get("_sensitive_features") or []:
        if is_reg:
            group_df = _calculate_group_metrics_regression(df, feature, y_true, y_pred)
            for _, row in group_df.iterrows():
                disparity.append({
                    "feature": feature.lower(),
                    "feature_value": str(row[feature]),
                    "class": None,
                    "Count": int(row["Count"]) if row["Count"] is not None else 0,
                    "Mean y_true": row.get("Mean y_true"),
                    "Mean y_pred": row.get("Mean y_pred"),
                    "Mean Error (pred-true)": row.get("Mean Error (pred-true)"),
                    "MAE": row.get("MAE"),
                    "RMSE": row.get("RMSE"),
                })
        elif is_mc:
            group_df = _calculate_group_metrics_multiclass_ovr(df, feature, y_true, y_pred)
            for _, row in group_df.iterrows():
                disparity.append({
                    "feature": feature.lower(),
                    "feature_value": str(row[feature]),
                    "class": str(row["Class"]),
                    "Count": int(row["Count"]),
                    "TP": int(row["TP"]),
                    "FN": int(row["FN"]),
                    "FP": int(row["FP"]),
                    "TN": int(row["TN"]),
                    "SR": float(row["SR (Selection Rate)"]),
                    "TPR": float(row["TPR"]),
                    "FPR": float(row["FPR"]),
                    "FNR": float(row["FNR"]),
                })
        else:
            group_df = _calculate_group_metrics_binary(df, feature, y_true, y_pred)
            for _, row in group_df.iterrows():
                disparity.append({
                    "feature": feature.lower(),
                    "feature_value": str(row[feature]),
                    "class": None,
                    "Count": int(row["Count"]),
                    "TP": int(row["TP"]),
                    "FN": int(row["FN"]),
                    "FP": int(row["FP"]),
                    "TN": int(row["TN"]),
                    "SR": float(row["SR (Selection Rate)"]),
                    "FPR": float(row["FPR"]),
                    "FNR": float(row["FNR"]),
                })

    report = {
        "metadata": metadata,
        "overall_fairness_disparity_summary": fairness,
        "disparity_metrics": disparity,
    }

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"{path_prefix}_{timestamp}.json"
    with open(path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"✅ Saved audit report → {path}")
    return report


# =====================================================
# SUBMIT FOR REVIEW (Flexible Args)
# =====================================================
def submit_for_review(*args, **kwargs):
    if len(args) == 2:
        project_name, results = args
    else:
        project_name = kwargs.get("project_name")
        results = kwargs.get("results")

    if project_name is None:
        raise ValueError("Missing required arg: project_name")
    if results is None:
        raise ValueError("Missing required arg: results")

    print("\n# ============================================================")
    print("# Submit for Governance Review")
    print("# ============================================================\n")
    print(f"Submitting project '{project_name}'...")
    time.sleep(0.8)

    steps = [
        "✓ Metrics synced",
        "✓ Compliance report generated",
        f"✓ Governance card updated for {project_name}",
    ]
    for s in steps:
        print(s)
        time.sleep(0.6)

    failures = sum(
        1 for f in results.get("fairness", [])
        if (f.get("Fail/Pass 4/5") == "Fail") or (f.get("High Risk Flag") == "High")
    )
    risk = "LOW" if failures == 0 else ("MEDIUM" if failures == 1 else "HIGH")
    project_id = f"proj_{random.randint(1000, 9999)}"

    print(f"\nRisk Level: {risk}")

    return {
        "project_name": project_name,
        "project_id": project_id,
        "risk_level": risk,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


# =====================================================
# COMPARE TWO RAW CSVs → JSON-SAFE (NO DATAFRAMES)
# =====================================================
def compare_from_raw_csv(
    file1,
    file2,
    y_true_col,
    y_pred_col,
    sensitive_features,
    model=None,
    model_type=None,
    train_on_each=False
):
    """
    Compare fairness across two CSV datasets.
    - For classification: if train_on_each=True, trains a demo logistic regression using sensitive features.
    - For regression: expects y_pred_col to already exist in the CSVs (or pass a model that can predict).
    """
    # Lazy import for demo training only (keeps core light)
    from sklearn.linear_model import LogisticRegression

    print("\n# ============================================================")
    print("# Compare Fairness Across Two Datasets")
    print("# ============================================================\n")

    name1 = os.path.basename(file1).replace(".csv", "")
    name2 = os.path.basename(file2).replace(".csv", "")

    print(f"→ Auditing: {file1}")
    df1 = pd.read_csv(file1)

    if train_on_each and not _is_regression(model_type):
        feature_cols = [c for c in ["Gender", "Age_Group", "Race_Ethnicity"] if c in df1.columns]
        if not feature_cols:
            raise ValueError("No demo feature cols found for training (Gender/Age_Group/Race_Ethnicity).")
        X1 = pd.get_dummies(df1[feature_cols], drop_first=True)
        y1 = df1[y_true_col]
        model1 = LogisticRegression(max_iter=1000).fit(X1, y1)
        df1[y_pred_col] = model1.predict(X1)
        r1 = test(
            model=None,
            eval_data=df1,
            y_true_col=y_true_col,
            y_pred_col=y_pred_col,
            sensitive_features=sensitive_features,
            model_type=model_type,
            suppress_display=True
        )
    else:
        if model is not None and y_pred_col not in df1.columns:
            df1[y_pred_col] = model.predict(pd.get_dummies(df1.drop(columns=[y_true_col]), drop_first=True))

        r1 = test(
            model=None,
            eval_data=df1,
            y_true_col=y_true_col,
            y_pred_col=y_pred_col,
            sensitive_features=sensitive_features,
            model_type=model_type,
            suppress_display=True
        )

    r1["_dataset_source"] = file1
    save_results(r1, f"{name1}_audit")

    print(f"\n→ Auditing: {file2}")
    df2 = pd.read_csv(file2)

    if train_on_each and not _is_regression(model_type):
        feature_cols = [c for c in ["Gender", "Age_Group", "Race_Ethnicity"] if c in df2.columns]
        if not feature_cols:
            raise ValueError("No demo feature cols found for training (Gender/Age_Group/Race_Ethnicity).")
        X2 = pd.get_dummies(df2[feature_cols], drop_first=True)
        y2 = df2[y_true_col]
        model2 = LogisticRegression(max_iter=1000).fit(X2, y2)
        df2[y_pred_col] = model2.predict(X2)
        r2 = test(
            model=None,
            eval_data=df2,
            y_true_col=y_true_col,
            y_pred_col=y_pred_col,
            sensitive_features=sensitive_features,
            model_type=model_type,
            suppress_display=True
        )
    else:
        if model is not None and y_pred_col not in df2.columns:
            df2[y_pred_col] = model.predict(pd.get_dummies(df2.drop(columns=[y_true_col]), drop_first=True))

        r2 = test(
            model=None,
            eval_data=df2,
            y_true_col=y_true_col,
            y_pred_col=y_pred_col,
            sensitive_features=sensitive_features,
            model_type=model_type,
            suppress_display=True
        )

    r2["_dataset_source"] = file2
    save_results(r2, f"{name2}_audit")

    def _clean(r):
        clean = {}
        for k, v in r.items():
            if isinstance(v, pd.DataFrame):
                continue
            if k == "_eval_data":
                continue
            clean[k] = v
        return clean

    return {
        name1: _clean(r1),
        name2: _clean(r2),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
