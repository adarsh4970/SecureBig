# HDFS Explainer — what every command does, why, and the security problem it solves

Per the master prompt: never just show commands. Each block below gives
**what it does → why we need it → security problem solved → expected output**.

## 1. Directory creation — `hdfs dfs -mkdir -p /securebig/...`

* **What:** creates the zone model in HDFS: `raw` (immutable originals),
  `processed` (cleaned features), `secure` (masked/pseudonymized/restricted),
  `results`, `reports`. `-p` creates parents in one call.
* **Why:** security starts with *segregation of data by sensitivity*. If raw
  PII-bearing files and analyst outputs live in one folder, one permission
  mistake exposes everything. Zones let us attach different permissions per zone.
* **Security problem solved:** blast-radius control; least-privilege becomes
  enforceable per directory.
* **Expected output:** none (silence = success); `hdfs dfs -ls /securebig`
  then shows the tree.

## 2. Ingestion — `hdfs dfs -put -f <local> <hdfs>`

* **What:** copies `creditcard.csv` (ULB, 284,807 rows) and the four
  activity-log CSVs from the local machine into HDFS, replication-managed by
  Hadoop. `-f` overwrites on re-runs (idempotent ingestion).
* **Why:** Spark/Hive/Pig read from HDFS, not from laptops. Once in HDFS the
  data is block-split (128 MB blocks), replicated 3× and fault tolerant.
* **Security problem solved:** centralized storage we can guard with
  authentication (Kerberos), authorization (ACLs), and at-rest encryption
  (HDFS Transparent Data Encryption zones) — instead of scattered local copies.
* **Expected output:** `put: 0..1.4 MB/s` progress lines (version-dependent),
  then `hdfs dfs -ls /securebig/raw/transactions` shows `creditcard.csv`
  (~150 MB) with replication 3.

## 3. Ownership — `hdfs dfs -chown -R securebig_admin:... /securebig/...`

* **What:** assigns owning user+group recursively. Secure zones →
  `securebig_admin:supergroup`; raw → group `hdfs_users`.
* **Why:** HDFS authorization is evaluated against owner/group/other mode bits
  first; ownership is the anchor of that model.
* **Security problem solved:** prevents accidental ownership by whichever user
  happened to upload the file (a classic misconfiguration).
* **Expected output:** silent; verify with `hdfs dfs -ls /securebig/secure`.

## 4. Mode bits — `hdfs dfs -chmod 750 /securebig/secure/restricted_data`

* **What:** `750` = owner rwx, group r‑‑, others ‑‑‑ on the directory holding
  the re-identification map. `640` on the masked file: owner rw, group r, others none.
* **Why:** coarse but cheap protection; anyone not owner/group cannot even list
  the directory, so file names stop leaking.
* **Security problem solved:** blocks "just browsing" access by random cluster
  users to the most sensitive artifact (pseudonym ↔ real identity map).
* **Expected output:** silent; `hdfs dfs -ls /securebig/secure` shows `drwxrwx---`.

## 5. ACLs — `hdfs dfs -setfacl -m user:security_analyst:r-- <file>`

* **What:** POSIX-style Access Control Lists extend mode bits with *named
  users/groups*. We grant `security_analyst` read on the map,
  `default:` ACLs so new files inherit, and `-R` on the processed zone for the
  data analyst. `getfacl -R` prints the effective ACLs as evidence.
* **Why:** mode bits only know one owner + one group. Real organizations need
  per-user exceptions without reshuffling groups.
* **Security problem solved:** precise least privilege — the analyst can do
  their job (read) but cannot write (`-w-` absent) or re-share.
* **Expected output:** `getfacl` shows lines like
  `user:security_analyst:r--` and `mask::r-x`.

## 6. Denial / authorized-access demo (02_acls_security.sh)

* **What:** runs the same reads as *different* OS users via `sudo -u`:
  `guest` on the restricted map (denied by mode bits), `security_analyst` on
  the map (allowed by ACL), `data_analyst` on raw zone (denied).
* **Why:** a security control you never tested is a guess. This is the
  demonstrable proof for the report/viva.
* **Security problem solved:** verifies authentication (Kerberos user),
  authorization (HDFS ACL evaluation) and auditing all work together.
* **Expected output:** `Permission denied` / `AccessControlException` for the
  denied cases; a CSV header line for the allowed case.

## Encryption at rest (concept, configured on the cluster)

HDFS **Transparent Data Encryption** puts each zone in an encryption zone with
its own key in the Hadoop KMS:
`hdfs crypto -createZone -keyName securebigKey -path /securebig/secure`
Blocks on disk are then unreadable even to someone stealing the disks —
completing the chain authentication → authorization → encryption → audit.
