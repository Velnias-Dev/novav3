from __future__ import annotations

from typing import Literal

EmotionState = Literal["happy", "thinking", "neutral", "playful", "serious"]

HAPPY_KEYWORDS = {
    "great",
    "awesome",
    "love",
    "nice",
    "perfect",
    "glad",
    "happy",
    "excellent",
    "cool",
}
THINKING_KEYWORDS = {
    "let's think",
    "consider",
    "analyze",
    "step by step",
    "it depends",
    "first,",
    "second,",
    "reasoning",
    "hmm",
}
PLAYFUL_KEYWORDS = {
    "hehe",
    "haha",
    "lol",
    "playful",
    "joke",
    "fun",
    "wink",
    "silly",
}
SERIOUS_KEYWORDS = {
    "important",
    "critical",
    "warning",
    "danger",
    "must",
    "urgent",
    "careful",
    "risk",
}


def detect_emotion(text: str) -> EmotionState:
    """
    Lightweight heuristic emotion detection for assistant output text.
    Keep this simple and deterministic so behavior is easy to tweak.
    """
    content = text.strip().lower()
    if not content:
        return "neutral"

    if any(keyword in content for keyword in SERIOUS_KEYWORDS):
        return "serious"
    if any(keyword in content for keyword in THINKING_KEYWORDS):
        return "thinking"
    if any(keyword in content for keyword in PLAYFUL_KEYWORDS):
        return "playful"
    if any(keyword in content for keyword in HAPPY_KEYWORDS) or "!" in content:
        return "happy"
    return "neutral"
