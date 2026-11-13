# Simulated Insider-Threat Scenarios (seed=42, deterministic)

SIMULATED DATA — no real people or real attacks. Archetypes follow publicly
documented CERT insider-threat scenario families:

| Scenario | Users | Behavior | Weeks active |
|---|---|---|---|
| A_exfil_usb   | E1042, E1077, E1131 | after-hours logons, bulk sensitive Copy, USB connect + GB-scale bytes_copied, upload URLs | 6-12 |
| B_new_ip_auth | E1058, E1103, E1188 | failed-logon bursts (5-15) then success, external 185.220.*.* IPs, odd hours | 4-10 |
| C_snooping    | E1019, E1064, E1110, E1155 | persistent sensitive-file Open/Copy, some after-hours | 0-12 |

All other users follow benign routines (8:00-18:00 logons, routine file/web
activity, rare USB use, rare typos -> FailedLogon).
The analytic label used for ML is: user-week rows belonging to a scenario
actor DURING their active weeks = 1 (suspicious), else 0 — see
spark/insider_pipeline.py. This is a scenario-derived label, not an
organizational ground truth from a real company.
