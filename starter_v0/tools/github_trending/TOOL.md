---
name: github_trending
version: 1.0.0
author: THELX-2A202600983
api_key_required: false
external_service: GitHub Trending (https://github.com/trending)
---

# github_trending

Get trending GitHub repositories by scraping the public GitHub trending page.

## When to use

Use when the user asks about popular open-source projects, trending repos, or what developers are building.

## Args

| Arg | Type | Default | Notes |
|-----|------|---------|-------|
| language | str | "" | Filter by language (python, javascript, etc.) |
| since | str | "daily" | Time period: "daily", "weekly", "monthly" |
| max_results | int | 5 | Repos to return |

## Returns

`{"items": [{"title": "owner/repo", "url": "https://github.com/...", "source": "github_trending", "summary": "Description | Stars: 1.2k"}], "total": 5}`
