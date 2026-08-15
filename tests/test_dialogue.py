"""Multi-turn dialogue: clarify, slot fill, then retrieve."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from src.core.dialogue import (
    DialogueState,
    apply_dialogue,
    is_new_preference_turn,
    missing_slots,
    next_action,
    resolve_offered_choice,
)
from src.core.entities import extract_entities
from src.core.intent import classify_intent


class DialoguePolicyTests(unittest.TestCase):
    def test_vague_recommend_needs_category(self) -> None:
        query = "recommend me Khmer food?"
        intent = classify_intent(query).intent
        entities = extract_entities(query)
        state = DialogueState()
        intent, entities, state, _ = apply_dialogue(query, intent, entities, state)
        self.assertEqual(intent, "recommend")
        self.assertEqual(missing_slots(state, intent, entities, query), ["category"])
        self.assertEqual(next_action(state, intent, entities, query), "clarify")

    def test_recommend_with_category_retrieves(self) -> None:
        query = "recommend a cha dish today"
        intent = classify_intent(query).intent
        entities = extract_entities(query)
        state = DialogueState()
        intent, entities, state, _ = apply_dialogue(query, intent, entities, state)
        self.assertEqual(state.category, "cha")
        self.assertEqual(next_action(state, intent, entities, query), "retrieve")

    def test_soup_fills_pending_category(self) -> None:
        state = DialogueState(goal="recommend", pending_slot="category", offered_options=["samlor", "cha", "dessert", "other"])
        query = "soup"
        intent = classify_intent(query).intent
        entities = extract_entities(query)
        intent, entities, state, filled = apply_dialogue(query, intent, entities, state)
        self.assertTrue(filled)
        self.assertEqual(intent, "recommend")
        self.assertEqual(state.category, "samlor")
        self.assertEqual(next_action(state, intent, entities, query), "retrieve")

    def test_ordinal_fills_first_category(self) -> None:
        offered = ["samlor", "cha", "dessert", "other"]
        self.assertEqual(resolve_offered_choice("1", offered), "samlor")
        self.assertEqual(resolve_offered_choice("the first one", offered), "samlor")
        self.assertEqual(resolve_offered_choice("2", offered), "cha")

    def test_ingredients_without_dish_asks(self) -> None:
        query = "list me all ingredient"
        intent = classify_intent(query).intent
        entities = extract_entities(query)
        state = DialogueState()
        intent, entities, state, _ = apply_dialogue(query, intent, entities, state)
        self.assertEqual(intent, "ingredients")
        self.assertIn(missing_slots(state, intent, entities, query)[0], ("category", "dish"))
        self.assertEqual(next_action(state, intent, entities, query), "clarify")

    def test_how_to_cook_khmer_food_asks(self) -> None:
        query = "how do I cook Khmer food?"
        intent = classify_intent(query).intent
        entities = extract_entities(query)
        state = DialogueState()
        intent, entities, state, _ = apply_dialogue(query, intent, entities, state)
        self.assertEqual(intent, "how_to_cook")
        self.assertEqual(next_action(state, intent, entities, query), "clarify")

    def test_spicy_preference_becomes_recommend_clarify(self) -> None:
        query = "I want to eat something spicy"
        intent = classify_intent(query).intent
        entities = extract_entities(query)
        state = DialogueState()
        intent, entities, state, _ = apply_dialogue(query, intent, entities, state)
        self.assertEqual(intent, "recommend")
        self.assertEqual(next_action(state, intent, entities, query), "clarify")

    def test_spicy_after_dessert_clears_leftover_slug(self) -> None:
        query = "I want to eat something spicy"
        intent = classify_intent(query).intent
        entities = extract_entities(query)
        self.assertTrue(is_new_preference_turn(query, intent, entities))
        state = DialogueState(goal="recommend", category="dessert", slug="chek_chien")
        intent, entities, state, _ = apply_dialogue(query, intent, entities, state)
        self.assertEqual(intent, "recommend")
        self.assertIsNone(state.slug)
        self.assertIsNone(state.category)
        self.assertFalse(entities.dish_known)
        self.assertEqual(next_action(state, intent, entities, query), "clarify")

    def test_out_of_scope_refuses(self) -> None:
        query = "what is the price of fish sauce at the market?"
        intent = classify_intent(query).intent
        entities = extract_entities(query)
        self.assertEqual(next_action(DialogueState(), intent, entities, query), "refuse")

    def test_unknown_named_dish_clears_leftover_slug(self) -> None:
        query = "how to make stack?"
        intent = classify_intent(query).intent
        entities = extract_entities(query)
        state = DialogueState(
            goal="how_to_cook",
            category="samlor",
            slug="samlor_chap_chhay",
        )
        intent, entities, state, _ = apply_dialogue(query, intent, entities, state)
        self.assertEqual(intent, "how_to_cook")
        self.assertIsNone(state.slug)
        self.assertIsNone(state.category)
        self.assertFalse(entities.dish_known)
        self.assertEqual(next_action(state, intent, entities, query), "refuse")


class DialogueEngineTests(unittest.TestCase):
    def _engine(self):
        from src.config import INDEX_DIR
        from src.core.engine import answer_query

        if not (INDEX_DIR / "faiss.index").exists():
            self.skipTest("FAISS index not built")
        return answer_query

    @patch("src.core.engine.llm_available", return_value=False)
    def test_recommend_khmer_food_asks_type(self, _llm: object) -> None:
        answer_query = self._engine()
        result = answer_query("recommend me Khmer food?", lang="en")
        self.assertEqual(result.intent, "recommend")
        self.assertEqual(result.action, "clarify")
        self.assertFalse(result.chunks_used)
        self.assertIn("samlor", result.text.lower())
        self.assertIn("cha", result.text.lower())
        self.assertNotIn("You could try", result.text)

    @patch("src.core.engine.llm_available", return_value=False)
    def test_soup_then_recommends_samlor(self, _llm: object) -> None:
        answer_query = self._engine()
        first = answer_query("recommend me Khmer food?", lang="en")
        second = answer_query("soup", lang="en", state=first.state)
        self.assertEqual(second.intent, "recommend")
        self.assertEqual(second.action, "answer")
        self.assertEqual(second.state.category, "samlor")
        self.assertTrue(second.chunks_used)
        self.assertIn("samlor", second.text.lower())

    @patch("src.core.engine.llm_available", return_value=False)
    def test_shopping_list_keeps_recommended_dish(self, _llm: object) -> None:
        answer_query = self._engine()
        first = answer_query("recommend me Khmer food?", lang="en")
        second = answer_query("soup", lang="en", state=first.state)
        third = answer_query("what should I buy at the market?", lang="en", state=second.state)
        self.assertEqual(third.intent, "shopping_list")
        self.assertEqual(third.action, "answer")
        self.assertTrue(third.state.slug)
        self.assertTrue(third.chunks_used)
        self.assertNotIn("which dish", third.text.lower())

    @patch("src.core.engine.llm_available", return_value=False)
    def test_dessert_instead_resets_category(self, _llm: object) -> None:
        answer_query = self._engine()
        first = answer_query("recommend me Khmer food?", lang="en")
        second = answer_query("soup", lang="en", state=first.state)
        third = answer_query("actually recommend a dessert instead", lang="en", state=second.state)
        self.assertEqual(third.intent, "recommend")
        self.assertEqual(third.action, "answer")
        self.assertEqual(third.state.category, "dessert")
        self.assertTrue(third.chunks_used)

    @patch("src.core.engine.llm_available", return_value=False)
    def test_named_dish_still_answers_immediately(self, _llm: object) -> None:
        answer_query = self._engine()
        result = answer_query("ingredients of cha mi sour", lang="en")
        self.assertEqual(result.action, "answer")
        self.assertIn("Mi Sour", result.text)

    @patch("src.core.engine.llm_available", return_value=False)
    def test_out_of_scope_still_refused(self, _llm: object) -> None:
        answer_query = self._engine()
        result = answer_query("what is the price of fish sauce at the market?", lang="en")
        self.assertEqual(result.action, "refuse")
        self.assertIn("outside", result.text.lower())

    @patch("src.core.engine.understand_turn")
    @patch("src.core.engine.llm_available", return_value=True)
    def test_understand_ask_becomes_clarify(
        self,
        _llm: object,
        mock_understand: object,
    ) -> None:
        from src.core.rewrite import UnderstandResult

        mock_understand.return_value = UnderstandResult(
            action="ask",
            question="This cookbook does not rate heat. Would you like samlor, cha, dessert, or other?",
        )
        answer_query = self._engine()
        result = answer_query("I want to eat something spicy", lang="en")
        self.assertEqual(result.action, "clarify")
        self.assertIn("does not rate heat", result.text)
        self.assertNotIn("chek chien", result.text.lower())

    @patch("src.core.engine.llm_available", return_value=False)
    def test_spicy_after_dessert_does_not_list_chek_chien(self, _llm: object) -> None:
        answer_query = self._engine()
        state = DialogueState(goal="recommend", category="dessert", slug="chek_chien")
        result = answer_query("I want to eat something spicy", lang="en", state=state)
        self.assertEqual(result.action, "clarify")
        self.assertNotEqual(result.state.category, "dessert")
        self.assertIsNone(result.state.slug)
        self.assertNotIn("chek chien", result.text.lower())
        self.assertNotIn("fried banana", result.text.lower())

    @patch("src.core.engine.llm_available", return_value=False)
    def test_clarify_works_without_llm(self, _llm: object) -> None:
        answer_query = self._engine()
        result = answer_query("recommend me Khmer food?", lang="en")
        self.assertEqual(result.action, "clarify")
        self.assertIn("14 Khmer dishes", result.text)

    @patch("src.core.engine.llm_available", return_value=False)
    def test_unknown_stack_does_not_use_leftover_chap_chhay(self, _llm: object) -> None:
        answer_query = self._engine()
        state = DialogueState(
            goal="how_to_cook",
            category="samlor",
            slug="samlor_chap_chhay",
        )
        result = answer_query(
            "how to make stack?",
            lang="en",
            focus_slug="samlor_chap_chhay",
            state=state,
        )
        self.assertEqual(result.action, "refuse")
        self.assertFalse(result.chunks_used)
        lowered = result.text.lower()
        self.assertIn("stack", lowered)
        self.assertIn("don't have", lowered)
        self.assertIn("menu", lowered)
        self.assertNotIn("how to cook samlor", lowered)
        self.assertNotIn("chap chhay", lowered)
        self.assertNotIn("chap chay", lowered)


if __name__ == "__main__":
    unittest.main()
