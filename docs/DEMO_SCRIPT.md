# Demo Script — Khmer Kitchen Companion (Phase 8)

## Golden demo path (course presentation)

1. Start app: `python scripts/run_app.py`
2. **Chat tab** (default) → sidebar **Samlor** → select **Samlor Proheur**
3. Language toggle: **EN** or **KH** (top right)
4. Type in chat input: *"How do I know when the fish is done in samlor proheur?"*
5. Verify:
   - User bubble + AI response in chat history
   - Green **published textbook** tag on answer
   - Retrieved recipe preview card below answer
6. Switch to **Recipe tab** for full ingredients + steps

## UI tabs

| Tab | Use |
|-----|-----|
| **Chat** | Ask questions, view conversation + citations |
| **Browse** | Click any dish in category → opens Recipe tab |
| **Recipe** | Full bilingual recipe card |

## 14-dish click-test checklist

| # | Slug | Category | Recipe card loads | Ask works | Citation |
|---|------|----------|-------------------|-----------|----------|
| 1 | samlor_chap_chhay | samlor | ☐ | ☐ | ☐ |
| 2 | samlor_kako_phlae_tnoat | samlor | ☐ | ☐ | ☐ |
| 3 | samlor_kari_kroeung_sach_ko | samlor | ☐ | ☐ | ☐ |
| 4 | samlor_proheur | samlor | ☐ | ☐ | ☐ |
| 5 | sngor_chrouk_spay_chrok | samlor | ☐ | ☐ | ☐ |
| 6 | sngor_prohet_trei_slat | samlor | ☐ | ☐ | ☐ |
| 7 | cha_khtuem_barang | cha | ☐ | ☐ | ☐ |
| 8 | kroeung_sach_trei | cha | ☐ | ☐ | ☐ |
| 9 | cha_mi_sour | cha | ☐ | ☐ | ☐ |
| 10 | bay_damnaeub_mukh_bangkea | dessert | ☐ | ☐ | ☐ |
| 11 | chek_chien | dessert | ☐ | ☐ | ☐ |
| 12 | num_ansom_chrouk | dessert | ☐ | ☐ | ☐ |
| 13 | nhoam_moan_tr_young_cek | other | ☐ | ☐ | ☐ |
| 14 | omelette | other | ☐ | ☐ | ☐ |

## Edge cases

| Query | Expected |
|-------|----------|
| `how to cook cha sach morn` | Not in cookbook + cha alternatives |
| `what is the price of fish sauce` | Out of scope refusal |
| `គ្រឿងផ្សំឆាមីសួ` | Khmer ingredient list |

## Sample questions per intent

- **Category:** what soups are in the samlor category?
- **Ingredients:** ingredients of cha mi sour
- **Shopping:** I want cha mi sour, what should I buy at the market?
- **How to cook:** how to cook samlor chap chhay
- **Recommend:** recommend a cha dish today
- **Substitution:** no fish sauce for cha mi sour
- **Technique:** should I stir-fry meat before adding water for soup?
