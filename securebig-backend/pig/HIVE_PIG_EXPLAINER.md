# Hive & Pig Explainer

## Why Hive at all?
Hive turns HDFS files into **SQL tables** so security analysts can query
millions of events with SQL instead of Java. In SecureBig it plays three roles
(master prompt §8): (1) schema-on-read catalogs for the two datasets,
(2) the **fraud-rule engine** (rules R1–R3 with weights → risk score → risk
band), (3) a **privacy-aware view** (`vw_security_events_masked`) that masks
pseudonyms and IPs before anything reaches a dashboard.

### What `01_create_tables.hql` does
| Object | Purpose | Security angle |
|---|---|---|
| `transactions` (EXTERNAL) | 284,807 ULB transactions from `/securebig/raw/transactions` | raw zone keeps originals immutable; ACL-gated |
| `security_events` (EXTERNAL) | pseudonymized logon events from the processed zone | only pseudonyms ever enter Hive |
| `fraud_results` (managed, partitioned) | rule scores written by the rules script | partition `batch` keeps runs reproducible |
| `vw_security_events_masked` | `USR_0***` style masking + truncated IP | analysts never see full identifiers |

*Expected output:* `SHOW TABLES;` → 3 tables + 1 view; `SELECT COUNT(*) FROM
transactions;` → 284807.

### What `02_fraud_rules.hql` does
1. Derives `hour` from the dataset's `Time` (seconds since first txn).
2. Computes per-hour frequency (Hive GROUP BY → MapReduce/Tez job).
3. Scores every transaction: `HIGH_AMOUNT(>1000)=+30`,
   `UNUSUAL_TIME(01–05h)=+15`, `HIGH_FREQUENCY=+20`, sums → 0–100.
4. Bands: 0–30 LOW, 31–60 MEDIUM, 61–100 HIGH.
5. Cross-checks rules vs reality: fraud share per risk level — this tells you
   whether the rules are *worth their false-positive cost*.

R4 (location) / R5 (device) exist in the master prompt but the ULB dataset has
no location/device columns — so they are **not implemented** rather than faked
(project rule 4: use actual column names / real fields).

*Expected output:* a 3-row table where MEDIUM/HIGH bands show an order of
magnitude higher fraud percentage than LOW — the rules are catching signal.

## Why Pig instead of plain Python?
Pig compiles to **parallel MapReduce/Tez** on the cluster: the same script that
joins 175k log rows here scales to billions on more nodes, with no code change.
Python-pandas runs on one machine and one core. Pig also plugs directly into
HDFS zones with our ACLs. That is the honest engineering answer to "why Pig".

### What `log_processing.pig` does
`LOAD` raw logon/file CSVs → `FILTER` header rows + keep `FailedLogon` /
`sensitive` events → `FOREACH…GENERATE` + `GROUP BY user` to count per-user
failed logons, external-IP logons, sensitive accesses, total events → `JOIN`
into one wide feature table with an `abnormal_score` → `STORE` to
`/securebig/processed/user_activity/features` for Spark.
`DUMP top10` prints the 10 highest-scoring users (report screenshot).

*Expected output:* a 6-column CSV where scenario actors (E1042, E1058, …) land
at the top of the `abnormal_score` ranking.
