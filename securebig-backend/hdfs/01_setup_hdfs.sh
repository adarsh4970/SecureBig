#!/usr/bin/env bash
# =============================================================================
# SecureBig — Phase 2: HDFS setup + data ingestion
# Run as the hdfs superuser on the cluster edge node:  bash hdfs/01_setup_hdfs.sh
# =============================================================================
set -euo pipefail

# ---- 1. Directory layout ----------------------------------------------------
# Zone model: raw (immutable originals) -> processed (cleaned/features)
#             secure (masked/pseudonymized/restricted) -> results, reports
hdfs dfs -mkdir -p /securebig/raw/transactions
hdfs dfs -mkdir -p /securebig/raw/user_activity
hdfs dfs -mkdir -p /securebig/raw/audit_logs
hdfs dfs -mkdir -p /securebig/processed/transactions
hdfs dfs -mkdir -p /securebig/processed/user_activity
hdfs dfs -mkdir -p /securebig/secure/masked_data
hdfs dfs -mkdir -p /securebig/secure/restricted_data
hdfs dfs -mkdir -p /securebig/results/fraud
hdfs dfs -mkdir -p /securebig/results/insider_threat
hdfs dfs -mkdir -p /securebig/results/model_metrics
hdfs dfs -mkdir -p /securebig/reports

# ---- 2. Ingest the two datasets ---------------------------------------------
# creditcard.csv   : ULB dataset (284,807 rows)  -> transactions zone
# user_activity/*  : insider-threat activity logs -> user_activity zone
hdfs dfs -put -f data/raw/transactions/creditcard.csv        /securebig/raw/transactions/
hdfs dfs -put -f data/raw/user_activity/logon.csv            /securebig/raw/user_activity/
hdfs dfs -put -f data/raw/user_activity/device.csv           /securebig/raw/user_activity/
hdfs dfs -put -f data/raw/user_activity/file.csv             /securebig/raw/user_activity/
hdfs dfs -put -f data/raw/user_activity/http.csv             /securebig/raw/user_activity/
hdfs dfs -put -f data/secure/restricted_data/user_pseudonym_map.csv /securebig/secure/restricted_data/
hdfs dfs -put -f data/secure/masked_data/file_masked.csv     /securebig/secure/masked_data/
hdfs dfs -put -f data/secure/anonymized_data/*.csv           /securebig/processed/user_activity/

# ---- 3. Ownership + coarse permissions ---------------------------------------
# Admins own secure zones; analysts get read on processed only.
hdfs dfs -chown -R securebig_admin:supergroup /securebig/secure
hdfs dfs -chown -R securebig_admin:hdfs_users /securebig/raw
hdfs dfs -chmod 750 /securebig/secure/restricted_data   # owner rwx, group -, others -
hdfs dfs -chmod 640 /securebig/secure/masked_data/file_masked.csv
hdfs dfs -chmod 755 /securebig/processed                # analysts may read/ls

echo "HDFS tree:"
hdfs dfs -ls -R /securebig
