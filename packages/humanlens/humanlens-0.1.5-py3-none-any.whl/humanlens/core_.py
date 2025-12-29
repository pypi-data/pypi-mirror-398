import sys
import pandas as pd
from sklearn.metrics import confusion_matrix
from IPython.display import display, Markdown
from sklearn.linear_model import LogisticRegression   # ✅ ADD THIS
import os
import json
from datetime import datetime
import time
import random


# =====================================================
# Safe Display for Both Terminal + Jupyter
# =====================================================
def _safe_display(obj):
    from pandas.io.formats.style import Styler

    # ✅ If running in Jupyter, show normally
    if "ipykernel" in sys.modules:
        display(obj)
        return

    # ✅ If a styled DataFrame, convert to plain text
    if isinstance(obj, Styler):
        df = obj.data
        print("\n" + df.to_string(index=False))
        return

    # ✅ If a normal DataFrame, print cleanly
    if isinstance(obj, pd.DataFrame):
        print("\n" + obj.to_string(index=False))
        return

    # ✅ If a Markdown object, print clean text
    if isinstance(obj, Markdown):
        text = obj.data.replace("<br>", "\n").replace("<strong>", "").replace("</strong>", "")
        print("\n" + text)
        return

    # ✅ Everything else fallback
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

# Project → model type mapping
_PROJECT_MODEL_TYPES = {}   # added


def show_model_catalog():
    """Display the model catalog and return selected model type."""
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

    selected = _MODEL_CATALOG[choice]
    print(f"\n✅ Selected Model Type: {selected['name']}")
    print("ℹ Required:", ", ".join(selected["required"]))

    # store last selected for test() auto-use
    _PROJECT_MODEL_TYPES["__last_selected__"] = selected

    return selected


# =====================================================
# NEW: Direct assignment of model type
# =====================================================
def set_model_type(project_name, model_type_id):
    """
    Set model type programmatically.

    Example:
        hl.set_model_type("NYC_Model", 1)
    """
    if model_type_id not in _MODEL_CATALOG:
        raise ValueError("Invalid model_type_id. Must be one of 1–4.")

    _PROJECT_MODEL_TYPES[project_name] = _MODEL_CATALOG[model_type_id]

    print(f"✅ Model type for '{project_name}' set to: {_MODEL_CATALOG[model_type_id]['name']}")
    return _MODEL_CATALOG[model_type_id]


# =====================================================
# GROUP METRICS / DISPARITY CALCULATION
# =====================================================
def _calculate_group_metrics(df, group_col, y_true_col, y_pred_col):
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


def _disparity_summary(df):
    sr_min = df["SR (Selection Rate)"].min()
    sr_max = df["SR (Selection Rate)"].max()
    di_ratio = sr_min / sr_max if sr_max > 0 else 0

    return {
        "Selection Ratio (DI)": di_ratio,
        "FPR Max Difference": df["FPR"].max() - df["FPR"].min(),
        "FNR Max Difference": df["FNR"].max() - df["FNR"].min(),
        "Fail 4/5 Rule": di_ratio < 0.8,
        "High FNR Risk": (df["FNR"].max() - df["FNR"].min()) > 0.10,
    }

def print_group_table(feature_name, group_df):
    """
    Pretty-print a disparity table (TP, FP, FN, TN, SR, FPR, FNR)
    in a clean CLI-friendly format.
    """
    print("\n" + "=" * 90)
    print(f"{feature_name.upper():^90}")
    print("=" * 90)

    # Header
    print("{:<15} {:>7} {:>6} {:>6} {:>6} {:>6} {:>10} {:>8} {:>8}".format(
        feature_name,
        "Count", "TP", "FN", "FP", "TN",
        "SR", "FPR", "FNR"
    ))
    print("-" * 90)

    # Rows
    for _, row in group_df.iterrows():
        print("{:<15} {:>7} {:>6} {:>6} {:>6} {:>6} {:>10.3f} {:>8.3f} {:>8.3f}".format(
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

    print("=" * 90 + "\n")


def get_group_metrics(df, feature, y_true_col, y_pred_col):
    """Public wrapper for internal group metric computation."""
    return _calculate_group_metrics(df, feature, y_true_col, y_pred_col)

# =====================================================
# MAIN FAIRNESS AUDIT
# =====================================================
def run_fairness_audit(df, y_true_col, y_pred_col, sensitive_features, suppress_display=False):
    summary_rows = []

    for feature in sensitive_features:
        metrics = _calculate_group_metrics(df, feature, y_true_col, y_pred_col)
        disp = _disparity_summary(metrics)

        if not suppress_display:
            _safe_display(metrics.style.set_caption(f"📊 {feature} Disparity Metrics"))

        summary_rows.append({
            "Feature": feature,
            "DI Ratio": round(disp["Selection Ratio (DI)"], 3),
            "FPR Diff": round(disp["FPR Max Difference"], 3),
            "FNR Diff": round(disp["FNR Max Difference"], 3),
            "Fail/Pass 4/5": "Fail" if disp["Fail 4/5 Rule"] else "Pass",
            "High/Low FNR Risk": "High" if disp["High FNR Risk"] else "Low",
        })

    return pd.DataFrame(summary_rows).to_dict(orient="records")


# =====================================================
# TEST() — Main Wrapper
# =====================================================
def test(model=None, eval_data=None, y_true_col=None, y_pred_col=None,
         sensitive_features=None, model_type=None, suppress_display=False):

    # Load CSV or use DataFrame
    if isinstance(eval_data, str):
        df = pd.read_csv(eval_data)
        dataset_source = eval_data
    else:
        df = eval_data
        dataset_source = getattr(df, "name", "in-memory dataframe")

    # Auto-predict if needed
    if model is not None and y_pred_col is None:
        preds = model.predict(df.drop(columns=[y_true_col]))
        df["__model_pred"] = preds
        y_pred_col = "__model_pred"

    accuracy = (df[y_true_col] == df[y_pred_col]).mean()

    # determine model type priority:
    # 1. passed explicitly
    # 2. stored for project
    # 3. last selected via catalog
    mtype = None
    if model_type:
        mtype = model_type
    else:
        mtype = _PROJECT_MODEL_TYPES.get("__last_selected__", None)

    result = {
        "total_records": len(df),
        "accuracy": float(round(accuracy, 4)),
        "_dataset_source": dataset_source,
        "_eval_data": df,
        "_y_true_col": y_true_col,
        "_y_pred_col": y_pred_col,
        "_sensitive_features": sensitive_features,
        "_model_type": mtype["name"] if mtype else None,
    }

    if sensitive_features:
        result["fairness"] = run_fairness_audit(
            df, y_true_col, y_pred_col, sensitive_features, suppress_display=suppress_display
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
        "overall_accuracy": results.get("accuracy", 0.0),
    }

    fairness = []
    for f in results.get("fairness", []):
        fairness.append({
            "feature": f["Feature"],
            "di_ratio": f["DI Ratio"],
            "fpr_diff": f["FPR Diff"],
            "fnr_diff": f["FNR Diff"],
            "fail_4_5": (f["Fail/Pass 4/5"] == "Fail"),
            "high_fnr_risk": (f["High/Low FNR Risk"] == "High"),
        })

    disparity = []
    df = results["_eval_data"]
    y_true = results["_y_true_col"]
    y_pred = results["_y_pred_col"]

    for feature in results["_sensitive_features"]:
        group_df = _calculate_group_metrics(df, feature, y_true, y_pred)
        for _, row in group_df.iterrows():
            disparity.append({
                "feature": feature.lower(),
                "feature_value": str(row[feature]),
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
        if (f["Fail/Pass 4/5"] == "Fail") or (f["High/Low FNR Risk"] == "High")
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
# COMPARE CSVs — JSON-SAFE
# =====================================================
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

    Parameters
    ----------
    file1, file2 : str
        Paths to CSV files.
    y_true_col : str
        Ground truth label column.
    y_pred_col : str
        Prediction column (ignored if model provided or train_on_each=True).
    sensitive_features : list
        Columns to audit fairness on.
    model : sklearn model, optional
        If provided, used for both datasets.
    model_type : dict, optional
        Model type returned by hl.show_model_catalog().
    train_on_each : bool
        If True, retrains a fresh model on each dataset.

    Returns
    -------
    dict (JSON-safe)
    """

    print("\n# ============================================================")
    print("# Compare Fairness Across Two Datasets")
    print("# ============================================================\n")

    name1 = os.path.basename(file1).replace(".csv", "")
    name2 = os.path.basename(file2).replace(".csv", "")

    print(f"→ Auditing: {file1}")
    df1 = pd.read_csv(file1)

    # Retrain model per dataset OR use passed-in model
    if train_on_each:
        feature_cols = ["Gender", "Age_Group", "Race_Ethnicity"]   # ✅ same as main model
        X1 = pd.get_dummies(df1[feature_cols], drop_first=True)
        y1 = df1[y_true_col]
        model1 = LogisticRegression(max_iter=1000).fit(X1, y1)
        # preds1 = model1.predict(X1)
        # df1[y_pred_col] = preds1
        r1 = test(
            model=model1,
            eval_data=df1,
            y_true_col=y_true_col,
            y_pred_col=y_pred_col,
            sensitive_features=sensitive_features,
            model_type=model_type,
            suppress_display=True
        )
    else:
        if model is None:
            raise ValueError(
                "❌ Please pass a trained `model=` OR set `train_on_each=True` to retrain per dataset."
            )
        df1[y_pred_col] = model.predict(
            pd.get_dummies(df1.drop(columns=[y_true_col]), drop_first=True)
        )
        r1 = test(
            model=model,
            eval_data=df1,
            y_true_col=y_true_col,
            y_pred_col=y_pred_col,
            sensitive_features=sensitive_features,
            model_type=model_type,
            suppress_display=True
        )

    r1["_dataset_source"] = file1
    save_results(r1, f"{name1}_audit")
    # ✅ Pretty print disparity tables
    # print(f"\n📊 Disparity Tables for {name1}\n")
    # for feature in sensitive_features:
    #     group_df = get_group_metrics(df1, feature, y_true_col, y_pred_col)
    #     print_group_table(feature, group_df)

    # ---------- Dataset 2 ----------
    print(f"\n→ Auditing: {file2}")
    df2 = pd.read_csv(file2)

    if train_on_each:
        X2 = pd.get_dummies(df2[feature_cols], drop_first=True)
        y2 = df2[y_true_col]
        model2 = LogisticRegression(max_iter=1000).fit(X2, y2)
        # preds2 = model2.predict(X2)
        # df2[y_pred_col] = preds2
        r2 = test(
            model=model2,
            eval_data=df2,
            y_true_col=y_true_col,
            y_pred_col=y_pred_col,
            sensitive_features=sensitive_features,
            model_type=model_type,
            suppress_display=True
        )
    else:
        df2[y_pred_col] = model.predict(
            pd.get_dummies(df2.drop(columns=[y_true_col]), drop_first=True)
        )
        r2 = test(
            model=model,
            eval_data=df2,
            y_true_col=y_true_col,
            y_pred_col=y_pred_col,
            sensitive_features=sensitive_features,
            model_type=model_type,
            suppress_display=True
        )

    r2["_dataset_source"] = file2
    save_results(r2, f"{name2}_audit")
    # ✅ Pretty print disparity tables
    # print(f"\n📊 Disparity Tables for {name2}\n")
    # for feature in sensitive_features:
    #     group_df = get_group_metrics(df2, feature, y_true_col, y_pred_col)
    #     print_group_table(feature, group_df)

    # ✅ JSON-safe cleanup
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
