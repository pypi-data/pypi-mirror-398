from typing import Dict, List, Tuple
from langdetect import DetectorFactory, detect_langs

DetectorFactory.seed = 0

COMMON_LANGUAGE_NAMES = {
    "en": "English",
    "fr": "French",
    "es": "Spanish",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "zh-cn": "Chinese",
    "zh-tw": "Chinese (Taiwan)",
}


def detect_languages(text: str) -> List[Tuple[str, float]]:
    """Return list of (lang, prob) candidates sorted by probability."""
    if not text or not text.strip():
        return []
    try:
        langs = detect_langs(text)
    except Exception:
        return []
    return [(cand.lang, cand.prob) for cand in langs]


def detect_language(text: str) -> Dict:
    """Detect top language and return dictionary with code, name and confidence."""
    candidates = detect_languages(text)
    if not candidates:
        return {"language": None, "name": None, "confidence": 0.0}
    lang, prob = candidates[0]
    name = COMMON_LANGUAGE_NAMES.get(lang, None)
    return {"language": lang, "name": name, "confidence": float(prob)}
