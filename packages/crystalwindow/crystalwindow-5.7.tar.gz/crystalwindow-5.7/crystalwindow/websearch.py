"""
WebBrowse — Universal Web Search Module
A modern, clean search helper for any Python application.
"""

from __future__ import annotations
import requests
import webbrowser
from dataclasses import dataclass
from typing import List, Tuple, Optional, Any



# ================================
# Dataclass: Unified Search Result
# ================================

@dataclass
class SearchResult:
    summary: str
    links: List[Tuple[str, str]]     # (title, url)
    raw: Any = None                  # raw API payload


# ================================
# Main WebBrowse Search Handler
# ================================

class WebBrowse:
    """
    Lightweight universal web search interface.
    Supports:
      - Google Search via Serper.dev (primary)
      - DuckDuckGo Instant Answer (fallback)

    Designed to be extendable and safe.
    """

    # --------------------------
    # API Endpoints
    # --------------------------
    DUCK_URL = "https://api.duckduckgo.com/"
    SERPER_URL = "https://google.serper.dev/search"

    # --------------------------
    # Set your Serper.dev key
    # --------------------------
    SERPER_API_KEY: str = ""     # <-- user must set manually

    # =====================================================
    # DuckDuckGo Instant Answer (fallback, small summaries)
    # =====================================================
    @classmethod
    def _search_duckduckgo(cls, query: str) -> SearchResult:
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "no_redirect": 1
        }

        try:
            r = requests.get(cls.DUCK_URL, params=params, timeout=8)
            r.raise_for_status()
        except Exception as e:
            return SearchResult(f"DuckDuckGo error: {e}", [], None)

        data = r.json()
        summary = data.get("AbstractText") or data.get("Abstract") or ""
        links: List[Tuple[str, str]] = []

        # Abstract main URL
        if data.get("AbstractURL"):
            links.append((data.get("Heading", "Result"), data["AbstractURL"]))

        # Recursive topic extractor
        def extract_topics(node):
            if isinstance(node, dict):
                if node.get("FirstURL") and node.get("Text"):
                    links.append((node["Text"], node["FirstURL"]))
                for k in ("Topics", "RelatedTopics"):
                    if isinstance(node.get(k), list):
                        for sub in node[k]:
                            extract_topics(sub)
            elif isinstance(node, list):
                for sub in node:
                    extract_topics(sub)

        extract_topics(data.get("RelatedTopics", []))

        # If summary is empty, generate from first few topics
        if not summary and links:
            summary = "\n".join(t for t, _ in links[:3])

        return SearchResult(summary.strip(), links, data)

    # =====================================================
    # Google Search via Serper.dev
    # =====================================================
    @classmethod
    def _search_google(cls, query: str) -> SearchResult:
        if not cls.SERPER_API_KEY:
            return SearchResult("Google engine requires SERPER_API_KEY.", [], None)

        headers = {
            "X-API-KEY": cls.SERPER_API_KEY,
            "Content-Type": "application/json",
        }
        body = {"q": query}

        try:
            r = requests.post(cls.SERPER_URL, headers=headers, json=body, timeout=8)
            r.raise_for_status()
        except Exception as e:
            return SearchResult(f"Google search error: {e}", [], None)

        data = r.json()
        links = []
        summaries = []

        for item in data.get("organic", []):
            title = item.get("title", "Untitled")
            url = item.get("link", "")
            snippet = item.get("snippet", "")

            links.append((title, url))
            if snippet:
                summaries.append(snippet)

        summary = "\n".join(summaries[:3]).strip() or "(no summary)"

        return SearchResult(summary, links, data)

    # =====================================================
    # Public search() method
    # =====================================================
    @classmethod
    def search(cls, query: str, engine: str = "google") -> SearchResult:
        if not query.strip():
            return SearchResult("", [], None)

        engine = engine.lower().strip()

        if engine == "google":
            return cls._search_google(query)

        if engine == "duckduckgo":
            return cls._search_duckduckgo(query)

        return SearchResult(f"Unknown search engine '{engine}'", [], None)

    # =====================================================
    # URL Opener
    # =====================================================
    @staticmethod
    def open_url(url: str) -> None:
        try:
            webbrowser.open(url)
        except Exception:
            pass
