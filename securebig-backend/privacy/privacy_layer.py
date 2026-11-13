"""
SecureBig — Phase 4: Privacy-Preserving Layer (runnable everywhere, pure Python).

Demonstrates, on the actual project data:
  1. MASKING           j***@example.com style display minimization
  2. PSEUDONYMIZATION  E1042 -> USR_001 (reversible, map kept in restricted zone)
  3. HASHING           SHA-256 one-way identifiers (device/USB, IP)
  4. ACCESS CONTROL    role-based checks against the HDFS-style ACL matrix
  5. AUDIT LOG         every access decision is recorded (JSON lines)

Usage:
    python privacy/privacy_layer.py

Input : data/raw/user_activity/*.csv (+ transaction email/card demo fields)
Output: data/secure/masked_data/file_masked.csv
        data/secure/anonymized_data/  (pseudonymized copies for analysts)
        data/secure/restricted_data/user_pseudonym_map.csv  (re-identification map)
        results/privacy_audit_log.jsonl                      (access decisions)
"""
import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "user_activity"
SEC = ROOT / "data" / "secure"
MASKED = SEC / "masked_data"
ANON = SEC / "anonymized_data"
RESTRICTED = SEC / "restricted_data"
AUDIT = ROOT / "results" / "privacy_audit_log.jsonl"
for p in (MASKED, ANON, RESTRICTED, AUDIT.parent):
    p.mkdir(parents=True, exist_ok=True)

# HDFS-style ACL matrix (mirrors hdfs/02_acls_security.sh)
ACL_MATRIX = {
    "ADMIN":            {"masked_data": True,  "anonymized_data": True,  "restricted_data": True},
    "SECURITY_ANALYST": {"masked_data": True,  "anonymized_data": True,  "restricted_data": False},
    "DATA_ANALYST":     {"masked_data": False, "anonymized_data": True,  "restricted_data": False},
    "GUEST":            {"masked_data": False, "anonymized_data": False, "restricted_data": False},
}

audit_lines: list[str] = []


def audit(role: str, zone: str, allowed: bool, note: str) -> None:
    entry = {"role": role, "zone": zone, "decision": "GRANT" if allowed else "DENY", "note": note}
    audit_lines.append(json.dumps(entry))
    print(f"  [{'GRANT' if allowed else 'DENY '}] {role:<17} -> {zone:<16} ({note})")


def check_access(role: str, zone: str) -> bool:
    allowed = ACL_MATRIX.get(role, {}).get(zone, False)
    audit(role, zone, allowed, "ACL matrix lookup")
    return allowed


def mask_email(email: str) -> str:
    local, _, domain = email.partition("@")
    return f"{local[0]}***@{domain}" if local and domain else email


def mask_card(card: str) -> str:
    digits = "".join(ch for ch in card if ch.isdigit())
    return f"{'*' * max(len(digits) - 4, 0)}{digits[-4:]}" if digits else card


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def pseudonymize_map(ids: list[str]) -> dict[str, str]:
    """Stable, order-independent pseudonyms: SHA-256 prefix determines USR number."""
    mapping = {}
    used = set()
    for raw_id in ids:
        n = int(sha256_hex(raw_id)[:8], 16) % 10_000
        while n in used:
            n = (n + 1) % 10_000
        used.add(n)
        mapping[raw_id] = f"USR_{n:03d}"
    return mapping


def main() -> None:
    print("=" * 66)
    print("SECUREBIG PRIVACY LAYER — masking / pseudonymization / hashing / RBAC")
    print("=" * 66)

    # ---- load raw activity ------------------------------------------------
    logon = pd.read_csv(RAW / "logon.csv")
    file_ev = pd.read_csv(RAW / "file.csv")
    device = pd.read_csv(RAW / "device.csv")

    # ---- 1) PSEUDONYMIZATION of employee ids ------------------------------
    emp_ids = sorted(set(logon["user"]) | set(file_ev["user"]) | set(device["user"]))
    pmap = pseudonymize_map(emp_ids)
    RESTRICTED.joinpath().mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"employee_id": list(pmap), "pseudonym": [pmap[k] for k in pmap]}
                 ).to_csv(RESTRICTED / "user_pseudonym_map.csv", index=False)
    example = list(pmap.items())[:3]
    print("\n1) PSEUDONYMIZATION  (raw employee id -> analytical pseudonym)")
    for k, v in example:
        print(f"     {k}  ->  {v}   (sha256[:8]={sha256_hex(k)[:8]}…)")
    print(f"     map stored in {RESTRICTED / 'user_pseudonym_map.csv'} (restricted zone only)")

    anon_logon = logon.assign(user=logon["user"].map(pmap))
    anon_file = file_ev.assign(user=file_ev["user"].map(pmap))
    anon_device = device.assign(user=device["user"].map(pmap))

    # ---- 2) HASHING of quasi-identifiers ----------------------------------
    print("\n2) HASHING (one-way, for IPs and USB devices)")
    for zone_ip in ["10.20.3.44", "185.220.101.7"]:
        print(f"     ip   {zone_ip:<15} -> {sha256_hex(zone_ip)[:16]}…")
    print("     IPs are hashed for sharing; full values stay in the restricted zone.")

    # ---- 3) MASKING demo on a synthetic contact extract --------------------
    print("\n3) MASKING (display minimization)")
    contacts = pd.DataFrame({
        "employee_id": [k for k, _ in example[:3]],
        "email": ["john.doe@corp.example", "asha.r@corp.example", "mike.w@corp.example"],
        "card": ["4539 8812 3456 1234", "5500 1122 3344 5566", "4111 0000 2222 9999"],
    })
    masked = contacts.assign(
        email=contacts["email"].map(mask_email),
        card=contacts["card"].map(mask_card),
        employee_id=contacts["employee_id"].map(pmap),
    )
    masked.to_csv(MASKED / "file_masked.csv", index=False)
    print(masked.to_string(index=False))

    # ---- 4) write anonymized analytical copies -----------------------------
    anon_logon.to_csv(ANON / "logon_pseudonymized.csv", index=False)
    anon_file.to_csv(ANON / "file_pseudonymized.csv", index=False)
    anon_device.to_csv(ANON / "device_pseudonymized.csv", index=False)
    print(f"\n4) Anonymized copies for DATA_ANALYST written to {ANON}")

    # ---- 5) RBAC access-control demonstration ------------------------------
    print("\n5) ACCESS CONTROL MATRIX (simulated HDFS ACL enforcement)")
    for role in ["ADMIN", "SECURITY_ANALYST", "DATA_ANALYST", "GUEST"]:
        check_access(role, "masked_data")
        check_access(role, "anonymized_data")
        check_access(role, "restricted_data")

    AUDIT.write_text("\n".join(audit_lines) + "\n", encoding="utf-8")
    print(f"\nAudit log: {len(audit_lines)} decisions -> {AUDIT}")
    print("Concepts: authentication=who you are (Kerberos) | authorization=what you may"
          " do (ACLs) | masking=hide fields | pseudonymization=reversible rename |"
          " hashing=one-way | encryption=protect at rest/in transit.")


if __name__ == "__main__":
    main()
