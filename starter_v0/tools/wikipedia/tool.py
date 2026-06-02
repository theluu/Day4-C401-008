from __future__ import annotations
from typing import Any
import requests
from tools._shared import TIMEOUT, err

def search_wikipedia(query: str) -> dict[str, Any]:
    """Search Wikipedia for a given query and return summaries of matching pages."""
    try:
        headers = {
            "User-Agent": "AI20k-Day04-Research-Agent/1.0 (educational lab)"
        }
        # Step 1: search for matching page titles
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "opensearch",
            "search": query,
            "limit": 3,
            "namespace": 0,
            "format": "json"
        }
        resp = requests.get(url, params=params, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        
        # opensearch returns: [query, [titles], [descriptions], [links]]
        titles = data[1] if len(data) > 1 else []
        links = data[3] if len(data) > 3 else []
        
        items = []
        for i, title in enumerate(titles):
            # Fetch summary for the page
            summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title.replace(' ', '_')}"
            try:
                s_resp = requests.get(summary_url, headers=headers, timeout=TIMEOUT)
                s_resp.raise_for_status()
                s_data = s_resp.json()
                summary = s_data.get("extract", "")
            except Exception:
                summary = data[2][i] if (len(data) > 2 and i < len(data[2])) else ""
            
            items.append({
                "title": title,
                "url": links[i] if i < len(links) else "",
                "source": "Wikipedia",
                "summary": summary
            })
            
        return {"tool": "wikipedia", "query": query, "items": items}
    except Exception as exc:
        return err("wikipedia", exc)
