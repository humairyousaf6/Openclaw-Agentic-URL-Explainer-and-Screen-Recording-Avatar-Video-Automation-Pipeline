from __future__ import annotations

import re
import urllib.request
from html.parser import HTMLParser
from typing import Any


SKIPPED_TAGS = {"script", "style", "noscript", "svg", "nav", "header", "footer", "aside", "form", "button", "select", "template"}
MAIN_CONTENT_TAGS = {"main", "article"}


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self._in_title = False
        self._skip_stack: list[str] = []
        self._main_depth = 0
        self.parts: list[str] = []
        self.main_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in SKIPPED_TAGS:
            self._skip_stack.append(tag)
        if tag in MAIN_CONTENT_TAGS:
            self._main_depth += 1
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag in SKIPPED_TAGS and self._skip_stack and self._skip_stack[-1] == tag:
            self._skip_stack.pop()
        if tag in MAIN_CONTENT_TAGS and self._main_depth:
            self._main_depth -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if not text or self._skip_stack:
            return
        if self._in_title:
            self.title += text
        else:
            self.parts.append(text)
            if self._main_depth:
                self.main_parts.append(text)


def extract_website(url: str, prompt: str) -> dict[str, Any]:
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "OpenClawContentWriter/0.1"})
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read()
            content_type = response.headers.get_content_charset()
        html = decode_html(raw, content_type)
        parser = TextExtractor()
        parser.feed(html)
        main_text = normalize_text(" ".join(parser.main_parts))
        # Prefer text scoped to <main>/<article> when the page provides one and it has
        # enough content — it's much less likely to be nav/boilerplate than the full page.
        text = main_text if len(main_text) >= 200 else normalize_text(" ".join(parser.parts))
        if not text:
            text = f"No readable page text was extracted. Use the user prompt as direction: {prompt}"
        return {
            "url": url,
            "title": normalize_text(parser.title)[:200],
            "text": text[:20000],
            "fetch_ok": True,
            "error": None,
        }
    except Exception as exc:
        return {
            "url": url,
            "title": "",
            "text": f"Website fetch failed. Use the user prompt as source context: {prompt}",
            "fetch_ok": False,
            "error": str(exc),
        }


SKIP_LINK_PATTERN = re.compile(r"\b[Ss]kip to [a-zA-Z0-9 ]{1,30}?(?=[A-Z]|$)")
CHARSET_META_PATTERN = re.compile(rb'charset=["\']?([a-zA-Z0-9_-]+)', re.IGNORECASE)


def decode_html(raw: bytes, header_charset: str | None) -> str:
    candidates = [c for c in [header_charset, *_sniff_meta_charset(raw), "utf-8", "cp1252"] if c]
    for encoding in candidates:
        try:
            return raw.decode(encoding)
        except (LookupError, UnicodeDecodeError):
            continue
    return raw.decode("utf-8", errors="replace")


def _sniff_meta_charset(raw: bytes) -> list[str]:
    match = CHARSET_META_PATTERN.search(raw[:4096])
    return [match.group(1).decode("ascii")] if match else []


def normalize_text(value: str) -> str:
    text = re.sub(r"\s+", " ", value).strip()
    return SKIP_LINK_PATTERN.sub("", text).strip()
