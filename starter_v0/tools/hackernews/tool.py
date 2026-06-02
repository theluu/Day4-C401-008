from __future__ import annotations
import httpx


def search_hackernews(query: str, max_results: int = 5, sort: str = "relevance") -> dict:
    """Search Hacker News stories via Algolia API. No API key required."""
    base = "https://hn.algolia.com/api/v1"
    endpoint = f"{base}/search_by_date" if sort == "date" else f"{base}/search"
    params = {"query": query, "tags": "story", "hitsPerPage": max_results}

    resp = httpx.get(endpoint, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    items = []
    for hit in data.get("hits", []):
        hn_url = f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"
        items.append({
            "title": hit.get("title", ""),
            "url": hit.get("url") or hn_url,
            "source": "hackernews",
            "summary": f"Points: {hit.get('points', 0)} | Comments: {hit.get('num_comments', 0)} | By: {hit.get('author', '')}",
            "section": "tech",
        })

    return {"items": items, "total": data.get("nbHits", 0)}
