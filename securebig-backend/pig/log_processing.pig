-- =============================================================================
-- SecureBig — Phase 6: Pig log processing (ETL over HDFS audit logs)
-- Run: pig -x mapreduce pig/log_processing.pig
-- (or 'pig -x local pig/log_processing.pig' on a single machine)
-- =============================================================================
-- Pipeline: LOAD -> FILTER -> FOREACH -> GROUP -> (JOIN) -> features -> STORE
-- Input : /securebig/raw/user_activity/{logon,file}.csv  (raw zone)
-- Output: /securebig/processed/user_activity/features    (analyst zone)

-- ---- 1. LOAD raw logs --------------------------------------------------------
logon = LOAD '/securebig/raw/user_activity/logon.csv'
        USING PigStorage(',')
        AS (ts:chararray, user:chararray, event:chararray, pc:chararray, ip:chararray);

files = LOAD '/securebig/raw/user_activity/file.csv'
        USING PigStorage(',')
        AS (ts:chararray, user:chararray, event:chararray, pc:chararray,
            filename:chararray, sensitivity:chararray);

-- ---- 2. FILTER: drop header rows and keep security-relevant events ----------
logon_clean = FILTER logon BY user != 'user';
failed      = FILTER logon_clean BY event == 'FailedLogon';
sensitive   = FILTER files   BY sensitivity == 'sensitive' AND user != 'user';

-- ---- 3. FOREACH + GROUP: per-user feature extraction ------------------------
failed_by_user  = GROUP failed BY user;
failed_counts   = FOREACH failed_by_user GENERATE
                    group AS user,
                    COUNT(failed) AS failed_logins;

ext_ips         = FILTER logon_clean BY INDEXOF(ip, '10.20.', 0) == -1;
ext_by_user     = GROUP ext_ips BY user;
ext_counts      = FOREACH ext_by_user GENERATE
                    group AS user,
                    COUNT(ext_ips) AS external_ip_logons;

sens_by_user    = GROUP sensitive BY user;
sens_counts     = FOREACH sens_by_user GENERATE
                    group AS user,
                    COUNT(sensitive) AS sensitive_file_access;

all_by_user     = GROUP logon_clean BY user;
event_counts    = FOREACH all_by_user GENERATE
                    group AS user,
                    COUNT(logon_clean) AS logon_events;

-- ---- 4. JOIN the per-user aggregates into one feature table -----------------
feat_tmp  = JOIN event_counts BY user, failed_counts BY user;
feat_tmp2 = JOIN feat_tmp  BY event_counts::user, ext_counts BY user;
features  = JOIN feat_tmp2 BY feat_tmp::event_counts::user, sens_counts BY user;

feature_table = FOREACH features GENERATE
    feat_tmp::event_counts::user        AS user,
    feat_tmp::event_counts::logon_events AS logon_events,
    feat_tmp::failed_counts::failed_logins AS failed_logins,
    ext_counts::external_ip_logons      AS external_ip_logons,
    sens_counts::sensitive_file_access  AS sensitive_file_access,
    (feat_tmp::failed_counts::failed_logins + ext_counts::external_ip_logons
     + sens_counts::sensitive_file_access) AS abnormal_score;

-- ---- 5. STORE back to HDFS (analyst-readable zone) --------------------------
STORE feature_table
  INTO '/securebig/processed/user_activity/features'
  USING PigStorage(',');

-- Quick sanity dump for the console/report screenshot
top10 = LIMIT (ORDER feature_table BY abnormal_score DESC) 10;
DUMP top10;
