# SecureBig: A Privacy-Preserving Big Data Analytics Framework for Fraud and Insider Threat Detection

## PROJECT REPORT

**Course:** CBCA293 — Security and Privacy for Big Data Analytics  
**Student:** Adarsh Singh  
**Academic Year:** 2025–2026 (BCA 3rd Year)  
**Platform:** SecureBig — Academic Prototype

---

## Table of Contents

1. [Abstract](#1-abstract)
2. [Introduction](#2-introduction)
3. [Problem Statement](#3-problem-statement)
4. [Motivation](#4-motivation)
5. [Objectives](#5-objectives)
6. [Literature & Background](#6-literature--background)
7. [Proposed Architecture](#7-proposed-architecture)
8. [Dataset Description](#8-dataset-description)
9. [HDFS Security](#9-hdfs-security)
10. [Privacy Mechanisms](#10-privacy-mechanisms)
11. [Hive Implementation](#11-hive-implementation)
12. [Pig Implementation](#12-pig-implementation)
13. [Spark Implementation](#13-spark-implementation)
14. [Machine Learning Models](#14-machine-learning-models)
15. [Model Evaluation](#15-model-evaluation)
16. [Power BI Dashboard](#16-power-bi-dashboard)
17. [Results](#17-results)
18. [Discussion](#18-discussion)
19. [Limitations](#19-limitations)
20. [Future Scope](#20-future-scope)
21. [Conclusion](#21-conclusion)
22. [References](#22-references)

---

## 1. Abstract

SecureBig is an academic prototype of a privacy-preserving big data security analytics platform that addresses two critical enterprise security challenges: financial fraud detection and insider threat detection. The system integrates Apache Spark MLlib, HDFS with access control lists, Apache Hive for rule-based fraud scoring, Apache Pig for log processing, and a comprehensive privacy layer implementing masking, pseudonymization, and SHA-256 hashing. Five machine learning models — Logistic Regression, Decision Tree, Random Forest, Naive Bayes, and Gradient-Boosted Trees — are trained and evaluated on both datasets using Accuracy, Precision, Recall, F1-score, and ROC-AUC. The fraud detection pipeline achieves an F1 score of **0.8161** (Random Forest) on the ULB credit card dataset (284,807 transactions, 0.17% fraud rate), while the insider threat pipeline achieves an F1 of **0.9524** on simulated CERT-style enterprise activity logs across 200 users. Results are visualized through both a Power BI dashboard (6 pages, star schema) and an interactive 3D web interface built with Three.js and ECharts.

---

## 2. Introduction

Organizations today generate massive volumes of data across financial transactions, network logs, user activity records, and access control events. This data, while valuable for business intelligence, also represents a critical attack surface. Two of the most damaging security threats facing enterprises are:

1. **Financial Fraud** — Unauthorized or deceptive financial transactions that result in direct monetary loss.
2. **Insider Threats** — Malicious or negligent actions by trusted employees who misuse their access privileges.

Traditional rule-based detection systems struggle with the volume, velocity, and variety of modern data streams. Big data technologies such as Hadoop (HDFS), Hive, Pig, and Spark provide the scalability needed to process these streams, while machine learning enables the detection of subtle patterns that hand-crafted rules miss.

SecureBig demonstrates how these technologies can be combined into a cohesive security analytics pipeline while maintaining data privacy through masking, pseudonymization, and role-based access control.

---

## 3. Problem Statement

How can an organization detect financial fraud and insider threats across large-scale datasets while:

- Processing hundreds of thousands of transactions efficiently?
- Protecting sensitive personal information (PII)?
- Enforcing role-based access controls on analytical data?
- Comparing multiple ML models to find the best detector?
- Presenting actionable intelligence through interactive dashboards?

---

## 4. Motivation

- **Financial Impact**: Global fraud losses exceed $5 trillion annually. Early detection saves organizations significant resources.
- **Insider Threat**: According to the Ponemon Institute, insider incidents cost an average of $15.4 million per organization per year.
- **Data Privacy**: GDPR, India's DPDP Act, and similar regulations mandate privacy-preserving data handling.
- **Academic Relevance**: The CBCA293 curriculum specifically requires demonstrating the intersection of Big Data, Security, and Privacy.

---

## 5. Objectives

1. Build a simulated enterprise security analytics platform using Big Data technologies.
2. Implement fraud detection on real-world credit card transaction data.
3. Implement insider threat detection on simulated enterprise activity logs.
4. Apply privacy-preserving techniques (masking, pseudonymization, hashing).
5. Enforce HDFS-based access control with POSIX ACLs.
6. Implement rule-based fraud scoring using Apache Hive.
7. Process security logs using Apache Pig.
8. Train and evaluate 5 ML models using Spark MLlib.
9. Compare models using Accuracy, Precision, Recall, F1, ROC-AUC, and Confusion Matrix.
10. Visualize results through Power BI dashboards and a 3D web interface.

---

## 6. Literature & Background

### 6.1 Big Data Security Analytics

Big Data analytics for security involves collecting, storing, and analyzing large volumes of security-relevant data to detect threats. The Hadoop ecosystem (HDFS, Hive, Pig, Spark) provides distributed storage and processing capabilities essential for handling enterprise-scale datasets (White, 2015).

### 6.2 Fraud Detection

Credit card fraud detection is a well-studied binary classification problem characterized by extreme class imbalance. The ULB/Kaggle Credit Card Fraud Detection dataset is the benchmark in this domain, containing PCA-transformed features to protect cardholder privacy (Dal Pozzolo et al., 2015).

### 6.3 Insider Threat Detection

The CERT Division at Carnegie Mellon University has published multiple versions of synthetic insider threat datasets (Glasser & Lindauer, 2013). Insider threats are categorized into behavioral archetypes including data exfiltration, credential abuse, and unauthorized access to sensitive information.

### 6.4 Privacy-Preserving Analytics

Data privacy techniques include:
- **Masking**: Replacing sensitive values with obfuscated versions (e.g., `j***@example.com`)
- **Pseudonymization**: Replacing identifiers with reversible pseudonyms (GDPR Article 4)
- **Hashing**: One-way cryptographic transformation (SHA-256)
- **Encryption**: Protecting data at rest and in transit (Hadoop KMS/TDE)

### 6.5 Machine Learning for Security

Supervised learning models (Logistic Regression, Decision Trees, Random Forest, Naive Bayes, Gradient-Boosted Trees) have been widely applied to anomaly and fraud detection. Class imbalance handling through oversampling (SMOTE, random oversampling) is critical for achieving meaningful recall on minority classes (Chawla et al., 2002).

---

## 7. Proposed Architecture

```
DATA SOURCES
     │
     ├─── Credit Card Fraud Dataset (284,807 transactions)
     └─── User Activity Logs (200 users × 90 days)
              │
          ┌───┴───┐
          │  HDFS  │  /raw → /processed → /secure → /results
          └───┬───┘
              │
      ┌───────┼────────┐
      │       │        │
    Hive     Pig    Privacy Layer
   (5 Fraud  (Log    (Masking, Pseudonymization,
    Rules)   ETL)    Hashing, RBAC, Audit)
      │       │        │
      └───────┼────────┘
              │
        Apache Spark MLlib
        (5 Models × 2 Datasets)
              │
     ┌────────┴────────┐
     │                 │
   Fraud          Insider Threat
   Detection      Detection
     │                 │
     └────────┬────────┘
              │
      Model Evaluation
      (Accuracy, Precision, Recall, F1, ROC-AUC)
              │
      ┌───────┴───────┐
      │               │
   Power BI      3D Web UI
   (6 pages)     (Three.js)
```

The architecture follows a layered approach:
1. **Data Layer**: Raw data stored in HDFS with zone-based access control.
2. **Processing Layer**: Hive for SQL-based rule scoring, Pig for ETL log processing.
3. **Privacy Layer**: Transforms applied before analytical access.
4. **ML Layer**: Spark MLlib pipelines with VectorAssembler, StandardScaler, and 5 classifiers.
5. **Visualization Layer**: Power BI star schema dashboard + Three.js 3D interface.

---

## 8. Dataset Description

### 8.1 Dataset 1: Credit Card Fraud Detection (ULB)

| Property | Value |
|---|---|
| Source | ULB Machine Learning Group via OpenML |
| Total Transactions | 284,807 |
| Fraudulent Transactions | 492 (0.173%) |
| Legitimate Transactions | 284,315 (99.827%) |
| Features | Time, V1–V28 (PCA-transformed), Amount |
| Target Variable | Class (0 = legitimate, 1 = fraud) |
| Class Imbalance Ratio | 1:577 |

The V1–V28 features are PCA-transformed to protect cardholder privacy. `Time` represents seconds elapsed from the first transaction, and `Amount` is the transaction value in euros. After deduplication, 283,726 unique transactions remain (1,081 duplicates removed).

### 8.2 Dataset 2: Insider Threat Activity Logs (Simulated)

| Property | Value |
|---|---|
| Source | Deterministic simulation (seed=42) following CERT r4.2 archetypes |
| Users | 200 employees |
| Duration | 90 days (13 weeks) |
| Total Events | ~175,000+ |
| Log Files | logon.csv, file.csv, device.csv, http.csv |
| Scenario Actors | 10 users across 3 threat scenarios |

**Transparency Note**: The real CERT r4.2 dataset is ~90 GB and requires a signed license agreement. This project uses a deterministic simulation that faithfully replicates the documented behavioral archetypes:

| Scenario | Users | Behavior | Active Weeks |
|---|---|---|---|
| A_exfil_usb | E1042, E1077, E1131 | After-hours logons, bulk sensitive file copying, USB exfiltration (GB-scale) | 6–12 |
| B_new_ip_auth | E1058, E1103, E1188 | Failed logon bursts (5–15 attempts) from external IPs (185.220.*.*), then success | 4–10 |
| C_snooping | E1019, E1064, E1110, E1155 | Persistent access to sensitive files (payroll, PII, M&A docs) | 0–12 |

The analytic label is: **1** = user-week belongs to a scenario actor during their active weeks; **0** = otherwise. This is a scenario-derived label, transparently documented, not fabricated ground truth.

---

## 9. HDFS Security

### 9.1 Zone Architecture

```
/securebig/
├── raw/                    # Immutable raw data (chmod 755)
│   ├── transactions/       # Credit card CSV
│   ├── user_activity/      # Activity log CSVs
│   └── audit_logs/         # System audit records
├── processed/              # Cleaned, engineered features (chmod 755)
├── secure/                 # Privacy-controlled zone
│   ├── masked_data/        # Display-minimized records (chmod 640)
│   ├── restricted_data/    # Re-identification maps (chmod 750)
│   └── anonymized_data/    # Pseudonymized copies for analysts
├── results/                # ML outputs and metrics
└── reports/                # Executive reports
```

### 9.2 Permissions & ACLs

The HDFS layer demonstrates:
- **Coarse Permissions**: `chmod 750 /securebig/secure/restricted_data` (owner rwx, group r-x, others none)
- **Fine-Grained ACLs**: `setfacl -m user:security_analyst:r-- /securebig/secure/restricted_data`
- **Ownership**: `chown -R securebig_admin:supergroup /securebig/secure`
- **Default ACLs**: `setfacl -m default:user:security_analyst:r--` for ACL inheritance

### 9.3 Access Control Verification

| Test | User | Action | Zone | Result |
|---|---|---|---|---|
| Negative | guest | Read pseudonym map | restricted_data | **DENIED** |
| Positive | security_analyst | Read pseudonym map | restricted_data | **ALLOWED** |
| Negative | security_analyst | Write to restricted | restricted_data | **DENIED** |
| Positive | data_analyst | Read processed data | processed | **ALLOWED** |
| Negative | data_analyst | Read raw PII logs | raw | **DENIED** |

---

## 10. Privacy Mechanisms

### 10.1 Masking

```python
def mask_email(email):     # john.doe@corp.example → j***@corp.example
def mask_card(card):       # 4539 8812 3456 1234  → ************1234
def mask_name(name):       # John Doe             → J*** D***
```

### 10.2 Pseudonymization

Employee IDs are mapped to pseudonyms using SHA-256 prefix-based deterministic indexing:
```
E1042 → USR_001    E1077 → USR_042    E1131 → USR_089
```
The reverse mapping table is stored in the restricted zone (`/securebig/secure/restricted_data/`), accessible only to ADMIN users.

### 10.3 Hashing (SHA-256)

One-way cryptographic hashing is applied to quasi-identifiers (IP addresses, USB device IDs) that need to be compared but not reversed:
```
10.20.3.44  → a7f3b2c1e8d4...   (irreversible)
```

### 10.4 Role-Based Access Control (RBAC)

| Role | Masked Data | Anonymized Data | Restricted Data |
|---|---|---|---|
| ADMIN | ✅ GRANT | ✅ GRANT | ✅ GRANT |
| SECURITY_ANALYST | ✅ GRANT | ✅ GRANT | ❌ DENY |
| DATA_ANALYST | ❌ DENY | ✅ GRANT | ❌ DENY |
| GUEST | ❌ DENY | ❌ DENY | ❌ DENY |

### 10.5 Audit Logging

Every access decision is recorded in `privacy_audit_log.jsonl`:
```json
{"role": "GUEST", "zone": "masked_data", "decision": "DENY", "note": "ACL matrix lookup"}
```

### 10.6 Key Distinctions

| Concept | Purpose | Reversible? |
|---|---|---|
| Authentication | Verify WHO you are (Kerberos) | N/A |
| Authorization | Verify WHAT you may do (ACLs) | N/A |
| Masking | Hide display fields | No (partial) |
| Pseudonymization | Replace identifiers | Yes (with map) |
| Hashing | One-way transformation | No |
| Encryption | Protect data at rest/transit | Yes (with key) |

---

## 11. Hive Implementation

### 11.1 Tables

- `transactions`: External table over `/securebig/raw/transactions` (31 ULB columns)
- `security_events`: External table over `/securebig/processed/user_activity`
- `fraud_results`: Partitioned managed table for scored transactions
- `vw_security_events_masked`: Privacy-preserving view masking user pseudonyms and IPs

### 11.2 Fraud Rule Engine (5 Rules)

| Rule | Condition | Weight | Rationale |
|---|---|---|---|
| R1 HIGH_AMOUNT | `amount > 1000` | +30 | Large transactions are higher risk |
| R2 HIGH_FREQUENCY | `>6000 txns/hour` | +20 | Abnormal transaction density |
| R3 UNUSUAL_TIME | `hour BETWEEN 1 AND 5` | +15 | Off-business-hours activity |
| R4 RAPID_VELOCITY | `>20 txns/10-min window` | +20 | Rapid consecutive transactions |
| R5 AMOUNT_OUTLIER | `amount > mean + 3σ` | +15 | Statistical anomaly (Z-score) |

### 11.3 Risk Classification

| Score Range | Risk Level |
|---|---|
| 0–30 | LOW |
| 31–60 | MEDIUM |
| 61–100 | HIGH |

---

## 12. Pig Implementation

### 12.1 Log Processing Pipeline

```
Raw CSVs (logon.csv, file.csv)
    ↓ LOAD (PigStorage)
    ↓ FILTER (remove headers, isolate failed logins, sensitive files)
    ↓ FOREACH...GENERATE (project relevant fields)
    ↓ GROUP BY user
    ↓ COUNT aggregations (failed_logins, external_ip_logons, sensitive_file_access)
    ↓ JOIN (multi-relation feature merge)
    ↓ STORE → /securebig/processed/user_activity/features
```

### 12.2 Why Pig Instead of Python?

Apache Pig compiles data flow scripts into directed acyclic graphs (DAGs) of MapReduce or Tez jobs that execute in parallel across a Hadoop cluster. For terabyte-scale log processing, Pig provides:
- **Horizontal scalability**: Automatic parallelism across cluster nodes
- **Direct HDFS integration**: Reads/writes directly from HDFS security zones
- **Optimized execution**: Tez engine optimizations for multi-stage pipelines

While Python/pandas works for our demonstration scale (~175K events), Pig becomes essential when processing billions of audit log entries in production environments.

---

## 13. Spark Implementation

### 13.1 Pipeline Structure

Both pipelines follow the same Spark MLlib workflow:

```
Raw Data → Cleaning (dedup, null drop) → Feature Engineering
    → VectorAssembler → StandardScaler → Train/Test Split (80/20, seed=42)
    → Minority Oversampling (TRAIN FOLD ONLY)
    → Model Training (5 models) → Prediction → Evaluation
```

### 13.2 Feature Engineering

**Fraud Pipeline**: 30 features (Time, V1–V28, Amount) → StandardScaler → feature vector

**Insider Pipeline**: 12 behavioral features per user-week:
- `logon_count`, `failed_login_count`, `after_hours_logons`, `external_ip_logons`
- `file_access_count`, `sensitive_file_count`, `file_copy_count`
- `usb_connects`, `usb_bytes`, `upload_events`, `upload_bytes`, `total_events`

### 13.3 Class Imbalance Handling

The credit card dataset has a 1:577 fraud-to-legitimate ratio. A model that predicts "always legitimate" achieves 99.83% accuracy but 0% recall — completely useless for fraud detection.

**Strategy**: Random oversampling applied **strictly to the training fold only**:
- Fraud: Minority class oversampled from 1:577 to ~1:10 ratio
- Insider: Minority class oversampled to ~1:3 ratio
- Test set is **never touched** — preserves natural distribution for honest evaluation

---

## 14. Machine Learning Models

| # | Model | Why Selected | Key Parameters |
|---|---|---|---|
| 1 | Logistic Regression | Baseline linear classifier; interpretable coefficients | maxIter=50 |
| 2 | Decision Tree | Captures non-linear splits; highly interpretable | maxDepth=5–6 |
| 3 | Random Forest | Ensemble of trees reduces overfitting; robust | numTrees=30, maxDepth=6–8 |
| 4 | Naive Bayes | Fast probabilistic classifier; baseline for comparison | modelType="gaussian" |
| 5 | Gradient-Boosted Trees | Sequential boosting corrects errors; high accuracy | maxIter=10–15, maxDepth=4 |

All models use `seed=42` for reproducibility where supported by Spark MLlib.

---

## 15. Model Evaluation

### 15.1 Evaluation Metrics

| Metric | Formula | Why Important for Security |
|---|---|---|
| Accuracy | (TP+TN) / Total | Overall correctness (misleading if imbalanced) |
| Precision | TP / (TP+FP) | How many flagged items are truly threats (reduces false alarms) |
| Recall | TP / (TP+FN) | How many real threats are caught (critical: missing fraud = loss) |
| F1-score | 2×P×R / (P+R) | Balanced measure of precision and recall |
| ROC-AUC | Area under ROC curve | Discriminative ability across all thresholds |

### 15.2 Fraud Detection Results (Test: 56,705 transactions, 83 frauds)

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|
| **Random Forest** | **0.9994** | **0.7802** | **0.8554** | **0.8161** | **0.9939** |
| GBT | 0.9990 | 0.6273 | 0.8313 | 0.7150 | 0.9793 |
| Decision Tree | 0.9980 | 0.4171 | 0.8795 | 0.5659 | 0.9460 |
| Logistic Regression | 0.9980 | 0.4061 | 0.8072 | 0.5403 | 0.9817 |
| Naive Bayes | 0.9910 | 0.0994 | 0.6386 | 0.1721 | 0.9681 |

**Best Model**: Random Forest — captures 71 of 83 frauds with only 20 false alarms.

### 15.3 Insider Threat Detection Results (Test: 512 user-weeks, 20 suspicious)

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|
| **Random Forest** | **0.9961** | **0.9091** | **1.0000** | **0.9524** | **0.9991** |
| Naive Bayes | 0.9961 | 0.9091 | 1.0000 | 0.9524 | 0.9980 |
| Decision Tree | 0.9961 | 0.9500 | 0.9500 | 0.9500 | 0.9745 |
| GBT | 0.9961 | 0.9500 | 0.9500 | 0.9500 | 0.9996 |
| Logistic Regression | 0.9922 | 1.0000 | 0.8000 | 0.8889 | 0.9752 |

**Best Model**: Random Forest — 100% recall (catches all 20 suspicious user-weeks) with only 2 false positives.

### 15.4 Confusion Matrix (Best Models)

**Fraud (Random Forest)**:
| | Predicted Legit | Predicted Fraud |
|---|---|---|
| **Actual Legit** | TN = 56,602 | FP = 20 |
| **Actual Fraud** | FN = 12 | TP = 71 |

**Insider Threat (Random Forest)**:
| | Predicted Normal | Predicted Suspicious |
|---|---|---|
| **Actual Normal** | TN = 490 | FP = 2 |
| **Actual Suspicious** | FN = 0 | TP = 20 |

---

## 16. Power BI Dashboard

### 16.1 Data Model (Star Schema)

**Fact Tables**: FACT_TRANSACTIONS (56,705 rows), FACT_MODEL_RESULTS (10 evaluations), FACT_USER_WEEK_FEATURES (2,600 rows), FACT_ACCESS_AUDIT (12 decisions)

**Dimension Tables**: DIM_MODEL, DIM_RISK, DIM_DATASET_FACTS

### 16.2 Dashboard Pages

| Page | Title | Key Visuals |
|---|---|---|
| 1 | Security Executive Overview | KPI cards, F1 donut, model summary table |
| 2 | Fraud Analytics | Scatter (amount vs probability), confusion matrix, filters |
| 3 | Insider Threat Analytics | Top-risk users, weekly trends, prediction filters |
| 4 | ML Model Lab | Cross-model F1/Precision/Recall comparison, dataset slicer |
| 5 | Privacy & Access Monitor | GRANT/DENY donut, role×zone ACL matrix, audit table |
| 6 | User Detail (Drill-Through) | Deep investigation into individual user activities |

### 16.3 DAX Measures (Sample)

```
Fraud Rate % = DIVIDE([Fraud Count], [Scored Transactions], 0) * 100
Model Precision = DIVIDE([True Positives], [True Positives] + [False Positives], 0)
Model Recall = DIVIDE([True Positives], [True Positives] + [False Negatives], 0)
Model F1 = 2 * [Model Precision] * [Model Recall] / ([Model Precision] + [Model Recall])
```

---

## 17. Results

### 17.1 Key Findings

1. **Random Forest** is the best model for both tasks, achieving the highest F1 score.
2. **Accuracy alone is misleading**: All models show >99% accuracy due to extreme class imbalance, but F1 scores range from 0.17 to 0.82 for fraud detection.
3. **Naive Bayes performs poorly** on the fraud dataset due to sensitivity to unscaled features (Time and Amount dominate PCA-normalized V1–V28).
4. **Training-only oversampling** is critical: oversampling the test set would artificially inflate metrics.
5. **Insider threat detection achieves higher scores** because the behavioral features (after-hours access, sensitive file copying, USB exfiltration) create strong signal separation.

### 17.2 Security Insights

- Rule R1 (HIGH_AMOUNT) flags transactions most strongly correlated with actual fraud
- After-hours logon activity (20:00–05:00) is the strongest single behavioral indicator for insider threats
- USB exfiltration scenarios (Scenario A) are the easiest to detect due to their extreme behavioral signature

---

## 18. Discussion

### 18.1 Model Selection

The Random Forest classifier provides the best balance between precision (minimizing false alarms) and recall (catching real threats). In a production Security Operations Center (SOC), this balance is critical — too many false alarms leads to "alert fatigue," while missed threats lead to direct losses.

### 18.2 Class Imbalance

The 0.17% fraud rate in the ULB dataset mirrors real-world scenarios. Our training-only oversampling strategy maintains honest evaluation while providing enough minority examples for the model to learn from.

### 18.3 Privacy vs Utility

The privacy layer demonstrates that meaningful analytics can be performed on pseudonymized data without accessing raw PII. The role-based access matrix ensures least-privilege access.

---

## 19. Limitations

1. **Simulated Insider Data**: The insider threat dataset is synthetically generated; real-world insider behavior is more subtle and variable.
2. **Single Machine**: The Spark pipeline runs in local mode rather than a distributed cluster.
3. **No Real-Time Processing**: This is a batch analytics system, not a streaming solution.
4. **Limited Feature Engineering**: Advanced techniques like temporal embeddings or graph-based features are not implemented.
5. **No Hyperparameter Tuning**: Models use reasonable defaults rather than cross-validated optimal parameters.
6. **Academic Prototype**: This is NOT a production-grade security system.

---

## 20. Future Scope

1. **Spark Structured Streaming** for real-time fraud detection.
2. **Deep Learning** models (LSTM, Transformer) for sequential behavioral analysis.
3. **Federated Learning** for privacy-preserving cross-organization model training.
4. **Graph Neural Networks** for detecting collusion and coordinated insider threats.
5. **Integration with SIEM** (Splunk, ELK) for production SOC deployment.
6. **Differential Privacy** for mathematically guaranteed privacy bounds.
7. **Automated Hyperparameter Tuning** using Spark MLlib's CrossValidator.
8. **Real CERT r4.2 Dataset** evaluation when license access is available.

---

## 21. Conclusion

SecureBig successfully demonstrates a complete, end-to-end big data security analytics pipeline that:

- Ingests and processes two distinct security datasets using the Hadoop ecosystem
- Enforces privacy through masking, pseudonymization, hashing, and RBAC
- Implements 5 rule-based fraud detection rules using Apache Hive
- Processes security logs using Apache Pig
- Trains and evaluates 5 machine learning models using Spark MLlib
- Achieves strong detection performance (F1 = 0.8161 for fraud, 0.9524 for insider threats)
- Visualizes results through a professional Power BI dashboard and 3D web interface

The project validates that **Big Data + Security + Privacy + Machine Learning + Visualization** can be integrated into a cohesive analytical platform suitable for enterprise security monitoring, while maintaining data privacy and access control throughout the pipeline.

---

## 22. References

1. Dal Pozzolo, A., Caelen, O., Johnson, R. A., & Bontempi, G. (2015). *Calibrating Probability with Undersampling for Unbalanced Classification*. IEEE Symposium on Computational Intelligence and Data Mining.

2. Glasser, J., & Lindauer, B. (2013). *Bridging the Gap: A Pragmatic Approach to Generating Insider Threat Data*. IEEE Security and Privacy Workshops.

3. Chawla, N. V., Bowyer, K. W., Hall, L. O., & Kegelmeyer, W. P. (2002). *SMOTE: Synthetic Minority Over-sampling Technique*. Journal of Artificial Intelligence Research, 16, 321–357.

4. White, T. (2015). *Hadoop: The Definitive Guide* (4th ed.). O'Reilly Media.

5. Apache Spark Documentation. *MLlib: Machine Learning Library*. https://spark.apache.org/mllib/

6. Apache Hive Documentation. https://hive.apache.org/

7. Apache Pig Documentation. https://pig.apache.org/

8. European Union. (2016). *General Data Protection Regulation (GDPR)*. Regulation (EU) 2016/679.

9. Ponemon Institute. (2023). *Cost of Insider Threats Global Report*.

10. ULB Machine Learning Group. *Credit Card Fraud Detection Dataset*. OpenML / Kaggle.
