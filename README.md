# 🔒 SecureBig

**A Privacy-Preserving Big Data Analytics Framework for Fraud and Insider Threat Detection**

> Academic prototype for **CBCA293 — Security and Privacy for Big Data Analytics** (BCA 3rd Year)

---

## 🏗️ Architecture

```
DATA SOURCES
     │
     ├── Credit Card Fraud (ULB, 284,807 txns)
     └── Insider Threat Activity (200 users × 90 days)
             │
         ┌───┴───┐
         │  HDFS  │  Zones: /raw → /processed → /secure → /results
         └───┬───┘
             │
     ┌───────┼───────┐
     │       │       │
   Hive     Pig   Privacy
  (Rules)  (ETL)  (Mask/Hash/RBAC)
     │       │       │
     └───────┼───────┘
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
     (Accuracy, Precision, Recall,
      F1, ROC-AUC, Confusion Matrix)
             │
     ┌───────┴───────┐
     │               │
  Power BI      3D Web UI
  Dashboard     (Three.js)
```

## 📂 Project Structure

```
SecureBig/
├── securebig-backend/          # Python + PySpark backend
│   ├── data/                   # Dataset acquisition & generation
│   ├── spark/                  # ML pipelines (fraud + insider threat)
│   ├── privacy/                # Masking, pseudonymization, hashing, RBAC
│   ├── hdfs/                   # HDFS setup, permissions, ACLs
│   ├── hive/                   # Fraud rule engine (5 rules)
│   ├── pig/                    # Log processing ETL
│   ├── results/                # ML metrics, confusion matrices, Power BI exports
│   ├── reports/                # Power BI project (.pbip)
│   ├── notebooks/              # Colab & Databricks guide
│   └── run_all.py              # Master runner (all phases)
│
└── securebig-3d-ui/            # Interactive 3D dashboard
    ├── index.html              # Three.js globe + ECharts + live feed
    └── dashboard_data.json     # Real Spark results overlay
```

## 🚀 Quick Start

### Prerequisites
- Python 3.12+ with `pip`
- Java 17+ (for PySpark)

### Run the Full Pipeline
```bash
cd securebig-backend
pip install -r requirements.txt
python run_all.py
```

This executes all phases automatically:
1. **Phase 1a** — Download credit card fraud dataset (284,807 rows)
2. **Phase 1b** — Generate insider threat activity logs (200 users, 90 days)
3. **Phase 4** — Privacy layer (masking, pseudonymization, hashing, RBAC audit)
4. **Phase 7-10** — Spark MLlib pipelines (5 models × 2 datasets)
5. **Phase 11** — Export results (Power BI star schema, dashboard JSON, Excel)

### View the 3D Dashboard
```bash
cd securebig-3d-ui
python -m http.server 8080
# Open http://localhost:8080
```

## 📊 ML Results (Real, seed=42)

### Fraud Detection (Best: Random Forest)
| Model | F1 | Precision | Recall | ROC-AUC |
|---|---|---|---|---|
| Random Forest | **0.8161** | 0.7802 | 0.8554 | 0.9939 |
| GBT | 0.7150 | 0.6273 | 0.8313 | 0.9793 |
| Decision Tree | 0.5659 | 0.4171 | 0.8795 | 0.9460 |
| Logistic Regression | 0.5403 | 0.4061 | 0.8072 | 0.9817 |
| Naive Bayes | 0.1721 | 0.0994 | 0.6386 | 0.9681 |

### Insider Threat Detection (Best: Random Forest)
| Model | F1 | Precision | Recall | ROC-AUC |
|---|---|---|---|---|
| Random Forest | **0.9524** | 0.9091 | 1.0000 | 0.9991 |
| Naive Bayes | 0.9524 | 0.9091 | 1.0000 | 0.9980 |
| GBT | 0.9500 | 0.9500 | 0.9500 | 0.9996 |
| Decision Tree | 0.9500 | 0.9500 | 0.9500 | 0.9745 |
| Logistic Regression | 0.8889 | 1.0000 | 0.8000 | 0.9752 |

## 🛡️ Technologies

| Layer | Technology |
|---|---|
| Storage | HDFS (simulated zones) |
| SQL Analytics | Apache Hive |
| ETL | Apache Pig |
| ML Engine | Apache Spark MLlib (PySpark 4.2) |
| Privacy | Masking, Pseudonymization, SHA-256, RBAC |
| Visualization | Power BI (.pbip), Three.js + ECharts |
| Language | Python 3.12+ |

## ⚠️ Disclaimer

This is an **academic prototype** — not a production security system. The insider threat dataset is a deterministic simulation (seed=42) following CERT r4.2 behavioral archetypes. All identifiers are masked/pseudonymized.

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.
