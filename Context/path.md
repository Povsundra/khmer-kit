AI Engineering Project Blueprint: Khmer Kitchen Companion (ម្ហូបខ្មែរ AI)
A Bilingual Retrieval-Augmented Generation (RAG) System Grounded in Traditional Culinary Knowledge
PART 1: Project Idea & Context (For Master Prompting)
Use this section as the "System Prompt/Context" when initializing your AI coding agents.
1.1 The Core Problem
Cambodia's traditional cooking knowledge (specifically regarding timing, sensory cues, and error correction) is primarily transmitted orally. Generic published recipes provide ingredient lists and brief steps, but omit the crucial technique-level details (e.g., "how hot should the oil be?", "how do I know the fish is 70% cooked?"). As a result, inexperienced diaspora or young Cambodians lack the ability to replicate authentic flavors without a family member present.
1.2 The Solution
Khmer Kitchen Companion is an advanced bilingual (Khmer/English) RAG system. It acts as an expert culinary assistant by answering specific, technique-level cooking questions.
1.3 Technical Uniqueness (The "AI Engineer" Edge)
This is not a basic RAG tutorial project. It implements enterprise-grade architecture to handle the complex data shape of recipes and the Khmer language:
Dual-Source Knowledge Base: Combines verified published cookbooks (for baseline steps) with original family interviews (for technique cues and common mistakes).
Contextual Retrieval: Prevents "chunking amnesia" by prepending specific dish context to every isolated recipe step before embedding (Anthropic's methodology).
Advanced Routing & Retrieval: Uses Query Rewriting (to fix vague user input), Hybrid Search (BM25 Lexical + Semantic Dense vectors), and Cross-Encoder Reranking (BGE-M3) to ensure maximum retrieval accuracy.
Strict Citation UI: Answers are never hallucinated; they are strictly grounded in retrieved context, with the frontend UI displaying source citations and safety warnings.
PART 2: The Structure Layer (Architecture & Directory Blueprint)
The physical layout of the project.
khmer-kitchen-companion/
│
├── data/                            # DATA LAYER (The Ground Truth)
│   ├── source_scans/                # Raw page photos/interview notes
│   ├── raw/                         # Raw LLM-transcribed text
│   ├── processed/                   # Final Structured JSON (Embedded)
│   └── index/                       # FAISS vectors & BM25 indices
│
├── src/
│   ├── data_prep/                   # PRE-PROCESSING (Run once)
│   │   ├── vision_extractor.py      # Gemini Vision API for page-by-page OCR -> JSON
│   │   └── contextualize.py         # LLM script to write Context Strings for chunks
│   │
│   ├── core/                        # RAG ENGINE (Interface-Agnostic)
│   │   ├── query_router.py          # Gemini Flash: Query rewriting/translation
│   │   ├── embed.py                 # paraphrase-multilingual-mpnet-base-v2
│   │   ├── retrieve.py              # Hybrid Search (BM25 + Semantic) + Reranker
│   │   ├── generate.py              # Claude Sonnet: Citation-aware synthesis
│   │   └── engine.py                # Main answer_query() pipeline
│   │
│   ├── safety/                      # SAFETY LAYER
│   │   └── guardrails.py            # Off-topic filter & Food Safety tag handler
│   │
│   └── interfaces/                  # APPLICATION LAYER
│       └── web/app.py               # Streamlit with Explainability UI
│
├── eval/                            # EVALUATION LAYER
│   ├── test_queries.json            # 20 Golden Queries
│   └── run_ragas_eval.py            # Automated RAGAS scoring (Precision, Faithfulness)
│
└── logs/                            # OBSERVABILITY
    ├── retrieval_logs.jsonl         # Logs what chunks were fetched per query
    └── generation_logs.jsonl        # Logs the final LLM inputs/outputs

PART 3: The Data Layer (Enhanced Version)
This is the most critical phase. If the data is bad, the RAG is bad.
3.1 Data Flow Strategy
We do not process entire books at once. We process image-by-image to enforce a strict Human-in-the-Loop Quality Assurance (QA) gate.
Capture: Take a photo of a recipe page (e.g., cha_kney.jpg).
Vision Extraction: Send the image + System Prompt to Gemini 1.5 Flash Vision.
JSON Structuring: Gemini returns a strictly formatted JSON file.
Human Verification: You review the JSON against the photo. If correct, it moves to the processed/ folder.
3.2 The Master JSON Schema
Every recipe will be structured exactly like this before embedding. This solves the measurement, context, and safety gaps.
{
  "dish_name_kh": "ឆាខ្ញី",
  "dish_name_en": "Cha Kney (Ginger Stir-fry)",
  "category": "cha",
  "source_type": "published_textbook_sala_digital",
  "source_citation": "SalaDigital - How to Cook Khmer Food (Page 45)",
  "ingredients": [
    {
      "raw_kh": "ប្រេងឆា ៣ ស្លាបព្រាបាយ",
      "standardized_en": "Cooking oil, 3 tablespoons"
    }
  ],
  "steps": [
    {
      "step": 1,
      "text_kh": "ខ្ញីចិតសំបកលាងទឹកអោយស្អាត ហាន់ជាសរសៃតូចៗ ។",
      "text_en": "Peel the ginger, wash it clean, and slice into thin julienne strips.",
      "technique_note": "Ensure strips are very thin so they crisp up in the oil. (Added from Grandma interview).",
      "requires_safety_review": false,
      "contextualized_text_en": "For the Khmer stir-fry Cha Kney, step 1 requires peeling the ginger, washing it clean, and slicing it into thin julienne strips. Technique note: Ensure strips are very thin so they crisp up in the oil."
    }
  ]
}

