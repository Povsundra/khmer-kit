# Data Preparation Guide — Quick Reference

## Where to save each file

```
data/source_scans/{category}/{slug}.png   ← YOU: cropped photo
data/raw/{category}/{slug}.txt            ← YOU verify, then save Khmer text
data/processed/{category}/{slug}.json     ← AGENT: after raw verified
```

**Categories (lowercase only):** `samlor` · `cha` · `other` · `dessert`

## Naming rules

- Use **slug** from `docs/dish_checklist.json` (snake_case)
- Example: `samlor_machu_pralit.png` not `Samlor Machu Pralit.png`
- Khmer dish name goes **inside** the file content, not the filename

## Book PDF workflow

1. Find page in PDF for your dish
2. **Crop ONE recipe** (skip the other recipe on same page)
3. Save PNG to `source_scans/{category}/{slug}.png`
4. Message agent: `Phase 3 — dish: {slug}` + file path
5. Agent drafts transcription → **you verify** Khmer
6. Save verified text to `raw/{category}/{slug}.txt`
7. Say: `Phase 3 gate pass — proceed Phase 4`

## Raw text template

Copy `data/raw/_TEMPLATE.txt` and fill in.

## Phase 2 complete when

All 15 rows in `docs/collection_log.md` have scans saved (or explicit deferral noted).
