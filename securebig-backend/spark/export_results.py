"""
SecureBig — Phase 11: result export for Power BI + the 3D web dashboard.

Builds a star-schema-ready CSV pack + DAX measures + dashboard JSON from the
REAL artifacts produced by the pipelines (never invented numbers).

Run:  python spark/export_results.py   (after both pipelines finished)

Out :  results/powerbi/FACT_TRANSACTIONS.csv       (scored txns, Power BI fact)
       results/powerbi/FACT_MODEL_RESULTS.csv      (both datasets, 5 models)
       results/powerbi/FACT_USER_WEEK_FEATURES.csv (from insider pipeline)
       results/powerbi/DIM_MODEL.csv / DIM_RISK.csv
       results/powerbi/DAX_measures.txt
       results/powerbi/POWERBI_BUILD_STEPS.md
       results/dashboard/dashboard_data.json       (3D web UI overlay)
"""
import json
from pathlib import Path

import pandas as pd

from common import ROOT, RESULTS

PBI = RESULTS / "powerbi"
DASH = RESULTS / "dashboard"
PBI.mkdir(parents=True, exist_ok=True)
DASH.mkdir(parents=True, exist_ok=True)


def main() -> None:
    # ---- model metrics (both datasets) --------------------------------------
    frames = []
    for ds, path in [("Fraud", RESULTS / "model_metrics" / "fraud_metrics.csv"),
                     ("Insider Threat", RESULTS / "model_metrics" / "insider_metrics.csv")]:
        df = pd.read_csv(path)
        df.insert(0, "Dataset", ds)
        frames.append(df)
    model_results = pd.concat(frames, ignore_index=True)
    model_results.to_csv(PBI / "FACT_MODEL_RESULTS.csv", index=False)

    dim_model = pd.DataFrame({
        "ModelId": range(1, 6),
        "Model": ["Logistic Regression", "Decision Tree", "Random Forest",
                  "Naive Bayes", "GBT"],
        "Family": ["Linear", "Tree", "Ensemble/Bagging", "Probabilistic",
                   "Ensemble/Boosting"],
    })
    dim_model.to_csv(PBI / "DIM_MODEL.csv", index=False)
    dim_risk = pd.DataFrame({
        "RiskLevel": ["LOW", "MEDIUM", "HIGH"], "MinScore": [0, 31, 61],
        "MaxScore": [30, 60, 100],
    })
    dim_risk.to_csv(PBI / "DIM_RISK.csv", index=False)

    # ---- scored transactions fact: FULL test fold of the BEST model ---------
    fact = pd.read_csv(ROOT / "results" / "fraud" / "fraud_scored_test.csv")
    fact.to_csv(PBI / "FACT_TRANSACTIONS.csv", index=False)

    # dataset-level facts (source totals — never recompute these from the
    # scored fold; the test fold is only ~20% of the data by design)
    n_total, n_fraud = 284807, 492          # from data/processed/fraud_inspection.txt
    test_rows = len(fact)
    test_fraud = int((fact["Class"] == 1).sum())
    pd.DataFrame([
        {"fact": "dataset_rows", "value": n_total},
        {"fact": "dataset_frauds", "value": n_fraud},
        {"fact": "dataset_fraud_rate_pct", "value": round(100 * n_fraud / n_total, 3)},
        {"fact": "scored_test_rows", "value": test_rows},
        {"fact": "scored_test_frauds", "value": test_fraud},
        {"fact": "scored_test_fraud_rate_pct", "value": round(100 * test_fraud / test_rows, 3)},
    ]).to_csv(PBI / "DIM_DATASET_FACTS.csv", index=False)

    # ---- DAX measures --------------------------------------------------------
    (PBI / "DAX_measures.txt").write_text(
        """// SecureBig — Power BI DAX measures (import via Modeling > New measure)
// FACT_TRANSACTIONS = the BEST model's full test fold (held-out data), so the
// confusion matrix here reconciles exactly with results/model_metrics CSVs.

Total Transactions (full dataset) =
    LOOKUPVALUE ( DIM_DATASET_FACTS[value], DIM_DATASET_FACTS[fact], "dataset_rows" )
Dataset Frauds (full dataset) =
    LOOKUPVALUE ( DIM_DATASET_FACTS[value], DIM_DATASET_FACTS[fact], "dataset_frauds" )
Dataset Fraud Rate % =
    LOOKUPVALUE ( DIM_DATASET_FACTS[value], DIM_DATASET_FACTS[fact], "dataset_fraud_rate_pct" )

Scored Transactions = COUNTROWS ( FACT_TRANSACTIONS )
Fraud Count = CALCULATE ( [Scored Transactions], FACT_TRANSACTIONS[Class] = 1 )
Fraud Rate % = DIVIDE ( [Fraud Count], [Scored Transactions], 0 ) * 100
Avg Fraud Probability = AVERAGE ( FACT_TRANSACTIONS[fraud_prob] )
High-Risk Txns = CALCULATE ( [Scored Transactions], FACT_TRANSACTIONS[prediction] = 1 )
True Positives = CALCULATE ( [Scored Transactions], FACT_TRANSACTIONS[Class] = 1, FACT_TRANSACTIONS[prediction] = 1 )
False Positives = CALCULATE ( [Scored Transactions], FACT_TRANSACTIONS[Class] = 0, FACT_TRANSACTIONS[prediction] = 1 )
False Negatives = CALCULATE ( [Scored Transactions], FACT_TRANSACTIONS[Class] = 1, FACT_TRANSACTIONS[prediction] = 0 )
Model Precision = DIVIDE ( [True Positives], [True Positives] + [False Positives], 0 )
Model Recall = DIVIDE ( [True Positives], [True Positives] + [False Negatives], 0 )
Model F1 = DIVIDE ( 2 * [Model Precision] * [Model Recall], [Model Precision] + [Model Recall], 0 )
Suspicious User-Weeks = CALCULATE ( COUNTROWS ( FACT_USER_WEEK_FEATURES ), FACT_USER_WEEK_FEATURES[prediction] = 1 )
Avg Suspicion Score = AVERAGE ( FACT_USER_WEEK_FEATURES[suspicion_prob] )
High-Risk Users =
COUNTROWS (
    FILTER (
        VALUES ( FACT_USER_WEEK_FEATURES[user] ),
        CALCULATE ( MAX ( FACT_USER_WEEK_FEATURES[suspicion_prob] ) ) > 0.5
    )
)
Best Model F1 =
MAXX ( FACT_MODEL_RESULTS, FACT_MODEL_RESULTS[F1] )
""",
        encoding="utf-8",
    )

    (PBI / "POWERBI_BUILD_STEPS.md").write_text(
        """# Power BI build steps (star schema)

## 1. Get data
Import from `results/powerbi/`: FACT_TRANSACTIONS, FACT_MODEL_RESULTS,
FACT_USER_WEEK_FEATURES, DIM_MODEL, DIM_RISK (all CSV/Text).

## 2. Relationships (Model view)
- FACT_MODEL_RESULTS[Model]  *—1  DIM_MODEL[Model]
- FACT_MODEL_RESULTS[Dataset] — slicer table (create with: Modeling > New table
  `Dataset = DATATABLE("Dataset", STRING, {{"Fraud"}, {"Insider Threat"}})`)
- FACT_TRANSACTIONS: add calculated column
  `Risk Band = IF([prediction]=1, "FLAGGED", "OK")`
- FACT_USER_WEEK_FEATURES: add
  `Risk Band = IF([suspicion_prob] > 0.66, "HIGH", IF([suspicion_prob] > 0.33, "MEDIUM", "LOW"))`

## 3. Measures
Paste every measure from `DAX_measures.txt` (New measure). Do not hard-code numbers.

## 4. Pages (map to the master prompt §16–20)
1. Executive Overview — card visuals (Total Transactions, Fraud Count, Fraud
   Rate %, Suspicious User-Weeks, High-Risk Users), donut: FACT_MODEL_RESULTS
   filtered to Fraud confusion counts, slicers: Dataset, Model.
2. Fraud Analytics — scatter fraud_prob vs Amount, table of flagged txns,
   confusion-matrix matrix visual (Class × prediction).
3. Insider Threat — bar: suspicious user-weeks by user (top N), line:
   suspicion_prob by week, table: features of top users (drill-through).
4. ML Model Lab — bar: F1/Precision/Recall by Model (slicer: Dataset),
   small multiples per metric.
5. Privacy & Access — import `results/privacy_audit_log.jsonl` (Power Query
   JSON) → role × decision table.

## 5. Theme
Dark cybersecurity theme: background #070B16, text #E6F1FF, accent #00F0FF,
alerts #FF3B5C, ok #00FF9D (matches the 3D web dashboard).
""",
        encoding="utf-8",
    )

    # ---- dashboard JSON overlay for the 3D web UI ---------------------------
    dash = {"engine": "Spark MLlib", "seed": 42, "source": "SecureBig backend run"}
    if (RESULTS / "model_metrics" / "fraud_metrics.csv").exists():
        fm = pd.read_csv(RESULTS / "model_metrics" / "fraud_metrics.csv")
        im = pd.read_csv(RESULTS / "model_metrics" / "insider_metrics.csv")
        ins = pd.read_csv(RESULTS / "powerbi" / "FACT_USER_WEEK_FEATURES.csv")
        dash["fraud_models"] = fm.to_dict(orient="records")
        dash["insider_models"] = im.to_dict(orient="records")
        dash["kpi"] = {
            "total_transactions": 284807, "fraud_transactions": 492,
            "fraud_rate": 0.1727,
            "monitored_users": int(ins["user"].nunique()),
            "suspicious_user_weeks": int(ins[ins["prediction"] == 1].shape[0]),
            "high_risk_users": int(
                ins.groupby("user")["suspicion_prob"].max().gt(0.5).sum()),
        }
        top_users = (ins.groupby("user")
                     .agg(events=("total_events", "sum"),
                          suspicious_weeks=("prediction", "sum"),
                          max_prob=("suspicion_prob", "max"))
                     .sort_values("max_prob", ascending=False).head(8)
                     .reset_index())
        dash["top_risk_users"] = top_users.to_dict(orient="records")
    (DASH / "dashboard_data.json").write_text(
        json.dumps(dash, indent=2), encoding="utf-8")
    print(f"wrote {PBI}/* and {DASH / 'dashboard_data.json'}")
    print(json.dumps(dash.get("kpi", {}), indent=2))

    build_excel_pack(model_results, fact)


def build_excel_pack(model_results: pd.DataFrame, fact: pd.DataFrame) -> None:
    """One Excel workbook holding every table — a single native Power BI import.

    Excel is the only one-file source Power BI Desktop imports natively without
    a gateway/driver, so this turns the whole star schema into a 4-click load.
    """
    audit_src = ROOT / "results" / "privacy_audit_log.jsonl"
    audit = pd.read_json(audit_src, lines=True)
    audit.to_csv(PBI / "FACT_ACCESS_AUDIT.csv", index=False)

    tables = {
        "FACT_TRANSACTIONS": fact,
        "FACT_MODEL_RESULTS": model_results,
        "FACT_USER_WEEK_FEATURES": pd.read_csv(PBI / "FACT_USER_WEEK_FEATURES.csv"),
        "FACT_ACCESS_AUDIT": audit,
        "DIM_MODEL": pd.read_csv(PBI / "DIM_MODEL.csv"),
        "DIM_RISK": pd.read_csv(PBI / "DIM_RISK.csv"),
        "DIM_DATASET_FACTS": pd.read_csv(PBI / "DIM_DATASET_FACTS.csv"),
    }
    xlsx = PBI / "SecureBig_Tables.xlsx"
    with pd.ExcelWriter(xlsx, engine="openpyxl") as xw:
        for sheet, df in tables.items():
            df.to_excel(xw, sheet_name=sheet, index=False)
    print(f"wrote {xlsx} — sheets: {', '.join(tables)}")


if __name__ == "__main__":
    main()
