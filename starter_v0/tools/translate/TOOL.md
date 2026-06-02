---
name: translate
version: 1.0.0
author: THELX-2A202600983
api_key_required: false
external_service: Google Translate (via deep-translator library)
---

# translate

Translate text between languages using Google Translate.

## When to use

Use when the user explicitly asks to translate text.

## Args

| Arg | Type | Default | Notes |
|-----|------|---------|-------|
| text | str | required | Text to translate |
| target_lang | str | "en" | Target: en, vi, zh-CN, fr, ja, ko, etc. |
| source_lang | str | "auto" | Source language (auto-detect by default) |

## Returns

`{"translated": "...", "original": "...", "source_lang": "auto", "target_lang": "en", "items": [...]}`
