# Decisions - vlsi-report-cluster

## [2026-02-11T05:38:00Z] Architectural Decisions
- Embedding model: sentence-transformers `all-MiniLM-L6-v2` (384-dim, local) default
- Clustering: HDBSCAN with `cluster_selection_method='leaf'` for finer-grained clusters
- Template extraction: Drain3 post-clustering (NOT as primary clustering method)
- Output: Rich terminal table default, JSON via `--output-format json`
- Encoding: UTF-8 default with `--encoding` CLI flag (no auto-detect)
