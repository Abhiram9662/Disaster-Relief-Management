"""
Unit tests for real-time translation, relief glossary, phrasebook fallback, and preservation verification.
"""

from app.translation.engine import detect_language, translator
from app.translation.glossary import find_glossary_terms, apply_glossary_constraints
from app.translation.phrasebook import find_phrasebook_match
from app.translation.verification import verify_critical_preservation

def test_language_detection():
    assert detect_language("Hello emergency coordinator") == "en"
    assert detect_language("हमें तुरंत पीने के पानी की आवश्यकता है") == "hi"
    assert detect_language("ਸਾਨੂੰ ਤੁਰੰਤ ਪੀਣ ਵਾਲੇ ਪਾਣੀ ਦੀ ਲੋੜ ਹੈ") == "pa"
    assert detect_language("আমাদের অবিলম্বে পানীয় জলের প্রয়োজন") == "bn"
    assert detect_language("எங்களுக்கு உடனடியாக குடிநீர் தேவை") == "ta"

def test_glossary_lookup_and_constraints():
    text = "We urgently need paracetamol and drinking water at Camp Alpha."
    terms = find_glossary_terms(text)
    assert "paracetamol" in terms
    assert "drinking water" in terms
    assert "camp alpha" in terms

    constrained_hi, matched = apply_glossary_constraints(text, "en", "hi")
    assert "पैरासिटामोल" in constrained_hi
    assert "पीने का पानी" in constrained_hi
    assert "कैंप अल्फा" in constrained_hi

def test_phrasebook_matching():
    match = find_phrasebook_match("We need drinking water urgently", "en", "hi")
    assert match is not None
    trans_text, key = match
    assert key == "water_urgent"
    assert "पीने के पानी" in trans_text

def test_critical_preservation_verification():
    # Exactly preserved numbers, units, locations
    src = "Deliver 50 boxes of paracetamol and 100 liters of drinking water to Camp Alpha."
    tgt_good = "कैंप अल्फा में 50 boxes पैरासिटामोल और 100 liters पीने का पानी पहुंचाएं।"
    passed, rate, missing = verify_critical_preservation(src, tgt_good)
    assert passed is True
    assert rate == 1.0
    assert len(missing) == 0

    # Dropped number (100) and place (Camp Alpha)
    tgt_bad = "दवाइयों के 50 डिब्बे पहुंचाएं।"
    passed_bad, rate_bad, missing_bad = verify_critical_preservation(src, tgt_bad)
    assert passed_bad is False
    assert rate_bad < 1.0
    assert any("100" in m for m in missing_bad)

def test_full_translation_pipeline():
    res = translator.translate("We need drinking water urgently", source_lang="en", target_lang="hi")
    assert res["detected_language"] == "en"
    assert res["target_language"] == "hi"
    assert res["used_phrasebook"] is True
    assert res["preservation_passed"] is True
    assert len(res["translated_text"]) > 0
