import sys
import pandas as pd
from sklearn.metrics import confusion_matrix
from IPython.display import display, Markdown
import os
import json
from datetime import datetime

def _safe_display(obj):
    """Render nicely in Jupyter, or fallback to text in terminal."""
    if "ipykernel" in sys.modules:  # running in Jupyter
        display(obj)
    else:
        # Fallback for console use
        if isinstance(obj, pd.DataFrame):
            print("\n" + obj.to_string(index=False))
        elif isinstance(obj, Markdown):
            # strip HTML tags and print clean text
            text = obj.data.replace("<br>", "\n").replace("<strong>", "").replace("</strong>", "")
            print("\n" + text)
        else:
            print(obj)

# =====================================================
# 1. Project registration
# =====================================================
_PROJECTS = {}

def register(name, purpose, jurisdiction, domain, company_api):
    """
    Register a model/project for audit.

    Returns
    -------
    dict
        Project metadata dictionary
    """
    project_info = {
        "name": name,
        "purpose": purpose,
        "jurisdiction": jurisdiction,
        "domain": domain,
        "company_api": company_api
    }
    _PROJECTS[name] = project_info
    print(f"✅ Registered project: {name}")
    return project_info

# =====================================================
# 2. Model type catalog (interactive)
# =====================================================

_MODEL_CATALOG = {
    1: {
        "name": "Binary Classification",
        "desc": "Two-class prediction (approved/rejected, pass/fail)",
        "use_cases": "Hiring, loan approval, fraud detection",
        "required": "predictions, ground_truth, demographics",
    },
    2: {
        "name": "Multi-Class Classification",
        "desc": "Multiple class prediction (3+ categories)",
        "use_cases": "Job role classification, risk tiers",
        "required": "predictions, ground_truth, demographics",
    },
    3: {
        "name": "Regression",
        "desc": "Continuous value prediction",
        "use_cases": "Credit scoring, salary prediction",
        "required": "predictions, ground_truth, demographics",
    },
    4: {
        "name": "RAG-Based LLM",
        "desc": "Retrieval-Augmented Generation systems",
        "use_cases": "Chatbots, Q&A systems, doc assistants",
        "required": "questions, answers, contexts",
    },
}

def show_model_catalog(project_info=None):
    """
    Display the model type catalog and prompt user for selection.
    Optionally set model type for a registered project.
    """
    border = "═" * 66
    print(f"╔{border}╗")
    print(f"║{'HumanLens Model Type Catalog'.center(66)}║")
    print(f"╠{border}╣")

    for mid, info in _MODEL_CATALOG.items():
        print(f"║  {mid}. {info['name']:<58}║")
        print(f"║     → {info['desc']:<58}║")
        print(f"║     → Use cases: {info['use_cases']:<46}║")
        print(f"║     → Required data: {info['required']:<42}║")
        print(f"║{'':66}║")

    print(f"╚{border}╝")

    # Prompt user input
    try:
        choice = int(input("Select model type (1-4): ").strip())
    except ValueError:
        print("⚠️  Invalid input. Please enter a number between 1 and 4.")
        return None

    if choice not in _MODEL_CATALOG:
        print("⚠️  Invalid choice. Please enter a number between 1 and 4.")
        return None

    # Set model type if project info provided
    model_info = _MODEL_CATALOG[choice]
    print(f"\n✓ Model type set: {model_info['name']}")
    print(f"ℹ Required EVAL data columns: {model_info['required']}")

    if project_info is not None:
        project_name = project_info.get("name") if isinstance(project_info, dict) else str(project_info)
        _PROJECTS[project_name]["model_type"] = model_info["name"]

    return model_info

# =====================================================
# 3. Helper functions for fairness audit
# =====================================================
def _calculate_group_metrics(df, group_col, y_true_col, y_pred_col):
    results = []
    for group, subset in df.groupby(group_col):
        y_true_g = subset[y_true_col]
        y_pred_g = subset[y_pred_col]

        labels = [0, 1]
        tn, fp, fn, tp = confusion_matrix(y_true_g, y_pred_g, labels=labels).ravel()
        total = len(subset)

        sr = tp / total if total > 0 else 0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0

        results.append({
            group_col: group,
            "Count": total,
            "TP": tp,
            "FN": fn,
            "FP": fp,
            "TN": tn,
            "SR (Selection Rate)": round(sr, 3),
            "FPR": round(fpr, 3),
            "FNR": round(fnr, 3)
        })
    return pd.DataFrame(results)


def _disparity_summary(df_metric):
    sr_min = df_metric["SR (Selection Rate)"].min()
    sr_max = df_metric["SR (Selection Rate)"].max()
    di_ratio = sr_min / sr_max if sr_max > 0 else 0
    fpr_diff = df_metric["FPR"].max() - df_metric["FPR"].min()
    fnr_diff = df_metric["FNR"].max() - df_metric["FNR"].min()
    return {
        "Lowest SR": sr_min,
        "Highest SR": sr_max,
        "Selection Ratio (DI)": di_ratio,
        "FPR Max Difference": fpr_diff,
        "FNR Max Difference": fnr_diff,
        "Fail 4/5 Rule": di_ratio < 0.8,
        "High FNR Risk": fnr_diff > 0.10
    }


def _display_risk_box(title, summary):
    di = summary["Selection Ratio (DI)"]
    fpr_diff = summary["FPR Max Difference"]
    fnr_diff = summary["FNR Max Difference"]
    fail = summary["Fail 4/5 Rule"]
    high_fnr = summary["High FNR Risk"]

    risk_html = f"""
<div style="border:2px solid red; background-color:#f8d7da; padding:15px; margin-top:10px; border-radius:5px;">
    <strong style="color:#721c24; font-size:16px;">🚨 {title} Disparity Audit</strong><br><br>
    <strong>Selection Ratio (DI):</strong> {di:.3f} 
    {'<span style="color:red; font-weight:bold;">(FAIL: &lt; 0.8)</span>' if fail else '(PASS)'}<br>
    <strong>FPR Max Diff:</strong> {fpr_diff*100:.1f}%<br>
    <strong>FNR Max Diff:</strong> {fnr_diff*100:.1f}% 
    {'<span style="color:red; font-weight:bold;">(HIGH RISK: &gt; 10%)</span>' if high_fnr else '(OK)'}
</div>
"""
    _safe_display(Markdown(risk_html))


# =====================================================
# 4. Main fairness audit
# =====================================================
def run_fairness_audit(df, y_true_col, y_pred_col, sensitive_features):
    """
    Runs fairness disparity analysis across sensitive features.
    """
    summary_rows = []

    for feature in sensitive_features:
        metrics = _calculate_group_metrics(df, feature, y_true_col, y_pred_col)
        disparity = _disparity_summary(metrics)

        _safe_display(metrics.style.set_caption(f"📊 {feature} Disparity Metrics (SR | FPR | FNR)"))
        _display_risk_box(feature, disparity)

        summary_rows.append({
            "Feature": feature,
            "DI Ratio": round(disparity["Selection Ratio (DI)"], 3),
            "FPR Diff": round(disparity["FPR Max Difference"], 3),
            "FNR Diff": round(disparity["FNR Max Difference"], 3),
            "Fail/Pass 4/5": "Fail" if disparity["Fail 4/5 Rule"] else "Pass",
            "High/Low FNR Risk": "High" if disparity["High FNR Risk"] else "Low"
        })

    overall_summary_df = pd.DataFrame(summary_rows)
    _safe_display(overall_summary_df.style.set_caption("🚨 Overall Fairness Disparity Summary"))
    return overall_summary_df.to_dict(orient="records")


# =====================================================
# 5. Test function — wrapper for model + audit
# =====================================================
def test(model=None, eval_data=None, y_true_col=None, y_pred_col=None, sensitive_features=None):
    """
    Run compliance & fairness audit on the provided model and data.

    Parameters
    ----------
    model : object with .predict() (optional)
    eval_data : DataFrame or str path
    y_true_col : str
    y_pred_col : str (optional if model is provided)
    sensitive_features : list of str (optional)

    Returns
    -------
    dict
        Summary dictionary with accuracy and fairness results
    """
    if eval_data is None:
        raise ValueError("`eval_data` must be provided")

    if isinstance(eval_data, str):
        eval_data = pd.read_csv(eval_data)

    # if model is provided, predict
    if model is not None and y_pred_col is None:
        preds = model.predict(eval_data.drop(columns=[y_true_col]))
        eval_data["__model_pred"] = preds
        y_pred_col = "__model_pred"

    # basic metrics
    total = len(eval_data)
    accuracy = (eval_data[y_true_col] == eval_data[y_pred_col]).mean()

    results = {
        "total_records": total,
        "accuracy": round(accuracy, 4),
    }

    # print(f"📊 Accuracy: {accuracy*100:.2f}% on {total} records")

    if sensitive_features:
        fairness_summary = run_fairness_audit(
            df=eval_data,
            y_true_col=y_true_col,
            y_pred_col=y_pred_col,
            sensitive_features=sensitive_features
        )
        results["fairness"] = fairness_summary

    # ✅ Store context for downstream save_results()
    results["_eval_data"] = eval_data
    results["_y_true_col"] = y_true_col
    results["_y_pred_col"] = y_pred_col
    results["_sensitive_features"] = sensitive_features

    if isinstance(eval_data, str):
        results["_dataset_source"] = eval_data
    else:
        results["_dataset_source"] = getattr(eval_data, "name", "in-memory dataframe")

    return results

# =====================================================
# 6. Submit for Governance Review
# =====================================================
import time
import random

def submit_for_review(project_info, results):
    """
    Simulate submission of audit results to the HumanLens Governance platform.
    Prints status updates and generates a mock dashboard link.
    """
    # Determine project name
    if isinstance(project_info, dict):
        project_name = project_info.get("name", "Unnamed Project")
    else:
        project_name = str(project_info)

    print("\n# ============================================================")
    print("# Submit for Governance Review")
    print("# ============================================================\n")
    print("Submitting to governance platform...")
    time.sleep(0.8)

    # Simulate processing
    steps = [
        "✓ Metrics synced to dashboard",
        "✓ Compliance report generated",
        f"✓ Project card updated: {project_name}"
    ]
    for step in steps:
        print(step)
        time.sleep(0.6)

    # Compute mock risk level based on fairness results
    fairness = results.get("fairness", [])
    fails = sum(1 for f in fairness if f.get("Fail 4/5") == "Fail" or f.get("High FNR Risk") == "High")
    if fails == 0:
        risk = "LOW"
    elif fails == 1:
        risk = "MEDIUM"
    else:
        risk = "HIGH"

    # Mock project ID and dashboard URL
    project_id = f"proj_{random.randint(1000,9999)}"
    dashboard_url = f"https://app.humanlens.ai/projects/{project_id}"

    print("\nProject Status: Ready for Review")
    print(f"Risk Level: {risk}")
    print(f"Dashboard: {dashboard_url}")

    print("\nNext Steps:")
    print("→ Governance team will review your submission")
    print("→ You'll be notified of any feedback or approval\n")

    # Return summary dictionary
    return {
        "project_name": project_name,
        "project_id": project_id,
        "status": "Ready for Review",
        "risk_level": risk,
        "dashboard_url": dashboard_url,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


# ---------------------------------------------------------------------
# 7. SAVE RESULTS — structured JSON format (metadata + fairness + disparity + dataset source)
# ---------------------------------------------------------------------
from sklearn.metrics import confusion_matrix

def save_results(results, path_prefix="fairness_summary"):
    """
    Save audit results in the standardized JSON format:
    {
      "metadata": {...},
      "overall_fairness_disparity_summary": [...],
      "disparity_metrics": [...]
    }

    Automatically includes the dataset filename (if available)
    in the 'metadata.dataset_source' field.
    """
    if "fairness" not in results:
        raise ValueError("Expected results to include 'fairness' key.")

    # === 1. METADATA ===
    dataset_source = results.get("_dataset_source", "N/A")

    metadata = {
        "dataset_source": dataset_source,
        "total_records": int(results.get("total_records", 0)),
        "overall_accuracy": float(results.get("accuracy", 0.0))
    }

    # === 2. OVERALL FAIRNESS DISPARITY SUMMARY ===
    fairness_summary = []
    for f in results["fairness"]:
        fail_45_val = f.get("Fail 4/5") or f.get("Fail/Pass 4/5") or f.get("fail_4_5", "")
        high_fnr_val = f.get("High FNR Risk") or f.get("High/Low FNR Risk") or f.get("high_fnr_risk", "")

        fairness_summary.append({
            "feature": f.get("Feature", ""),
            "di_ratio": float(f.get("DI Ratio", 0)),
            "fpr_diff": float(f.get("FPR Diff", 0)),
            "fnr_diff": float(f.get("FNR Diff", 0)),
            "fail_4_5": True if fail_45_val in ["❌", "Fail", "Yes", True] else False,
            "high_fnr_risk": True if high_fnr_val in ["❌", "High", "Yes", True] else False
        })

    # === 3. DISPARITY METRICS PER GROUP ===
    disparity_metrics = []
    eval_data = results.get("_eval_data")
    y_true_col = results.get("_y_true_col")
    y_pred_col = results.get("_y_pred_col")
    sensitive_features = results.get("_sensitive_features", [])

    if eval_data is not None and y_true_col and y_pred_col and sensitive_features:
        for feature in sensitive_features:
            group_metrics = _calculate_group_metrics(eval_data, feature, y_true_col, y_pred_col)
            for _, row in group_metrics.iterrows():
                disparity_metrics.append({
                    "feature": feature.lower(),
                    "feature_value": str(row[feature]),
                    "Count": int(row["Count"]),
                    "TP": int(row["TP"]),
                    "FN": int(row["FN"]),
                    "FP": int(row["FP"]),
                    "TN": int(row["TN"]),
                    "SR": float(row["SR (Selection Rate)"]),
                    "FPR": float(row["FPR"]),
                    "FNR": float(row["FNR"])
                })

    # === 4. STRUCTURED REPORT ===
    report = {
        "metadata": metadata,
        "overall_fairness_disparity_summary": fairness_summary,
        "disparity_metrics": disparity_metrics
    }

    # === 5. SAVE OUTPUT FILE ===
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = f"{path_prefix}_{timestamp}.json"

    with open(json_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"✅ Saved HumanLens audit report:\n  - {json_path}")
    print(f"📊 Dataset: {dataset_source}")
    print(f"📊 Total disparity metrics: {len(disparity_metrics)} groups\n")

    return report


# =====================================================
# 8. Compare multiple model versions (with export)
# =====================================================


def compare_results(results_list, save=True, output_dir="."):
    """
    Compare multiple model test results side-by-side and optionally save results.

    Parameters
    ----------
    results_list : list of (str, dict)
        List of tuples containing (dataset_name, results_dict)
        where results_dict is the output of hl.test().
    save : bool, default=True
        If True, saves comparison summary as CSV and JSON files.
    output_dir : str, default="."
        Directory to save results.

    Returns
    -------
    list of dict
        Summary table with Model, Accuracy, Gender DI, Race DI, and Risk Level.
    """

    if not results_list:
        print("No results to compare.")
        return []

    print("\n" + "═" * 66)
    print("║{:^64}║".format("Dataset Comparison"))
    print("═" * 66)
    print("║ {:<15}│ {:^9}│ {:^9}│ {:^9}│ {:^10}║".format(
        "Dataset", "Accuracy", "Gender DI", "Race DI", "Risk Level"
    ))
    print("═" * 66)

    summaries = []
    best_model = None
    best_fairness_score = -1

    for name, res in results_list:
        acc = res.get("accuracy", 0) * 100
        fairness = res.get("fairness", [])
        gender_di = race_di = None

        # Extract fairness metrics
        for f in fairness:
            feat = f.get("Feature", "").lower()
            if "gender" in feat:
                gender_di = f.get("DI Ratio", None)
            elif "race" in feat:
                race_di = f.get("DI Ratio", None)

        fairness_values = [v for v in [gender_di, race_di] if v is not None]
        fairness_score = sum(fairness_values) / len(fairness_values) if fairness_values else 0

        # Risk classification
        if fairness_score >= 0.8:
            risk = "LOW"
        elif fairness_score >= 0.7:
            risk = "MEDIUM"
        else:
            risk = "HIGH"

        if fairness_score > best_fairness_score:
            best_fairness_score = fairness_score
            best_model = name

        print("║ {:<15}│ {:>7.1f}% │ {:>7} │ {:>7} │ {:>8}   ║".format(
            name,
            acc,
            f"{gender_di:.3f}" if gender_di is not None else "N/A",
            f"{race_di:.3f}" if race_di is not None else "N/A",
            risk
        ))

        summaries.append({
            "Model": name,
            "Accuracy (%)": round(acc, 2),
            "Gender DI": round(gender_di, 3) if gender_di is not None else None,
            "Race DI": round(race_di, 3) if race_di is not None else None,
            "Risk Level": risk
        })

    print("═" * 66)
    print(f"Recommendation: {best_model} has best fairness metrics\n")

    # # --- Save to CSV + JSON ---
    # if save:
    #     os.makedirs(output_dir, exist_ok=True)
    #     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    #     csv_path = os.path.join(output_dir, f"model_comparison_{timestamp}.csv")
    #     json_path = os.path.join(output_dir, f"model_comparison_{timestamp}.json")

    #     pd.DataFrame(summaries).to_csv(csv_path, index=False)
    #     with open(json_path, "w") as f:
    #         json.dump(summaries, f, indent=2)

    #     print(f"📁 Comparison results saved to:\n  - {csv_path}\n  - {json_path}\n")

    return summaries

# =====================================================
# 9. Compare two raw prediction CSV files end-to-end (with dataset tracking)
# =====================================================
def compare_from_raw_csv(file1, file2, y_true_col, y_pred_col, sensitive_features):
    """
    Run fairness audits on two separate raw CSVs and compare the results.

    Automatically attaches 'dataset_source' metadata so the generated
    audit JSON files clearly indicate which dataset each result came from.

    Parameters
    ----------
    file1 : str
        Path to the first prediction CSV (e.g., hiring_bias.csv)
    file2 : str
        Path to the second prediction CSV (e.g., hiring_fair.csv)
    y_true_col : str
        Name of the ground-truth label column
    y_pred_col : str
        Name of the model prediction column
    sensitive_features : list of str
        Sensitive feature columns to audit fairness on

    Returns
    -------
    dict
        Dictionary containing both audit results and comparison summary
    """

    print("\n# ============================================================")
    print("# Run Fairness Comparison on Two Raw CSVs")
    print("# ============================================================\n")
    print(f"→ File 1: {file1}")
    print(f"→ File 2: {file2}\n")

    # Derive clean dataset names from filenames (no path or .csv extension)
    dataset_name_1 = os.path.basename(file1).replace(".csv", "")
    dataset_name_2 = os.path.basename(file2).replace(".csv", "")

    # --- Run audits for both datasets ---
    print(f"🔍 Running fairness audit for {dataset_name_1}...")
    results_v1 = test(
        eval_data=file1,
        y_true_col=y_true_col,
        y_pred_col=y_pred_col,
        sensitive_features=sensitive_features
    )
    results_v1["_dataset_source"] = file1  # attach dataset source
    save_results(results_v1, f"{dataset_name_1}_audit")
    print(f"✅ {dataset_name_1} audit complete.\n")

    print(f"🔍 Running fairness audit for {dataset_name_2}...")
    results_v2 = test(
        eval_data=file2,
        y_true_col=y_true_col,
        y_pred_col=y_pred_col,
        sensitive_features=sensitive_features
    )
    results_v2["_dataset_source"] = file2  # attach dataset source
    save_results(results_v2, f"{dataset_name_2}_audit")
    print(f"✅ {dataset_name_2} audit complete.\n")

    # --- Compare results using dataset names ---
    print("📊 Comparing audit results...\n")
    hl_results = compare_results([
        (dataset_name_1, results_v1),
        (dataset_name_2, results_v2)
    ])

    # --- Build structured output with dataset traceability ---
    comparison_summary = {
        "datasets": {
            dataset_name_1: {
                "file": file1,
                "metadata": results_v1.get("metadata", {}),
                "accuracy": results_v1.get("accuracy"),
            },
            dataset_name_2: {
                "file": file2,
                "metadata": results_v2.get("metadata", {}),
                "accuracy": results_v2.get("accuracy"),
            },
        },
        "comparison": hl_results,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # --- Save unified comparison summary ---
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    comparison_json_path = f"comparison_summary_{timestamp}.json"
    with open(comparison_json_path, "w") as f:
        json.dump(comparison_summary, f, indent=2)

    print(f"✅ Comparison summary saved:\n  - {comparison_json_path}\n")

    return comparison_summary
