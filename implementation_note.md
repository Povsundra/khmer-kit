# Khmer Kitchen Companion — Implementation Tracker

**Project:** ម្ហូបខ្មែរ AI · Bilingual RAG for traditional Khmer cooking technique  
**Course:** AI Engineering · Track B — RAG Application  
**Workspace:** `khmer-kit`  
**Last updated:** 2026-08-14  

---

## North Star (Demo Must Work)

> User selects **Samlor** → asks *"How do I know when the fish is done in samlor machu pralit?"* → gets **~70% doneness** technique → sees **`Source: family interview`** → recipe card shows **Samlor Machu Pralit · ingredients · steps**.

---

## Locked Tech Decisions

| Layer | Choice |
|-------|--------|
| Embedding | `paraphrase-multilingual-mpnet-base-v2` |
| Vector store | FAISS IndexFlatIP, hierarchical |
| Retrieval | Hybrid (BM25 + semantic) + Contextual Retrieval |
| Generation | Gemini Flash (routine) · Claude Sonnet (final answers) |
| Citation | Every answer states `family_interview` or `published_textbook` |
| Categories | `samlor`, `cha`, `other`, `dessert` (lowercase only) |
| Demo UI | Streamlit (Telegram = optional Phase 12 later) |

---

## 10 Phases — Master Checklist

| # | Phase | Owner | Status |
|---|-------|-------|--------|
| 1 | Setup + dish checklist + folder structure | Agent | ✅ Done |
| 2 | Collect source scans (15 dishes) | **You** | ✅ Done (14 scans) |
| 3 | Transcribe + verify raw `.txt` (one dish at a time) | Agent drafts → **You verify** | ✅ Done (14/14) |
| 4 | Structure + translate + contextualize → JSON | Agent | ✅ Done (14/14 + 4 parents) |
| 5 | Build FAISS + BM25 index | Agent | ✅ Done |
| 6 | Hybrid / hierarchical / contextual retrieval + 3 comparisons | Agent | ✅ Done |
| 7 | `answer_query()` in engine.py + safety + citations | Agent | ✅ Done |
| 8 | Streamlit app + manual E2E test (15 dishes) | Agent build → **You test** | ✅ Done |
| 9 | Eval harness + comparison tables | Agent | ✅ Done |
| 10 | 10+ failure cases + D3 + ai_use_log | Together | ✅ Done |

**Optional bonus:** Phase 11 Docker · Phase 12 Telegram bot

**Current position:** Phase 10 complete — core course path done (optional Docker / Telegram)

**Progress:** 15 failure cases · D3 report · AI use log

---

## How We Collaborate

### Rules
1. **One phase at a time** — say `"Phase 3, dish: slug"` not `"do everything"`.
2. **One dish at a time** in Phases 3–4.
3. **Always include file paths.**
4. **Say `gate pass`** when Khmer is verified — unlocks next step.
5. **Say `Execute Phase X`** to start coding.

### Who does what

| Phase | You | AI Agent |
|-------|-----|----------|
| 1 | Review + fill dish checklist | Scaffold repo, scripts, templates |
| 2 | Crop photos → `source_scans/` | Flag gaps in collection log |
| 3 | **Verify Khmer accuracy** | Draft transcription from image |
| 4 | Spot-check JSON vs source | Structure, translate, contextualize |
| 5–7 | Test sample queries | Build RAG pipeline |
| 8 | Click-test all 15 dishes | Build Streamlit |
| 9–10 | Review failures for accuracy | Run eval, comparison tables |

### Message templates

```
Execute Phase 1.
```

```
Phase 3 — dish: samlor_machu_pralit
File: data/source_scans/samlor/samlor_machu_pralit.jpg
Source type: family_interview
Please draft transcription. I will verify.
```

```
Phase 3 gate pass — samlor_machu_pralit
Raw saved: data/raw/samlor/samlor_machu_pralit.txt
Execute Phase 4 for this dish.
```

```
Phases 1–4 complete. Execute Phase 5.
```

---

## Folder Structure

```
khmer-kit/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── implementation_note.md          ← this file
│
├── Context/
│   ├── idea.md
│   └── path.md
│
├── data/
│   ├── schema/recipe.schema.json
│   ├── source_scans/{samlor,cha,other,dessert}/   ← cropped photos (audit)
│   ├── raw/{samlor,cha,other,dessert}/            ← verified Khmer .txt
│   ├── processed/
│   │   ├── _parents/                              ← 4 category parent JSON
│   │   └── {samlor,cha,other,dessert}/            ← 15 dish JSON
│   └── index/                                     ← FAISS + BM25 + docstore
│
├── src/
│   ├── config.py
│   ├── core/          embed.py · retrieve.py · generate.py · engine.py
│   ├── safety/        prompt_guard.py · scope_filter.py
│   ├── data_prep/     transcribe.py · translate.py · structure.py
│   │                  contextualize.py · build_index.py
│   └── interfaces/
│       ├── web/app.py           ← Streamlit demo
│       └── telegram/bot.py      ← optional Phase 12
│
├── eval/
│   ├── test_queries.json
│   ├── retrieval_configs.json
│   ├── run_eval.py
│   ├── results/
│   └── failure_log.md
│
├── docs/
│   ├── dish_checklist.json        ← 15 dishes locked with sources
│   ├── collection_log.md
│   └── ai_use_log.md
│
├── logs/
│   ├── retrieval_logs.jsonl
│   └── generation_logs.jsonl
│
├── scripts/
│   ├── check_structure.py
│   └── validate_corpus.py
│
└── tests/
    └── test_core.py
```

---

## Data Pipeline (How Data Flows)

```
Book PDF / interview
    → crop ONE dish per photo
    → data/source_scans/{category}/{slug}.jpg
    → AI transcribes (Vision LLM)
    → YOU verify Khmer
    → data/raw/{category}/{slug}.txt
    → structure + translate + contextualize
    → data/processed/{category}/{slug}.json
    → build_index.py
    → data/index/
```

### Data prep — which path?

| Source | What you do |
|--------|-------------|
| **Book photo / PDF page** | Crop one dish → save JPG → AI extract → **you verify** → save `.txt` |
| **Already have verified Khmer text** | Skip photo → save directly to `raw/{category}/{slug}.txt` |

**Do NOT:** process whole PDF at once · use 512-token chunking · copy textbook verbatim.

### Chunking strategy

| Level | Unit | Embedded? |
|-------|------|-----------|
| Page image | Audit only | No |
| Dish JSON | One file per recipe | Optional |
| **Step + context** | `steps[].contextualized_text_en` | **Yes — primary** |
| Category parent | `_parents/{category}.json` | Yes |

---

## 15-Dish Tracker (fill as you go)

| # | Slug | Dish (EN) | Category | Source | Scan | Raw ✓ | JSON ✓ |
|---|------|-----------|----------|--------|------|-------|--------|
| 1 | samlor_machu_pralit | Samlor Machu Pralit | samlor | family_interview | ⬜ | ⬜ | ⬜ |
| 2 | samlor_machu_trakuon | Samlor Machu Trakuon | samlor | | ⬜ | ⬜ | ⬜ |
| 3 | samlor_machu_moan | Samlor Machu Moan | samlor | | ⬜ | ⬜ | ⬜ |
| 4 | samlor_machu_kdam_samut | Samlor Machu Kdam Samut | samlor | | ⬜ | ⬜ | ⬜ |
| 5 | samlor_machu_tralach | Samlor Machu Tralach | samlor | | ⬜ | ⬜ | ⬜ |
| 6 | saraman | Saraman | samlor | | ⬜ | ⬜ | ⬜ |
| 7 | cha_trakuon_oyster | Cha Trakuon (oyster sauce) | cha | | ⬜ | ⬜ | ⬜ |
| 8 | cha_beef_yam | Cha Beef with Fried Yam | cha | | ⬜ | ⬜ | ⬜ |
| 9 | cha_holy_basil | Cha Holy Basil | cha | | ⬜ | ⬜ | ⬜ |
| 10 | cha_kney | Cha Kney (Ginger Stir-fry) | cha | | ⬜ | ⬜ | ⬜ |
| 11 | amok | Amok | other | | ⬜ | ⬜ | ⬜ |
| 12 | lok_lak | Lok Lak | other | | ⬜ | ⬜ | ⬜ |
| 13 | chao_horn | Chao Horn | other | | ⬜ | ⬜ | ⬜ |
| 14 | banana_sugar_syrup | Banana in Sugar Syrup | dessert | | ⬜ | ⬜ | ⬜ |
| 15 | mung_bean_porridge | Sweet Mung Bean Porridge | dessert | | ⬜ | ⬜ | ⬜ |

Fill `source` column in `docs/dish_checklist.json` with `family_interview` or `published_textbook`.

**Start with row 1** (Samlor Machu Pralit — sample already in `Context/idea.md`).

---

## Phase Gates (Pass Before Moving On)

### Phase 1
- [ ] All folders exist (`python scripts/check_structure.py`)
- [ ] `docs/dish_checklist.json` — 15 entries, each with `source_type`
- [ ] Root files: README, requirements.txt, .env.example, .gitignore

### Phase 2
- [ ] 15/15 dishes have scan or logged deferral in `docs/collection_log.md`

### Phase 3 (per dish)
- [ ] Transcription verified by you (zero unresolved `[UNCLEAR]`)
- [ ] Saved to `data/raw/{category}/{slug}.txt`

### Phase 4 (full corpus)
- [ ] 15 dish JSON + 4 parent JSON validate
- [ ] `python scripts/validate_corpus.py` passes

### Phase 5
- [ ] Index rebuilds with one command
- [ ] Spot query returns correct dish

### Phase 6
- [x] 3 retrieval comparisons run; winner documented

### Phase 7
- [x] `answer_query()` returns cited, grounded answers

### Phase 8
- [x] Streamlit runs; golden demo path works; all 14 browsable

### Phase 9
- [x] ~20 test queries scored; comparison table produced

### Phase 10
- [x] ≥10 failure cases with root cause; D3 + ai_use_log complete

---

## What the Completed System Can Do

| Capability | Supported? |
|------------|------------|
| Ask technique questions (timing, doneness, mistakes) | ✅ Main feature |
| Ask how to cook a dish (15 in corpus) | ✅ |
| Ingredient list for one dish | ✅ |
| Shopping list before market (one dish) | ✅ |
| Shopping list (multiple dishes) | ⚠️ Partial — ask explicitly |
| Browse by category (Samlor/Cha/Other/Dessert) | ✅ |
| Khmer + English toggle | ✅ |
| Source citation on every answer | ✅ |
| Any dish outside 15 · prices · nutrition · restaurants | ❌ Out of scope |

---

## JSON Schema (per dish)

```json
{
  "dish_name_kh": "",
  "dish_name_en": "",
  "category": "samlor|cha|other|dessert",
  "source_type": "family_interview|published_textbook",
  "source_citation": "",
  "ingredients": [{ "raw_kh": "", "standardized_en": "" }],
  "steps": [{
    "step": 1,
    "text_kh": "",
    "text_en": "",
    "technique_note": "",
    "requires_safety_review": false,
    "contextualized_text_en": ""
  }],
  "common_mistake": ""
}
```

---

## Raw Text Template

```text
# slug: samlor_machu_pralit
# source_type: family_interview
# source_citation: Interview with [relation], 2026
# verified: yes

[Khmer dish name]

គ្រឿងផ្សំ
[ingredients exactly as in source]

របៀបធ្វើ
1- [step one]
2- [step two]
```

---

## Week Plan (5-week course)

| Week | Focus | Target |
|------|-------|--------|
| 1 | Phase 1–2 | Checklist + start collecting scans |
| 2 | Phase 3–4 | 15 raw txt + 15 JSON validated |
| 3 | Phase 5–6 | Index + retrieval experiments |
| 4 | Phase 7–9 | Engine + Streamlit + eval harness |
| 5 | Phase 8–10 | UI polish + failure log + demo + D3 |

---

## Interface Strategy

- **Now:** Streamlit for D4 live demo
- **Later (optional):** Telegram bot calls same `engine.answer_query()` — no RAG logic in bot file
- **Rule:** All intelligence in `engine.py`; UI is thin

---

## Quantitative Targets (Eval)

| Metric | Minimum | Strong |
|--------|---------|--------|
| Retrieval Hit@1 (exact lookup) | ≥ 70% | ≥ 85% |
| Retrieval Hit@3 (technique queries) | ≥ 60% | ≥ 75% |
| Faithfulness (LLM-judge 1–5) | ≥ 3.5 | ≥ 4.2 |
| Citation correctness | ≥ 80% | ≥ 95% |
| Documented failure cases | ≥ 10 | ≥ 15 |

---

## Out of Scope (Do Not Build)

- Fine-tuning · Reinforcement learning · Classical ML classifier
- Full Khmer cuisine database (15 dishes = proof of concept)
- Food safety authority · verbatim textbook copy
- Market prices · restaurant recommendations

---

## Session Log (update each work session)

| Date | Phase | What was done | Next step |
|------|-------|---------------|-----------|
| 2026-08-14 | Phase 1 | Folders, checklist, templates, check_structure.py | Phase 2: crop scans |
| 2026-08-14 | Phase 2 | 14 PNG scans collected | Phase 3: verify Khmer raw |
| 2026-08-14 | Phase 3–4 | PNG extraction → DRAFT.txt; Phase 4 tooling; pilot JSON samlor_chap_chhay | Verify remaining 13 raw → JSON batch |
| 2026-08-14 | Phase 5 | FAISS + BM25 index (58 chunks), hybrid query tested | Execute Phase 6 |
| 2026-08-14 | Phase 6 | 3-way retrieval eval (18 queries); hybrid wins 100% Hit@3 | Execute Phase 7 |
| 2026-08-14 | Phase 7 | Multi-intent engine (10 query types); answer_query.py; 10/10 eval | Execute Phase 8 |
| 2026-08-14 | Phase 8 | Streamlit warm-minimal UI; browse + ask + recipe cards | Execute Phase 9 |
| 2026-08-14 | Phase 9 | 20 golden queries; Hit@1/3 + citation + faithfulness tables | Execute Phase 10 |
| 2026-08-14 | Phase 10 | 15 failure cases; D3 report; ai_use_log | Demo / optional Phase 11–12 |

---

## How to run transcription (Phase 3)

```bash
# 1. Setup (once)
pip install -r requirements.txt
copy .env.example .env    # add OPENROUTER_API_KEY

# 2. One dish
python scripts/process_scan.py --slug omelette

# 3. All pending scans
python scripts/process_all_pending.py

# 4. Re-run overwriting drafts
python scripts/process_all_pending.py --force
```

Output: `data/raw/{category}/{slug}.DRAFT.txt` — **you verify**, then set `# verified: yes` and rename to `{slug}.txt`.


1. Say **`Execute Phase 1`** to scaffold repo
2. Fill **`docs/dish_checklist.json`** (15 dishes + sources)
3. Crop first dish → **`data/source_scans/samlor/samlor_machu_pralit.jpg`**
4. Say **`Phase 3, dish: samlor_machu_pralit`** + file path
5. Verify Khmer → say **`Phase 3 gate pass`**
6. Say **`Execute Phase 4 for this dish`**
7. Repeat for remaining 14 dishes
8. Then **`Execute Phase 5`**

**Golden rule:** IMPLEMENT → VERIFY → CONFIRM → next phase.

---

## GitHub Repository

**Repo:** [github.com/Povsundra/khmer-kit](https://github.com/Povsundra/khmer-kit.git)

```bash
git clone https://github.com/Povsundra/khmer-kit.git
cd khmer-kit
```

---

## Quick Status (read this first)

| Item | Count | Status |
|------|-------|--------|
| Source scans | 14/14 | ✅ Done |
| Raw Khmer verified (`.txt`) | 14/14 | ✅ Done |
| Processed JSON | 14/14 | ✅ Done |
| Category parent JSON | 4/4 | ✅ Done |
| Category parent JSON | 0/4 | ⬜ Not started |
| FAISS + BM25 index | 58 chunks | ✅ Done |
| Retrieval experiments | hybrid winner | ✅ Done |
| RAG engine (`answer_query`) | 10/10 eval | ✅ Done |
| Streamlit demo | warm minimal UI | ✅ Done |
| Phase 9 eval harness | 20 queries, all gates PASS | ✅ Done |
| Failure log | 15 cases | ✅ Done |
| D3 report | `docs/D3_REPORT.md` | ✅ Done |
| AI use log | `docs/ai_use_log.md` | ✅ Done |

**You are here:** Phase 10 complete. Next: live demo (`docs/DEMO_SCRIPT.md`) or optional Phase 11 Docker / Phase 12 Telegram.

**All categories complete:** samlor 6/6 · cha 3/3 · dessert 3/3 · other 2/2

**Key docs:** `docs/dish_checklist.json` · `docs/PHASE3_QUEUE.md` · `data/processed/samlor/samlor_chap_chhay.json` (pilot)

---

## All Phases — Key Idea, Checklist, Status

### Phase 1 — Setup ✅ Done

**Key idea:** Scaffold repo, folders, schema, and dish checklist so every later phase has a fixed structure.

- [x] Folder tree (`data/`, `src/`, `scripts/`, `docs/`, `eval/`)
- [x] `docs/dish_checklist.json` (14 dishes + sources)
- [x] `data/schema/recipe.schema.json`
- [x] `scripts/check_structure.py` passes
- [x] `requirements.txt`, `.env.example`, `.gitignore`

**Say to start Phase 2:** `Execute Phase 2` (collection — already done)

---

### Phase 2 — Collect scans ✅ Done

**Key idea:** One cropped PNG per dish = audit trail and input for transcription.

- [x] 14 PNGs in `data/source_scans/{category}/`
- [x] `docs/collection_log.md` updated
- [x] Filenames mapped to slugs in checklist

**Output path:** `data/source_scans/{category}/{name}.png`

---

### Phase 3 — Transcribe + verify Khmer 🔄 In progress (1/14)

**Key idea:** Raw files are **Khmer only**, human-verified ground truth. English comes in Phase 4.

- [x] All 14 `.DRAFT.txt` extracted from PNG scans
- [ ] Each dish: compare DRAFT to PNG, fix Khmer, `# verified: yes`
- [ ] Rename `{slug}.DRAFT.txt` → `{slug}.txt`
- [ ] Message: `Phase 3 gate pass — {slug}`

**Dessert batch:** ✅ complete (3/3 raw + JSON)

**Verified so far:** all 6 samlor + all 3 cha + all 3 dessert

**Your workflow per dish:**
1. Open `.DRAFT.txt` + matching PNG side by side
2. Fix characters → set `# verified: yes` → save as `{slug}.txt`

---

### Phase 4 — Structure + translate + contextualize 🔄 In progress (1/14)

**Key idea:** Turn verified Khmer raw into **bilingual JSON** for RAG (Khmer + English in `processed/`, not in `raw/`).

- [x] `src/data_prep/structure.py` — parse raw → ingredients + steps
- [x] `src/data_prep/translate.py` — English names + step text (paraphrased)
- [x] `src/data_prep/contextualize.py` — `contextualized_text_en` per step
- [x] `scripts/process_raw.py` — `python scripts/process_raw.py --slug X`
- [x] `scripts/validate_corpus.py` — schema check
- [ ] 14 dish JSON files in `data/processed/{category}/`
- [ ] 4 parent JSON in `data/processed/_parents/`
- [ ] Full corpus validation passes

**JSON so far:** `data/processed/samlor/samlor_chap_chhay.json` (14 ingredients · 6 steps)

**Say after raw verified:** `Execute Phase 4 for {slug}`

**Gate pass:** `Phase 4 gate pass` (all 14 + 4 parents validate)

---

### Phase 5 — Build index ✅ Done

**Key idea:** Embed `contextualized_text_en` per step + category parents → FAISS + BM25 in `data/index/`.

- [x] `src/core/embed.py` — `paraphrase-multilingual-mpnet-base-v2`
- [x] `src/data_prep/build_index.py` + `scripts/build_index.py`
- [x] `scripts/query_index.py` — hybrid spot queries
- [x] 58 chunks indexed (54 steps + 4 parents)
- [x] Spot queries return correct dish

**Rebuild index:** `python scripts/build_index.py`  
**Test query:** `python scripts/query_index.py "fried bananas"`

**Say to start Phase 6:** `Execute Phase 6`

---

### Phase 6 — Retrieval experiments ✅ Done

**Key idea:** Compare semantic-only, hybrid, and hierarchical retrieval; pick winner for engine.

- [x] 3 retrieval configs in `eval/retrieval_configs.json`
- [x] 18 golden queries in `eval/test_queries_retrieval.json`
- [x] `scripts/run_retrieval_experiments.py` — Hit@1 / Hit@3 metrics
- [x] Results in `eval/results/retrieval_comparison.json` + `.md`
- [x] Winner locked: **`hybrid`** (100% Hit@3) → `eval/retrieval_winner.json`
- [x] `src/core/retrieve.py` — `search(mode=...)` for all three strategies

**Results (18 queries):**

| Config | Hit@1 | Hit@3 |
|--------|-------|-------|
| Semantic only | 83.3% | 83.3% |
| **Hybrid (winner)** | **100%** | **100%** |
| Hierarchical | 72.2% | 72.2% |

Hierarchical hurt technique queries (42.9% Hit@3) by over-filtering to predicted categories.

**Run experiments:** `python scripts/run_retrieval_experiments.py`

**Say to start Phase 7:** `Execute Phase 7`

---

### Phase 7 — RAG engine ✅ Done

**Key idea:** `answer_query()` classifies intent, retrieves with hybrid search, returns template or grounded LLM answers.

- [x] `src/core/intent.py` — rule-based intent router (10 intents)
- [x] `src/core/entities.py` — dish / category / ingredient extraction
- [x] `src/core/entity_resolve.py` — typo-tolerant alias + fuzzy dish resolution (rapidfuzz)
- [x] `data/knowledge/dish_aliases.json` — curated EN/KH dish synonyms
- [x] `src/core/rewrite.py` — conversational query rewrite
- [x] `src/core/retrieve.py` — `search_for_intent()` with chunk-type boost + requery
- [x] `src/core/format.py` — template answers (category list, shopping, steps, substitution refusal)
- [x] `src/core/prompts.py` + `src/core/llm.py` — grounded OpenRouter generation (technique, recommend)
- [x] `src/core/engine.py` — `answer_query()` orchestrator
- [x] `scripts/answer_query.py` — user-facing CLI
- [x] `scripts/query_index.py --engine` — engine mode
- [x] `eval/test_queries_engine.json` + `scripts/run_engine_eval.py` — 12/12 pass
- [x] `eval/test_queries_typo.json` + `scripts/run_typo_eval.py` — typo/alias resolution eval

**Supported question types:** category browse · ingredients · shopping list · how to cook · technique · recommend · substitution (corpus-only refusal) · out of scope

**Ask a question:**
```bash
python scripts/answer_query.py "what soups are in the samlor category?"
python scripts/answer_query.py "I want cha mi sour, what should I buy at the market?"
python scripts/answer_query.py "recommend a cha dish today"
python scripts/answer_query.py "no fish sauce for cha mi sour"
python scripts/answer_query.py "should I stir-fry meat before adding water for soup?"
```

**Run eval:** `python scripts/run_engine_eval.py`

**Say to start Phase 8:** `Execute Phase 8`

---

### Phase 8 — Streamlit demo ✅ Done

**Key idea:** Warm minimal browser UI — browse 14 dishes, ask questions, view recipe cards.

- [x] `src/interfaces/web/app.py` — main Streamlit app
- [x] `src/interfaces/web/theme.py` — custom CSS (cream/terracotta/green)
- [x] `src/interfaces/web/recipe_card.py` — bilingual recipe cards
- [x] `scripts/run_app.py` — launcher
- [x] `docs/DEMO_SCRIPT.md` — golden demo + 14-dish checklist
- [ ] **You** click-test all 14 dishes (see DEMO_SCRIPT.md)

**Run the app:**
```powershell
pip install -r requirements.txt
python scripts/run_app.py
# opens http://localhost:8501
```

**Golden demo:** Samlor → Samlor Proheur → ask *"How do I know when the fish is done?"*

**Say to start Phase 9:** `Execute Phase 9`

---

### Phase 9 — Evaluation ✅ Done

**Key idea:** ~20 golden queries, automated scoring, comparison tables for course report.

- [x] `eval/test_queries.json` — 20 queries (category, ingredients, shopping, how-to, technique, recommend, substitution, OOS, Khmer, missing dish)
- [x] `scripts/run_eval.py` — Hit@1, Hit@3, faithfulness, citation, intent, must-contain
- [x] Results in `eval/results/phase9_eval.md` + `eval/results/phase9_eval.json`

**Run eval:**
```powershell
python scripts/run_eval.py
```

**Latest scores (2026-08-14):**

| Metric | Score | Target | Gate |
|--------|-------|--------|------|
| Hit@1 | 18/18 (100%) | ≥ 70% | PASS |
| Hit@3 | 18/18 (100%) | ≥ 60% | PASS |
| Faithfulness | 4.64 / 5 | ≥ 3.5 | PASS |
| Citation | 20/20 (100%) | ≥ 80% | PASS |
| Intent | 20/20 (100%) | — | — |

Faithfulness uses lexical overlap with retrieved chunks; LLM-as-judge runs when `OPENROUTER_API_KEY` is set. Category rewrite no longer injects “soups” (so dessert/cha browse ranks the right parent).

**Say to start Phase 10:** `Execute Phase 10`

---

### Phase 10 — Failure log + deliverables ✅ Done

**Key idea:** Document ≥10 real failures with root cause; complete D3 report + `docs/ai_use_log.md`.

- [x] `eval/failure_log.md` — 15 cases (F01–F15), root cause + status
- [x] `docs/D3_REPORT.md` — evaluation write-up
- [x] `docs/ai_use_log.md` — AI disclosure

**Highest open risks:** F07 (`samlor machu pralit` → beef soup); F11 (Chek Chien “Chicken” gloss).

**Say to start (optional):** `Execute Phase 11` (Docker) or `Execute Phase 12` (Telegram)

---

### Optional (bonus)

| Phase | Key idea | Status |
|-------|----------|--------|
| 11 Docker | Containerize app | ⬜ |
| 12 Telegram | Bot calls same `engine.answer_query()` | ⬜ |

---

## 14-Dish Progress Tracker

| # | Slug | Category | Scan | Raw ✓ | JSON ✓ |
|---|------|----------|------|-------|--------|
| 1 | samlor_chap_chhay | samlor | ✅ | ✅ | ✅ |
| 2 | samlor_kako_phlae_tnoat | samlor | ✅ | ✅ | ✅ |
| 3 | samlor_kari_kroeung_sach_ko | samlor | ✅ | ✅ | ✅ |
| 4 | samlor_proheur | samlor | ✅ | ✅ | ✅ |
| 5 | sngor_chrouk_spay_chrok | samlor | ✅ | ✅ | ✅ |
| 6 | sngor_prohet_trei_slat | samlor | ✅ | ✅ | ✅ |
| 7 | cha_khtuem_barang | cha | ✅ | ✅ | ✅ |
| 8 | kroeung_sach_trei | cha | ✅ | ✅ | ✅ |
| 9 | cha_mi_sour | cha | ✅ | ✅ | ✅ |
| 10 | bay_damnaeub_mukh_bangkea | dessert | ✅ | ✅ | ✅ |
| 11 | chek_chien | dessert | ✅ | ✅ | ✅ |
| 12 | num_ansom_chrouk | dessert | ✅ | ✅ | ✅ |
| 13 | nhoam_moan_tr_young_cek | other | ✅ | ✅ | ✅ |
| 14 | omelette | other | ✅ | ✅ | ✅ |

*Raw ✓ = `{slug}.txt` with `# verified: yes` · JSON ✓ = `data/processed/{category}/{slug}.json`*

---

## Commands Cheat Sheet

```bash
# Phase 1 gate
python scripts/check_structure.py

# Phase 4 — one dish (raw must be verified first)
python scripts/process_raw.py --slug samlor_chap_chhay

# Phase 4 gate — all JSON
python scripts/validate_corpus.py

# Phase 5 (later)
python scripts/build_index.py

# Phase 9
python scripts/run_eval.py
```

---

## What to Say Next (copy-paste)

```
Execute Phase 11
```

or

```
Execute Phase 12
```

Live demo: `python scripts/run_app.py` · script in `docs/DEMO_SCRIPT.md`