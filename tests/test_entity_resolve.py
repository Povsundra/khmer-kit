"""Unit tests for typo-tolerant dish entity resolution."""

from __future__ import annotations

import unittest

from src.core.entities import extract_entities
from src.core.entity_resolve import normalize_text, resolve_dish_phrase


class EntityResolveTests(unittest.TestCase):
    def test_normalize_strips_punctuation(self) -> None:
        self.assertEqual(normalize_text("Omelette?"), "omelette")

    def test_exact_omelette_spelling(self) -> None:
        entities = extract_entities("How to make Omelette?")
        self.assertTrue(entities.dish_known)
        self.assertEqual(entities.slug, "omelette")
        self.assertEqual(entities.requested_name, "Omelette")

    def test_fuzzy_oemlette(self) -> None:
        result = resolve_dish_phrase("Oemlette")
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.slug, "omelette")
        self.assertEqual(result.method, "alias")

    def test_fuzzy_omlette(self) -> None:
        result = resolve_dish_phrase("omlette")
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.slug, "omelette")
        self.assertIn(result.method, ("alias", "fuzzy"))

    def test_alias_samlor_korko(self) -> None:
        result = resolve_dish_phrase("samlor korko")
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.slug, "samlor_kako_phlae_tnoat")

    def test_unknown_dish_rejected(self) -> None:
        result = resolve_dish_phrase("cha sach morn")
        self.assertIsNone(result)

    def test_generic_soup_not_resolved(self) -> None:
        result = resolve_dish_phrase("soup")
        self.assertIsNone(result)

    def test_extract_entities_typo_query(self) -> None:
        entities = extract_entities("How to make Oemlette?")
        self.assertTrue(entities.dish_known)
        self.assertEqual(entities.slug, "omelette")
        self.assertEqual(entities.match_method, "alias")

    def test_khmer_omelette_query(self) -> None:
        from src.core.intent import classify_intent

        q = "របៀបចៀនពងមាន់"
        self.assertEqual(classify_intent(q).intent, "how_to_cook")
        entities = extract_entities(q)
        self.assertTrue(entities.dish_known)
        self.assertEqual(entities.slug, "omelette")

    def test_khmer_omelette_alias_phrase(self) -> None:
        result = resolve_dish_phrase("ពងទាឬពងមាន់")
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.slug, "omelette")

    def test_khmer_fried_duck_egg_resolves_omelette(self) -> None:
        result = resolve_dish_phrase("ពងទាចៀន")
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.slug, "omelette")
        entities = extract_entities("ពងទាចៀន")
        self.assertTrue(entities.dish_known)
        self.assertEqual(entities.slug, "omelette")

    def test_khmer_fried_duck_egg_reversed_resolves_omelette(self) -> None:
        result = resolve_dish_phrase("ចៀនពងទា")
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.slug, "omelette")

    def test_unknown_khmer_dish_rejected(self) -> None:
        result = resolve_dish_phrase("ភីហ្សា")
        self.assertIsNone(result)
        entities = extract_entities("ភីហ្សា")
        self.assertFalse(entities.dish_known)

    def test_kako_short_name_resolves(self) -> None:
        result = resolve_dish_phrase("កកូរ")
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.slug, "samlor_kako_phlae_tnoat")
        entities = extract_entities("កកូរ")
        self.assertTrue(entities.dish_known)
        self.assertEqual(entities.slug, "samlor_kako_phlae_tnoat")

    def test_unique_substring_proheur(self) -> None:
        result = resolve_dish_phrase("ប្រហើរ")
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.slug, "samlor_proheur")

    def test_aliases_copied_into_embed_text(self) -> None:
        from src.data_prep.corpus_chunks import aliases_for_slug, _alias_embed_suffix

        self.assertIn("កកូរ", aliases_for_slug("samlor_kako_phlae_tnoat"))
        self.assertIn("កកូរ", _alias_embed_suffix("samlor_kako_phlae_tnoat"))

    def test_generic_samlor_rejected(self) -> None:
        result = resolve_dish_phrase("សម្ល")
        self.assertIsNone(result)
        entities = extract_entities("សម្ល")
        self.assertFalse(entities.dish_known)

    def test_khmer_ingredients_ansom_alias(self) -> None:
        from src.core.intent import classify_intent

        q = "គ្រឿងផ្សំនំអន្សម"
        self.assertEqual(classify_intent(q).intent, "ingredients")
        entities = extract_entities(q)
        self.assertTrue(entities.dish_known)
        self.assertEqual(entities.slug, "num_ansom_chrouk")
        self.assertEqual(entities.requested_name, "នំអន្សម")

    def test_khmer_ingredients_cha_mi_sour(self) -> None:
        from src.core.intent import classify_intent

        q = "គ្រឿងផ្សំឆាមីសួ"
        self.assertEqual(classify_intent(q).intent, "ingredients")
        entities = extract_entities(q)
        self.assertTrue(entities.dish_known)
        self.assertEqual(entities.slug, "cha_mi_sour")

    def test_khmer_ingredients_samlor_kako_alias(self) -> None:
        from src.core.intent import classify_intent

        q = "គ្រឿងផ្សំសម្លកកូ"
        self.assertEqual(classify_intent(q).intent, "ingredients")
        entities = extract_entities(q)
        self.assertTrue(entities.dish_known)
        self.assertEqual(entities.slug, "samlor_kako_phlae_tnoat")

    def test_khmer_ingredients_dish_first_ansom(self) -> None:
        from src.core.intent import classify_intent

        q = "នំអន្សមគ្រឿងផ្សំ"
        self.assertEqual(classify_intent(q).intent, "ingredients")
        entities = extract_entities(q)
        self.assertTrue(entities.dish_known)
        self.assertEqual(entities.slug, "num_ansom_chrouk")

    def test_khmer_ingredients_ansom_engine(self) -> None:
        from src.config import INDEX_DIR
        from src.core.engine import answer_query

        if not (INDEX_DIR / "faiss.index").exists():
            self.skipTest("FAISS index not built")

        result = answer_query("គ្រឿងផ្សំនំអន្សម", lang="kh")
        self.assertEqual(result.intent, "ingredients")
        self.assertIn("អង្ករដំណើប", result.text)
        self.assertIn("សាច់ជ្រូក", result.text)
        self.assertTrue(result.chunks_used)
        self.assertEqual(result.chunks_used[0].get("slug"), "num_ansom_chrouk")


if __name__ == "__main__":
    unittest.main()
