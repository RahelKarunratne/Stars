"""
Utilities: fuzzy spelling correction using RapidFuzz and simple helpers.
"""
from typing import List, Tuple
from rapidfuzz import process, fuzz


def fuzzy_correct_phrase(phrase: str, candidate_tokens: List[str], threshold: int = 85) -> Tuple[str, bool]:
    """Try to correct words in phrase by comparing to candidate_tokens.

    - phrase: user input string
    - candidate_tokens: tokens from search results (lowercased)
    Returns: (corrected_phrase, changed_flag)
    """
    words = phrase.split()
    changed = False

    # choose a limited list for performance
    tokens = candidate_tokens[:200]
    for i, w in enumerate(words):
        lw = w.lower()
        if lw in tokens:
            continue
        # try best match
        match = process.extractOne(lw, tokens, scorer=fuzz.ratio)
        if match and match[1] >= threshold:
            words[i] = match[0]
            changed = True
    corrected = " ".join(words)
    return corrected, changed


def normalize_pair(title: str, artist: str) -> Tuple[str, str]:
    """Return normalized form for dedup: lower, trimmed, minimal punctuation."""
    import re

    def clean(s: str) -> str:
        s2 = s.lower().strip()
        s2 = re.sub(r"[^a-z0-9 ]+", "", s2)
        s2 = " ".join(s2.split())
        return s2

    return clean(title), clean(artist)
