# SECUREBIG — 3D Security Intelligence Center (Web UI)

A single-file, futuristic 3D SOC-style dashboard UI built for the **SecureBig**
academic project (CBCA293 — Security & Privacy for Big Data Analytics).

## Run it

Option 1 — just double-click `index.html` (needs internet for the CDN libraries).

Option 2 — local server (recommended, avoids any file:// quirks):

```bash
cd securebig-3d-ui
python -m http.server 8080
# open http://localhost:8080
```

## What's inside

| Area | Details |
|---|---|
| 3D hero | Three.js particle globe, threat markers, orbit rings, mouse parallax |
| KPI strip | 6 glass cards, 3D tilt-on-hover, animated counters (real ULB figures: 284,807 txns / 492 fraud) |
| Fraud page | Dual-axis fraud timeline + Hive risk-score donut (ECharts) |
| Insider page | Threat-by-hour bars, live simulated security event feed, top-risk-user drill table (pseudonymized USR-###) |
| ML Lab | 5-model F1 comparison bars + RF-vs-GBT radar — **sample layout values** |
| Privacy | Masking, pseudonymization + SHA-256 examples, HDFS ACL role matrix |

Stack: vanilla HTML/CSS/JS + Three.js r128 + ECharts 5 (CDN), Orbitron/Rajdhani fonts.
No build step, no dependencies to install.

## Connect your real project data

The dashboard auto-loads **`dashboard_data.json`** when it sits next to
`index.html`. It is produced by the backend:

```bash
cd ../securebig-backend
python run_all.py                 # trains everything, writes results/
cp results/dashboard/dashboard_data.json ../securebig-3d-ui/
```

When the JSON is present: KPI cards, the ML F1 bars, the RF-vs-GBT radar and
the top-risk-user table switch to the real Spark MLlib numbers (and labels
update from "sample" to "real"). When it is missing, the page falls back to
clearly-labeled sample layout values. Static charts (fraud timeline, hourly
bars, feed) remain illustrative demo visuals — see
`securebig-backend/results/powerbi/POWERBI_BUILD_STEPS.md` for the full
Power BI version of every page.

Per project rule #2 — the KPI counters for the ULB dataset (284,807 / 492 /
0.173%) are the real published figures; insider-threat figures come from the
documented simulation, never present either as production results.

## For the report

Screenshot the hero (3D globe), KPI strip, each section, and the privacy panel —
these map cleanly to the Power BI page structure in the master prompt
(Pages 1–5), so you can reuse the same narrative in both.
