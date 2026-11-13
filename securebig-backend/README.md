# SecureBig — Backend

**Privacy-Preserving Big Data Analytics Framework for Fraud & Insider Threat
Detection** — CBCA293 academic prototype. Not a production SOC.

```
Datasets (real ULB + documented simulation)
   └─ HDFS zones + ACLs            hdfs/   (needs a Hadoop VM)
   └─ Privacy layer                privacy/(runs anywhere)
   └─ Hive rule engine             hive/   (needs Hadoop)
   └─ Pig log ETL                  pig/    (needs Hadoop)
   └─ Spark MLlib pipelines        spark/  (runs locally or Colab/Databricks)
        └─ Results → Power BI pack + 3D web dashboard JSON
```

## Quick start (local, no Hadoop needed)

```bash
pip install -r requirements.txt        # pinned; pyspark 4.2 needs Java 17+
python run_all.py --preflight          # 5 s: checks interpreter + Java + inputs
python run_all.py                      # runs every runnable phase end-to-end
```

`run_all.py` does **not** assume `python` is the right interpreter — on Windows
`python` is often a different install from the one holding pyspark. It probes
for an interpreter that can `import pyspark`, uses it for every step, and writes
the whole environment (python + package versions, Java, seed, SHA-256 of every
input file) to `results/environment_manifest.json`. Override the probe with
`set SECUREBIG_PYTHON=C:\path\to\python.exe`.

Useful flags: `--preflight` (environment check only), `--skip-spark` (phases 1
and 4 only, no Java needed), `--skip-data` (reuse the existing raw CSVs).
Every step's console output is mirrored to `results/logs/<nn>_<script>.log` so
report screenshots always have a matching text artifact.

Approximate duration: 5–15 min (the fraud pipeline trains 5 models on
283,726 transactions). Artifacts land in `results/`.

## What actually ran to produce the numbers in `results/`

| Step | Engine | Status |
|---|---|---|
| ULB creditcard.csv download + inspection | Python (OpenML mirror of the Kaggle dataset) | ✅ real data, 284,807 × 31, 492 frauds |
| Insider activity logs | Python generator, seed=42, documented CERT-style archetypes | ✅ **simulated** (real CERT r4.2 is ~90 GB + license) |
| Privacy layer (mask/pseudo/hash/RBAC) | Python | ✅ executed, audit log written |
| Fraud ML (5 models) | **Spark MLlib 4.2, local[*], seed 42** | ✅ executed |
| Insider ML (5 models) | **Spark MLlib 4.2, local[*], seed 42** | ✅ executed |
| HDFS / Hive / Pig | shell/HQL/Pig scripts | 📋 provided, need a Hadoop VM (see explainer docs) |

Every metric file records the engine + seed. **Never quote these numbers as
production results** — they are a reproducible academic baseline.

## Folder map

```
data/get_fraud_data.py        Phase 1 — download/convert + inspection report
data/make_insider_logs.py     Phase 1 — simulated insider logs (SCENARIOS.md)
data/raw/, data/processed/, data/secure/
hdfs/01_setup_hdfs.sh         Phase 2 — zones + ingestion (+ HDFS_EXPLAINER.md)
hdfs/02_acls_security.sh      Phase 3 — ACL grants/denials demo
privacy/privacy_layer.py      Phase 4 — mask/pseudonymize/sha256/RBAC + audit log
hive/01_create_tables.hql     Phase 5 — external tables + masked view
hive/02_fraud_rules.hql       Phase 5 — rule engine R1–R3 → risk score/bands
pig/log_processing.pig        Phase 6 — LOAD/FILTER/GROUP/JOIN/STORE ETL
spark/common.py               SparkSession builder (pins python workers)
spark/fraud_pipeline.py       Phases 7,8,10 — clean→features→oversample→5 models
spark/insider_pipeline.py     Phases 7,9,10 — user-week features→5 models
spark/export_results.py       Phase 11 — Power BI pack + dashboard JSON
notebooks/COLAB_DATABRICKS_GUIDE.md   Colab/Databricks run instructions
run_all.py                    one-command runner
results/                      ALL outputs (metrics, confusion, ROC, Power BI)
```

## Results artifacts (after a run)

```
results/processed inspection: data/processed/fraud_inspection.txt
results/model_metrics/fraud_metrics.csv       5 models × {Accuracy, Precision, Recall, F1, ROC-AUC, TP/FP/TN/FN}
results/model_metrics/insider_metrics.csv     same, insider threat
results/model_metrics/*_confusion_*.csv       per-model confusion counts
results/fraud/roc_points_best.json            ROC curve of the best model
results/insider_threat/roc_points_best.json   same
results/privacy_audit_log.jsonl               access decisions (GRANT/DENY)
results/powerbi/                              FACT_* + DIM_* + DAX_measures.txt + build steps
results/dashboard/dashboard_data.json         overlay consumed by securebig-3d-ui
```

## Methodology notes (for the report/viva)

* **Split:** 80/20 random, seed 42. The test fold keeps the natural 0.17%
  imbalance — never evaluate oversampled data on oversampled tests.
* **Imbalance handling:** minority **oversampling of the training fold only**
  (fraud ≈ 1:10, insider ≈ 1:3). Logistic Regression trains deterministically;
  DT/RF/GBT fix `seed=42`. NB uses gaussian smoothing 1.0.
* **Why not only accuracy:** with 1:577 imbalance, predicting "always legit"
  scores 99.83% accuracy and 0 recall — precision/recall/F1/ROC-AUC are the
  real story. `fraud_inspection.txt` documents the class distribution.
* **Hive rules vs ML:** rules R1–R3 use only real columns (`Time`, `Amount`);
  R4/R5 (location/device) are omitted rather than faked — the ULB dataset has
  no such fields.
* **Insider labels:** scenario-derived from the generator (transparent, in
  `scenario_ground_truth.csv`) — the pipeline includes a stub for the real
  CERT r4.2 files if your institution obtains them.
* **Privacy:** analytics only ever see pseudonyms (`USR_xxx`); the
  re-identification map stays in the restricted zone with 750/640 permissions
  plus explicit ACLs (see `hdfs/02_acls_security.sh`).
