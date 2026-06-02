---
name: hackernews
version: 1.0.0
author: THELX-2A202600983
api_key_required: false
external_service: HN Algolia API (https://hn.algolia.com/api/v1)
---

# hackernews

Search Hacker News stories and discussions using the Algolia search API.

## When to use

Use when the user asks about tech news, startup discussions, developer community opinions, or content from Hacker News.

## Args

| Arg | Type | Default | Notes |
|-----|------|---------|-------|
| query | str | required | Search keywords |
| max_results | int | 5 | Stories to return |
| sort | str | "relevance" | "relevance" or "date" |

## Returns

```json
{
  "items": [
    {
      "title": "Story title",
      "url": "https://...",
      "source": "hackernews",
      "summary": "Points: 120 | Comments: 45 | By: username",
      "section": "tech"
    }
  ],
  "total": 1234
}
```

## No API key needed

Uses Algolia public HN search API. Rate limits are generous for classroom use.
