from __future__ import annotations

from typing import Any

import requests

from tools._shared import TIMEOUT, err


def translate_text(text: str = "", source_lang: str = "en", target_lang: str = "vi") -> dict[str, Any]:
    try:
        if not text.strip():
            raise ValueError("text is required")
        langpair = f"{source_lang}|{target_lang}"
        response = requests.get(
            "https://api.mymemory.translated.net/get",
            params={"q": text[:500], "langpair": langpair},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        translated = data.get("responseData", {}).get("translatedText", "")
        quality = data.get("responseData", {}).get("match", 0)
        return {
            "tool": "translate",
            "original": text,
            "translated": translated,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "quality": quality,
        }
    except Exception as exc:
        return err("translate", exc)
