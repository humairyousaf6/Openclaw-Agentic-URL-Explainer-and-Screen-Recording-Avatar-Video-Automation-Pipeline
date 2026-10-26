from __future__ import annotations

# ~150 words per minute is a natural, unhurried spoken pace for creator-style narration.
WORDS_PER_SECOND = 2.5
MIN_WORD_BUDGET = 6


def word_budget(duration_sec: int) -> int:
    """Roughly how many spoken words fit in duration_sec at a natural pace."""
    return max(MIN_WORD_BUDGET, round(duration_sec * WORDS_PER_SECOND))


def trim_to_word_budget(text: str, duration_sec: int) -> str:
    words = text.split()
    budget = word_budget(duration_sec)
    if len(words) <= budget:
        return text
    return " ".join(words[:budget]).rstrip(",;:") + "."
