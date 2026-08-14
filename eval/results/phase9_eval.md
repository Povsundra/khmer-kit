# Phase 9 Evaluation

Generated: 2026-08-14T09:14:54.030414+00:00

Golden set: `eval/test_queries.json` · engine path: hybrid `search_for_intent()` + `answer_query()`.

## Summary vs course targets

| Metric | Score | Target | Gate |
|--------|-------|--------|------|
| Retrieval Hit@1 | 18/18 (100.0%) | ≥ 70.0% | PASS |
| Retrieval Hit@3 | 18/18 (100.0%) | ≥ 60.0% | PASS |
| Faithfulness (1–5) | 4.64 | ≥ 3.5 | PASS |
| Citation correctness | 20/20 (100.0%) | ≥ 80.0% | PASS |
| Intent accuracy | 20/20 (100.0%) | — | — |
| Answer must-contain | 20/20 (100.0%) | — | — |

Faithfulness judge: lexical overlap heuristic (LLM unavailable).

## By query type

| Type | n | Hit@1 | Hit@3 | Citation | Faithfulness |
|------|---|-------|-------|----------|--------------|
| category | 2 | 2/2 (100.0%) | 2/2 (100.0%) | 2/2 (100.0%) | 4.69 |
| ingredients | 3 | 3/3 (100.0%) | 3/3 (100.0%) | 3/3 (100.0%) | 4.67 |
| shopping | 1 | 1/1 (100.0%) | 1/1 (100.0%) | 1/1 (100.0%) | 4.26 |
| how_to_cook | 6 | 6/6 (100.0%) | 6/6 (100.0%) | 6/6 (100.0%) | 4.77 |
| technique | 3 | 3/3 (100.0%) | 3/3 (100.0%) | 3/3 (100.0%) | 4.67 |
| recommend | 1 | 1/1 (100.0%) | 1/1 (100.0%) | 1/1 (100.0%) | 4.22 |
| substitution | 1 | 1/1 (100.0%) | 1/1 (100.0%) | 1/1 (100.0%) | 4.35 |
| out_of_scope | 1 | — | — | 1/1 (100.0%) | 5.0 |
| khmer | 1 | 1/1 (100.0%) | 1/1 (100.0%) | 1/1 (100.0%) | 3.95 |
| missing_dish | 1 | — | — | 1/1 (100.0%) | 5.0 |

## Per-query results

| ID | Type | Intent | Hit@1 | Hit@3 | Cite | Contain | Faith |
|----|------|--------|-------|-------|------|---------|-------|
| g01 | category | Y | Y | Y | Y | Y | 4.76 |
| g02 | ingredients | Y | Y | Y | Y | Y | 4.69 |
| g03 | shopping | Y | Y | Y | Y | Y | 4.26 |
| g04 | how_to_cook | Y | Y | Y | Y | Y | 4.86 |
| g05 | technique | Y | Y | Y | Y | Y | 4.62 |
| g06 | recommend | Y | Y | Y | Y | Y | 4.22 |
| g07 | substitution | Y | Y | Y | Y | Y | 4.35 |
| g08 | technique | Y | Y | Y | Y | Y | 4.69 |
| g09 | out_of_scope | Y | — | — | Y | Y | 5.0 |
| g10 | khmer | Y | Y | Y | Y | Y | 3.95 |
| g11 | missing_dish | Y | — | — | Y | Y | 5.0 |
| g12 | how_to_cook | Y | Y | Y | Y | Y | 4.59 |
| g13 | how_to_cook | Y | Y | Y | Y | Y | 4.7 |
| g14 | how_to_cook | Y | Y | Y | Y | Y | 4.84 |
| g15 | ingredients | Y | Y | Y | Y | Y | 4.6 |
| g16 | how_to_cook | Y | Y | Y | Y | Y | 4.81 |
| g17 | ingredients | Y | Y | Y | Y | Y | 4.73 |
| g18 | category | Y | Y | Y | Y | Y | 4.62 |
| g19 | how_to_cook | Y | Y | Y | Y | Y | 4.81 |
| g20 | technique | Y | Y | Y | Y | Y | 4.69 |

## Failures / misses

None — all scored queries met intent, contain, citation, Hit@3, and faithfulness floor.
