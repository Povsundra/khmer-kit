# Retrieval Comparison (Phase 6)

Generated: 2026-08-14T06:54:45.167519+00:00

## Summary

| Config | Hit@1 | Hit@3 |
|--------|-------|-------|
| Semantic only (FAISS) | 15/18 (83.3%) | 15/18 (83.3%) |
| Hybrid (FAISS + BM25) | 18/18 (100.0%) | 18/18 (100.0%) |
| Hierarchical (category parent → dish steps) | 13/18 (72.2%) | 13/18 (72.2%) |

**Winner for Phase 7:** `hybrid` — Hybrid (FAISS + BM25)

## By query type

### Semantic only (FAISS)

| Type | Hit@1 | Hit@3 |
|------|-------|-------|
| exact_lookup | 6/9 (66.7%) | 6/9 (66.7%) |
| technique | 7/7 (100.0%) | 7/7 (100.0%) |
| category | 2/2 (100.0%) | 2/2 (100.0%) |

### Hybrid (FAISS + BM25)

| Type | Hit@1 | Hit@3 |
|------|-------|-------|
| exact_lookup | 9/9 (100.0%) | 9/9 (100.0%) |
| technique | 7/7 (100.0%) | 7/7 (100.0%) |
| category | 2/2 (100.0%) | 2/2 (100.0%) |

### Hierarchical (category parent → dish steps)

| Type | Hit@1 | Hit@3 |
|------|-------|-------|
| exact_lookup | 8/9 (88.9%) | 8/9 (88.9%) |
| technique | 3/7 (42.9%) | 3/7 (42.9%) |
| category | 2/2 (100.0%) | 2/2 (100.0%) |

