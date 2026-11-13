# Running SecureBig on Google Colab / Databricks (the "big data" way)

The pipelines in `spark/` are plain SparkSession scripts, so they run on Colab
or Databricks with no code changes. This is where the project demonstrates the
Big Data ecosystem at scale.

## Option A — Google Colab (free)

1. New notebook → first cell:
   ```python
   !pip install -q pyspark==4.0.0
   !java -version   # Colab ships Java 11/17 — fine
   ```
2. Upload the two datasets (or mount Drive):
   - `creditcard.csv` → `/content/data/raw/transactions/creditcard.csv`
   - the four `user_activity/*.csv` + `scenario_ground_truth.csv`
     → `/content/data/raw/user_activity/`
3. Upload `spark/common.py`, `spark/fraud_pipeline.py`, `spark/insider_pipeline.py`,
   `spark/export_results.py` into `/content/spark/`, then:
   ```python
   %cd /content/spark
   !python fraud_pipeline.py
   !python insider_pipeline.py
   !python export_results.py
   ```
   Results land in `/content/results/` → zip and download for Power BI.

> On Colab the dataset paths inside `common.py` resolve relative to the
> `spark/` folder's parent — keep the same folder layout (`/content/spark`,
> `/content/data`, …) and everything works unchanged.

## Option B — Databricks (master prompt Phase 14)

Import the `spark/*.py` files as notebook files (File > Import, or paste each
into a notebook cell prefixed with `%run`-style cells). Recommended notebook
sequence matching the master prompt:

| # | Databricks notebook | Source file |
|---|---|---|
| 01 | Data_Ingestion | upload CSVs to DBFS, `spark.read.csv` (see fraud_pipeline ingest block) |
| 02 | Data_Cleaning | `dropDuplicates().dropna()` block of fraud_pipeline |
| 03 | Data_Transformation | Hive rules equivalent (`hive/02_fraud_rules.hql`) or the user-week feature block |
| 04 | Feature_Engineering | insider_pipeline `build_features()` |
| 05 | Fraud_ML | fraud_pipeline models loop |
| 06 | Insider_Threat_ML | insider_pipeline models loop |
| 07 | Model_Evaluation | metrics_from() + BinaryClassificationEvaluator (same code) |
| 08 | Result_Export | export_results.py |

A Databricks **Cluster** (any recent runtime with Spark 3.5+/4.x) replaces
`local[*]`; change `get_spark()` master via
`SparkSession.builder.getOrCreate()` (Databricks already provides a session —
just remove `.master()`).

## Option C — run locally (what this repo did)

`python run_all.py` from `securebig-backend/`. Everything runs in Spark local
mode on your machine; results are identical in format to the cluster runs,
only wall-clock time differs. This is the reproducible baseline for the report.

## Where HDFS/Hive/Pig fit

`hdfs/*.sh`, `hive/*.hql`, `pig/*.pig` run on a Hadoop VM (Cloudera/Hortonworks
sandbox, or a 3-node Docker cluster). They are NOT needed for the ML numbers —
they demonstrate the storage/security/query layers required by the course
(HDFS ACLs, Hive rule engine, Pig ETL). The Spark pipelines read the same CSVs
either from HDFS (`hdfs://...` paths — one-line change in the scripts) or from
local disk.
