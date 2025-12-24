"""
DuckDuckGo HTML search helper and title/snippet parser.
We only fetch search result titles/snippets (no lyric pages).
"""
from typing import List, Dict, Optional, Tuple
import requests
from bs4 import BeautifulSoup
import re

DUCKDUCKGO_HTML = "https://html.duckduckgo.com/html/"
HEADERS = {"User-Agent": "lyrics-finder-bot/1.0 (+https://example.local)"}


def bing_search(query: str, max_results: int = 30) -> List[Dict[str, str]]:
    """Fallback using Bing HTML search (parses titles and snippets)."""
    url = "https://www.bing.com/search"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    r = requests.get(url, params={"q": query}, headers=headers, timeout=10)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    results = []
    # Bing uses li.b_algo elements
    for li in soup.find_all("li", class_=re.compile(r"b_algo")):
        h2 = li.find("h2")
        if not h2:
            continue
        a = h2.find("a")
        if not a or not a.get_text(strip=True):
            continue
        title = a.get_text(" ", strip=True)
        snippet = ""
        p = li.find("p")
        if p:
            snippet = p.get_text(" ", strip=True)
        results.append({"title": title, "snippet": snippet, "source": "bing"})
        if len(results) >= max_results:
            break
    return results


def ddg_search(query: str, max_results: int = 30) -> List[Dict[str, str]]:
    """Return list of dicts with 'title' and 'snippet' for query. Tries DuckDuckGo and falls back to Bing.
    Each result dict may include 'source' indicating which search engine was used."""
    # try DuckDuckGo first
    try:
        # some servers block non-browser UAs; use a browser-like UA here
        r = requests.post(DUCKDUCKGO_HTML, data={"q": query}, headers={**HEADERS, "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        results = []
        # DuckDuckGo uses div.result blocks; be flexible with selectors
        # look for anchors inside results
        for div in soup.find_all(class_=re.compile(r"result")):
            title_tag = div.find("a")
            if not title_tag or not title_tag.get_text(strip=True):
                continue
            title = title_tag.get_text(" ", strip=True)

            snippet = ""
            # multiple possible class names for snippet
            s = div.find(class_=re.compile(r"snippet|result__snippet"))
            if s:
                snippet = s.get_text(" ", strip=True)

            results.append({"title": title, "snippet": snippet, "source": "ddg"})
            if len(results) >= max_results:
                break

        # If nothing useful found, try Bing as a fallback
        if not results:
            return bing_search(query, max_results=max_results)
        return results

    except Exception:
        # On any error talking to DuckDuckGo, try Bing
        try:
            return bing_search(query, max_results=max_results)
        except Exception:
            return []


# heuristics to extract song title and artist
TITLE_SEP_RE = re.compile(r"\s+[-–—|:•]\s+")
QUOTE_BY_RE = re.compile(r'"(?P<title>[^\"]+)"\s+by\s+(?P<artist>.+)', re.I)
BY_RE = re.compile(r"(?P<title>.+)\s+by\s+(?P<artist>.+)", re.I)


def _clean_text(t: str) -> str:
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"\(.*?\)", "", t)  # remove parenthetical remarks
    t = re.sub(r"lyrics$", "", t, flags=re.I)
    return t.strip(" -–—|:")


def parse_title_artist(title: str, snippet: str = "") -> Optional[Tuple[str, str]]:
    """Try to parse (song_title, artist) from a title/snippet pair.

    Returns None if it can't find a reasonable pair.
    """
    t = _clean_text(title)

    # 1) "Title" by Artist (often in snippet)
    m = QUOTE_BY_RE.search(snippet) or QUOTE_BY_RE.search(title)
    if m:
        return (m.group("title").strip(), m.group("artist").strip())

    m = BY_RE.search(snippet) or BY_RE.search(title)
    if m:
        maybe_title = _clean_text(m.group("title"))
        maybe_artist = _clean_text(m.group("artist"))
        return (maybe_title, maybe_artist)

    # 2) Split on common separators, attempt to guess which side is title/artist
    parts = TITLE_SEP_RE.split(t)
    if len(parts) >= 2:
        left, right = parts[0].strip(), parts[1].strip()
        # heuristics: if left contains 'lyrics' or 'song' it's probably title
        if re.search(r"lyrics|song|official", left, re.I):
            return (left, right)
        # sometimes format is Artist - Title
        # guess: if left has more than 2 words and right fewer, left is artist less likely
        if len(left.split()) <= len(right.split()):
            return (right, left)
        else:
            return (left, right)

    # 3) fallback: look for pattern Artist: Title or Title: Artist
    if ":" in t:
        a, b = [p.strip() for p in t.split(":", 1)]
        # guess by length
        if len(a.split()) > len(b.split()):
            return (b, a)
        else:
            return (a, b)

    return None


def _clean_artist_text(a: str) -> str:
    """Trim common noisy suffixes from artist text (like dots, extra sentences)."""
    a = a.strip()
    # cut at first dot or ' with ' or ' - ' or ' | '
    a = re.split(r"\.| with | - | \|| -\s|,", a, maxsplit=1)[0].strip()
    return a


def extract_candidates(results: List[Dict[str, str]]) -> List[Tuple[str, str]]:
    """From DDG results list, return list of (title, artist) parsed pairs."""
    pairs = []
    for r in results:
        parsed = parse_title_artist(r["title"], r.get("snippet", ""))
        if parsed:
            t, a = parsed
            if t and a:
                t = t.strip()
                a = _clean_artist_text(a)
                # remove trailing 'lyrics' from title
                t = re.sub(r"\s*lyrics$", "", t, flags=re.I).strip()
                pairs.append((t, a))
    return pairs


def result_tokens(results: List[Dict[str, str]]) -> List[str]:
    """Tokenize titles and snippets into lowercase words (for fuzzy correction)."""
    tokens = []
    for r in results:
        text = f"{r.get('title','')} {r.get('snippet','')}"
        for w in re.findall(r"[A-Za-z0-9'-]{3,}", text):
            tokens.append(w.lower())
    # return unique tokens, most common first
    from collections import Counter

    c = Counter(tokens)
    return [w for w, _ in c.most_common()]
