# Collection Log — Phase 2

Track every dish as you add source scans. Update `status` when scan is saved.

**Legend:** `pending` · `scan_ready` · `raw_verified` · `json_done`

---

## Phase 1 dishes (required — 15 total)

| # | Slug | Scan saved? | File path | Source type | Notes |
|---|------|-------------|-----------|-------------|-------|
| 1 | samlor_machu_pralit | ⬜ | `data/source_scans/samlor/samlor_machu_pralit.png` | family_interview | Start here — sample in Context/idea.md |
| 2 | samlor_machu_trakuon | ⬜ | `data/source_scans/samlor/samlor_machu_trakuon.png` | | |
| 3 | samlor_machu_moan | ⬜ | `data/source_scans/samlor/samlor_machu_moan.png` | | |
| 4 | samlor_machu_kdam_samut | ⬜ | `data/source_scans/samlor/samlor_machu_kdam_samut.png` | | |
| 5 | samlor_machu_tralach | ⬜ | `data/source_scans/samlor/samlor_machu_tralach.png` | | |
| 6 | saraman | ⬜ | `data/source_scans/samlor/saraman.png` | | |
| 7 | cha_trakuon_oyster | ⬜ | `data/source_scans/cha/cha_trakuon_oyster.png` | | |
| 8 | cha_beef_yam | ⬜ | `data/source_scans/cha/cha_beef_yam.png` | | |
| 9 | cha_holy_basil | ⬜ | `data/source_scans/cha/cha_holy_basil.png` | | |
| 10 | cha_kney | ⬜ | `data/source_scans/cha/cha_kney.png` | | |
| 11 | amok | ⬜ | `data/source_scans/other/amok.png` | | |
| 12 | lok_lak | ⬜ | `data/source_scans/other/lok_lak.png` | | |
| 13 | chao_horn | ⬜ | `data/source_scans/other/chao_horn.png` | published_textbook | MoEYS / SalaDigital |
| 14 | banana_sugar_syrup | ⬜ | `data/source_scans/dessert/banana_sugar_syrup.png` | | |
| 15 | mung_bean_porridge | ⬜ | `data/source_scans/dessert/mung_bean_porridge.png` | | |

---

## Extra scans (not in Phase 1 list — do not count toward 15)

| Slug | File | Actual dish in image | Action |
|------|------|----------------------|--------|
| nhoam_moan_tr_young_cek | `data/source_scans/other/nhoam_moan_tr_young_cek.png` | ញាំមាន់ត្រយូងចេក (chicken + banana blossom salad) | **Extra** — good crop example; not in 15-dish list unless you swap a dish |

---

## Your submitted file — review (2026-08-14)

| Check | Result |
|-------|--------|
| One dish per image | ✅ Good — single recipe crop |
| Includes title + ingredients + method | ✅ Good |
| Footers/URLs excluded | ✅ Mostly good |
| Correct folder | ❌ Was `data/Nhoam_Sach_Trei_Ros.png` — should be under `source_scans/{category}/` |
| Correct filename | ❌ Name said "fish salad" but image is **ញាំមាន់ត្រយូងចេក** (chicken salad) |
| In Phase 1 list | ❌ Not one of the 15 dishes — keep as practice or swap list |

**Fixed copy saved to:** `data/source_scans/other/nhoam_moan_tr_young_cek.png`

---

## Crop checklist (use for each of 15 dishes)

```
[ ] ONE dish only (crop if page has 2 recipes)
[ ] Boxed title visible
[ ] គ្រឿងផ្សំ section included
[ ] របៀបធ្វើ section included
[ ] No page number / URLs / other recipe
[ ] Saved as: data/source_scans/{category}/{slug}.png
[ ] slug matches docs/dish_checklist.json exactly
```
