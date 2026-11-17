---
marp: true
theme: default
paginate: true
backgroundColor: #070B16
color: #E6F1FF
style: |
  section { font-family: 'Segoe UI', sans-serif; }
  h1 { color: #00F0FF; }
  h2 { color: #00F0FF; font-size: 28px; }
  table { font-size: 18px; }
  strong { color: #00F0FF; }
  em { color: #A855F7; }
---

<!-- Slide 1 -->
# 🔒 SecureBig

## A Privacy-Preserving Big Data Analytics Framework for Fraud and Insider Threat Detection

**Student:** Adarsh Singh
**Course:** CBCA293 — Security and Privacy for Big Data Analytics
**Program:** BCA 3rd Year (2025–2026)

---

<!-- Slide 2 -->
## Problem Statement

### Two Critical Enterprise Security Challenges:

🏦 **Financial Fraud Detection**
- Credit card fraud costs billions annually
- Fraudulent transactions are rare (0.17%) — needle in a haystack
- Traditional rules miss sophisticated patterns

👤 **Insider Threat Detection**
- Trusted employees misusing access privileges
- After-hours data exfiltration, credential abuse, snooping
- Costs organizations $15.4M/year on average (Ponemon Institute)

### Key Question:
> *How to detect threats at scale while preserving data privacy?*

---

<!-- Slide 3 -->
## Objectives

1. ✅ Build an end-to-end **Big Data security analytics platform**
2. ✅ Detect **financial fraud** using real-world credit card data
3. ✅ Detect **insider threats** from enterprise activity logs
4. ✅ Apply **privacy-preserving** techniques (masking, pseudonymization, hashing)
5. ✅ Enforce **HDFS access control** with POSIX ACLs
6. ✅ Implement **5 fraud rules** using Apache Hive
7. ✅ Process **security logs** using Apache Pig
8. ✅ Train **5 ML models** using Spark MLlib on both datasets
9. ✅ Compare models using **Accuracy, Precision, Recall, F1, ROC-AUC**
10. ✅ Visualize through **Power BI dashboard** and **3D web UI**

---

<!-- Slide 4 -->
## System Architecture

```
  Credit Card Data (284,807 txns)    User Activity (200 users × 90 days)
            │                                    │
            └──────────── HDFS ──────────────────┘
                          │
              ┌───────────┼───────────┐
              │           │           │
            HIVE         PIG       PRIVACY
          (5 Rules)     (ETL)    (Mask/Hash/RBAC)
              │           │           │
              └───────────┼───────────┘
                          │
                    SPARK MLlib
                   (5 Models × 2)
                          │
                ┌─────────┴─────────┐
                │                   │
             FRAUD             INSIDER THREAT
           DETECTION            DETECTION
                │                   │
                └─────────┬─────────┘
                          │
               ┌──────────┴──────────┐
               │                     │
           POWER BI              3D WEB UI
          (6 Pages)             (Three.js)
```

---

<!-- Slide 5 -->
## Datasets

### Dataset 1: ULB Credit Card Fraud
| Property | Value |
|---|---|
| Transactions | **284,807** |
| Frauds | **492** (0.173%) |
| Features | Time, V1–V28 (PCA), Amount |
| Imbalance | **1:577** |

### Dataset 2: Enterprise Activity Logs (Simulated)
| Property | Value |
|---|---|
| Users | **200** employees |
| Duration | **90 days** (13 weeks) |
| Events | **175,000+** across 4 log files |
| Threat Actors | **10** users in 3 scenarios |
| Scenarios | USB exfil, credential abuse, file snooping |

---

<!-- Slide 6 -->
## HDFS Security

### Zone Architecture
```
/securebig/
├── raw/          (chmod 755) — Immutable ingested data
├── processed/    (chmod 755) — Cleaned feature tables
├── secure/
│   ├── masked_data/      (chmod 640)
│   ├── restricted_data/  (chmod 750) — Re-ID maps
│   └── anonymized_data/  — For analysts
├── results/      — ML outputs
└── reports/      — Dashboards
```

### Access Control Verified:
- ❌ **GUEST** reading restricted data → **DENIED**
- ✅ **SECURITY_ANALYST** reading masked data → **ALLOWED**
- ❌ **DATA_ANALYST** reading raw PII → **DENIED**
- POSIX ACLs: `setfacl -m user:security_analyst:r--`

---

<!-- Slide 7 -->
## Privacy Mechanisms

| Technique | Example | Reversible? |
|---|---|---|
| **Masking** | `john.doe@corp.example` → `j***@corp.example` | No |
| **Name Masking** | `John Doe` → `J*** D***` | No |
| **Card Masking** | `4539 8812 3456 1234` → `************1234` | No |
| **Pseudonymization** | `E1042` → `USR_001` | Yes (with map) |
| **Hashing (SHA-256)** | `10.20.3.44` → `a7f3b2c1...` | No |

### RBAC Matrix:
| Role | Masked | Anonymized | Restricted |
|---|---|---|---|
| ADMIN | ✅ | ✅ | ✅ |
| SECURITY_ANALYST | ✅ | ✅ | ❌ |
| DATA_ANALYST | ❌ | ✅ | ❌ |
| GUEST | ❌ | ❌ | ❌ |

---

<!-- Slide 8 -->
## Apache Hive — Fraud Rule Engine

### 5 Weighted Fraud Rules:
| Rule | Condition | Weight |
|---|---|---|
| R1 HIGH_AMOUNT | `amount > 1000` | +30 |
| R2 HIGH_FREQUENCY | `>6000 txns/hour` | +20 |
| R3 UNUSUAL_TIME | `hour 1–5 AM` | +15 |
| R4 RAPID_VELOCITY | `>20 txns/10-min` | +20 |
| R5 AMOUNT_OUTLIER | `amount > μ + 3σ` | +15 |

### Risk Classification:
| Score | Level | Action |
|---|---|---|
| 0–30 | 🟢 LOW | Monitor |
| 31–60 | 🟡 MEDIUM | Review |
| 61–100 | 🔴 HIGH | Investigate |

---

<!-- Slide 9 -->
## Apache Pig — Log Processing

### ETL Pipeline:
```
Raw CSVs (logon.csv, file.csv)
    ↓ LOAD (PigStorage)
    ↓ FILTER (failed logins, sensitive files, external IPs)
    ↓ GROUP BY user
    ↓ FOREACH...GENERATE (feature counts)
    ↓ JOIN (merge feature tables)
    ↓ STORE → HDFS /processed/features
```

### Extracted Features:
- `failed_logins` — Count of failed authentication attempts
- `external_ip_logons` — Logins from outside corporate subnet
- `sensitive_file_access` — Access to confidential files
- `abnormal_score` — Composite heuristic risk metric

### Why Pig over Python?
> Pig compiles to **MapReduce/Tez DAGs** for distributed execution — scales to billions of log entries across a Hadoop cluster.

---

<!-- Slide 10 -->
## Spark MLlib — ML Pipeline

### Pipeline Flow:
```
Raw Data → Cleaning → VectorAssembler → StandardScaler
    → 80/20 Split (seed=42) → Oversample TRAIN only
    → Train 5 Models → Evaluate on TEST fold
```

### 5 Models:
1. **Logistic Regression** — Linear baseline
2. **Decision Tree** — Interpretable non-linear splits
3. **Random Forest** — Ensemble of 30 trees (reduces overfitting)
4. **Naive Bayes** — Probabilistic baseline
5. **Gradient-Boosted Trees** — Sequential error correction

### Class Imbalance Strategy:
- Fraud: Oversample minority from **1:577 → ~1:10** (train only)
- Insider: Oversample to **~1:3** (train only)
- **Test set never touched** → honest evaluation

---

<!-- Slide 11 -->
## Results — Fraud Detection

### Test Set: 56,705 transactions (83 frauds)

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|
| **Random Forest** | **0.9994** | **0.7802** | **0.8554** | **0.8161** | **0.9939** |
| GBT | 0.9990 | 0.6273 | 0.8313 | 0.7150 | 0.9793 |
| Decision Tree | 0.9980 | 0.4171 | 0.8795 | 0.5659 | 0.9460 |
| Logistic Regression | 0.9980 | 0.4061 | 0.8072 | 0.5403 | 0.9817 |
| Naive Bayes | 0.9910 | 0.0994 | 0.6386 | 0.1721 | 0.9681 |

### 🏆 Best: Random Forest
- Catches **71 of 83 frauds** with only **20 false alarms**
- Precision 78% keeps alert fatigue manageable

> ⚠️ **All models show >99% accuracy but F1 ranges from 0.17 to 0.82** — accuracy alone is misleading at 0.17% fraud rate!

---

<!-- Slide 12 -->
## Results — Insider Threat Detection

### Test Set: 512 user-weeks (20 suspicious)

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|
| **Random Forest** | **0.9961** | **0.9091** | **1.0000** | **0.9524** | **0.9991** |
| Naive Bayes | 0.9961 | 0.9091 | 1.0000 | 0.9524 | 0.9980 |
| Decision Tree | 0.9961 | 0.9500 | 0.9500 | 0.9500 | 0.9745 |
| GBT | 0.9961 | 0.9500 | 0.9500 | 0.9500 | 0.9996 |
| Logistic Regression | 0.9922 | 1.0000 | 0.8000 | 0.8889 | 0.9752 |

### 🏆 Best: Random Forest
- **100% recall** — catches all 20 suspicious user-weeks
- Only **2 false positives** out of 492 normal user-weeks
- Behavioral features (after-hours access, USB exfiltration) provide strong signal

---

<!-- Slide 13 -->
## Power BI Dashboard

### 6-Page Interactive Dashboard:

| Page | Purpose |
|---|---|
| 1. **Executive Overview** | KPIs, model summary, dataset slicer |
| 2. **Fraud Analytics** | Amount vs probability scatter, confusion matrix |
| 3. **Insider Threat** | Top-risk users, weekly trends, filters |
| 4. **ML Model Lab** | Cross-model comparison, F1/Precision/Recall bars |
| 5. **Privacy Monitor** | GRANT/DENY split, role×zone ACL audit |
| 6. **User Drill-Through** | Deep-dive into individual user activity |

### Technical Design:
- ⭐ **Star Schema**: 4 fact tables + 3 dimension tables
- 📊 **16+ DAX Measures** (Fraud Rate, Model Precision, Recall, F1, etc.)
- 🎨 **Custom SOC Dark Theme** (SecureBigSOC)
- 📁 **PBIP Format**: Version-controlled TMDL definitions

---

<!-- Slide 14 -->
## Security Insights & Future Scope

### Key Security Insights:
- 💡 **After-hours access** is the strongest behavioral indicator for insider threats
- 💡 **High-value transactions** (R1) most strongly correlated with actual fraud
- 💡 **USB exfiltration** scenarios are easiest to detect (extreme behavioral signature)
- 💡 **Accuracy is misleading** at 0.17% fraud rate — F1 and recall are the real story

### Future Scope:
1. 🔄 **Spark Structured Streaming** for real-time detection
2. 🧠 **Deep Learning** (LSTM, Transformer) for sequential behavior
3. 🤝 **Federated Learning** for cross-org privacy-preserving training
4. 📊 **Graph Neural Networks** for collusion detection
5. 🔐 **Differential Privacy** for mathematical privacy guarantees
6. 🔧 **Hyperparameter Tuning** via CrossValidator

---

<!-- Slide 15 -->
## Conclusion

### SecureBig Successfully Demonstrates:

✅ **End-to-end Big Data security pipeline**
  (HDFS → Hive → Pig → Spark MLlib → Power BI)

✅ **5 ML models** achieving F1 = **0.82** (fraud) and **0.95** (insider threat)

✅ **Privacy preservation** through masking, pseudonymization, hashing, RBAC

✅ **5 Hive fraud rules** with weighted risk scoring

✅ **Professional visualization** — Power BI (6 pages) + 3D Three.js dashboard

✅ **Reproducible** — seed=42, SHA-256 manifests, pinned dependencies

---

### 🙏 Thank You!

**Questions?**

*SecureBig is an academic prototype for CBCA293.*
*Not a production security system.*

---

**GitHub**: https://github.com/adarsh4970/SecureBig
