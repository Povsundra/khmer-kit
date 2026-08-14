# Failure Log — Khmer Kitchen Companion

**Course:** AI Engineering · Track B (RAG)  
**Requirement:** ≥10 documented failures with root-cause analysis  
**Last updated:** 2026-08-14  
**Status key:** `fixed` = mitigated in code · `open` = still reproducible · `accepted` = known limitation, not a bug to “fix” this phase

Failures below were observed in CLI, Streamlit, retrieval experiments, or corpus review — not invented for the report.

---

## Summary

| ID | Theme (idea.md §13.3) | Query / trigger | Status |
|----|----------------------|-----------------|--------|
| F01 | Ambiguous / entity resolution | `How to make Omelette?` | fixed |
| F02 | Hierarchical / wrong chunk type | `ingredients of cha mi sour` returned steps | fixed |
| F03 | Hybrid over-index / rewrite bias | dessert category → Samlor parent | fixed |
| F04 | Unknown dish → wrong recipe | `how to cook cha sach morn` | fixed |
| F05 | Hierarchical misses dish child | technique queries Hit@3 42.9% | accepted |
| F06 | Semantic-only exact lookup | Khmer/English dish-name Hit@1 66.7% | accepted |
| F07 | Similar-dish confusion | `how to cook samlor machu pralit` | open |
| F08 | Intent / substitution miss | `no chicken for nhoam moan` | open |
| F09 | Ambiguous query handling | `how to fry garlic for chap chhay soup` | open |
| F10 | Ambiguous query handling | `I want to eat something spicy` | open |
| F11 | Translation drift | Chek Chien `ចេកពងមាន់` → “Chicken” | open |
| F12 | Faithfulness / technique | `how do I know when the fish is 70% done` | open |
| F13 | Citation / corpus gap | North-star `family_interview` | accepted |
| F14 | UI overlay | Chat/Browse/Recipe appeared pinned on scroll | fixed |
| F15 | Eval process | Phase 9 LLM-as-judge skipped | accepted |

---

## F01 — Omelette treated as unknown dish

**Category:** Ambiguous query / entity resolution  
**Query:** `How to make Omelette?`  
**Observed (before fix):** Refusal — dish not in the 14-recipe collection.  
**Expected:** Steps for slug `omelette` (it is in `docs/dish_checklist.json` and the Other parent).  
**Root cause:** `omelette` was treated as a generic token (or failed a minimum-length / stopword gate) while still being a registered slug. Entity resolver ran before retrieval, so RAG never saw the dish.  
**Fix:** Allow registered slugs through `_is_valid_dish_match`; add aliases `oemlette` / `omlette`.  
**Evidence:** `eval/test_queries_typo.json` t01–t02, t08 now pass.  
**Status:** fixed

---

## F02 — Ingredient questions retrieved step chunks

**Category:** Hierarchical retrieval returns wrong child type  
**Query:** `ingredients of cha mi sour`  
**Observed:** How-to / step text instead of the ingredient list.  
**Expected:** Ingredients chunk (lean pork, glass noodles, …).  
**Root cause:** Early index stored mostly step chunks. Intent `ingredients` had no preferred `chunk_type`, so hybrid ranked narrative steps above the list.  
**Fix:** Separate `ingredients` chunks in `corpus_chunks.py`; `preferred_chunk_types("ingredients")` + requery in `search_for_intent()`.  
**Status:** fixed

---

## F03 — Dessert category browse returned Samlor

**Category:** Hybrid search over-indexes on a rewrite keyword  
**Query:** `what dishes are in the dessert category?`  
**Observed (Phase 9 first run):** Hit@1 = `_parent_samlor`; answer listed soups, not Chek Chien. Hit@3 still contained dessert.  
**Expected:** `_parent_dessert`.  
**Root cause:** `rewrite_query()` for `category_browse` always appended the word `soups`, biasing BM25 toward the Samlor parent even when `entities.category == dessert`.  
**Fix:** Rewrite to `{category} category dishes list` (no forced “soups”). Re-eval: g18 Hit@1 pass.  
**Status:** fixed

---

## F04 — Missing dish answered as a different recipe (or empty refuse)

**Category:** Retrieval confuses similar dishes / missing-dish handling  
**Queries:** `how to cook cha sach morn`; `how to cook samlor mju ?`  
**Observed (before fix):** Generic “not in collection” with no alternatives, or retrieval of an unrelated cha/samlor recipe.  
**Expected:** Explicit miss + list of dishes in the inferred category.  
**Root cause:** No `dish_known` gate; engine generated from nearest hybrid hits. Punctuation (`?`) also leaked into the displayed name (`Samlor Mju ?`).  
**Fix:** `format_unknown_dish_with_alternatives()`; strip trailing punctuation in `extract_requested_dish_phrase`.  
**Status:** fixed (refusal path). Remaining risk: see F07.

---

## F05 — Hierarchical retrieval fails technique questions

**Category:** Hierarchical returns parent, misses dish child  
**Trigger:** Phase 6 config `hierarchical` on 7 technique queries.  
**Observed:** Hit@3 **3/7 (42.9%)** vs hybrid **7/7 (100%)**. Overall hierarchical 13/18 (72.2%).  
**Expected:** Correct dish step in top-3.  
**Root cause:** Category prediction restricts candidates to 1–2 parents. Conceptual queries (“how do I know fish is done”) match the samlor parent more than a specific step child, so the dish chunk never enters the candidate set.  
**Decision:** Lock **hybrid** for Phase 7 (`eval/retrieval_winner.json`). Hierarchical kept as a comparison, not production.  
**Status:** accepted

---

## F06 — Semantic-only misses exact dish-name lookup

**Category:** Hybrid vs semantic (keyword strength)  
**Trigger:** Phase 6 `semantic_only`, 9 exact-lookup queries (incl. Khmer titles).  
**Observed:** Hit@1 **6/9 (66.7%)**. Hybrid **9/9 (100%)**.  
**Root cause:** Short Khmer titles and Latin spellings are sparse in the multilingual embedding; BM25 exact tokens recover them.  
**Decision:** Hybrid (0.6 semantic + 0.4 BM25) is the production retriever.  
**Status:** accepted

---

## F07 — `samlor machu pralit` resolved to beef offal soup

**Category:** Retrieval confuses two similar samlor variants  
**Query:** `how to cook samlor machu pralit`  
**Observed (2026-08-14):** `dish_known=True`, slug=`samlor_kari_kroeung_sach_ko`. Full **how-to for Samlor Machu Kroeung Sach Ko** (beef/liver/heart) with no miss warning.  
**Expected:** Unknown-dish refusal (Pralit is not in the 14-dish corpus) or a clarifying question.  
**Root cause:** Curated alias `"samlor machu"` on the kari/machu beef dish plus RapidFuzz `token_set_ratio`: all tokens of the short alias appear in `samlor machu pralit`, so the score is near 100 and the engine treats it as a known dish.  
**Impact:** High — user receives a confident wrong recipe (food-safety / offal steps).  
**Status:** open  
**Suggested fix:** Do not alias a generic “samlor machu” to one child; require leftover tokens (`pralit`) to match or refuse when unmatched.

---

## F08 — Substitution phrasing not classified

**Category:** Intent router miss  
**Query:** `no chicken for nhoam moan`  
**Observed:** Intent=`dish_lookup`. Answer dumps salad steps that **still include chicken** — no corpus-only substitute refusal.  
**Expected:** Intent=`substitution`; “this cookbook does not specify a substitute for chicken…”.  
**Root cause:** Substitution regexes cover `don't have`, `without `, `no fish sauce`, not the pattern `no <ingredient>`.  
**Status:** open

---

## F09 — “How to fry …” not routed as how-to / technique

**Category:** Ambiguous / brittle intent rules  
**Query:** `how to fry garlic for chap chhay soup`  
**Observed:** Intent=`dish_lookup`. Fallback “Related steps from this cookbook” (step 6 does mention frying garlic, but the answer is a dump, not a technique sentence).  
**Expected:** `how_to_cook` or `technique`; a short grounded answer about frying garlic until golden.  
**Root cause:** `how_to_cook` only matches cook/make/prepare — not fry/steam/wrap. Technique patterns require `should i` / `how do i know` / `doneness`.  
**Status:** open

---

## F10 — Preference query dumps unrelated steps

**Category:** Ambiguous query handling — system guesses instead of clarifying  
**Query:** `I want to eat something spicy`  
**Observed:** Intent=`dish_lookup`, no dish/category. Top chunks: Cha Khtuem Barang, pickled-cabbage sngor, Chap Chhay — none framed as a recommendation or a clarifying question.  
**Expected:** Ask which category, or `recommend` from corpus with an explicit hedge.  
**Root cause:** No intent for preference/mood; default `dish_lookup` always retrieves and (without a successful LLM call) prints `format_technique_fallback`.  
**Status:** open

---

## F11 — Translation drift: banana cultivar labeled “Chicken”

**Category:** Translation drift (Khmer ↔ English)  
**Where:** `data/processed/dessert/chek_chien.json`  
**Observed:** Ingredient `raw_kh`: `ឬចេកពងមាន់` → `standardized_en`: **Chicken**. Ingredient list for fried bananas therefore includes chicken.  
**Expected:** A banana cultivar (often “chicken-egg banana” / ចេកពងមាន់), not poultry.  
**Root cause:** Vision/structure LLM (or later English standardization) translated `មាន់` as chicken and dropped `ចេក`. Human verify caught Khmer raw but not the English gloss.  
**Impact:** Grounded answers faithfully repeat a wrong English label (faithful to JSON, unfaithful to the scan).  
**Status:** open (data)

---

## F12 — Technique question without a dish; no 70% doneness

**Category:** Faithfulness / technique coverage  
**Query:** `how do I know when the fish is 70 percent done`  
**Observed:** Intent=`technique`, no slug. Retrieved Machu beef soup (meat tender) and Cha Kroeung fish stir-fry. Answer is a step dump. Corpus never states “70% done”.  
**Expected:** Either answer only what the cookbook says (e.g. “cook through”) and refuse the 70% figure, or ask which dish.  
**Root cause:** (1) No dish entity → hybrid picks any fish/meat step. (2) Original north-star cue lived in a planned *family interview* for Samlor Machu Pralit, which was never ingested. (3) Technique fallback dumps chunks when LLM generate() is skipped or errors.  
**Status:** open

---

## F13 — Citation cannot show `family_interview`

**Category:** Citation misattribution (corpus, not runtime)  
**Trigger:** North star: *Source: family interview* on fish doneness.  
**Observed:** All 14 processed JSON files use `source_type: published_textbook`. UI/engine always cite published textbook.  
**Expected (proposal):** Dual source types.  
**Root cause:** Collection used textbook scans only; family interviews were not transcribed into `data/processed/`. Citation code is correct given the JSON.  
**Status:** accepted for this corpus; expand sources in a later phase.

---

## F14 — Tab buttons stayed on screen while scrolling

**Category:** UI (not RAG)  
**Observed:** Chat / Browse / Recipe pills remained visible at the top after the category title scrolled away.  
**Root cause:** Streamlit `stHeader` is `position: fixed`. Theme set `background: transparent`, so pill buttons showed through the overlay.  
**Fix:** Opaque header background + `position: static` on main-pane radios (`src/interfaces/web/theme.py`).  
**Status:** fixed

---

## F15 — Phase 9 faithfulness used lexical overlap, not LLM-as-judge

**Category:** Evaluation methodology gap  
**Observed:** `eval/results/phase9_eval.md`: “Faithfulness judge: lexical overlap heuristic (LLM unavailable).”  
**Expected (idea.md §13.2):** Gemini/Claude scores 1–5 groundedness.  
**Root cause:** `run_eval.py` calls `llm_available()`; that process did not see `OPENROUTER_API_KEY` (Streamlit’s process did). Harness still records heuristic 4.64/5.  
**Status:** accepted for the submitted tables; re-run `python scripts/run_eval.py` with `.env` loaded to fill LLM-judge columns.

---

## Patterns

1. **Resolve entities before retrieve** — F01, F04, F07. Typos and aliases dominate over vector quality.  
2. **Rewrite tokens leak into BM25** — F03.  
3. **Rule-based intent is brittle** — F08, F09, F10.  
4. **English glosses need a second human pass** — F11.  
5. **Technique answers need the LLM path or a better extractive template** — F09, F12.

## What we will not treat as failures

- Out-of-scope prices/nutrition (`calories in cha mi sour`) — correct refusal.  
- Missing dishes with category alternatives (`cha sach morn` after F04) — intended behavior.
