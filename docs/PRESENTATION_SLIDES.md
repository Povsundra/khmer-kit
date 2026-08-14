# Khmer Kitchen Companion — Presentation Slides
**CS695 AI Engineering · Final Project (Track B — RAG)**  
**Format:** 10-min live demo + 5-min Q&A  
**Presenter notes:** bullets after `🎤` on each slide

---

## Slide 1 — Title

**Khmer Kitchen Companion**  
*ម្ហូបខ្មែរ AI — Bilingual RAG Cooking Assistant*

- **Course:** CS695 AI Engineering · Track B (RAG Application)
- **Team:** [Your name(s)]
- **Repo:** github.com/Povsundra/khmer-kit
- **Demo:** Streamlit chat app · 14 traditional Khmer recipes

🎤 *Open with one sentence: “A bilingual assistant that answers real cooking questions grounded in a verified Khmer recipe corpus — not generic LLM guesses.”*

---

## Slide 2 — Problem & Target User

**Problem**  
Home cooks and diaspora learners struggle to find **trustworthy, step-level** Khmer cooking guidance in **Khmer + English**, especially for technique questions (“when is the fish done?”) and ingredient shopping.

**Target users**
- Khmer speakers preserving family recipes
- English speakers learning Khmer cuisine
- Students / demo audience evaluating a **domain-grounded** RAG system

**Why not ChatGPT alone?**
- Hallucinated ingredients & steps
- No source citation (`published_textbook` vs future `family_interview`)
- Weak handling of Khmer dish names & typos

🎤 *Tie to real pain: wrong spellings, mixed languages, need for citations.*

---

## Slide 3 — Track B Justification

**Track B: RAG Application** ✓

| Requirement (D1/D2) | Our answer |
|---------------------|------------|
| Custom knowledge base | 14 verified dishes · 72 indexed chunks |
| LLM as core component | OpenRouter (Gemini Flash) for technique/recommend |
| Grounded answers | Hybrid retrieval → template or LLM-with-context |
| Evaluation | 20-query harness · Hit@1/3 · faithfulness · typo suite |

**Not chosen:** Agent track (no multi-tool planner) · Product track (focused research/demo app, not monetized product)

🎤 *30 seconds max — show you read the assignment and made a deliberate track choice.*

---

## Slide 4 — Solution Overview

**What we built**  
A **multi-intent RAG engine** + **Streamlit chat UI** that:

1. Classifies question type (ingredients, how-to, technique, recommend, …)
2. Resolves dish names (exact + alias + fuzzy — e.g. *Oemlette → Omelette*)
3. Retrieves relevant chunks with **hybrid BM25 + semantic search**
4. Answers with **templates** (deterministic) or **grounded LLM** (technique)
5. Shows **source citation** on every answer

**Corpus:** 4 categories · `samlor` · `cha` · `dessert` · `other`

🎤 *This slide is the “elevator pitch” before architecture.*

---

## Slide 5 — System Architecture

```
User (EN/KH) → Streamlit UI
      ↓
answer_query()
  → Intent router (rule-based)
  → Entity extraction + typo resolution
  → Query rewrite
  → Hybrid retrieval (FAISS + BM25)
  → Template answer OR LLM + retrieved chunks
      ↓
Answer + citation + recipe preview
```

**Key modules:** `engine.py` · `entities.py` · `entity_resolve.py` · `retrieve.py` · `format.py`

**Embedding:** `paraphrase-multilingual-mpnet-base-v2` (Khmer + English)

🎤 *Point to the pre-RAG entity resolution step — recent fix for typos and “Omelette” bug.*

---

## Slide 6 — Data Pipeline

**From scan to index**

| Stage | Output | Count |
|-------|--------|-------|
| Source scans | `data/source_scans/` | 14 dishes |
| Verified raw Khmer | `data/raw/` | 14 `.txt` |
| Structured JSON | `data/processed/` | 14 dishes + 4 category parents |
| Index | FAISS + BM25 + docstore | 72 chunks |

**Chunk types:** ingredients · steps · category parent lists

**Schema:** bilingual names, standardized EN ingredients, numbered steps, `source_type`, citation

🎤 *Emphasize human-verified Khmer transcription — quality over quantity.*

---

## Slide 7 — Retrieval Design (Phase 6 Winner)

**Compared 3 configs on 18 golden queries**

| Config | Hit@1 | Hit@3 |
|--------|-------|-------|
| Semantic only | lower | lower |
| **Hybrid (winner)** | **100%** | **100%** |
| Hierarchical | 42.9% Hit@3 | over-filters technique Qs |

**Hybrid =** BM25 keyword + dense semantic, merged and re-ranked  
**Intent-aware boost:** ingredient queries prefer ingredient chunks; slug/category filters when entity known

🎤 *Show you ran experiments and locked a winner — rubric: System design (15 pts).*

---

## Slide 8 — Entity Resolution & Edge Cases

**Typo-tolerant resolution (before RAG)**

```
"How to make Oemlette?" → detect term → alias/fuzzy → slug: omelette → retrieve → steps
```

- Text normalization (Unicode, punctuation)
- Curated aliases (`samlor korko` → Samlor Kako)
- Fuzzy match (`rapidfuzz`) with confidence gates
- Unknown dish → refuse + suggest dishes from category (no wrong recipe)

**Eval:** 8/8 typo suite · 12/12 engine suite

🎤 *Optional live typo demo: Oemlette, samlor korko, cha sach morn (should refuse).*

---

## Slide 9 — Evaluation Results (D3 Preview)

**Phase 9 harness — 20 golden queries**

| Metric | Result | Target |
|--------|--------|--------|
| Hit@1 | 100% (18/18) | ≥ 70% |
| Hit@3 | 100% (18/18) | ≥ 60% |
| Citation rate | 100% (20/20) | ≥ 80% |
| Faithfulness (lexical) | 4.64 / 5 | ≥ 3.5 |
| Intent accuracy | 100% (20/20) | — |

**Intent coverage:** category browse · ingredients · shopping · how-to · technique · recommend · substitution · out-of-scope · Khmer queries · missing dish

🎤 *Mention LLM-as-judge when API key available; honest about lexical faithfulness limits.*

---

## Slide 10 — LLM Integration & Safety

**When LLM is used**
- Technique questions (e.g. fish doneness, stir-fry order)
- Recommendations (optional; template fallback without API key)

**When templates are used**
- Ingredients, shopping lists, step-by-step how-to (no hallucination risk)

**Safety choices**
- Substitution queries → **corpus-only refusal** (no invented substitutes)
- Out-of-scope → explicit refusal (e.g. market prices)
- Every answer tags `published_textbook` citation

**Prompt design:** retrieved chunks injected in `prompts.py`; language follows query (EN/KH)

🎤 *Rubric: LLM integration (20 pts) — show you control when the model fires.*

---

## Slide 11 — Live Demo Script (10 minutes)

**Setup:** `python scripts/run_app.py` → http://localhost:8501

| Step | Action | What to highlight |
|------|--------|-------------------|
| 1 | Browse → **Samlor Proheur** | Recipe card · bilingual UI |
| 2 | Ask: *"How do I know when the fish is done in samlor proheur?"* | Technique + citation + retrieval preview |
| 3 | Ask: *"ingredients of cha mi sour"* | Intent routing · ingredient chunk |
| 4 | Ask: *"How to make Oemlette?"* | Typo resolution → Omelette steps |
| 5 | Ask: *"how to cook cha sach morn"* | Unknown dish · no wrong recipe |
| 6 | Toggle **KH** · ask Khmer ingredient query | Multilingual embedding + display |

🎤 *Do NOT use pre-recorded video for core flow (assignment rule). Have terminal + browser ready.*

---

## Slide 12 — Limitations & Failure Cases (D3)

**Known limitations (honest)**
- Only **14 recipes** — narrow domain by design
- Rule-based intent router — brittle on novel phrasing
- Fuzzy match tuned for small corpus — risk if scaled without review
- Streamlit — no auth; local demo only

**Example failure themes (for D3 report)**
- Ambiguous single-word queries (“soup” → category, not a dish)
- LLM technique answers without API key → retrieval fallback
- Khmer romanization variants not in alias table
- Very long conversational queries may miss entity

🎤 *Rubric: Evaluation rigor (20 pts) — show you know what breaks.*

---

## Slide 13 — Future Work & Reflection (D5 Preview)

**If +3 weeks**
- Expand corpus + family_interview sources
- LLM-as-judge in CI; expand failure log to 20+ cases
- Khmer ASR / voice input for hands-free cooking
- Docker deploy · optional Telegram bot (same `answer_query()`)

**What broke & we fixed**
- Omelette blocked as “generic token” while listed in category → entity resolution bug
- Ingredient queries returned step chunks → added ingredient chunks + re-index

**One insight:** *Resolve entities before retrieval — typos break RAG even with perfect vectors.*

🎤 *Optional +5 bonus: reflection memo (D5).*

---

## Slide 14 — Q&A Backup (keep hidden until asked)

**Anticipated questions**

| Question | Short answer |
|----------|--------------|
| Why hybrid over hierarchical? | Hierarchical hurt technique Qs (42.9% Hit@3) |
| Why multilingual-mpnet? | Single model for Khmer + English queries |
| Why templates for how-to? | Deterministic, citeable, works offline |
| How prevent hallucination? | Retrieve first; LLM only with chunks; refusal paths |
| Scale to 1000 dishes? | Alias curation + eval gates; consider learned entity linker |
| AI use in project? | Documented in `docs/ai_use_log.md` per course policy |

🎤 *Be ready to explain any AI-generated component live.*

---

## Slide 15 — Thank You

**Khmer Kitchen Companion**  
Repository · Demo · Eval scripts

```bash
python scripts/run_app.py
python scripts/run_eval.py
python scripts/run_typo_eval.py
```

**Contact / GitHub:** [your link]

🎤 *End on working system — offer to live-query from audience if time.*

---

## Timing Guide (10-minute demo block)

| Minutes | Content |
|---------|---------|
| 0–1 | Slides 1–2: Problem |
| 1–2 | Slides 3–4: Track B + solution |
| 2–3 | Slides 5–7: Architecture + retrieval |
| 3–4 | Slide 8–9: Entity resolution + metrics |
| 4–9 | **Slide 11: Live demo** (majority of time) |
| 9–10 | Slides 12–13: Limitations + close |

*Reserve Slides 14–15 for Q&A session (5 min).*

---

## Mapping to Grading Rubric (100 pts)

| Rubric component | Slides / demo moment |
|------------------|----------------------|
| Application quality (25) | Slide 11 live demo · edge cases |
| LLM integration (20) | Slide 10 · technique query in demo |
| Evaluation rigor (20) | Slide 9 · Slide 12 failures |
| System design (15) | Slides 5–8 architecture |
| Code quality (10) | Mention repo structure, eval scripts, no secrets in git |
| Demo & communication (10) | Clear narrative · live Q&A prep Slide 14 |
