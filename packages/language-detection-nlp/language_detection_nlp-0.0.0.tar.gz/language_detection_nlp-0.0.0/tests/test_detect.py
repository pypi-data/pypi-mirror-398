from langdetector import detect_language


def test_detect_english():
    text = "This is a simple English sentence."
    res = detect_language(text)
    assert res["language"] == "en"
    assert res["confidence"] > 0.5


def test_detect_french():
    text = "Ceci est une phrase en français."
    res = detect_language(text)
    assert res["language"] == "fr"
