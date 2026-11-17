"""
SecureBig — Phases 7, 8, 10, 11 (Dataset 1): Spark MLlib fraud pipeline.

Flow (master prompt §11):
  raw CSV -> cleaning (dupes/missing) -> feature prep -> train/test split
  -> VectorAssembler -> minority OVERSAMPLING on the TRAIN fold only
     (handles 0.17% class imbalance; test set stays untouched)
  -> train 5 MLlib models (LR, DT, RF, NB, GBT, all seed=42)
  -> predict -> confusion counts -> Accuracy/Precision/Recall/F1/ROC-AUC
  -> export metrics + confusion matrices + ROC curve + scored transactions

Run:  python spark/fraud_pipeline.py
Out :  results/model_metrics/fraud_metrics.csv
       results/model_metrics/fraud_confusion_<model>.csv
       results/fraud/roc_points_best.json
       results/fraud/fraud_scored_sample.csv   (preview for reports)
"""
import json

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

CSV = ROOT / "data" / "raw" / "transactions" / "creditcard.csv"
MODELS = {
    "Logistic Regression": lambda: LogisticRegression(
        featuresCol="features", labelCol="Class", maxIter=50),
    "Decision Tree": lambda: DecisionTreeClassifier(
        featuresCol="features", labelCol="Class", maxDepth=6, seed=SEED),
    "Random Forest": lambda: RandomForestClassifier(
        featuresCol="features", labelCol="Class", numTrees=30, maxDepth=8, seed=SEED),
    "Naive Bayes": lambda: NaiveBayes(
        featuresCol="features", labelCol="Class", smoothing=1.0, modelType="gaussian"),
    "GBT": lambda: GBTClassifier(
        featuresCol="features", labelCol="Class", maxIter=10, maxDepth=4, seed=SEED),
}


def confusion_counts(pred_df) -> dict:
    r = (pred_df.groupBy("Class", "prediction").count()
         .collect())
    c = {(int(row["Class"]), int(row["prediction"])): int(row["count"]) for row in r}
    tp, fp = c.get((1, 1), 0), c.get((0, 1), 0)
    tn, fn = c.get((0, 0), 0), c.get((1, 0), 0)
    return {"TP": tp, "FP": fp, "TN": tn, "FN": fn}


def metrics_from(cm: dict, roc_auc: float) -> dict:
    tp, fp, tn, fn = cm["TP"], cm["FP"], cm["TN"], cm["FN"]
    acc = (tp + tn) / max(tp + tn + fp + fn, 1)
    prec = tp / max(tp + fp, 1)
    rec = tp / max(tp + fn, 1)
    f1 = 2 * prec * rec / max(prec + rec, 1e-12)
    return {"Accuracy": acc, "Precision": prec, "Recall": rec, "F1": f1,
            "ROC_AUC": roc_auc, **cm}


def main() -> None:
    spark = get_spark("SecureBig-Fraud", cores="4", mem="3g")
    print("== Phase 7: ingest + clean ==")
    df = (spark.read.csv(str(CSV), header=True, inferSchema=True))
    n0 = df.count()
    df = df.dropDuplicates().dropna()
    print(f"rows: {n0} -> {df.count()} after duplicate/NA drop")
    print(f"schema: {', '.join(df.columns)}")

    # ---- Phase 7: features ---------------------------------------------------
    # Include all columns except the label. Time and Amount are raw (unscaled)
    # alongside PCA-normalized V1–V28, so we apply StandardScaler to level the
    # field for linear/probabilistic models (LR, NB) while trees are unaffected.
    feature_cols = [c for c in df.columns if c != "Class"]
    assembler = VectorAssembler(inputCols=feature_cols, outputCol="raw_features")
    scaler = StandardScaler(inputCol="raw_features", outputCol="features",
                            withStd=True, withMean=False)
    from pyspark.ml import Pipeline as _P
    prep_model = _P(stages=[assembler, scaler]).fit(df)
    df = prep_model.transform(df).select("features", "Class", "Time", "Amount")

    train, test = df.randomSplit([0.8, 0.2], seed=SEED)
    n_fraud = train.filter("Class = 1").count()
    n_legit = train.filter("Class = 0").count()
    print(f"train: {train.count()} rows (fraud {n_fraud} / legit {n_legit})")
    print(f"test : {test.count()} rows (untouched natural distribution)")

    # ---- Phase 8: imbalance handling = oversample train fold to ≈1:10 ---------
    # (1:1 would double training cost for little gain; 1:10 is a documented,
    #  defensible middle ground. Oversampling happens ONLY on the train fold.)
    fraud_train = train.filter("Class = 1")
    legit_train = train.filter("Class = 0")
    target_fraud = n_legit // 10
    k = max(target_fraud // n_fraud, 1)
    fraud_up = fraud_train.crossJoin(
        spark.range(k).withColumnRenamed("id", "dup")).drop("dup")
    train_bal = legit_train.unionByName(fraud_up.select(legit_train.columns))
    train_bal = train_bal.cache()
    train_bal.count()
    n_bal_fraud = train_bal.filter("Class=1").count()
    print(f"oversampled train: {train_bal.count()} rows "
          f"(fraud {n_bal_fraud} ≈ 1:{n_legit // max(n_bal_fraud, 1)})", flush=True)

    # ---- Phase 9: train + evaluate the 5 models ------------------------------
    evaluator = BinaryClassificationEvaluator(labelCol="Class",
                                              rawPredictionCol="probability",
                                              metricName="areaUnderROC")
    rows, best = [], None
    scored_fraud_sample = None
    for name, maker in MODELS.items():
        import time
        t0 = time.time()
        model = Pipeline(stages=[maker()]).fit(train_bal)
        pred = model.transform(test)
        cm = confusion_counts(pred)
        try:
            auc = evaluator.evaluate(pred)
        except Exception:
            auc = float("nan")
        m = metrics_from(cm, auc)
        m["Model"] = name
        m["train_seconds"] = round(time.time() - t0, 1)
        rows.append(m)
        print(f"{name:<20} acc={m['Accuracy']:.4f} P={m['Precision']:.4f} "
              f"R={m['Recall']:.4f} F1={m['F1']:.4f} AUC={m['ROC_AUC']:.4f} "
              f"({m['train_seconds']}s)")
        save_pd(pred.groupBy("Class", "prediction").count().toPandas(),
                f"results/model_metrics/fraud_confusion_{name.replace(' ', '_').lower()}.csv")
        if scored_fraud_sample is None:
            scored_fraud_sample = (pred.select("Time", "Amount", "Class", "prediction",
                                               F.round(vector_to_array("probability")[1], 6)
                                               .alias("fraud_prob"))
                                   .limit(2000).toPandas())

    import pandas as pd
    pdf = pd.DataFrame(rows)[["Model", "Accuracy", "Precision", "Recall", "F1",
                              "ROC_AUC", "TP", "FP", "TN", "FN", "train_seconds"]]
    save_pd(pdf, "results/model_metrics/fraud_metrics.csv")
    print("\nModel comparison (fraud):")
    print(pdf.to_string(index=False))

    # ---- ROC curve points + FULL test-fold export for the best model --------
    best_name = pdf.sort_values("F1", ascending=False).iloc[0]["Model"]
    print(f"\nbest model by F1: {best_name}", flush=True)
    maker = MODELS[best_name]
    model = Pipeline(stages=[maker()]).fit(train_bal)
    pred_best = model.transform(test)
    cm_best = confusion_counts(pred_best)
    auc_best = evaluator.evaluate(pred_best)
    print(f"best-model test metrics: {cm_best} AUC={auc_best:.4f}", flush=True)
    (pred_best.select("Time", "Amount", "Class", "prediction",
                      F.round(vector_to_array("probability")[1], 6).alias("fraud_prob"))
     .toPandas()
     .to_csv(RESULTS / "fraud" / "fraud_scored_test.csv", index=False))
    print(f"exported full test-fold predictions -> results/fraud/fraud_scored_test.csv "
          f"({pred_best.count()} rows)", flush=True)
    pred = pred_best.select("Class", "probability").toPandas()
    import numpy as np
    probs = pred["probability"].apply(lambda v: float(v[1])).to_numpy()
    y = pred["Class"].to_numpy()
    order = np.argsort(-probs)
    y, probs = y[order], probs[order]
    tp = np.cumsum(y); fp = np.cumsum(1 - y)
    tpr = tp / max(tp[-1], 1); fpr = fp / max(fp[-1], 1)
    pts = [[round(float(f), 5), round(float(t), 5)] for f, t in
           zip(fpr[:: max(len(fpr) // 120, 1)], tpr[:: max(len(tpr) // 120, 1)])]
    (RESULTS / "fraud" / "roc_points_best.json").write_text(
        json.dumps({"model": best_name, "points": pts}), encoding="utf-8")
    scored_fraud_sample.to_csv(RESULTS / "fraud" / "fraud_scored_sample.csv", index=False)
    spark.stop()
    print("fraud pipeline complete.")


if __name__ == "__main__":
    main()
