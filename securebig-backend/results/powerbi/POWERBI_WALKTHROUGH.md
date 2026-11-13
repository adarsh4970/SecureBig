# Power BI Walkthrough — build the SecureBig dashboard in ~30 minutes

Exact clicks, no guessing. Everything you import comes from
`securebig-backend/results/powerbi/` — all numbers are real Spark MLlib output.

> Path used below: `C:\Users\Adarsh singh\.zcode\workspace\default\securebig-backend\results\powerbi\`
> (adjust if you moved the project).

## STEP 0 — open & theme (2 min)

1. Start **Power BI Desktop** (Start menu → "Power BI").
2. If a sign-in screen appears, click the ✕ / "Cancel" — sign-in is optional
   for local work.
3. Blank report opens. Ribbon **View → Themes → Browse for themes** →
   select `securebig-theme.json`. The canvas turns dark SOC-style.

## STEP 1 — import the data (3 min — one import, all 7 tables)

**Home → Get data → Excel workbook** → pick `SecureBig_Tables.xlsx`
(in `results/powerbi/`) → in the Navigator tick the checkbox on the folder
line (selects all 7 tables) → **Load**.

| Sheet | Table |
|---|---|
| FACT_TRANSACTIONS | best model's full scored test fold (56,705 rows) |
| FACT_MODEL_RESULTS | all 10 model evaluations |
| FACT_USER_WEEK_FEATURES | insider user-week features + predictions |
| FACT_ACCESS_AUDIT | privacy ACL decisions (GRANT/DENY) |
| DIM_MODEL / DIM_RISK / DIM_DATASET_FACTS | dimensions |

(Individual CSVs remain in the same folder if you prefer file-by-file imports;
the workbook simply replaces six separate imports with one.)

## STEP 2 — model & measures (5 min)

1. Left rail → **Model view** (third icon).
2. Drag `DIM_MODEL[Model]` onto `FACT_MODEL_RESULTS[Model]` → relationship
   **One-to-many (1:*), Single direction** → OK.
3. Back to **Report view**. Ribbon **Modeling → New measure**, paste one at a
   time (from `DAX_measures.txt`; the essentials):

```dax
Total Transactions (full dataset) =
    LOOKUPVALUE ( DIM_DATASET_FACTS[value], DIM_DATASET_FACTS[fact], "dataset_rows" )
Dataset Fraud Rate % =
    LOOKUPVALUE ( DIM_DATASET_FACTS[value], DIM_DATASET_FACTS[fact], "dataset_fraud_rate_pct" )

Scored Transactions = COUNTROWS ( FACT_TRANSACTIONS )
Fraud Count = CALCULATE ( [Scored Transactions], FACT_TRANSACTIONS[Class] = 1 )
Fraud Rate % = DIVIDE ( [Fraud Count], [Scored Transactions], 0 ) * 100
True Positives = CALCULATE ( [Scored Transactions], FACT_TRANSACTIONS[Class] = 1, FACT_TRANSACTIONS[prediction] = 1 )
False Positives = CALCULATE ( [Scored Transactions], FACT_TRANSACTIONS[Class] = 0, FACT_TRANSACTIONS[prediction] = 1 )
False Negatives = CALCULATE ( [Scored Transactions], FACT_TRANSACTIONS[Class] = 1, FACT_TRANSACTIONS[prediction] = 0 )
Model Precision = DIVIDE ( [True Positives], [True Positives] + [False Positives], 0 )
Model Recall = DIVIDE ( [True Positives], [True Positives] + [False Negatives], 0 )
Model F1 = DIVIDE ( 2 * [Model Precision] * [Model Recall], [Model Precision] + [Model Recall], 0 )
Suspicious User-Weeks = CALCULATE ( COUNTROWS ( FACT_USER_WEEK_FEATURES ), FACT_USER_WEEK_FEATURES[prediction] = 1 )
High-Risk Users =
COUNTROWS (
    FILTER (
        VALUES ( FACT_USER_WEEK_FEATURES[user] ),
        CALCULATE ( MAX ( FACT_USER_WEEK_FEATURES[suspicion_prob] ) ) > 0.5
    )
)
```

> Why two "totals"? `FACT_TRANSACTIONS` holds the **best model's full test
> fold** (held-out rows only — that's what makes the confusion matrix here
> reconcile exactly with the reported metrics). Dataset-level totals come
> from `DIM_DATASET_FACTS`. Say this out loud in the viva — it shows you
> understand train/test discipline.

## STEP 3 — PAGE 1: Executive Overview (5 min)

Bottom of canvas → double-click **Page 1** → rename `Executive Overview`.

Insert (Visualizations pane) and set fields:

| Visual | Fields |
|---|---|
| Card ×5 | [Total Transactions], [Fraud Count], [Fraud Rate %], [Suspicious User-Weeks], [High-Risk Users] |
| Donut chart | Legend `FACT_MODEL_RESULTS[Model]` (filter this visual: Dataset = "Fraud"), Values `SUM(FACT_MODEL_RESULTS[F1])` |
| Slicer | Field `FACT_MODEL_RESULTS[Dataset]` (style: Dropdown) |
| Table | `FACT_MODEL_RESULTS[Model]`, [Model F1], [Model Recall], [Model Precision] |
| Text box | Title "SECUREBIG — SECURITY INTELLIGENCE CENTER" |

Insert → **Buttons → Navigator → Page navigator** (bottom-left) for free tabs.

## STEP 4 — PAGE 2: Fraud Analytics (5 min)

New page → rename `Fraud Analytics`.

| Visual | Fields |
|---|---|
| Scatter chart | X `FACT_TRANSACTIONS[Amount]`, Y `FACT_TRANSACTIONS[fraud_prob]`, Legend `FACT_TRANSACTIONS[prediction]` |
| Clustered bar chart | Axis `FACT_TRANSACTIONS[Class]`, X count; add legend `FACT_TRANSACTIONS[prediction]` (actual vs predicted) |
| Matrix | Rows `FACT_TRANSACTIONS[Class]`, Columns `FACT_TRANSACTIONS[prediction]`, Values count → the confusion matrix |
| Slicers | `Amount` (Between slider), `prediction` |

## STEP 5 — PAGE 3: Insider Threat (5 min)

New page → rename `Insider Threat`.

| Visual | Fields |
|---|---|
| Clustered bar | Y-axis `FACT_USER_WEEK_FEATURES[user]` (Top N filter: top 10 by value), X `COUNTROWS` |
| Line chart | X `FACT_USER_WEEK_FEATURES[week]`, Y `AVERAGE(suspicion_prob)` |
| Table | user, `total_events`, `sensitive_file_count`, `after_hours_logons`, `failed_login_count`, `suspicion_prob` — sorted by suspicion desc |
| Slicer | `FACT_USER_WEEK_FEATURES[prediction]` |

Drill-through: right-click the user table visual → nothing needed; instead
create page `User Detail`, put per-user visuals there, then on the user
column: right-click field `user` → **Add to drill-through** → `User Detail`.

## STEP 6 — PAGE 4: ML Model Lab (4 min)

New page → rename `ML Model Lab`.

| Visual | Fields |
|---|---|
| Clustered bar chart | Y-axis `FACT_MODEL_RESULTS[Model]`, X-axis `FACT_MODEL_RESULTS[F1]`, `FACT_MODEL_RESULTS[Precision]`, `FACT_MODEL_RESULTS[Recall]`, `FACT_MODEL_RESULTS[ROC_AUC]` |
| Slicer | `FACT_MODEL_RESULTS[Dataset]` → switching Fraud ↔ Insider re-scores the whole page |
| Matrix | Rows `Model`, Values `TP`, `FP`, `TN`, `FN` (confusion per model) |
| Card | [Model F1] titled "Best available F1" |

## STEP 7 — PAGE 5: Privacy & Access (2 min)

Already imported with the workbook: `FACT_ACCESS_AUDIT` (the privacy layer's
real GRANT/DENY decisions).

- Visual: **Table** — `role`, `zone`, `decision`, `note`
- Visual: **Donut** — Legend `decision`, Values count → GRANT vs DENY split
- Visual: **Matrix** — Rows `role`, Columns `zone`, Values count → the ACL matrix

## STEP 8 — save (1 min)

**File → Save as** → `reports/SecureBig_Dashboard.pbix` (inside the backend
folder). That file is your CBCA293 submission artifact — every number in it
traces to `results/model_metrics/*.csv` produced by the Spark run.

## Sanity checks before the viva

- Executive page: "Total Transactions (full dataset)" card = **284,807**;
  Dataset Fraud Rate % ≈ **0.173**.
- Scored test fold: **56,705 rows**, 83 frauds = **0.146 %** fraud (natural
  distribution kept). Cross-check against `DIM_DATASET_FACTS.csv`.
- ML Lab with Dataset=Fraud: Random Forest F1 ≈ **0.816**, NB ≈ **0.172**.
- Confusion matrix (Fraud page) must equal the numbers in
  `results/model_metrics/fraud_confusion_random_forest.csv` — that's the proof
  the dashboard reconciles with the Spark run.
- If a number looks invented — it is; re-run `python run_all.py` in the
  backend and re-import. Never hand-edit values.
