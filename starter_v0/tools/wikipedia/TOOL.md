---
name: wikipedia
version: 1.0.0
author: THELX-2A202600983
api_key_required: false
external_service: Wikipedia API (https://en.wikipedia.org/w/api.php)
---

# wikipedia

Search Wikipedia articles. No API key required.

## When to use

Use when the user asks for background information, definitions, or encyclopedic knowledge about a topic.

## Args

| Arg | Type | Default | Notes |
|-----|------|---------|-------|
| query | str | required | Search term |
| max_results | int | 3 | Articles to return |
| lang | str | "en" | Language code: en, vi, zh, fr, etc. |

## Returns

`{"items": [{"title": "...", "url": "...", "source": "wikipedia", "summary": "..."}], "total": 3}`
