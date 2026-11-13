"""
SecureBig — Phase 1: Dataset 1 acquisition + inspection (ULB Credit Card Fraud).

Downloads the ULB Credit Card Fraud Detection dataset (284,807 transactions,
492 frauds) from OpenML — a reputable public mirror of the Kaggle original.

Usage:
    python data/get_fraud_data.py

Output:
    data/raw/transactions/creditcard.csv        (the dataset, real values)
    data/processed/fraud_inspection.txt         (schema + quality report)
"""
import io
import json
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import arff

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "transactions"
PROC = ROOT / "data" / "processed"
RAW.mkdir(parents=True, exist_ok=True)
PROC.mkdir(parents=True, exist_ok=True)
CSV_PATH = RAW / "creditcard.csv"
INSP_PATH = PROC / "fraud_inspection.txt"
OPENML_API = "https://www.openml.org/api/v1/json"


def http_get(url: str, timeout: int = 120) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "SecureBig-academic/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def find_openml_dataset() -> tuple[int, int]:
    """Locate the ULB creditcard dataset on OpenML. Returns (data_id, file_id).

    The list API returns quality as a list of {name, value} pairs, so match on
    NumberOfInstances == 284807 and MinorityClassSize == 492 to be certain we
    get the real ULB version rather than any same-named dataset.
    """
    listing = json.loads(http_get(f"{OPENML_API}/data/list/data_name/creditcard/limit/20").decode())
    rows = listing["data"]["dataset"]
    for d in rows:
        q = {item["name"]: float(item["value"]) for item in d.get("quality", [])}
        if q.get("NumberOfInstances") == 284807 and q.get("MinorityClassSize") == 492:
            return int(d["did"]), int(d.get("file_id", -1))
    raise RuntimeError("ULB creditcard dataset (284807/492) not found on OpenML")


def download_arff(data_id: int) -> bytes:
    meta = json.loads(http_get(f"{OPENML_API}/data/{data_id}").decode())
    file_id = meta["data_set_description"]["file_id"]
    url = f"https://www.openml.org/data/v1/download/{file_id}/{meta['data_set_description']['name']}.arff"
    print(f"Downloading dataset id={data_id} file_id={file_id} (~140 MB)…")
    return http_get(url, timeout=1800)


def main() -> None:
    if CSV_PATH.exists():
        print(f"Found existing {CSV_PATH} — skipping download.")
    else:
        arff_path = RAW / "creditcard.arff"
        if arff_path.exists():
            print(f"Converting existing {arff_path}…")
            text = arff_path.read_text(encoding="utf-8", errors="replace")
        else:
            data_id, _ = find_openml_dataset()
            blob = download_arff(data_id)
            print("Parsing ARFF…")
            text = blob.decode("utf-8", errors="replace")
        lower = text.lower()
        marker = lower.index("@data") + len("@data")
        header_part, data_part = text[:marker], text[marker:]
        names = [
            ln.split()[1].strip().strip("'")
            for ln in header_part.splitlines()
            if ln.lower().startswith("@attribute")
        ]
        df = pd.read_csv(io.StringIO(data_part), header=None, names=names,
                         comment="%", skip_blank_lines=True)
        # ARFF quotes the nominal class: '0' / '1'
        df["Class"] = df["Class"].astype(str).str.strip("'").astype(int)
        df.to_csv(CSV_PATH, index=False)
        print(f"Saved {CSV_PATH} ({CSV_PATH.stat().st_size/1e6:.1f} MB)")

    # ---- inspection (never assume schema — always report the real one) ----
    df = pd.read_csv(CSV_PATH)
    lines = []
    w = lines.append
    w("SECUREBIG — DATASET 1 INSPECTION REPORT (ULB Credit Card Fraud)")
    w("=" * 64)
    w(f"file            : {CSV_PATH}")
    w(f"rows x cols     : {df.shape[0]} x {df.shape[1]}")
    w(f"columns         : {', '.join(map(str, df.columns))}")
    w(f"dtypes          : {dict(df.dtypes.astype(str))}")
    w(f"missing values  : {int(df.isna().sum().sum())} total "
          f"(per col: {df.isna().sum()[df.isna().sum() > 0].to_dict() or 'none'})")
    w(f"duplicate rows  : {int(df.duplicated().sum())}")
    cls = df["Class"].value_counts().sort_index()
    w(f"class 0 (legit): {cls.get(0, 0)}")
    w(f"class 1 (fraud): {cls.get(1, 0)}")
    w(f"fraud rate      : {df['Class'].mean()*100:.3f}%  (imbalance ratio 1:{int(cls.get(0,0)/max(cls.get(1,1),1))})")
    w(f"amount stats    : min={df['Amount'].min():.2f} mean={df['Amount'].mean():.2f} "
          f"max={df['Amount'].max():.2f}")
    fraud_amt = df.loc[df["Class"] == 1, "Amount"]
    w(f"fraud amounts   : min={fraud_amt.min():.2f} mean={fraud_amt.mean():.2f} max={fraud_amt.max():.2f}")
    t = df["Time"]
    w(f"time span       : {t.min():.0f}s .. {t.max():.0f}s  (~{(t.max()-t.min())/3600:.1f} hours)")
    w("V1..V28         : PCA features (pre-transformed by source dataset; not interpretable directly)")
    w("note            : V-features are anonymized by the source (PCA). Class is the target.")
    text = "\n".join(lines)
    INSP_PATH.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    sys.exit(main())
