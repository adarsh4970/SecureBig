-- =============================================================================
-- SecureBig — Phase 5 (b): Hive fraud-rule engine + risk scoring
-- Run: hive -f hive/02_fraud_rules.hql
--
-- Rules (weights from the master prompt, computed ONLY from real columns
-- 'Time' and 'Amount' — the ULB dataset has no location/device fields,
-- so R4 and R5 are analytical substitutes using the available schema):
--   R1 HIGH_AMOUNT     amount > 1000                       -> +30
--   R2 HIGH_FREQUENCY  >6000 txns in the same hour bucket  -> +20
--   R3 UNUSUAL_TIME    txns between 01:00 and 05:00        -> +15
--   R4 RAPID_VELOCITY  >20 txns in same 10-min window      -> +20
--   R5 AMOUNT_OUTLIER  amount > mean + 3*stddev (Z-score)  -> +15
--                                                    Max possible: 100
-- =============================================================================
USE securebig;

-- 1) enrich with derived temporal columns
CREATE TEMPORARY TABLE txn_enriched AS
SELECT monotonically_increasing_id() AS txn_id,
       time, amount, class,
       CAST(FROM_UNIXTIME(86400 + time, 'HH') AS INT) AS hour,   -- day1 starts 00:00
       CAST(FLOOR(time / 600) AS INT) AS time_bin_10m             -- 10-minute windows
FROM transactions;

-- 2) aggregation tables for frequency and velocity rules
CREATE TEMPORARY TABLE hour_freq AS
SELECT hour, COUNT(*) AS cnt FROM txn_enriched GROUP BY hour;

-- R4: velocity — transactions per 10-minute window
CREATE TEMPORARY TABLE velocity_freq AS
SELECT time_bin_10m, COUNT(*) AS vel_cnt FROM txn_enriched GROUP BY time_bin_10m;

-- R5: amount outlier — global mean + 3 * stddev threshold
CREATE TEMPORARY TABLE amount_stats AS
SELECT AVG(amount) AS avg_amt, STDDEV(amount) AS std_amt FROM txn_enriched;

-- 3) rule flags + weighted risk score + risk band (5 rules)
INSERT OVERWRITE TABLE fraud_results PARTITION (batch='rules_v1')
SELECT t.txn_id, t.time, t.amount, t.hour,
       -- Rule flag columns
       CAST(t.amount > 1000 AS INT)                                  AS high_amount,
       CAST(t.hour BETWEEN 1 AND 5 AS INT)                           AS unusual_time,
       CAST(f.cnt > 6000 AS INT)                                     AS high_frequency,
       -- Weighted risk score = R1(+30) + R2(+20) + R3(+15) + R4(+20) + R5(+15)
       (CASE WHEN t.amount > 1000 THEN 30 ELSE 0 END)
     + (CASE WHEN t.hour BETWEEN 1 AND 5 THEN 15 ELSE 0 END)
     + (CASE WHEN f.cnt > 6000 THEN 20 ELSE 0 END)
     + (CASE WHEN v.vel_cnt > 20 THEN 20 ELSE 0 END)
     + (CASE WHEN t.amount > (s.avg_amt + 3 * s.std_amt) THEN 15 ELSE 0 END)
                                                                      AS risk_score,
       -- Risk band classification
       CASE
         WHEN (CASE WHEN t.amount > 1000 THEN 30 ELSE 0 END)
            + (CASE WHEN t.hour BETWEEN 1 AND 5 THEN 15 ELSE 0 END)
            + (CASE WHEN f.cnt > 6000 THEN 20 ELSE 0 END)
            + (CASE WHEN v.vel_cnt > 20 THEN 20 ELSE 0 END)
            + (CASE WHEN t.amount > (s.avg_amt + 3 * s.std_amt) THEN 15 ELSE 0 END) > 60 THEN 'HIGH'
         WHEN (CASE WHEN t.amount > 1000 THEN 30 ELSE 0 END)
            + (CASE WHEN t.hour BETWEEN 1 AND 5 THEN 15 ELSE 0 END)
            + (CASE WHEN f.cnt > 6000 THEN 20 ELSE 0 END)
            + (CASE WHEN v.vel_cnt > 20 THEN 20 ELSE 0 END)
            + (CASE WHEN t.amount > (s.avg_amt + 3 * s.std_amt) THEN 15 ELSE 0 END) > 30 THEN 'MEDIUM'
         ELSE 'LOW'
       END                                                            AS risk_level,
       t.class
FROM txn_enriched t
JOIN hour_freq f ON t.hour = f.hour
JOIN velocity_freq v ON t.time_bin_10m = v.time_bin_10m
CROSS JOIN amount_stats s;

-- 4) security analytics over the result table
SELECT risk_level, COUNT(*) AS txns, SUM(class) AS actual_frauds,
       ROUND(100*SUM(class)/COUNT(*), 3) AS fraud_pct
FROM fraud_results WHERE batch='rules_v1'
GROUP BY risk_level ORDER BY fraud_pct DESC;

-- Do rule-flagged high-risk txns actually contain more fraud?
SELECT high_amount, unusual_time, COUNT(*) AS txns, SUM(class) AS frauds
FROM fraud_results WHERE batch='rules_v1'
GROUP BY high_amount, unusual_time;
