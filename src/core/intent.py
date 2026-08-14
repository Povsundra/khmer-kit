"""Rule-based query intent classification."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

QueryIntent = Literal[
    "substitution",
    "shopping_list",
    "ingredients",
    "recommend",
    "category_browse",
    "how_to_cook",
    "technique",
    "dish_lookup",
    "out_of_scope",
]

INTENT_PRIORITY: list[QueryIntent] = [
    "out_of_scope",
    "substitution",
    "shopping_list",
    "ingredients",
    "recommend",
    "category_browse",
    "how_to_cook",
    "technique",
    "dish_lookup",
]

_PATTERNS: dict[QueryIntent, list[re.Pattern[str]]] = {
    "out_of_scope": [
        re.compile(p, re.I)
        for p in [
            r"\bprice\b",
            r"\bcost\b",
            r"\brestaurant\b",
            r"\bnutrition\b",
            r"\bcalories\b",
            r"\bwhere to buy\b",
            r"\bmarket price\b",
        ]
    ],
    "substitution": [
        re.compile(p, re.I)
        for p in [
            r"don'?t have",
            r"without ",
            r"substitute",
            r"replacement for",
            r"no fish sauce",
            r"out of ",
            r"គ្មាន",
            r"ជំនួស",
        ]
    ],
    "shopping_list": [
        re.compile(p, re.I)
        for p in [
            r"\bmarket\b",
            r"\bshopping\b",
            r"what (?:do i|should i) buy",
            r"what to buy",
            r"buy at",
            r"go to the market",
            r"ទិញ",
            r"ផ្សារ",
        ]
    ],
    "ingredients": [
        re.compile(p, re.I)
        for p in [
            r"\bingredients?\b",
            r"what(?:'s| is) in",
            r"what do i need",
            r"គ្រឿងផ្សំ",
        ]
    ],
    "recommend": [
        re.compile(p, re.I)
        for p in [
            r"\brecommend\b",
            r"\bsuggest\b",
            r"which (?:one|dish)",
            r"what should i (?:eat|cook|make)",
            r"don'?t know which",
            r"ណែនាំ",
        ]
    ],
    "category_browse": [
        re.compile(p, re.I)
        for p in [
            r"what .*(?:in|are in) (?:the )?(?:samlor|sngor|cha|dessert|other)",
            r"list (?:all )?(?:samlor|sngor|cha|dessert|soup|dishes)",
            r"(?:samlor|cha|dessert|other) category",
            r"how many (?:soup|dish|cha)",
        ]
    ],
    "how_to_cook": [
        re.compile(p, re.I)
        for p in [
            r"how to (?:cook|make|prepare)",
            r"how do i (?:cook|make|prepare)",
            r"recipe for",
            r"steps for",
            r"tell me how to",
            r"របៀបធ្វើ",
            r"របៀបចៀន",
            r"របៀបដាំ",
            r"វិធីធ្វើ",
        ]
    ],
    "technique": [
        re.compile(p, re.I)
        for p in [
            r"\bshould i\b",
            r"\bwhen (?:is|do)\b",
            r"\bhow (?:long|do i know)\b",
            r"stir.?fry.*before",
            r"boil.*direct",
            r"doneness",
        ]
    ],
}


@dataclass
class IntentResult:
    intent: QueryIntent
    confidence: float
    signals: list[str] = field(default_factory=list)


def classify_intent(query: str) -> IntentResult:
    q = query.strip()
    if not q:
        return IntentResult("dish_lookup", 0.0)

    matches: dict[QueryIntent, list[str]] = {}
    for intent, patterns in _PATTERNS.items():
        hit_labels: list[str] = []
        for pat in patterns:
            if pat.search(q):
                hit_labels.append(pat.pattern)
        if hit_labels:
            matches[intent] = hit_labels

    for intent in INTENT_PRIORITY:
        if intent in matches:
            signals = matches[intent]
            confidence = min(0.95, 0.55 + 0.1 * len(signals))
            return IntentResult(intent, confidence, signals)

    return IntentResult("dish_lookup", 0.4)


def preferred_chunk_types(intent: QueryIntent) -> list[str]:
    mapping: dict[QueryIntent, list[str]] = {
        "category_browse": ["parent"],
        "recommend": ["parent"],
        "ingredients": ["ingredients"],
        "shopping_list": ["ingredients"],
        "how_to_cook": ["step"],
        "technique": ["step"],
        "substitution": ["ingredients", "step"],
        "dish_lookup": ["ingredients", "step", "parent"],
        "out_of_scope": [],
    }
    return mapping.get(intent, ["step", "ingredients", "parent"])
