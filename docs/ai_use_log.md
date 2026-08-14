# AI Use Log

Significant AI-assisted decisions for the Khmer Kitchen Companion (course disclosure).  
Logged as work happened; summarized for D3 (`docs/D3_REPORT.md`).

**Human gate:** Khmer transcriptions were not accepted until the owner verified raw `.txt`. English JSON and eval tables were spot-checked against sources and scripts.

| Date | Phase | Task | Model / tool | Prompt / role (short) | Validation |
|------|-------|------|----------------|----------------------|------------|
| 2026-08-14 | 1 | Repo scaffold, schema, `dish_checklist.json`, `check_structure.py` | Cursor Grok 4.6 | Implement folder tree from `Context/path.md` | `python scripts/check_structure.py` |
| 2026-08-14 | 1 | `implementation_note.md` tracker | Cursor Grok 4.6 | Write phase checklist from idea/path | Owner used as working tracker all day |
| 2026-08-14 | 3 | `transcribe.py` + `process_scan.py` Vision pipeline | `google/gemini-2.0-flash-001` via OpenRouter | System prompt: transcribe scan **exactly** in Khmer; `[UNCLEAR]`; no invented technique | Owner verified each `data/raw/**/*.txt` (`# verified: yes`) |
| 2026-08-14 | 4 | Structure/translate/contextualize raw → JSON | Cursor agent + Gemini (batch scripts) | Map Khmer to schema; English `standardized_en`; contextual prefix on steps | `python scripts/validate_corpus.py`; spot-check vs scans. **Residual error:** F11 Chek Chien “Chicken” |
| 2026-08-14 | 5 | FAISS + BM25 index, chunk schema | Cursor Grok 4.6 | Contextual Retrieval prepend; ingredients + step + parent chunks | Index manifest 58 chunks; spot query |
| 2026-08-14 | 6 | Three retrieval configs + comparison tables | Cursor Grok 4.6 | semantic_only vs hybrid vs hierarchical | `eval/results/retrieval_comparison.md` — hybrid 18/18 |
| 2026-08-14 | 7 | Intent router, entities, `answer_query()`, templates | Cursor Grok 4.6 | Multi-intent engine; substitution refusal; OOS | `run_engine_eval.py` 12/12 |
| 2026-08-14 | 7 | Grounded generation prompts | Cursor + OpenRouter Gemini Flash | `prompts.py`: answer only from chunks; cite source type | Manual technique/recommend queries in CLI |
| 2026-08-14 | 7 | Missing-dish + typo handling | Cursor Grok 4.6 | Unknown dish + category alternatives; RapidFuzz aliases | `run_typo_eval.py` 8/8; F07 still open |
| 2026-08-14 | 8 | Streamlit Chat / Browse / Recipe UI | Cursor Grok 4.6 | Warm dark theme; bilingual cards | `python scripts/run_app.py` localhost:8501 |
| 2026-08-14 | 8 | Header scroll / tab overlay CSS | Cursor Grok 4.6 | Stop Chat/Browse/Recipe sticking to viewport | Visual check after theme change (F14) |
| 2026-08-14 | 9 | Golden set + `run_eval.py` Hit@k / citation / faithfulness | Cursor Grok 4.6 | 20 queries; lexical faithfulness + optional LLM judge | `eval/results/phase9_eval.md` all gates PASS |
| 2026-08-14 | 10 | Failure log, D3 report, this log | Cursor Grok 4.6 | ≥10 real failures from CLI probes + eval artifacts | Cross-checked against live `answer_query()` on 2026-08-14 |

## Models in the running system

| Use | Model | Notes |
|-----|--------|--------|
| Scan transcription | Gemini 2.0 Flash (OpenRouter) | Image → Khmer draft only |
| Embedding | `paraphrase-multilingual-mpnet-base-v2` | Local Sentence-Transformers |
| Technique / recommend answers | `OPENROUTER_MODEL` (default Gemini Flash) | Chunk-grounded; template fallback if key missing |
| Eval LLM-as-judge | Same OpenRouter key when present | Phase 9 submitted tables used lexical overlap (F15) |

## What AI was not allowed to do

- Accept Khmer as final without human verify.
- Invent substitutes or dishes outside JSON.
- Commit `.env` / API keys.
- Fine-tune or train a classifier (course out of scope).

## Prompt locations (for audit)

- Vision transcription: `src/data_prep/transcribe.py` (`SYSTEM_PROMPT`)
- Answer generation: `src/core/prompts.py` (`SYSTEM_PROMPT` + intent templates)
- Faithfulness judge: `scripts/run_eval.py` (`JUDGE_SYSTEM`)
