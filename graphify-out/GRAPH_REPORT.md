# Graph Report - default  (2026-11-10)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 100 nodes · 194 edges · 8 communities (5 shown, 3 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 5 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7

## God Nodes (most connected - your core abstractions)
1. `main()` - 9 edges
2. `main()` - 8 edges
3. `save_pd()` - 7 edges
4. `build_manifest()` - 7 edges
5. `normal_day()` - 7 edges
6. `main()` - 7 edges
7. `get_spark()` - 6 edges
8. `main()` - 6 edges
9. `exfil_day()` - 6 edges
10. `newip_day()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `save_pd()`  [EXTRACTED]
  securebig-backend/spark/fraud_pipeline.py → securebig-backend/spark/common.py
- `main()` --calls--> `save_pd()`  [EXTRACTED]
  securebig-backend/spark/insider_pipeline.py → securebig-backend/spark/common.py
- `main()` --calls--> `get_spark()`  [EXTRACTED]
  securebig-backend/spark/fraud_pipeline.py → securebig-backend/spark/common.py
- `main()` --calls--> `get_spark()`  [EXTRACTED]
  securebig-backend/spark/insider_pipeline.py → securebig-backend/spark/common.py

## Import Cycles
- None detected.

## Communities (8 total, 3 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.16
Nodes (9): get_spark(), save_pd(), confusion_counts(), main(), metrics_from(), build_features(), confusion_counts(), main() (+1 more)

### Community 1 - "Community 1"
Cohesion: 0.19
Nodes (10): build_manifest(), can_import(), _candidates(), find_python(), java_version(), main(), print_manifest(), run_step() (+2 more)

### Community 2 - "Community 2"
Cohesion: 0.17
Nodes (6): download_arff(), find_openml_dataset(), http_get(), main(), build_excel_pack(), main()

### Community 3 - "Community 3"
Cohesion: 0.27
Nodes (7): exfil_day(), newip_day(), normal_day(), pick_ip(), snoop_day(), ts(), week()

### Community 4 - "Community 4"
Cohesion: 0.33
Nodes (7): audit(), check_access(), main(), mask_card(), mask_email(), pseudonymize_map(), sha256_hex()

## Knowledge Gaps
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `main()` connect `Community 0` to `Community 2`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Why does `save_pd()` connect `Community 0` to `Community 5`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._