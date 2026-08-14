AI Engineering — My Project
Khmer Kitchen Companion
ម្ហូបខ្មែរ AI
A systematic implementation guide: bilingual retrieval-augmented generation grounded in family-collected and government-published Khmer culinary knowledge
 
1. Background and motivation
Cambodia's traditional cooking knowledge is held primarily through oral transmission — mothers and grandmothers teaching technique directly, in the kitchen, with no written record of the judgment calls that separate a correctly made dish from a mediocre one. As fewer people learn to cook this way, and as the diaspora grows further from direct family teaching, this technique-level knowledge is genuinely at risk of being lost. At the same time, Cambodia is in an early period of AI Engineering adoption, with very little applied work grounded in Khmer-language data or Cambodian cultural domains. This project sits at the intersection of those two facts: an applied, technically rigorous RAG system built on a genuinely underserved problem and a genuinely underserved language.
2. Problem statement
Generic recipes — whether sourced online or from print cookbooks — typically provide an ingredient list and a brief method, but omit the technique-level detail that determines success: the precise timing of when each ingredient enters the pot, the sensory cues that indicate doneness, and the common mistakes a first-time cook is likely to make. This is exactly the knowledge an experienced home cook carries but rarely writes down, because it was never written down for them either — it was demonstrated and corrected, in person, over many repetitions.
Someone without a family member available to teach them directly is left with recipes that tell them what to use, but not how to actually use it.
2.1 Target user
Young Cambodians or diaspora who want to learn authentic Khmer cooking — particularly traditional soups (samlor) and stir-fries (cha) — but do not have a family member available to teach them directly, in person, in real time.
3. Objectives
3.1 General objective
To design, build, and evaluate a bilingual (Khmer/English) retrieval-augmented generation system that answers specific, technique-level Khmer cooking questions, grounded in a custom knowledge base built from original family interviews and a Ministry of Education-published cookbook, with every answer traceable to its source.
3.2 Specific objectives
1.   Collect and structure a multi-source corpus of 10–15 Khmer dishes (Phase 1), spanning samlor, cha, and other categories, from family interviews and supplementary published sources.
2.   Build a multilingual retrieval pipeline (FAISS, hierarchical structure, Contextual Retrieval) that handles short-document recipes and category/variation disambiguation (e.g., the many samlor and cha sub-types).
3.   Run a controlled comparison of retrieval techniques — flat vs. hierarchical retrieval, semantic-only vs. hybrid (BM25 + semantic) search, with and without Contextual Retrieval — to determine which combination performs best for this domain.
4.   Build source-citation metadata into the system architecture itself, so every generated answer states whether it came from a family recipe or a published source.
5.   Evaluate the system using a fixed, categorized test-query set, LLM-as-judge scoring, and a minimum of 10 documented failure cases with root-cause analysis.
4. Significance of the study
•     Cultural preservation — captures oral and family cooking knowledge that exists nowhere in writing, before it is lost across generations.
•     Real, underserved skill gap — serves people who genuinely have no other accessible way to learn this technique-level knowledge.
•     Technical contribution — addresses RAG problems that do not appear in typical English-document tutorials: short-document corpora where internal chunking is largely meaningless, category/variation disambiguation across many similar dishes, and multilingual Khmer–English retrieval within a single embedding space.
•     Data literacy and citation discipline — demonstrates a citation-aware system design, where source attribution is a first-class part of the architecture rather than an afterthought in the written report.
•     Early-mover positioning — very little applied AI Engineering work currently exists grounded in Khmer-language, Cambodia-specific data; this project is a concrete, demonstrable example of that gap being filled.
5. Track justification and rubric alignment
Track B — RAG Application. This is a retrieval-augmented system grounded in a custom knowledge base — a domain-expert assistant, matching the syllabus's own description of this track almost exactly.
Syllabus requirement
How this project satisfies it
Clear problem statement and target user
Section 2 above
Chosen track and justification
Track B, above
Planned tech stack
Section 9
Evaluation plan
Section 11
Team member roles
Solo project (Section 12)
At least 10 documented failure cases
Failure categories pre-identified in Section 11.3
Document every significant AI-assisted decision
Section 13 — AI use disclosure approach

 
6. Data sources
Three source types are used, each with a different role and a different standard of care regarding copyright and citation.
6.1 Family interviews (primary source)
Original recipes collected directly from family members, in Khmer, in their own words — including the technique detail (timing, sensory cues, common mistakes) that published sources typically omit. This is the copyright-clean, authentic core of the corpus. Each entry is logged with the contributor's relation and the date of the interview.
6.2 Ministry of Education, Youth and Sport — SalaDigital (cited reference source)
វិធីធ្វើម្ហូប និងបង្អែមខ្មែរ — “How to Cook Khmer Food and Desserts”
Author/publisher: ឡុង សាវឹង. Published 2025. Hosted on SalaDigital, the official digital library of Cambodia's Ministry of Education, Youth and Sport (sala.moeys.gov.kh), tagged under “education” and “life skills.”
This is treated as an authoritative reference for verifying technique accuracy and filling gaps in family-collected entries. Content is paraphrased into original corpus entries, never reproduced verbatim, and is cited explicitly by source in every record that draws on it, consistent with standard academic citation practice.
6.3 Printed cookbook and online recipe index (cross-check only)
A printed Khmer cookbook and a public recipe blog index (choukhmer.wordpress.com) were reviewed for scope and structure — specifically, to confirm the breadth of samlor and cha variations that justify this project's hierarchical retrieval design. The blog itself discloses that undated content is excerpted from a 2009 newspaper source, and the cookbook is a commercially published work. Neither is used as a verbatim text source in the corpus; both are used only to verify completeness of family-collected entries and to scope the candidate dish list in Section 7.
7. Candidate dish list (Phase 1)
Sources are confirmed (family interviews, the MoEYS textbook, and supplementary cross-checks) but the final dish selection has not yet been locked. The following 15-dish candidate list is proposed to give Phase 1 enough category depth — particularly within samlor and cha — to make the hierarchical retrieval comparison in Section 10 meaningful. This list is expected to expand in later phases as more dishes are collected from the same sources.
7.1 Samlor — sour soups (6 dishes, for the hierarchical parent/child demonstration)
•     សម្លម្ជូរព្រលិត — Samlor Machu Pralit (worked sample, Section 8)
•     សម្លម្ជូរត្រកួន — Samlor Machu Trakuon (morning glory sour soup)
•     សម្លម្ជូរមាន់ — Samlor Machu Moan (chicken sour soup)
•     សម្លម្ជូរក្ដាមសមុទ្រ — Samlor Machu Kdam Samut (sea crab sour soup)
•     សម្លម្ជូរត្រឡាច — Samlor Machu Tralach (winter melon sour soup)
•     សារ៉ាម៉ាន់ — Saraman (curry-style soup)
7.2 Cha — stir-fries (4 dishes)
•     ឆាត្រកួនប្រេងខ្យង — Cha Trakuon with oyster sauce
•     ឆាសាច់គោដំឡូងជ្វា — Cha beef with fried yam
•     ឆាម្រះព្រៅ — Cha holy basil stir-fry
•     ឆាខ្ញី — ginger stir-fry
7.3 Other notable dishes (3 dishes)
•     អាម៉ុក — Amok (steamed fish curry, iconic dish)
•     ឡុកឡាក់ — Lok Lak (beef dish)
•     ចៅហន — Chao Horn (from the MoEYS cookbook)
7.4 Dessert (2 dishes)
•     ចេកឆឹងស្ករ — Banana in sugar syrup
•     បបរសណ្ដែកបាយ — Sweet mung bean porridge
8. Worked data sample
The following is an actual collected entry, shown in its original Khmer form, followed by the structured record format applied to it.
8.1 Raw collected text
សម្លម្ជូរព្រលិត
គ្រឿងផ្សំ
ត្រីរ៉ស់ កំពឹស ព្រលិត ក្រសាំង ទឹកត្រី អំបិល ស្ករ ម្សៅស៊ុប រំដេង ខ្ទឹមស ម្ទេសខ្មាំង ជីរនាងវង ម្អម ។
វិធីធ្វើ
១-ត្រីរ៉ស់សកស្រកា លាងទឹកឲ្យស្អាតហើយកាត់ជាកង់ៗ ។ កំពឹសលាងទឹកឲ្យស្អាតរួចក្ដិចក្បាលចោល ។ ព្រលិតបកសំបក រួចកាច់ប៉ុនពីរថ្នាំងដៃ លាងទឹក ដាក់កញ្ច្រែងឲ្យស្រោះទឹក ។ ក្រសាំង ឆ្កៀលយកគ្រាប់ រួចយកទៅជ្រំទឹកក្ដៅចេញជាតិជូរ ។ រំដេង ខ្ទឹមស ម្ទេសខ្មាំង បុកលាយគ្នាឲ្យម៉ដ្ឋ ។
២-យកឆ្នាំងដាំទឹកឲ្យពុះ បង់ត្រីស្ងោរឲ្យឆ្អិន៧០ភាគរយ ជាមួយកំពឹស (បុកឲ្យបែក) ចាក់ទឹកត្រី អំបិល ក្រសាំង ស្ករ ម្សៅស៊ុប និងគ្រឿងដែលបុកចូលគ្នា ដាំទឹកឲ្យពុះសឹមបង់ព្រលិតចូល ដាំមួយពុះទៀតទើបភ្លក្សមើលតាមចូលចិត្ដ រួចលើកចុះ បង់ជីរនាងវង ម្អម ជាការស្រេច ។
Source: original family interview, collected directly from a household contributor.
8.2 Structured record (corpus format)
Field
Value
dish_name_kh
សម្លម្ជូរព្រលិត
dish_name_en
Samlor Machu Pralit
category
samlor
source_type
family_interview
source_citation
Interview with household contributor, 2026
technique_note
Fish is cooked to ~70% doneness before being returned to the pot — prevents overcooking once the broth returns to a boil a second time
common_mistake
Adding pralit too early causes it to overcook and lose texture

 
Every record carries the source_citation field through the full pipeline — from corpus storage through retrieval to the final generated answer — so the system can state which type of source supports each piece of advice it gives.
9. System methodology
The pipeline runs in eight stages. Stages 1–3 are data preparation, 4–6 form the RAG core, and 7–8 are delivery and evaluation. Evaluation findings (stage 8) feed back into retrieval configuration choices (stage 5).
9.1 Data collection
Three source types as described in Section 6: family interviews (primary), the MoEYS textbook (cited reference), and the printed cookbook/blog index (cross-check and scoping only, never copied verbatim).
9.2 Transcription and translation
Scanned or photographed source pages are transcribed using a vision-capable LLM, then verified by a Khmer speaker against the original image — chosen over conventional OCR tools (e.g., Tesseract), which historically perform weakly on Khmer script due to its lack of inter-word spacing and stacked diacritics. Each page is processed individually rather than in batches, to keep verification tractable and to prevent errors in one recipe from contaminating others. Recipes are then translated to English using the same LLM, with an explicit instruction to remain grounded in the source text rather than introducing new claims.
9.3 Structuring
Verified text is converted into the structured JSON record shown in Section 8.2: ingredients, numbered steps with technique notes, common mistakes, and source citation metadata.
9.4 Embedding and indexing
Records are embedded using a multilingual sentence-transformer model (paraphrase-multilingual-mpnet-base-v2), chosen specifically because Khmer-language retrieval performs poorly under English-centric embedding models such as all-MiniLM-L6-v2. Embeddings are indexed in FAISS using a hierarchical structure: a category-level parent document (e.g., general samlor technique) with dish-level child documents beneath it, addressing the large number of near-duplicate dish variations within categories such as samlor and cha.
9.5 Retrieval
The primary experimental layer of the project, detailed fully in Section 10.
9.6 Generation
Gemini Flash handles routine, high-volume tasks (translation, transcription support); Claude Sonnet performs final answer synthesis. The generation prompt requires the model to state which source type (family interview or published textbook) supports its answer.
9.7 Application
A Streamlit interface with a Khmer/English language toggle, supporting both free-form question answering and a structured, step-by-step recipe browsing view.
9.8 Evaluation
Detailed fully in Section 11.
10. Technology stack
Layer
Tool / technique
Data preparation
Vision-LLM transcription with human verification; LLM-assisted, source-grounded translation
Embeddings
paraphrase-multilingual-mpnet-base-v2 (sentence-transformers)
Vector store
FAISS (IndexFlatIP), hierarchical category/dish structure
Retrieval
Hybrid search (BM25 + semantic), Contextual Retrieval, LLM-based reranking (stretch)
Generation
Gemini Flash (OpenRouter) for routine tasks; Claude Sonnet for final synthesis
Application
Streamlit, bilingual interface
Evaluation
LLM-as-judge scoring; structured failure-case logging
Deployment
Streamlit Community Cloud or local; GitHub for version control

 
11. Retrieval technique experiments
Rather than testing every possible RAG technique exhaustively, three core comparisons are prioritized based on what genuinely matters for this domain's data shape — short, single-chunk documents with heavy within-category variation — with two stretch additions if time allows.
11.1 Core comparisons
6.   Flat retrieval vs. hierarchical retrieval (category parent + dish child documents).
7.   Semantic-only search vs. hybrid search (BM25 + semantic) — hypothesis: hybrid performs better on exact dish-name lookups, semantic-only performs better on vague or conceptual queries.
8.   With vs. without Contextual Retrieval (situating sentences prepended before embedding).
11.2 Stretch additions (only if core experiments are complete with time remaining)
•     With vs. without LLM-based reranking of retrieved candidates.
•     With vs. without query rewriting for colloquial or vague input queries.
11.3 Test query categories
Category
Example query
Tests
Exact lookup
How do I make samlor machu pralit?
Hybrid / keyword strength
Conceptual / technique
How do I know when fish is done in a sour soup?
Semantic strength
Category / comparison
What are the different types of samlor?
Hierarchical strength

 
Approximately 20 queries spread across these three categories will be run against every technique combination, with retrieval accuracy and LLM-as-judge faithfulness scored for each — producing a comparison table in the same format as prior coursework, applied to this new domain and these new techniques.
12. Deliberately out of scope
12.1 Fine-tuning
Not used. The corpus is too small (10–15 dishes, well under the hundreds-to-thousands of examples fine-tuning typically requires), and RAG offers better traceability — every answer can be pointed to its exact source, which matters for a system giving practical cooking guidance. Fine-tuning would also require GPU infrastructure outside this project's budget and timeline.
12.2 Reinforcement learning
Not used. RL-based retrieval policies require substantial interaction data and training infrastructure that this project does not have. User feedback (thumbs up/down) may be logged in the application as a foundation for future work, without an actual learned policy being trained on it during this project.
12.3 Classical ML model + RAG hybrid
Not used, per explicit course guidance. This project is pure LLM engineering — retrieval, prompting, and generation — with no separate trained classifier component.
13. Evaluation plan
13.1 Quantitative metrics
•     Retrieval accuracy — does the correct dish or document section get retrieved for a given test query?
•     Faithfulness — does the generated answer only state claims traceable to the retrieved source text? Scored via LLM-as-judge on a defined rubric.
•     Citation correctness — does the system correctly identify and state the source type behind each answer?
13.2 LLM-as-judge methodology
Claude or Gemini scores each generated answer 1–5 against the source-grounded test query set, following the same generate → judge → select pattern used in prior coursework: a question is judged for groundedness (answerable from context), relevance, and stand-alone clarity before being included in the final test set.
13.3 Failure case categories (minimum 10 required)
•     Retrieval confuses two similar dish variations within the same category (e.g., two samlor types)
•     Citation misattribution — answer cites the wrong source type
•     Faithfulness violation — answer states a technique detail not present in any retrieved source
•     Hierarchical retrieval returns the category parent but misses the specific dish child, or vice versa
•     Hybrid search over-indexes on keyword match for a conceptual query
•     Translation drift between the Khmer and English versions of the same entry
•     Ambiguous query handling — system guesses a dish instead of asking for clarification
13.4 Bias and safety considerations
At scale, the system's main risk is technique advice that is subtly wrong but stated with confidence — particularly around food safety cues (e.g., doneness for fish or meat). The evaluation explicitly checks faithfulness for exactly this reason, and the written report will discuss this as a known limitation rather than treating the system as authoritative on food-safety judgment calls.
14. Timeline
Week
Milestone
Week 1
D1 proposal submitted. Family interviews begin; MoEYS textbook content reviewed and cited.
Week 2
Corpus structuring complete for the 15-dish Phase 1 list. Embedding and FAISS indexing pipeline built.
Week 3
Hierarchical and hybrid retrieval implemented. Progress check-in / prototype demo.
Week 4
Full retrieval comparison run; evaluation harness complete; D3 report written; code freeze.
Week 5
Demo rehearsal on verified dishes; D4 live demo and Q&A; optional D5 reflection memo.

 
15. AI use disclosure approach
Significant AI-assisted decisions — model used, prompt given, and how the output was validated—are logged as they occur, rather than reconstructed retroactively. This covers: transcription of scanned sources, source-grounded translation, retrieval technique implementation assistance, and evaluation harness design. This log is maintained throughout development and summarized in the D3 report and AI use documentation required by the course.
16. Known limitations and future work
•     Phase 1 covers only 15 dishes — a meaningful proof of concept, not comprehensive coverage of Khmer cuisine; expansion is planned contingent on Phase 1 results.
•     The system is not a substitute for food-safety authority — doneness and safety cues are technique guidance grounded in collected sources, not a verified food-safety standard.
•     Multilingual embedding quality for Khmer is generally weaker than for English; this is measured directly rather than assumed in the evaluation.
•     With more time, user feedback logging (Section 12.2) could become the foundation for a genuinely learned retrieval-ranking improvement.
17. References
ឡុង សាវឹង. វិធីធ្វើម្ហូប និងបង្អែមខ្មែរ. SalaDigital, Ministry of Education, Youth and Sport, Cambodia, 2025. sala.moeys.gov.kh/kh/library/00007430
https://drive.google.com/file/d/0B6PFH-cFZihVY1c5OUViNzctRWM/view?resourcekey=0-PTIAPr_Q0oNHF25MGiaQyw
Anthropic. “Contextual Retrieval.” Course materials, CS 695 AI Engineering, RAG lecture slides.
CS 695 · AI Engineering Final Project Assignment, Graduate AI Engineering Program.
https://choukhmer.wordpress.com/how-to-cook-khmer-foods/
https://choukhmer.wordpress.com/2010/07/31/small-scale-fish-processing/
 
 

