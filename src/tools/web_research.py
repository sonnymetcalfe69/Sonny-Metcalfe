"""Pluggable web research. Returns None until you wire a real search API.

The Researcher agent checks for a real result set here first; when this
returns None it falls back to the model's own general knowledge and labels
the output accordingly, rather than fabricating fake search results.

To wire a real provider, implement `search()` to call it and return a list
of {"title": ..., "url": ..., "snippet": ...} dicts. Example with a generic
HTTP search API (pseudocode, fill in your provider's actual endpoint/key):

    import os, requests

    def search(query: str, max_results: int = 5) -> list[dict] | None:
        api_key = os.environ.get("SEARCH_API_KEY")
        if not api_key:
            return None
        resp = requests.get(
            "https://api.example-search-provider.com/search",
            params={"q": query, "count": max_results},
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10,
        )
        resp.raise_for_status()
        return [
            {"title": r["title"], "url": r["url"], "snippet": r["snippet"]}
            for r in resp.json().get("results", [])
        ]
"""

from __future__ import annotations


def search(query: str, max_results: int = 5) -> list[dict] | None:
    return None
