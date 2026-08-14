# Phase 3 Transcription Queue

**Status:** Phase 2 complete (14/14 scans) · Phase 3 drafts ready for human verify

| # | Slug | Scan | Raw draft | Verified |
|---|------|------|-----------|----------|
| 1 | samlor_chap_bampong | ✅ | ✅ DRAFT | ⬜ |
| 2 | samlor_kako_phlae_tnoat | ✅ | ✅ DRAFT | ⬜ |
| 3 | samlor_kari_kroeung_sach_ko | ✅ | ✅ DRAFT | ⬜ |
| 4 | samlor_proheur | ✅ | ✅ DRAFT | ⬜ |
| 5 | sngor_chrouk_spay_chrok | ✅ | ✅ DRAFT | ⬜ |
| 6 | sngor_prohet_trei_slat | ✅ | ✅ DRAFT | ⬜ |
| 7 | cha_khtuem_barang | ✅ | ✅ DRAFT | ⬜ |
| 8 | kroeung_sach_trei | ✅ | ✅ DRAFT | ⬜ |
| 9 | cha_mi_sour | ✅ | ✅ DRAFT | ⬜ |
| 10 | bay_damnaeub_mukh_bangkea | ✅ | ✅ DRAFT | ⬜ |
| 11 | chek_chien | ✅ | ✅ DRAFT | ⬜ |
| 12 | num_ansom_chrouk | ✅ | ✅ DRAFT | ⬜ |
| 13 | nhoam_moan_tr_young_cek | ✅ | ✅ DRAFT | ⬜ |
| 14 | omelette | ✅ | ✅ DRAFT | ⬜ |

## Review workflow (manual gate)

1. Open `{slug}.DRAFT.txt` side-by-side with its PNG in `data/source_scans/`
2. Fix any Khmer character errors; resolve scan ambiguities in `# notes`
3. Set `# verified: yes`
4. Rename `{slug}.DRAFT.txt` → `{slug}.txt`
5. Message: `Phase 3 gate pass — {slug}`

> Vision-LLM scripts remain in `scripts/` for later batch use; current drafts were extracted directly from PNG reads.

