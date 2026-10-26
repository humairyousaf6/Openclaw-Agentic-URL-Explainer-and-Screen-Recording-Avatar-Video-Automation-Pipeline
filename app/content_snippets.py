from __future__ import annotations

import re


SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+")
# Nav/button labels (e.g. "LEARN MORE", "TRY FOR FREE") often sit right before a real sentence with
# no punctuation between them in the source HTML, so they get glued onto it when text nodes are joined.
LEADING_BUTTON_LABEL_PATTERN = re.compile(r"^(?:[A-Z][A-Z0-9']*\s+){1,4}(?=[A-Z][a-z])")


def extract_content_snippets(text: str, count: int = 3, min_len: int = 20, max_len: int = 160) -> list[str]:
    """Pick a few real, prose-like sentences out of extracted page text for use as fallback narration
    content, skipping short all-caps button/menu fragments (e.g. "LEARN MORE", "TRY FOR FREE")."""
    snippets: list[str] = []
    for sentence in SENTENCE_SPLIT_PATTERN.split(text):
        sentence = LEADING_BUTTON_LABEL_PATTERN.sub("", sentence.strip()).strip()
        if not (min_len <= len(sentence) <= max_len):
            continue
        letters = [c for c in sentence if c.isalpha()]
        if not letters or sum(1 for c in letters if c.isupper()) / len(letters) > 0.4:
            continue
        snippets.append(sentence)
        if len(snippets) >= count:
            break
    return snippets
