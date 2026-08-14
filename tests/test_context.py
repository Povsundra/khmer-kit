"""Unit tests for conversational follow-up dish focus."""

from __future__ import annotations

import unittest

from src.core.context import apply_focus, is_followup_query
from src.core.entities import extract_entities
from src.core.intent import classify_intent


class FollowupContextTests(unittest.TestCase):
    def test_this_soup_is_followup(self) -> None:
        self.assertTrue(is_followup_query("Ingredients of this soup", "this soup"))

    def test_khmer_anaphora_is_followup(self) -> None:
        self.assertTrue(is_followup_query("គ្រឿងផ្សំនៃសម្លនេះ"))

    def test_named_unknown_dish_is_not_followup(self) -> None:
        self.assertFalse(is_followup_query("How to cook cha sach morn", "cha sach morn"))

    def test_apply_focus_fills_chap_chhay(self) -> None:
        query = "Ingredients of this soup"
        intent = classify_intent(query).intent
        entities = extract_entities(query)
        self.assertFalse(entities.dish_known)
        applied = apply_focus(query, intent, entities, "samlor_chap_chhay")
        self.assertTrue(applied)
        self.assertTrue(entities.dish_known)
        self.assertEqual(entities.slug, "samlor_chap_chhay")
        self.assertEqual(entities.match_method, "focus")

    def test_named_dish_keeps_own_slug(self) -> None:
        query = "Ingredients of omelette"
        intent = classify_intent(query).intent
        entities = extract_entities(query)
        applied = apply_focus(query, intent, entities, "samlor_chap_chhay")
        self.assertFalse(applied)
        self.assertEqual(entities.slug, "omelette")

    def test_unknown_named_dish_not_overridden(self) -> None:
        query = "How to cook cha sach morn"
        intent = classify_intent(query).intent
        entities = extract_entities(query)
        applied = apply_focus(query, intent, entities, "samlor_chap_chhay")
        self.assertFalse(applied)
        self.assertFalse(entities.dish_known)

    def test_parent_slug_ignored(self) -> None:
        query = "Ingredients of this soup"
        intent = classify_intent(query).intent
        entities = extract_entities(query)
        applied = apply_focus(query, intent, entities, "_parent_samlor")
        self.assertFalse(applied)
        self.assertFalse(entities.dish_known)

    def test_category_browse_unchanged(self) -> None:
        query = "list all samlor dishes"
        intent = classify_intent(query).intent
        entities = extract_entities(query)
        applied = apply_focus(query, intent, entities, "samlor_chap_chhay")
        self.assertFalse(applied)


class FollowupEngineTests(unittest.TestCase):
    def test_ingredients_of_this_soup_uses_focus_slug(self) -> None:
        from src.config import INDEX_DIR
        from src.core.engine import answer_query

        if not (INDEX_DIR / "faiss.index").exists():
            self.skipTest("FAISS index not built")

        result = answer_query(
            "Ingredients of this soup",
            lang="en",
            focus_slug="samlor_chap_chhay",
        )
        self.assertEqual(result.intent, "ingredients")
        self.assertIn("Chap Chhay", result.text)
        self.assertNotIn("don't have", result.text.lower())
        self.assertTrue(result.chunks_used)
        self.assertEqual(result.chunks_used[0].get("slug"), "samlor_chap_chhay")


if __name__ == "__main__":
    unittest.main()
