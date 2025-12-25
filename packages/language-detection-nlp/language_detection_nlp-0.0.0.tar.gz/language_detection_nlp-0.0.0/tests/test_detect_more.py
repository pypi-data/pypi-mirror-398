from langdetector import detect_language, detect_languages


def test_detect_empty_returns_none():
    res = detect_language("")
    assert res["language"] is None
    assert res["confidence"] == 0.0


def test_detect_languages_candidates():
    text = "Hola, buenos días"
    cands = detect_languages(text)
    assert isinstance(cands, list)
    assert len(cands) >= 1
    assert any(code == "es" for code, _ in cands)
