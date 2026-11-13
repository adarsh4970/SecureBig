-- =============================================================================
-- SecureBig — Phase 5 (a): Hive tables over HDFS zones
-- Run: hive -f hive/01_create_tables.hql
-- =============================================================================
-- External tables: Hive manages metadata only; data stays under our ACL zones.

CREATE DATABASE IF NOT EXISTS securebig;
USE securebig;

-- ---- Fact: credit-card transactions (ULB, 284,807 rows) ----------------------
CREATE EXTERNAL TABLE IF NOT EXISTS transactions (
  time BIGINT, v1 DOUBLE, v2 DOUBLE, v3 DOUBLE, v4 DOUBLE, v5 DOUBLE,
  v6 DOUBLE, v7 DOUBLE, v8 DOUBLE, v9 DOUBLE, v10 DOUBLE, v11 DOUBLE,
  v12 DOUBLE, v13 DOUBLE, v14 DOUBLE, v15 DOUBLE, v16 DOUBLE, v17 DOUBLE,
  v18 DOUBLE, v19 DOUBLE, v20 DOUBLE, v21 DOUBLE, v22 DOUBLE, v23 DOUBLE,
  v24 DOUBLE, v25 DOUBLE, v26 DOUBLE, v27 DOUBLE, v28 DOUBLE,
  amount DOUBLE, class INT
)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ',' STORED AS TEXTFILE
LOCATION '/securebig/raw/transactions'
TBLPROPERTIES ('skip.header.line.count'='1');

-- ---- Fact: pseudonymized logon events ----------------------------------------
CREATE EXTERNAL TABLE IF NOT EXISTS security_events (
  `timestamp` STRING, user STRING, event STRING, pc STRING, ip STRING
)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ',' STORED AS TEXTFILE
LOCATION '/securebig/processed/user_activity'
TBLPROPERTIES ('skip.header.line.count'='1');

-- ---- Result: rule-based fraud scoring (written by 02_fraud_rules.hql) --------
CREATE TABLE IF NOT EXISTS fraud_results (
  txn_id BIGINT, time BIGINT, amount DOUBLE, hour INT,
  high_amount INT, unusual_time INT, high_frequency INT,
  risk_score INT, risk_level STRING, actual_class INT
)
PARTITIONED BY (batch STRING)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
STORED AS TEXTFILE;

-- ---- Privacy-aware view: analysts see masked pseudonyms only -----------------
CREATE VIEW IF NOT EXISTS vw_security_events_masked AS
SELECT `timestamp`,
       concat(substr(user,1,3), '***') AS user_masked,
       event, pc,
       concat(substr(ip,1,6), '***')   AS ip_masked
FROM security_events;
