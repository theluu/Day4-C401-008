from __future__ import annotations
from deep_translator import GoogleTranslator


def translate_text(text: str, target_lang: str = "en", source_lang: str = "auto") -> dict:
    """Translate text using Google Translate via deep-translator."""
    translator = GoogleTranslator(source=source_lang, target=target_lang)
    translated = translator.translate(text)
    return {
        "items": [{
            "title": f"Translation ({source_lang} → {target_lang})",
            "url": "",
            "source": "translate",
            "summary": translated,
            "section": "translation",
        }],
        "original": text,
        "translated": translated,
        "source_lang": source_lang,
        "target_lang": target_lang,
    }
