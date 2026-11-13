-- =============================================================================
-- SecureBig — Phase 5 (b): Hive fraud-rule engine + risk scoring
-- Run: hive -f hive/02_fraud_rules.hql
--
-- Rules (weights from the master prompt, computed ONLY from real columns
-- 'Time' and 'Amount' — the ULB dataset has no location/device fields):
--   R1 HIGH_AMOUNT     amount > 1000                       -> +30
--   R2 HIGH_FREQUENCY  >10 txns in the same hour bucket    -> +20
--   R3 UNUSUAL_TIME    txns between 01:00 and 05:00        -> +15
--   R4/R5 (location / new-device) are not computable on this dataset and are
--   deliberately omitted rather than faked (project rule: use real fields).
-- =============================================================================
USE securebig;

-- 1) per-hour frequency map
CREATE TEMPORARY TABLE txn_enriched AS
SELECT monotonically_increasing_id() AS txn_id,
       time, amount, class,
       CAST(FROM_UNIXTIME(86400 + time, 'HH') AS INT) AS hour   -- day1 starts 00:00
FROM transactions;

CREATE TEMPORARY TABLE hour_freq AS
SELECT hour, COUNT(*) AS cnt FROM txn_enriched GROUP BY hour;

-- 2) rule flags + weighted risk score + risk band
INSERT OVERWRITE TABLE fraud_results PARTITION (batch='rules_v1')
SELECT t.txn_id, t.time, t.amount, t.hour,
       CAST(t.amount > 1000 AS INT)                                  AS high_amount,
       CAST(t.hour BETWEEN 1 AND 5 AS INT)                           AS unusual_time,
       CAST(f.cnt > 6000 AS INT)                                     AS high_frequency,
       (CASE WHEN t.amount > 1000 THEN 30 ELSE 0 END)
     + (CASE WHEN t.hour BETWEEN 1 AND 5 THEN 15 ELSE 0 END)
     + (CASE WHEN f.cnt > 6000 THEN 20 ELSE 0 END)                   AS risk_score,
       CASE
         WHEN (CASE WHEN t.amount > 1000 THEN 30 ELSE 0 END)
            + (CASE WHEN t.hour BETWEEN 1 AND 5 THEN 15 ELSE 0 END)
            + (CASE WHEN f.cnt > 6000 THEN 20 ELSE 0 END) > 60 THEN 'HIGH'
         WHEN (CASE WHEN t.amount > 1000 THEN 30 ELSE 0 END)
            + (CASE WHEN t.hour BETWEEN 1 AND 5 THEN 15 ELSE 0 END)
            + (CASE WHEN f.cnt > 6000 THEN 20 ELSE 0 END) > 30 THEN 'MEDIUM'
         ELSE 'LOW'
       END                                                            AS risk_level,
       t.class
FROM txn_enriched t
JOIN hour_freq f ON t.hour = f.hour;

-- 3) security analytics over the result table
SELECT risk_level, COUNT(*) AS txns, SUM(class) AS actual_frauds,
       ROUND(100*SUM(class)/COUNT(*), 3) AS fraud_pct
FROM fraud_results WHERE batch='rules_v1'
GROUP BY risk_level ORDER BY fraud_pct DESC;

-- Do rule-flagged high-risk txns actually contain more fraud?
SELECT high_amount, unusual_time, COUNT(*) AS txns, SUM(class) AS frauds
FROM fraud_results WHERE batch='rules_v1'
GROUP BY high_amount, unusual_time;
