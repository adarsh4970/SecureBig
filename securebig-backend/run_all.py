"""
SecureBig - one-command backend runner.

Runs every phase that works on a plain machine (no Hadoop needed):
  Phase 1     fraud dataset acquisition + inspection, simulated insider logs
  Phase 4     privacy layer (mask / pseudonymize / hash / RBAC)
  Phase 7-10  Spark MLlib pipelines (fraud + insider threat, 5 models each)
  Phase 11    export Power BI pack + dashboard JSON

Phases 2-3 (HDFS) and 5-6 (Hive/Pig) need a Hadoop cluster - run those scripts
on the VM/Databricks per hdfs/HDFS_EXPLAINER.md and pig/HIVE_PIG_EXPLAINER.md.

Usage (from the securebig-backend folder):
    python run_all.py                 full run (5-15 min, needs Java 17+)
    python run_all.py --preflight     environment check + manifest only
    python run_all.py --skip-spark    phases 1 and 4 only (no Java needed)
    python run_all.py --skip-data     skip phase 1, reuse the existing CSVs

Why this file is fussy about interpreters: on Windows `python` often resolves to
an install that does NOT have pyspark (on the reference machine the PATH python
is 3.12 while the packages live in 3.13), so the runner probes for an
interpreter that can actually import pyspark and uses it for every step.
Override the probe with:  set SECUREBIG_PYTHON=C:\\path\\to\\python.exe

Every step's console output is mirrored to results/logs/<nn>_<script>.log so the
report screenshots always have a matching text artifact.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
LOG_DIR = RESULTS / "logs"
MANIFEST = RESULTS / "environment_manifest.json"
SEED = 42

# (label, script relative to ROOT, needs_spark, phase_group)
STEPS = [
    ("Phase 1a: fraud dataset acquisition + inspection", "data/get_fraud_data.py", False, "data"),
    ("Phase 1b: simulated insider-threat logs", "data/make_insider_logs.py", False, "data"),
    ("Phase 4: privacy layer", "privacy/privacy_layer.py", False, "privacy"),
    ("Phase 7-10: fraud ML pipeline (Spark)", "spark/fraud_pipeline.py", True, "spark"),
    ("Phase 7-10: insider ML pipeline (Spark)", "spark/insider_pipeline.py", True, "spark"),
    ("Phase 11: exports (Power BI + dashboard)", "spark/export_results.py", False, "export"),
]

EXPECTED_INPUTS = [
    "data/raw/transactions/creditcard.csv",
    "data/raw/user_activity/logon.csv",
    "data/raw/user_activity/file.csv",
    "data/raw/user_activity/device.csv",
    "data/raw/user_activity/http.csv",
    "data/raw/user_activity/scenario_ground_truth.csv",
]

VERSION_PROBE = """
import importlib.metadata as md
import json
import platform
import sys

pkgs = ["pyspark", "pandas", "numpy", "scipy", "scikit-learn", "openpyxl"]
out = {"python": platform.python_version(), "executable": sys.executable, "packages": {}}
for p in pkgs:
    try:
        out["packages"][p] = md.version(p)
    except Exception:
        out["packages"][p] = None
print(json.dumps(out))
"""


def setup_console() -> None:
    """Keep em-dashes/arrows in child output from killing a cp1252 console."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def can_import(py: str, module: str) -> bool:
    try:
        r = subprocess.run(
            [py, "-c", f"import {module}"],
            capture_output=True, timeout=180, cwd=ROOT,
        )
        return r.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def _candidates() -> list[str]:
    cands: list[str] = []
    env_py = os.environ.get("SECUREBIG_PYTHON")
    if env_py:
        cands.append(env_py)
    cands.append(sys.executable)

    # Windows py launcher: ask each version where it lives.
    for ver in ("3.13", "3.12", "3.11", "3.10"):
        try:
            r = subprocess.run(
                ["py", f"-{ver}", "-c", "import sys;print(sys.executable)"],
                capture_output=True, text=True, timeout=60,
            )
            if r.returncode == 0 and r.stdout.strip():
                cands.append(r.stdout.strip())
        except (OSError, subprocess.SubprocessError):
            pass

    local = os.environ.get("LOCALAPPDATA", "")
    for ver in ("313", "312", "311", "310"):
        if local:
            cands.append(str(Path(local) / "Programs" / "Python" / f"Python{ver}" / "python.exe"))

    for name in ("python", "python3", "python3.13"):
        found = shutil.which(name)
        if found:
            cands.append(found)
    return cands


def find_python(need_spark: bool) -> tuple[str | None, str]:
    """First interpreter that satisfies the run's heaviest requirement."""
    module = "pyspark" if need_spark else "pandas"
    seen: set[str] = set()
    for cand in _candidates():
        if not cand or cand in seen:
            continue
        seen.add(cand)
        if not Path(cand).exists():
            continue
        if can_import(cand, module):
            return cand, f"can import {module}"
    return None, f"no interpreter on this machine can import {module}"


def sha256_of(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def java_version() -> str | None:
    if not shutil.which("java"):
        return None
    try:
        r = subprocess.run(["java", "-version"], capture_output=True, text=True, timeout=60)
        text = (r.stderr or r.stdout or "").strip().splitlines()
        return text[0] if text else None
    except (OSError, subprocess.SubprocessError):
        return None


def build_manifest(py: str) -> dict:
    probe = subprocess.run(
        [py, "-c", VERSION_PROBE], capture_output=True, text=True, timeout=180, cwd=ROOT
    )
    runtime: dict = {}
    if probe.returncode == 0:
        try:
            runtime = json.loads(probe.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            runtime = {"raw": probe.stdout[-400:]}

    inputs = []
    for rel in EXPECTED_INPUTS:
        p = ROOT / rel
        if p.exists():
            inputs.append({
                "path": rel,
                "bytes": p.stat().st_size,
                "sha256": sha256_of(p),
            })
        else:
            inputs.append({"path": rel, "bytes": None, "sha256": None})

    return {
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "project": "SecureBig (CBCA293 academic prototype)",
        "seed": SEED,
        "runner_python": {"executable": sys.executable, "version": platform.python_version()},
        "engine_python": runtime,
        "java": java_version(),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "inputs": inputs,
    }


def print_manifest(m: dict) -> None:
    eng = m.get("engine_python", {})
    pkgs = eng.get("packages", {}) or {}
    print(f"  engine python : {eng.get('python', '?')}  ({eng.get('executable', '?')})")
    for name in ("pyspark", "pandas", "numpy", "scipy", "scikit-learn", "openpyxl"):
        print(f"    {name:<13} {pkgs.get(name) or 'MISSING'}")
    print(f"  java          : {m.get('java') or 'NOT FOUND (Spark needs Java 17+)'}")
    print(f"  platform      : {m['platform']['system']} {m['platform']['release']} "
          f"{m['platform']['machine']}")
    missing = [i["path"] for i in m["inputs"] if i["bytes"] is None]
    print(f"  inputs        : {len(m['inputs']) - len(missing)}/{len(m['inputs'])} present"
          + (f"  (missing: {', '.join(missing)})" if missing else ""))


def run_step(py: str, index: int, label: str, script: str) -> int:
    log_path = LOG_DIR / f"{index:02d}_{Path(script).stem}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"\n{'=' * 68}\n{label}\n{'=' * 68}", flush=True)
    tail: deque[str] = deque(maxlen=40)

    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        log.write(f"# {label}\n$ {py} {script}\n\n")
        log.flush()
        proc = subprocess.Popen(
            [py, script],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            print(line, end="", flush=True)
            log.write(line)
            tail.append(line)
        rc = proc.wait()

    if rc != 0:
        print(f"\n!! {label} FAILED (exit {rc})")
        print(f"!! full log: {log_path}")
        print("!! last lines:")
        for line in list(tail)[-15:]:
            print("   " + line.rstrip())
        return rc
    print(f"-- {label} OK   (log: {log_path.relative_to(ROOT)})")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="SecureBig backend runner")
    parser.add_argument("--preflight", action="store_true",
                        help="check the environment and write the manifest, then stop")
    parser.add_argument("--skip-spark", action="store_true",
                        help="run phases 1 and 4 only (no Java/Spark needed)")
    parser.add_argument("--skip-data", action="store_true",
                        help="skip phase 1 (reuse the existing raw CSVs)")
    args = parser.parse_args()

    setup_console()
    RESULTS.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    selected = []
    for index, (label, script, needs_spark, group) in enumerate(STEPS, start=1):
        if args.skip_spark and needs_spark:
            continue
        if args.skip_data and group == "data":
            continue
        selected.append((index, label, script, needs_spark))

    need_spark = any(step_needs_spark for _, _, _, step_needs_spark in selected)
    py, why = find_python(need_spark=need_spark)
    if py is None:
        print(f"!! {why}")
        print(f"!! interpreter on PATH: {sys.executable}")
        print("!! Fix one of these, then re-run:")
        print(f'     "{sys.executable}" -m pip install -r requirements.txt')
        print("   or point the runner at an interpreter that already has pyspark:")
        print(r"     set SECUREBIG_PYTHON=C:\path\to\python.exe")
        print("   or run only the non-Spark phases:  python run_all.py --skip-spark")
        return 2

    print("SecureBig backend runner")
    print(f"  chosen python : {py}  ({why})")
    manifest = build_manifest(py)
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("  environment:")
    print_manifest(manifest)
    print(f"  manifest      : {MANIFEST.relative_to(ROOT)}")

    if args.preflight:
        print("\nPreflight OK. Nothing was executed. Remove --preflight to run the pipeline.")
        return 0

    failures = 0
    for order, (index, label, script, _needs_spark) in enumerate(selected, start=1):
        rc = run_step(py, index, label, script)
        if rc != 0:
            failures += 1
            print("\nStopping: fix the error above and re-run. "
                  "Steps 1b/4 can be re-run safely (idempotent).")
            return rc

    print(f"\n{'-' * 68}")
    print(f"ALL REQUESTED PHASES COMPLETE ({len(selected)} steps, {failures} failures).")
    print("Artifacts  : results/model_metrics, results/fraud, results/insider_threat,")
    print("             results/powerbi, results/dashboard, results/logs")
    print("Manifest   : results/environment_manifest.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
