"""Unit tests for conversational follow-up dish focus."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from src.core.context import apply_focus, is_followup_query, leftover_after_intent_strip
from src.core.entities import extract_entities, extract_requested_dish_phrase
from src.core.intent import classify_intent

FOCUS = "cha_mi_sour"

# One EN and one KH example per follow-up type A–G (same last dish, new ask).
FOLLOWUP_CATALOG: list[tuple[str, str, str]] = [
    ("A-en", "ingredients of this food", "ingredients"),
    ("A-kh", "គ្រឿងផ្សំរបស់វា", "ingredients"),
    ("B-en", "ingredients", "ingredients"),
    ("B-kh", "គ្រឿងផ្សំ", "ingredients"),
    ("C-en", "list me all ingredient", "ingredients"),
    ("C-kh", "ត្រូវការអ្វីខ្លះ", "ingredients"),
    ("D-kh", "គ្រឿហផ្សំរបស់វា", "ingredients"),
    ("E-en", "how do I cook it", "how_to_cook"),
    ("E-kh", "របៀបធ្វើ", "how_to_cook"),
    ("F-en", "I don't have fish sauce", "substitution"),
    ("F-kh", "គ្មានទឹកត្រី", "substitution"),
    ("G-en", "how long", "technique"),
    ("G-kh", "របៀបធ្វើម្ហូបហ្នឹង", "how_to_cook"),
]


class FollowupContextTests(unittest.TestCase):
    def test_this_soup_is_followup(self) -> None:
        self.assertTrue(is_followup_query("Ingredients of this soup", "this soup"))

    def test_khmer_anaphora_is_followup(self) -> None:
        self.assertTrue(is_followup_query("គ្រឿងផ្សំនៃសម្លនេះ"))

    def test_named_unknown_dish_is_not_followup(self) -> None:
        self.assertFalse(is_followup_query("How to cook cha sach morn", "cha sach morn"))

    def test_named_how_to_make_is_not_followup(self) -> None:
        self.assertFalse(is_followup_query("How to make cha mi sour?"))

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

    def test_recommend_not_followup_focus(self) -> None:
        query = "what should I cook"
        intent = classify_intent(query).intent
        self.assertEqual(intent, "recommend")
        entities = extract_entities(query)
        applied = apply_focus(query, intent, entities, FOCUS)
        self.assertFalse(applied)

    def test_bare_samlor_not_followup(self) -> None:
        self.assertFalse(is_followup_query("សម្ល"))
        leftover = leftover_after_intent_strip("សម្ល")
        self.assertEqual(leftover, "សម្ល")


class FollowupCatalogTests(unittest.TestCase):
    def test_catalog_is_followup_and_attaches_last_dish(self) -> None:
        for label, query, expected_intent in FOLLOWUP_CATALOG:
            with self.subTest(label=label, query=query):
                self.assertTrue(is_followup_query(query), msg=f"{label} not a follow-up")
                intent = classify_intent(query).intent
                self.assertEqual(intent, expected_intent, msg=f"{label} intent")
                entities = extract_entities(query)
                self.assertFalse(entities.dish_known, msg=f"{label} already named a dish")
                applied = apply_focus(query, intent, entities, FOCUS)
                self.assertTrue(applied, msg=f"{label} did not attach focus")
                self.assertEqual(entities.slug, FOCUS)

    def test_list_me_all_ingredient_strips_requested_name(self) -> None:
        self.assertIsNone(extract_requested_dish_phrase("list me all ingredient"))
        self.assertEqual(classify_intent("list me all ingredient").intent, "ingredients")
        self.assertEqual(leftover_after_intent_strip("list me all ingredient"), "")

    def test_khmer_typo_ingredients_intent(self) -> None:
        self.assertEqual(classify_intent("គ្រឿហផ្សំរបស់វា").intent, "ingredients")
        self.assertEqual(classify_intent("គ្រឿងផ្សំឆាមីសួ").intent, "ingredients")


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

    def test_list_me_all_ingredient_uses_cha_mi_sour(self) -> None:
        from src.config import INDEX_DIR
        from src.core.engine import answer_query

        if not (INDEX_DIR / "faiss.index").exists():
            self.skipTest("FAISS index not built")

        result = answer_query(
            "list me all ingredient",
            lang="en",
            focus_slug=FOCUS,
        )
        self.assertEqual(result.intent, "ingredients")
        self.assertIn("Mi Sour", result.text)
        self.assertTrue(result.chunks_used)
        self.assertEqual(result.chunks_used[0].get("slug"), FOCUS)
        self.assertNotIn("don't have", result.text.lower())

    def test_khmer_typo_its_ingredients_uses_cha_mi_sour(self) -> None:
        from src.config import INDEX_DIR
        from src.core.engine import answer_query

        if not (INDEX_DIR / "faiss.index").exists():
            self.skipTest("FAISS index not built")

        result = answer_query(
            "គ្រឿហផ្សំរបស់វា",
            lang="kh",
            focus_slug=FOCUS,
        )
        self.assertEqual(result.intent, "ingredients")
        self.assertTrue(result.chunks_used)
        self.assertEqual(result.chunks_used[0].get("slug"), FOCUS)

    def test_no_focus_list_ingredients_is_unknown(self) -> None:
        from src.config import INDEX_DIR
        from src.core.engine import answer_query

        if not (INDEX_DIR / "faiss.index").exists():
            self.skipTest("FAISS index not built")

        result = answer_query("list me all ingredient", lang="en")
        self.assertEqual(result.intent, "ingredients")
        self.assertFalse(result.chunks_used)

    def test_unknown_named_dish_not_rewritten_to_focus(self) -> None:
        from src.config import INDEX_DIR
        from src.core.engine import answer_query

        if not (INDEX_DIR / "faiss.index").exists():
            self.skipTest("FAISS index not built")

        result = answer_query(
            "How to cook cha sach morn",
            lang="en",
            focus_slug=FOCUS,
        )
        self.assertEqual(result.intent, "how_to_cook")
        self.assertFalse(result.chunks_used)
        self.assertIn("don't have", result.text.lower())
        self.assertNotIn("How to cook Cha Mi Sour", result.text)

    @patch("src.core.rewrite.generate", return_value="ingredients for cha mi sour")
    @patch("src.core.engine.llm_available", return_value=True)
    def test_mocked_rewrite_resolves_when_rules_miss(
        self,
        _llm: object,
        _gen: object,
    ) -> None:
        from src.config import INDEX_DIR
        from src.core.engine import answer_query

        if not (INDEX_DIR / "faiss.index").exists():
            self.skipTest("FAISS index not built")

        result = answer_query(
            "enumerate the stuff for cooking",
            lang="en",
            focus_slug=FOCUS,
            prior_query="How to make cha mi sour?",
        )
        self.assertEqual(result.intent, "ingredients")
        self.assertTrue(result.chunks_used)
        self.assertEqual(result.chunks_used[0].get("slug"), FOCUS)


class RewriteOutputTests(unittest.TestCase):
    def _rewrite(self, raw: str) -> str | None:
        from src.core.rewrite import rewrite_followup_query

        with patch("src.core.rewrite.generate", return_value=raw):
            return rewrite_followup_query(
                "គ្រឿហផ្សំរបស់វា",
                focus_slug=FOCUS,
                prior_query="របៀបឆាមីសួរ",
            )

    def test_plain_line_passes_through(self) -> None:
        self.assertEqual(self._rewrite("គ្រឿងផ្សំរបស់ឆាមីសួរ"), "គ្រឿងផ្សំរបស់ឆាមីសួរ")

    def test_quotes_and_label_stripped(self) -> None:
        self.assertEqual(
            self._rewrite('Output: "ingredients of cha mi sour"'),
            "ingredients of cha mi sour",
        )

    def test_chatty_preamble_drops_to_query_line(self) -> None:
        raw = "Sure! Here is the rewritten query:\n\ningredients of cha mi sour"
        self.assertEqual(self._rewrite(raw), "ingredients of cha mi sour")

    def test_long_answer_paragraph_rejected(self) -> None:
        raw = "To make Cha Mi Sour you will need " + "rice noodles, fish sauce, garlic, " * 10
        self.assertIsNone(self._rewrite(raw))

    def test_empty_reply_is_none(self) -> None:
        self.assertIsNone(self._rewrite("   \n\n  "))

    def test_unknown_focus_slug_skips_llm(self) -> None:
        from src.core.rewrite import rewrite_followup_query

        with patch("src.core.rewrite.generate") as gen:
            self.assertIsNone(rewrite_followup_query("ingredients", focus_slug="_parent_samlor"))
        gen.assert_not_called()


class UnderstandTurnTests(unittest.TestCase):
    def _understand(self, raw: str, query: str = "I want to eat something spicy"):
        from src.core.rewrite import understand_turn

        with patch("src.core.rewrite.generate", return_value=raw):
            return understand_turn(
                query,
                intent="recommend",
                history=[{"role": "user", "content": query}],
                last_slug=None,
                last_category=None,
            )

    def test_ask_spicy_without_category(self) -> None:
        result = self._understand(
            '{"action":"ask","question":"This cookbook does not rate heat. Samlor, cha, dessert, or other?","query":null,"category":null,"slug":null}'
        )
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.action, "ask")
        self.assertIn("samlor", (result.question or "").lower())

    def test_followup_retrieve_includes_soup(self) -> None:
        from src.core.rewrite import understand_turn

        raw = (
            '{"action":"retrieve","question":null,'
            '"query":"How long to cook the fish for sngor prohet trei slat",'
            '"category":"samlor","slug":"sngor_prohet_trei_slat"}'
        )
        with patch("src.core.rewrite.generate", return_value=raw):
            result = understand_turn(
                "How long for the fish?",
                intent="technique",
                history=[{"role": "user", "content": "how to cook sngor prohet trei slat"}],
                last_slug="sngor_prohet_trei_slat",
                last_category="samlor",
            )
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.action, "retrieve")
        self.assertIn("sngor prohet trei slat", (result.query or "").lower())
        self.assertEqual(result.slug, "sngor_prohet_trei_slat")

    def test_invented_slug_dropped(self) -> None:
        result = self._understand(
            '{"action":"retrieve","query":"spicy pho","category":"samlor","slug":"pho_bo"}'
        )
        self.assertIsNotNone(result)
        assert result is not None
        self.assertIsNone(result.slug)
        self.assertEqual(result.query, "spicy pho")

    def test_plain_query_line_is_retrieve(self) -> None:
        result = self._understand("samlor chili pepper kroeung")
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.action, "retrieve")
        self.assertEqual(result.query, "samlor chili pepper kroeung")


class UnknownDishEngineTests(unittest.TestCase):
    def test_fried_duck_egg_returns_omelette(self) -> None:
        from src.config import INDEX_DIR
        from src.core.engine import answer_query

        if not (INDEX_DIR / "faiss.index").exists():
            self.skipTest("FAISS index not built")

        result = answer_query("ពងទាចៀន", lang="kh")
        self.assertEqual(result.intent, "how_to_cook")
        self.assertIn("ពងទា", result.text)
        self.assertTrue(result.chunks_used)
        self.assertTrue(all(c.get("slug") == "omelette" for c in result.chunks_used))

    def test_unknown_khmer_name_refuses(self) -> None:
        from src.config import INDEX_DIR
        from src.core.engine import answer_query

        if not (INDEX_DIR / "faiss.index").exists():
            self.skipTest("FAISS index not built")

        result = answer_query("ភីហ្សា", lang="kh")
        self.assertEqual(result.intent, "dish_lookup")
        self.assertIn("មិនមាន", result.text)
        self.assertIn("ភីហ្សា", result.text)
        self.assertIn("ម៉ឺនុយ", result.text)
        self.assertFalse(result.chunks_used)

    def test_bare_samlor_refuses(self) -> None:
        from src.config import INDEX_DIR
        from src.core.engine import answer_query

        if not (INDEX_DIR / "faiss.index").exists():
            self.skipTest("FAISS index not built")

        result = answer_query("សម្ល", lang="kh", focus_slug=FOCUS)
        self.assertFalse(result.chunks_used)
        self.assertNotIn("មីសួ", result.text)


class MinMaxScoreTests(unittest.TestCase):
    def test_flat_scores_are_zero_not_ones(self) -> None:
        import numpy as np

        from src.core.retrieve import _min_max

        flat = _min_max(np.zeros(4))
        self.assertTrue(np.allclose(flat, 0.0))
        same = _min_max(np.array([0.2, 0.2, 0.2]))
        self.assertTrue(np.allclose(same, 0.0))


if __name__ == "__main__":
    unittest.main()
