# D3 Report — Khmer Kitchen Companion (ម្ហូបខ្មែរ AI)

**Course:** AI Engineering · Track B — RAG Application  
**Project:** Bilingual RAG for traditional Khmer cooking technique  
**Author:** Solo project  
**Date:** 2026-08-14  
**Workspace:** `khmer-kit`

This report is the Phase 10 / D3 evaluation write-up. Live demo notes are in `docs/DEMO_SCRIPT.md` and `docs/PRESENTATION_SLIDES.md`.

---

## 1. Problem and target user

Generic Khmer recipes list ingredients and brief steps but omit technique: when food enters the pot, sensory cues for doneness, and common mistakes. That knowledge is mostly oral. The target user is a young Cambodian or diaspora cook who wants authentic **samlor** and **cha** without a family member in the kitchen.

The system answers bilingual questions from a **closed 14-dish corpus**, with a citation on every grounded answer (`published_textbook` in this collection).

## 2. What was built

A retrieval-augmented engine (`src/core/engine.py` → `answer_query()`) behind a Streamlit UI.

| Layer | Implementation |
|-------|----------------|
| Corpus | 14 dishes + 4 category parents; scan → verified Khmer `.txt` → JSON |
| Embeddings | `paraphrase-multilingual-mpnet-base-v2` (Khmer + English, one space) |
| Index | FAISS IndexFlatIP + BM25; Contextual Retrieval on step chunks |
| Retrieval | Hybrid (0.6 semantic / 0.4 BM25), intent-aware chunk boost, one requery |
| Routing | Rule-based intent + entity/alias resolution (RapidFuzz) |
| Generation | Templates for lists/steps; OpenRouter (Gemini Flash) for technique/recommend |
| Safety | Substitution = corpus-only refusal; prices/nutrition/restaurants = out of scope |
| UI | Streamlit: Chat / Browse / Recipe, EN/KH, source footer |

Intelligence stays in `engine.py`. The UI is a thin client. A Telegram bot (optional Phase 12) would call the same function.

**Out of scope (by design):** fine-tuning, RL, a trained classifier, full Khmer cuisine coverage, food-safety authority.

## 3. Corpus vs original proposal

The proposal listed 15 dishes including Samlor Machu Pralit and family interviews. The delivered corpus is **14 textbook-scan dishes** (samlor 6, cha 3, dessert 3, other 2). All JSON `source_type` values are `published_textbook`. Family-interview technique cues (e.g. “~70% doneness”) were **not ingested**. That is a scope change, not a silent citation bug (see failure F13).

## 4. Retrieval experiments (Phase 6)

Eighteen queries (`eval/test_queries_retrieval.json`) were run on three configs. Results: `eval/results/retrieval_comparison.md`.

| Config | Hit@1 | Hit@3 |
|--------|-------|-------|
| Semantic only (FAISS) | 15/18 (83.3%) | 15/18 (83.3%) |
| **Hybrid (FAISS + BM25)** | **18/18 (100%)** | **18/18 (100%)** |
| Hierarchical (parent → dish) | 13/18 (72.2%) | 13/18 (72.2%) |

**By query type (highlights):**

- Exact lookup: semantic 66.7% Hit@1 vs hybrid 100% — Khmer titles need lexical match.
- Technique: hierarchical 42.9% Hit@3 vs hybrid 100% — category gating drops the dish child.

**Winner locked for production:** hybrid. Hierarchical is useful for *browse-by-category* but harmful as a hard filter on technique questions.

Contextual Retrieval (dish name prepended to each step before embedding) is on for all configs; it was not A/B’d separately in the timebox.

## 5. Engine evaluation (Phase 7–9)

### 5.1 Intent / substring suites

- Engine golden set: `python scripts/run_engine_eval.py` (12/12).
- Typo / alias set: `python scripts/run_typo_eval.py` (8/8 after F01).

### 5.2 Phase 9 harness (course metrics)

Twenty fixed queries in `eval/test_queries.json`. Command: `python scripts/run_eval.py`.  
Tables: `eval/results/phase9_eval.md`.

| Metric | Result | Target | Gate |
|--------|--------|--------|------|
| Retrieval Hit@1 | 18/18 (100%) | ≥ 70% | PASS |
| Retrieval Hit@3 | 18/18 (100%) | ≥ 60% | PASS |
| Faithfulness (1–5) | 4.64 | ≥ 3.5 | PASS |
| Citation correctness | 20/20 (100%) | ≥ 80% | PASS |
| Intent accuracy | 20/20 (100%) | — | — |
| Answer must-contain | 20/20 (100%) | — | — |

Coverage: category, ingredients, shopping list, how-to, technique, recommend, substitution, out-of-scope, Khmer query, missing dish.

**Honesty on faithfulness:** the submitted Phase 9 run used **lexical overlap** with retrieved chunks because that process did not load `OPENROUTER_API_KEY` (F15). The harness *does* call an LLM-as-judge when the key is present. Lexical overlap over-rewards extractive templates and under-tests free-form technique answers.

## 6. Failure analysis

Fifteen cases are logged in `eval/failure_log.md` (requirement ≥ 10).

**Fixed during the project:** omelette entity gate (F01); ingredient vs step chunks (F02); category rewrite leaking “soups” (F03); missing-dish alternatives (F04); Streamlit tab overlay (F14).

**Accepted from experiments:** hierarchical technique collapse (F05); semantic-only exact-name misses (F06); textbook-only citations (F13).

**Still open (highest severity first):**

1. **F07** — `how to cook samlor machu pralit` fuzzy-matches alias `samlor machu` → beef offal soup, served as a full recipe. Wrong-dish, high confidence.
2. **F11** — `ចេកពងមាន់` standardized as “Chicken” on fried bananas (translation drift).
3. **F08–F10** — rule-based intent misses (`no chicken…`, `how to fry…`, preference queries) → chunk dumps instead of refusal, technique answer, or clarification.
4. **F12** — “70% done” is not in the corpus; retrieval guesses a fish/meat step.

**Design insight:** *Resolve entities before retrieval.* Typos and aliases broke more demos than FAISS did. The same resolver, if too greedy (F07), is more dangerous than a miss.

## 7. LLM integration and safety

The LLM is **not** on the critical path for ingredients, shopping lists, or numbered how-to (templates from JSON). It is used for technique synthesis and optional recommendations, with retrieved chunks in `src/core/prompts.py`. If the API fails, the engine falls back to printing related steps — extractive, citable, but a poor answer (F09, F12).

Safety choices that showed up in eval:

- Substitutions: refuse to invent replacements (when intent fires).
- Out of scope: prices, restaurants, nutrition.
- Liver / prahok steps: `requires_safety_review` banner on recipe cards.

The system is **not** a food-safety authority. Doneness language is whatever the paraphrased cookbook says (“cook through”), not a validated 70% cue.

## 8. AI use (summary)

Significant AI-assisted work is logged in `docs/ai_use_log.md`. In short: Cursor agents scaffolded the repo, drafted Vision-LLM transcriptions (human-verified Khmer), structured JSON, retrieval/eval scripts, and the Streamlit UI. Production answers are either templates or OpenRouter generations **constrained by retrieved chunks**. No secrets were committed (`.env` gitignored).

## 9. Limitations and next work

- 14 dishes; no family-interview source type in JSON.
- Rule-based intent will not scale to open phrasing.
- Fuzzy aliases can over-match (F07).
- English standardization of Khmer ingredients needs a dedicated review pass (F11).
- Streamlit demo has no auth; local / course demo only.

If time allowed: fix F07 alias policy, correct Chek Chien English, run Phase 9 with LLM-as-judge in CI, ingest 1–2 family interviews so citation types actually differ.

## 10. Conclusion

The hybrid RAG engine meets the quantitative D3 targets on a 20-query golden set and a 3-way retrieval comparison. The more important result for the course is the **failure log**: similar samlor names, greedy aliases, and translation drift are the real risks in a short Khmer corpus — not “the vector store is empty.” Production retrieval is hybrid; hierarchical and semantic-only are documented as inferior for this data shape. The live demo path is Samlor Proheur + a technique question, with citation `published textbook`, plus a missing-dish refusal (`cha sach morn`) to show the system will not silently cook the wrong stir-fry — except in the Machu Pralit alias case, which we call out rather than hide.

---

**Artifacts**

| File | Role |
|------|------|
| `eval/results/retrieval_comparison.md` | Phase 6 table |
| `eval/results/phase9_eval.md` | Phase 9 table |
| `eval/failure_log.md` | ≥10 root-cause cases |
| `docs/ai_use_log.md` | AI disclosure |
| `docs/DEMO_SCRIPT.md` | D4 live path |
