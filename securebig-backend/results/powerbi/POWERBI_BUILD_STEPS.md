# Power BI build steps (star schema)

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
