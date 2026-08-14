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


if __name__ == "__main__":
    unittest.main()
