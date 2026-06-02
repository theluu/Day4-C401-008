from __future__ import annotations
import httpx


def search_wikipedia(query: str, max_results: int = 3, lang: str = "en") -> dict:
    """Search Wikipedia articles."""
    url = f"https://{lang}.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": max_results,
        "format": "json",
        "utf8": 1,
    }
    headers = {"User-Agent": "AI20k-Research-Agent/1.0 (educational project; contact: thexuanluu@gmail.com)"}
    resp = httpx.get(url, params=params, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    items = []
    for hit in data.get("query", {}).get("search", []):
        page_url = f"https://{lang}.wikipedia.org/wiki/{hit['title'].replace(' ', '_')}"
        snippet = hit.get("snippet", "")
        for tag in ['<span class="searchmatch">', "</span>"]:
            snippet = snippet.replace(tag, "")
        items.append({
            "title": hit["title"],
            "url": page_url,
            "source": "wikipedia",
            "summary": snippet,
            "section": "encyclopedia",
        })

    return {"items": items, "total": len(items)}
