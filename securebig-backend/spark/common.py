"""SecureBig — shared Spark helpers."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyspark.sql import SparkSession

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

# Every directory a pipeline writes into. Created eagerly so a clean clone can
# run `python run_all.py` straight through instead of dying with
# "No such file or directory" ten minutes into a Spark job.
RESULT_DIRS = [
    RESULTS / "fraud",
    RESULTS / "insider_threat",
    RESULTS / "model_metrics",
    RESULTS / "powerbi",
    RESULTS / "dashboard",
    RESULTS / "logs",
]
for _d in RESULT_DIRS:
    _d.mkdir(parents=True, exist_ok=True)

SEED = 42


def setup_console() -> None:
    """Force UTF-8 on stdout/stderr.

    Scripts print em-dashes and arrows; on a Windows cp1252 console those raise
    UnicodeEncodeError mid-run. No-op on shells that are already UTF-8.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


setup_console()

# Pin worker/ driver python explicitly (Windows Store alias can shadow `python`
# in non-interactive shells and break toPandas/Arrow workers).
os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
os.environ.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)


def get_spark(app: str, cores: str = "*", mem: str = "4g") -> SparkSession:
    from pyspark.sql import SparkSession

    spark = (
        SparkSession.builder.master(f"local[{cores}]")
        .appName(app)
        .config("spark.ui.enabled", "false")
        .config("spark.sql.shuffle.partitions", "8")
        .config("spark.driver.memory", mem)
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    return spark


def save_pd(pdf, rel_path: str) -> Path:
    """Write via pandas (avoids Hadoop FileSystem quirks on Windows)."""
    out = ROOT / rel_path
    out.parent.mkdir(parents=True, exist_ok=True)
    pdf.to_csv(out, index=False)
    return out
