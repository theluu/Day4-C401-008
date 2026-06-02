from __future__ import annotations
import httpx
from bs4 import BeautifulSoup


def get_github_trending(language: str = "", since: str = "daily", max_results: int = 5) -> dict:
    """Scrape GitHub trending repositories."""
    url = "https://github.com/trending"
    if language:
        url += f"/{language.lower().replace(' ', '-')}"
    params = {"since": since}

    headers = {"User-Agent": "AI20k-Research-Agent/1.0"}
    resp = httpx.get(url, params=params, headers=headers, timeout=20, follow_redirects=True)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    items = []
    for repo in soup.select("article.Box-row")[:max_results]:
        name_el = repo.select_one("h2 a")
        desc_el = repo.select_one("p")
        stars_el = repo.select_one("a[href$='/stargazers']")
        if not name_el:
            continue
        repo_path = name_el.get("href", "").strip("/")
        items.append({
            "title": repo_path,
            "url": f"https://github.com/{repo_path}",
            "source": "github_trending",
            "summary": (desc_el.text.strip() if desc_el else "") + (f" | Stars: {stars_el.text.strip()}" if stars_el else ""),
            "section": "open-source",
        })

    return {"items": items, "total": len(items)}
