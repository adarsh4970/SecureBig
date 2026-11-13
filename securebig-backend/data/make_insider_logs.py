"""
SecureBig — Phase 1: Dataset 2 generation (simulated insider-threat activity logs).

IMPORTANT TRANSPARENCY NOTE (project rule 8 + section 5 of the master prompt):
The real CERT r4.2 insider-threat dataset is ~90 GB and requires a signed
usage agreement, so it cannot be redistributed or downloaded here. This script
therefore GENERATES a simulated enterprise activity log whose behavioral
archetypes follow the publicly documented CERT insider-threat scenario families
(after-hours bulk copying to USB, repeated failed logons from a new IP,
privilege misuse / snooping of sensitive files).

  * The simulation is deterministic (seed=42) and fully reproducible.
  * Ground truth (which users are scenario actors, and when) is exported
    alongside the logs — nothing is hidden and no real people are involved.
  * spark/insider_pipeline.py also contains a loader stub for real CERT r4.2
    files so the same pipeline can be re-run on the genuine dataset later.

Usage:
    python data/make_insider_logs.py

Output (data/raw/user_activity/):
    logon.csv    timestamp,user,event,pc,ip
    device.csv   timestamp,user,event,pc,usb_id,bytes_copied
    file.csv     timestamp,user,event,pc,filename,sensitivity
    http.csv     timestamp,user,url,bytes,download_count
    scenario_ground_truth.csv   user,scenario,weeks_active
    SCENARIOS.md                documentation of each archetype
"""
import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "user_activity"
OUT.mkdir(parents=True, exist_ok=True)

SEED = 42
N_USERS = 200
N_DAYS = 90
EPOCH = datetime(2025, 7, 1)
START_HOUR, END_HOUR = 8, 18          # normal working window
SENSITIVE_FILES = [
    "finance_q3_report.csv", "customer_pii_export.sql", "payroll_master.xlsx",
    "m&a_project_plan.docx", "source_keys_vault.md", "board_meeting_minutes.pdf",
]
NORMAL_FILES = [
    "meeting_notes.docx", "sprint_board.md", "qa_checklist.xlsx",
    "team_announcement.txt", "helpdesk_ticket.csv", "training_slide.pdf",
]
NORMAL_URLS = ["intranet.corp", "wiki.corp", "mail.corp", "crm.corp"]
DL_URLS = ["drive-personal.example", "filedrop.example", "pastebin.example"]

rng = random.Random(SEED)


def ts(day: int, hour: float) -> datetime:
    base = EPOCH + timedelta(days=day)
    return base.replace(hour=int(hour) % 24, minute=int((hour % 1) * 60),
                        second=rng.randrange(60))


def week(d: int) -> int:
    return d // 7


def pick_ip(suspicious: bool) -> str:
    if suspicious and rng.random() < 0.85:
        return f"185.220.{rng.randrange(100, 250)}.{rng.randrange(1, 250)}"   # known exit-node range
    return f"10.20.{rng.randrange(0, 8)}.{rng.randrange(2, 250)}"             # internal range


# ---------------------------------------------------------------- users -----
users: list[dict] = []
for i in range(N_USERS):
    users.append({"id": f"E{1000 + i}", "pc": f"PC-{i:04d}", "scenario": None})
# Scenario actors (documented archetypes, CERT-style families)
SCENARIOS = {
    "A_exfil_usb":   ["E1042", "E1077", "E1131"],   # after-hours bulk copy to USB
    "B_new_ip_auth": ["E1058", "E1103", "E1188"],   # failed-logon bursts from new IP
    "C_snooping":    ["E1019", "E1064", "E1110", "E1155"],   # sensitive-file snooping
}
for s, ids in SCENARIOS.items():
    for uid in ids:
        next(u for u in users if u["id"] == uid)["scenario"] = s

logon_rows, device_rows, file_rows, http_rows = [], [], [], []


def normal_day(u: dict, d: int) -> None:
    """One ordinary working day for a benign employee."""
    if rng.random() < 0.06:                     # leave / weekend
        return
    start = rng.uniform(START_HOUR, START_HOUR + 1.5)
    logon_rows.append([ts(d, start), u["id"], "Logon", u["pc"], pick_ip(False)])
    logon_rows.append([ts(d, min(start + rng.uniform(7.5, 9.5), 23.5)), u["id"], "Logoff", u["pc"], pick_ip(False)])
    for _ in range(rng.randrange(2, 9)):        # routine file touches
        file_rows.append([ts(d, rng.uniform(START_HOUR, END_HOUR)), u["id"], rng.choice(["Open", "Open", "Copy"]),
                          u["pc"], rng.choice(NORMAL_FILES), "normal"])
    for _ in range(rng.randrange(1, 6)):        # routine web
        http_rows.append([ts(d, rng.uniform(START_HOUR, END_HOUR)), u["id"],
                          rng.choice(NORMAL_URLS), rng.randrange(10_000, 5_000_000), 0])
    if rng.random() < 0.04:                     # occasional USB (policy-compliant)
        device_rows.append([ts(d, rng.uniform(10, 16)), u["id"], "Connect", u["pc"],
                            f"USB-{rng.randrange(100, 999)}", 0])
    if rng.random() < 0.02:                     # rare typo failed logon
        logon_rows.append([ts(d, rng.uniform(START_HOUR, END_HOUR)), u["id"], "FailedLogon",
                           u["pc"], pick_ip(False)])


def exfil_day(u: dict, d: int) -> None:
    """Scenario A: after-hours bulk sensitive copy to removable media."""
    if week(d) < 6 or rng.random() < 0.25:
        normal_day(u, d)
        return
    start = rng.uniform(21, 23.5)
    logon_rows.append([ts(d, start), u["id"], "Logon", u["pc"], pick_ip(False)])
    logon_rows.append([ts(d, (start + rng.uniform(1.5, 3)) % 24), u["id"], "Logoff", u["pc"], pick_ip(False)])
    usb = f"USB-{rng.randrange(100, 999)}"
    device_rows.append([ts(d, start + 0.1), u["id"], "Connect", u["pc"], usb, 0])
    for _ in range(rng.randrange(15, 40)):      # mass staging
        file_rows.append([ts(d, rng.uniform(start + 0.2, start + 2.4)), u["id"], "Copy", u["pc"],
                          rng.choice(SENSITIVE_FILES), "sensitive"])
    device_rows.append([ts(d, start + 2.5), u["id"], "Disconnect", u["pc"], usb,
                        rng.randrange(200_000_000, 4_000_000_000)])  # GBs leave with the device
    http_rows.append([ts(d, start + 2.7), u["id"], rng.choice(DL_URLS),
                      rng.randrange(1_000_000, 900_000_000), rng.randrange(3, 30)])


def newip_day(u: dict, d: int) -> None:
    """Scenario B: failed-logon bursts then success from an unusual IP."""
    if week(d) < 4 or rng.random() < 0.3:
        normal_day(u, d)
        return
    start = rng.uniform(1, 5) if rng.random() < 0.6 else rng.uniform(19.5, 23.5)
    ext_ip = pick_ip(True)
    for _ in range(rng.randrange(5, 16)):
        logon_rows.append([ts(d, start + rng.uniform(0, 0.9)), u["id"], "FailedLogon", u["pc"], ext_ip])
    logon_rows.append([ts(d, start + 1.0), u["id"], "Logon", u["pc"], ext_ip])
    logon_rows.append([ts(d, (start + rng.uniform(1.2, 2.5)) % 24), u["id"], "Logoff", u["pc"], ext_ip])
    for _ in range(rng.randrange(4, 14)):       # scoping the environment
        file_rows.append([ts(d, rng.uniform(START_HOUR, END_HOUR)), u["id"], "Open", u["pc"],
                          rng.choice(SENSITIVE_FILES + NORMAL_FILES), "normal"])
    http_rows.append([ts(d, start + 1.4), u["id"], rng.choice(DL_URLS), rng.randrange(100_000, 50_000_000),
                      rng.randrange(1, 8)])


def snoop_day(u: dict, d: int) -> None:
    """Scenario C: sustained sensitive-file access beyond job role."""
    if rng.random() < 0.2:
        normal_day(u, d)
        return
    start = rng.uniform(START_HOUR, END_HOUR)
    logon_rows.append([ts(d, start), u["id"], "Logon", u["pc"], pick_ip(False)])
    logon_rows.append([ts(d, min(start + rng.uniform(7.5, 9.5), 23.5)), u["id"], "Logoff", u["pc"], pick_ip(False)])
    for _ in range(rng.randrange(6, 18)):       # persistent snooping
        file_rows.append([ts(d, rng.uniform(START_HOUR, min(END_HOUR + 3, 23))),
                          u["id"], rng.choice(["Open", "Copy"]), u["pc"],
                          rng.choice(SENSITIVE_FILES), "sensitive"])
    if rng.random() < 0.35:                     # some after-hours follow-ups
        logon_rows.append([ts(d, rng.uniform(20, 23.5)), u["id"], "Logon", u["pc"], pick_ip(False)])
        file_rows.append([ts(d, rng.uniform(20.2, 23.5)), u["id"], "Open", u["pc"],
                          rng.choice(SENSITIVE_FILES), "sensitive"])


ACTORS = {u["id"]: u["scenario"] for u in users if u["scenario"]}
DAY_FN = {"A_exfil_usb": exfil_day, "B_new_ip_auth": newip_day, "C_snooping": snoop_day}

for d in range(N_DAYS):
    for u in users:
        (DAY_FN.get(u["scenario"], normal_day))(u, d)

# ------------------------------------------------------------- write out ----
cols = {
    "logon.csv": (logon_rows, ["timestamp", "user", "event", "pc", "ip"]),
    "device.csv": (device_rows, ["timestamp", "user", "event", "pc", "usb_id", "bytes_copied"]),
    "file.csv": (file_rows, ["timestamp", "user", "event", "pc", "filename", "sensitivity"]),
    "http.csv": (http_rows, ["timestamp", "user", "url", "bytes", "download_count"]),
}
for name, (rows, columns) in cols.items():
    df = pd.DataFrame(rows, columns=columns).sort_values("timestamp")
    df.to_csv(OUT / name, index=False)
    print(f"{name:>12}: {len(df):>7} events")

gt = pd.DataFrame(
    [{"user": u, "scenario": s, "weeks_active": "6-12" if s == "A_exfil_usb"
      else "4-10" if s == "B_new_ip_auth" else "0-12"} for u, s in ACTORS.items()]
).sort_values("user")
gt.to_csv(OUT / "scenario_ground_truth.csv", index=False)
print(f"ground truth : {len(gt)} scenario actors (of {N_USERS} users)")

(OUT / "SCENARIOS.md").write_text(
    "# Simulated Insider-Threat Scenarios (seed=42, deterministic)\n\n"
    "SIMULATED DATA — no real people or real attacks. Archetypes follow publicly\n"
    "documented CERT insider-threat scenario families:\n\n"
    "| Scenario | Users | Behavior | Weeks active |\n"
    "|---|---|---|---|\n"
    "| A_exfil_usb   | E1042, E1077, E1131 | after-hours logons, bulk sensitive Copy, USB connect + GB-scale bytes_copied, upload URLs | 6-12 |\n"
    "| B_new_ip_auth | E1058, E1103, E1188 | failed-logon bursts (5-15) then success, external 185.220.*.* IPs, odd hours | 4-10 |\n"
    "| C_snooping    | E1019, E1064, E1110, E1155 | persistent sensitive-file Open/Copy, some after-hours | 0-12 |\n\n"
    "All other users follow benign routines (8:00-18:00 logons, routine file/web\n"
    "activity, rare USB use, rare typos -> FailedLogon).\n"
    "The analytic label used for ML is: user-week rows belonging to a scenario\n"
    "actor DURING their active weeks = 1 (suspicious), else 0 — see\n"
    "spark/insider_pipeline.py. This is a scenario-derived label, not an\n"
    "organizational ground truth from a real company.\n",
    encoding="utf-8",
)
print(f"\nTotal events: {len(logon_rows)+len(device_rows)+len(file_rows)+len(http_rows):,}")
print(f"Wrote SCENARIOS.md + scenario_ground_truth.csv to {OUT}")
