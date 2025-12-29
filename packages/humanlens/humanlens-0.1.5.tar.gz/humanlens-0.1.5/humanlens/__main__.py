import sys
import pandas as pd
from .core_ import run_fairness_audit

def main():
    if len(sys.argv) < 2:
        print("Usage: humanlens <csv_path>")
        sys.exit(1)

    csv_path = sys.argv[1]
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"❌ Failed to load CSV: {e}")
        sys.exit(1)

    # Adjust column names as needed — or make this configurable
    y_true_col = "Qualified_Actual"
    y_pred_col = "Model_Recommendation"
    sensitive_features = ["Gender", "Age_Group", "Race_Ethnicity"]

    print(f"📂 Loaded {len(df)} rows from {csv_path}")
    print(f"🚀 Running fairness audit...")

    results = run_fairness_audit(
        df=df,
        y_true_col=y_true_col,
        y_pred_col=y_pred_col,
        sensitive_features=sensitive_features
    )

    print("\n=== ✅ Fairness Audit Summary ===")
    for row in results:
        print(f"{row['Feature']}: DI={row['DI Ratio']}, FPR Δ={row['FPR Diff']}, FNR Δ={row['FNR Diff']}, 4/5={row['Fail 4/5']}, FNR Risk={row['High FNR Risk']}")

if __name__ == "__main__":
    main()
