"""
SecureBig — Phases 7, 9, 10, 11 (Dataset 2): Spark MLlib insider-threat pipeline.

Feature engineering (CERT-style per user-week aggregation over the simulated
activity logs, seed=42, documented in data/raw/user_activity/SCENARIOS.md):
  logon_count, failed_login_count, after_hours_logons, external_ip_logons,
  file_access_count, sensitive_file_count, file_copy_count,
  usb_connects, usb_bytes, upload_events, upload_bytes, total_events

Label (transparent, scenario-derived — NOT real-world ground truth):
  1 = user-week belongs to a documented scenario actor within their active
      weeks (A_exfil_usb weeks 6-12, B_new_ip_auth weeks 4-10, C any week),
  0 = otherwise. Loaded from scenario_ground_truth.csv.

Run:  python spark/insider_pipeline.py
Out :  results/model_metrics/insider_metrics.csv (+ confusion matrices)
       results/insider_threat/roc_points_best.json
       results/powerbi/FACT_USER_WEEK_FEATURES.csv  (features + ML prediction)
"""
import json
import time

import pandas as pd
from pyspark.ml import Pipeline
from pyspark.ml.classification import (DecisionTreeClassifier,
                                       GBTClassifier,
                                       LogisticRegression,
                                       NaiveBayes,
                                       RandomForestClassifier)
from pyspark.ml.evaluation import BinaryClassificationEvaluator
from pyspark.ml.feature import StandardScaler, VectorAssembler
from pyspark.ml.functions import vector_to_array
from pyspark.sql import functions as F

from common import ROOT, RESULTS, SEED, get_spark, save_pd

RAW = ROOT / "data" / "raw" / "user_activity"
EPOCH = "2025-07-01"
FEATURES = ["logon_count", "failed_login_count", "after_hours_logons",
            "external_ip_logons", "file_access_count", "sensitive_file_count",
            "file_copy_count", "usb_connects", "usb_bytes",
            "upload_events", "upload_bytes", "total_events"]
MODELS = {
    "Logistic Regression": lambda: LogisticRegression(
        featuresCol="features", labelCol="label", maxIter=50),
    "Decision Tree": lambda: DecisionTreeClassifier(
        featuresCol="features", labelCol="label", maxDepth=5, seed=SEED),
    "Random Forest": lambda: RandomForestClassifier(
        featuresCol="features", labelCol="label", numTrees=30, maxDepth=6, seed=SEED),
    "Naive Bayes": lambda: NaiveBayes(
        featuresCol="features", labelCol="label", smoothing=1.0, modelType="gaussian"),
    "GBT": lambda: GBTClassifier(
        featuresCol="features", labelCol="label", maxIter=15, maxDepth=4, seed=SEED),
}


def confusion_counts(pred_df) -> dict:
    c = {(int(r["label"]), int(r["prediction"])): int(r["count"])
         for r in pred_df.groupBy("label", "prediction").count().collect()}
    return {"TP": c.get((1, 1), 0), "FP": c.get((0, 1), 0),
            "TN": c.get((0, 0), 0), "FN": c.get((1, 0), 0)}


def metrics_from(cm: dict, roc_auc: float) -> dict:
    tp, fp, tn, fn = cm["TP"], cm["FP"], cm["TN"], cm["FN"]
    acc = (tp + tn) / max(tp + tn + fp + fn, 1)
    prec = tp / max(tp + fp, 1)
    rec = tp / max(tp + fn, 1)
    f1 = 2 * prec * rec / max(prec + rec, 1e-12)
    return {"Accuracy": acc, "Precision": prec, "Recall": rec, "F1": f1,
            "ROC_AUC": roc_auc, **cm}


def build_features(spark):
    logon = (spark.read.csv(str(RAW / "logon.csv"), header=True, inferSchema=True))
    files = (spark.read.csv(str(RAW / "file.csv"), header=True, inferSchema=True))
    device = (spark.read.csv(str(RAW / "device.csv"), header=True, inferSchema=True))
    http = (spark.read.csv(str(RAW / "http.csv"), header=True, inferSchema=True))
    for d in (logon, files, device, http):
        d.cache()

    wk = (F.floor(F.datediff(F.to_date(F.col("timestamp").cast("timestamp")),
                             F.to_date(F.lit(EPOCH))) / 7)
          .cast("int").alias("week"))
    hour_of_day = F.hour(F.col("timestamp").cast("timestamp"))

    f_logon = (logon.withColumn("week", wk)
               .groupBy("user", "week")
               .agg(F.count("*").alias("logon_count"),
                    F.sum(F.when(F.col("event") == "FailedLogon", 1).otherwise(0))
                    .alias("failed_login_count"),
                    F.sum(F.when(hour_of_day.isin([0, 1, 2, 3, 4, 5, 20, 21, 22, 23])
                                 & (F.col("event") == "Logon"), 1).otherwise(0))
                    .alias("after_hours_logons"),
                    F.sum(F.when(~F.col("ip").startswith("10.20."), 1).otherwise(0))
                    .alias("external_ip_logons")))

    f_file = (files.withColumn("week", wk)
              .groupBy("user", "week")
              .agg(F.count("*").alias("file_access_count"),
                   F.sum(F.when(F.col("sensitivity") == "sensitive", 1).otherwise(0))
                   .alias("sensitive_file_count"),
                   F.sum(F.when(F.col("event") == "Copy", 1).otherwise(0))
                   .alias("file_copy_count")))

    f_dev = (device.withColumn("week", wk)
             .groupBy("user", "week")
             .agg(F.sum(F.when(F.col("event") == "Connect", 1).otherwise(0)).alias("usb_connects"),
                  F.coalesce(F.sum("bytes_copied"), F.lit(0)).alias("usb_bytes")))

    f_http = (http.withColumn("week", wk)
              .groupBy("user", "week")
              .agg(F.sum(F.when(F.col("download_count") > 0, 1).otherwise(0)).alias("upload_events"),
                   F.coalesce(F.sum(F.when(F.col("download_count") > 0, F.col("bytes"))),
                              F.lit(0)).alias("upload_bytes")))

    feats = (f_logon
             .join(f_file, ["user", "week"], "full_outer")
             .join(f_dev, ["user", "week"], "full_outer")
             .join(f_http, ["user", "week"], "full_outer"))
    for c in FEATURES[:-1]:
        feats = feats.withColumn(c, F.coalesce(c, F.lit(0)))
    feats = feats.withColumn("total_events",
                             F.col("logon_count") + F.col("file_access_count")
                             + F.col("usb_connects") + F.col("upload_events"))

    gt = pd.read_csv(RAW / "scenario_ground_truth.csv")
    weeks_map = {"A_exfil_usb": range(6, 13), "B_new_ip_auth": range(4, 11),
                 "C_snooping": range(0, 13)}
    pos = [(r["user"], w) for _, r in gt.iterrows()
           for w in weeks_map[r["scenario"]]]
    pos_df = spark.createDataFrame(pos, ["user", "week"]).withColumn("label", F.lit(1))
    labeled = (feats.join(pos_df, ["user", "week"], "left")
               .withColumn("label", F.coalesce("label", F.lit(0))))
    labeled.cache()
    return labeled


def main() -> None:
    spark = get_spark("SecureBig-Insider")
    print("== Phase 7: user-week feature table ==")
    labeled = build_features(spark)
    n_total, n_pos = labeled.count(), labeled.filter("label = 1").count()
    print(f"user-week rows: {n_total}  suspicious: {n_pos} "
          f"({n_pos / n_total * 100:.1f}%)")

    assembler = VectorAssembler(inputCols=FEATURES, outputCol="raw_feats")
    scaler = StandardScaler(inputCol="raw_feats", outputCol="features")
    train, test = labeled.randomSplit([0.8, 0.2], seed=SEED)
    print(f"train {train.count()} / test {test.count()} (natural distribution kept)")

    # class weighting via oversampling on the train fold only (≈1:3)
    pos = train.filter("label = 1")
    neg = train.filter("label = 0")
    target = neg.count() // 3
    k = target // max(pos.count(), 1)
    pos_up = pos.crossJoin(spark.range(max(k, 1)).withColumnRenamed("id", "d"))
    train_bal = neg.unionByName(pos_up.select(neg.columns))
    print(f"oversampled train: {train_bal.count()} rows")

    evaluator = BinaryClassificationEvaluator(labelCol="label",
                                              rawPredictionCol="probability",
                                              metricName="areaUnderROC")
    rows, scored = [], None
    for name, maker in MODELS.items():
        t0 = time.time()
        model = Pipeline(stages=[assembler, scaler, maker()]).fit(train_bal)
        pred = model.transform(test)
        cm = confusion_counts(pred)
        auc = evaluator.evaluate(pred)
        m = metrics_from(cm, auc)
        m["Model"] = name
        m["train_seconds"] = round(time.time() - t0, 1)
        rows.append(m)
        print(f"{name:<20} acc={m['Accuracy']:.4f} P={m['Precision']:.4f} "
              f"R={m['Recall']:.4f} F1={m['F1']:.4f} AUC={m['ROC_AUC']:.4f} "
              f"({m['train_seconds']}s)")
        save_pd(pred.groupBy("label", "prediction").count().toPandas(),
                f"results/model_metrics/insider_confusion_{name.replace(' ', '_').lower()}.csv")
        if scored is None:
            scored = pred

    pdf = pd.DataFrame(rows)[["Model", "Accuracy", "Precision", "Recall", "F1",
                              "ROC_AUC", "TP", "FP", "TN", "FN", "train_seconds"]]
    save_pd(pdf, "results/model_metrics/insider_metrics.csv")
    print("\nModel comparison (insider threat):")
    print(pdf.to_string(index=False))

    best_name = pdf.sort_values("F1", ascending=False).iloc[0]["Model"]
    print(f"\nbest model by F1: {best_name}")
    model = Pipeline(stages=[assembler, scaler, MODELS[best_name]()]).fit(train_bal)
    scored = (model.transform(labeled)
              .select("user", "week", "label", "prediction",
                      F.round(vector_to_array("probability")[1], 6)
                      .alias("suspicion_prob"), *FEATURES)
              .toPandas())
    scored.to_csv(RESULTS / "powerbi" / "FACT_USER_WEEK_FEATURES.csv", index=False)

    import numpy as np
    probs = scored["suspicion_prob"].to_numpy()
    y = scored["label"].to_numpy()
    order = np.argsort(-probs)
    y, probs = y[order], probs[order]
    tp, fp = np.cumsum(y), np.cumsum(1 - y)
    tpr = tp / max(tp[-1], 1)
    fpr = fp / max(fp[-1], 1)
    pts = [[round(float(f), 5), round(float(t), 5)] for f, t in
           zip(fpr[:: max(len(fpr) // 120, 1)], tpr[:: max(len(tpr) // 120, 1)])]
    (RESULTS / "insider_threat" / "roc_points_best.json").write_text(
        json.dumps({"model": best_name, "points": pts}), encoding="utf-8")
    spark.stop()
    print("insider pipeline complete.")


if __name__ == "__main__":
    main()
