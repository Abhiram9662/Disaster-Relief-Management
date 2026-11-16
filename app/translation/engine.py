"""
Translation Pipeline (Section 4.2):
- Language Identification
- Translation into recipient's language
- Constrained relief glossary terms
- Number, unit, place preservation verification
- Confidence/check-triggered fallback to pre-verified phrasebook
- Human review flagging
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from app.translation.glossary import find_glossary_terms, apply_glossary_constraints, RELIEF_GLOSSARY
from app.translation.phrasebook import find_phrasebook_match, PHRASEBOOK
from app.translation.verification import verify_critical_preservation, extract_numbers, extract_units

def detect_language(text: str) -> str:
    """Detects language based on Unicode character script ranges."""
    for ch in text:
        code = ord(ch)
        if 0x0900 <= code <= 0x097F:
            return "hi"  # Devanagari / Hindi
        if 0x0A00 <= code <= 0x0A7F:
            return "pa"  # Gurmukhi / Punjabi
        if 0x0980 <= code <= 0x09FF:
            return "bn"  # Bengali
        if 0x0B80 <= code <= 0x0BFF:
            return "ta"  # Tamil
    return "en"  # Default English

# Lightweight bilingual translation vocabulary for disaster coordination
RELIEF_DICTIONARY: Dict[str, Dict[str, str]] = {
    "urgent": {"hi": "तुरंत", "pa": "ਤੁਰੰਤ", "bn": "জরুরি", "ta": "அவசரம்"},
    "emergency": {"hi": "आपातकालीन", "pa": "ਐਮਰਜੈਂਸੀ", "bn": "জরুরী অবস্থা", "ta": "அவசரநிலை"},
    "help": {"hi": "मदद", "pa": "ਮਦਦ", "bn": "সাহায্য", "ta": "உதவி"},
    "need": {"hi": "आवश्यकता", "pa": "ਲੋੜ", "bn": "প্রয়োজন", "ta": "தேவை"},
    "food": {"hi": "भोजन", "pa": "ਭੋਜਨ", "bn": "খাবার", "ta": "உணவு"},
    "water": {"hi": "पानी", "pa": "ਪਾਣੀ", "bn": "জল", "ta": "தண்ணீர்"},
    "medicine": {"hi": "दवाई", "pa": "ਦਵਾਈ", "bn": "ওষুধ", "ta": "மருந்து"},
    "doctor": {"hi": "चिकित्सक", "pa": "ਡਾਕਟਰ", "bn": "ডাক্তার", "ta": "மருத்துவர்"},
    "nurse": {"hi": "नर्स", "pa": "ਨਰਸ", "bn": "নার্স", "ta": "செவிலியர்"},
    "hospital": {"hi": "अस्पताल", "pa": "ਹਸਪਤਾਲ", "bn": "হাসপাতাল", "ta": "மருத்துவமனை"},
    "camp": {"hi": "शिविर", "pa": "ਕੈਂਪ", "bn": "ক্যাম্প", "ta": "முகாம்"},
    "people": {"hi": "लोग", "pa": "ਲੋਕ", "bn": "মানুষ", "ta": "மக்கள்"},
    "injured": {"hi": "घायल", "pa": "ਜ਼ਖਮੀ", "bn": "আহত", "ta": "காயமடைந்த"},
    "shelter": {"hi": "आश्रय", "pa": "ਆਸਰਾ", "bn": "আশ্রয়", "ta": "தங்குமிடம்"},
    "children": {"hi": "बच्चे", "pa": "ਬੱਚੇ", "bn": "শিশুরা", "ta": "குழந்தைகள்"},
    "supply": {"hi": "आपूर्ति", "pa": "ਸਪਲਾਈ", "bn": "সরবরাহ", "ta": "விநியோகம்"},
    "volunteer": {"hi": "स्वयंसेवक", "pa": "ਵਲੰਟੀਅਰ", "bn": "স্বেচ্ছাসেবক", "ta": "தன்னார்வலர்"},
    "boat": {"hi": "नाव", "pa": "ਕਿਸ਼ਤੀ", "bn": "নৌকা", "ta": "படகு"},
    "safe": {"hi": "सुरक्षित", "pa": "ਸੁਰੱਖਿਅਤ", "bn": "নিরাপদ", "ta": "பாதுகாப்பான"},
}

class TranslationPipeline:
    def __init__(self):
        pass

    def translate(
        self,
        text: str,
        source_lang: Optional[str] = None,
        target_lang: str = "hi"
    ) -> Dict[str, Any]:
        """
        Executes full Section 4.2 translation pipeline:
        1. Language ID
        2. Phrasebook check
        3. Glossary & entity constrained translation
        4. Preservation verification (numbers, units, places)
        5. Fallback & human review flagging if verification fails
        """
        if not source_lang or source_lang == "auto":
            source_lang = detect_language(text)

        if source_lang == target_lang:
            return {
                "original_text": text,
                "detected_language": source_lang,
                "target_language": target_lang,
                "translated_text": text,
                "glossary_terms": find_glossary_terms(text),
                "preservation_passed": True,
                "preservation_rate": 1.0,
                "used_phrasebook": False,
                "flagged_for_human_review": False,
                "missing_entities": []
            }

        # Step 1: Pre-verified phrasebook lookup
        phrase_match = find_phrasebook_match(text, source_lang, target_lang)
        if phrase_match:
            translated_text, phrase_key = phrase_match
            # Verify preservation on phrasebook output
            passed, rate, missing = verify_critical_preservation(text, translated_text)
            return {
                "original_text": text,
                "detected_language": source_lang,
                "target_language": target_lang,
                "translated_text": translated_text,
                "glossary_terms": find_glossary_terms(text),
                "preservation_passed": passed,
                "preservation_rate": rate,
                "used_phrasebook": True,
                "flagged_for_human_review": not passed,
                "missing_entities": missing
            }

        # Step 2: Glossary and dictionary entity-preserving translation
        # First extract numbers and units to ensure strict preservation
        numbers = extract_numbers(text)
        units = extract_units(text)
        glossary_terms = find_glossary_terms(text)

        # Apply glossary constraints
        intermediate_text, applied_terms = apply_glossary_constraints(text, source_lang, target_lang)

        # Token-based domain mapping for relief phrases
        words = intermediate_text.split()
        translated_tokens = []
        for word in words:
            clean_w = re.sub(r'[^\w]', '', word.lower())
            if clean_w in RELIEF_DICTIONARY:
                tgt_word = RELIEF_DICTIONARY[clean_w].get(target_lang, word)
                translated_tokens.append(tgt_word)
            else:
                translated_tokens.append(word)

        draft_translation = " ".join(translated_tokens)

        # Step 3: Check preservation
        passed, rate, missing = verify_critical_preservation(text, draft_translation)

        used_phrasebook = False
        flagged_for_review = False

        # Step 4: Fallback to safe phrasebook / template if critical preservation failed
        if not passed:
            flagged_for_review = True
            # Find closest general safety phrase
            fallback_match = find_phrasebook_match("emergency relief required", "en", target_lang)
            if fallback_match:
                draft_translation = f"{fallback_match[0]} [Original: {text}]"
                used_phrasebook = True

        return {
            "original_text": text,
            "detected_language": source_lang,
            "target_language": target_lang,
            "translated_text": draft_translation,
            "glossary_terms": glossary_terms,
            "preservation_passed": passed,
            "preservation_rate": rate,
            "used_phrasebook": used_phrasebook,
            "flagged_for_human_review": flagged_for_review,
            "missing_entities": missing
        }

translator = TranslationPipeline()
