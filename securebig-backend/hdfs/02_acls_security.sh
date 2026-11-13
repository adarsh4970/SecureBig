#!/usr/bin/env bash
# =============================================================================
# SecureBig — Phase 3: HDFS access control + ACL demonstration
# Shows: setfacl grants, DENIAL of an unauthorized user, authorized access.
# Run on the cluster edge node:  bash hdfs/02_acls_security.sh
# =============================================================================
set -euo pipefail

MAP=/securebig/secure/restricted_data/user_pseudonym_map.csv

# ---- 1. Baseline: default (mode-bit) permissions already deny others --------
echo "== unauthorized user (guest) tries restricted map =="
if hdfs dfs -test -e $MAP; then :; fi
# 'guest' has no permission bits on the dir -> expected: Permission denied
sudo -u guest hdfs dfs -cat $MAP || echo ">>> ACCESS DENIED for guest (expected)"

# ---- 2. Grant an analyst scoped access with ACLs ----------------------------
# security_analist may READ the pseudonym map but never WRITE it.
hdfs dfs -setfacl -m user:security_analyst:r-- $MAP
hdfs dfs -setfacl -m default:user:security_analyst:r-- /securebig/secure/restricted_data
echo "== authorized analyst reads the map (expected: CSV head) =="
sudo -u security_analyst hdfs dfs -head -1 $MAP

echo "== analyst attempts write (expected: Access denied) =="
sudo -u security_analyst hdfs dfs -touchz /securebig/secure/restricted_data/hack.txt \
  || echo ">>> WRITE DENIED for security_analyst (expected)"

# ---- 3. Data analyst: read anonymized zone, nothing else --------------------
hdfs dfs -setfacl -R -m user:data_analyst:r-x /securebig/processed
echo "== data analyst reads anonymized feature data =="
sudo -u data_analyst hdfs dfs -ls /securebig/processed/user_activity | head -5
echo "== data analyst tries raw PII-bearing zone (expected: denied) =="
sudo -u data_analyst hdfs dfs -cat /securebig/raw/user_activity/logon.csv \
  || echo ">>> ACCESS DENIED for data_analyst on raw zone (expected)"

# ---- 4. Show the effective ACLs (evidence for the report) -------------------
hdfs dfs -getfacl -R /securebig/secure | head -40
