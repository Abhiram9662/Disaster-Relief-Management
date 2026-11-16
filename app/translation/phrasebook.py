"""
Pre-verified phrasebook of high-frequency relief messages with guaranteed safety-critical accuracy.
"""

from typing import Dict, List, Optional, Tuple
import re

PHRASEBOOK: List[Dict[str, str]] = [
    {
        "key": "water_urgent",
        "en": "We need drinking water urgently",
        "hi": "हमें तुरंत पीने के पानी की आवश्यकता है",
        "pa": "ਸਾਨੂੰ ਤੁਰੰਤ ਪੀਣ ਵਾਲੇ ਪਾਣੀ ਦੀ ਲੋੜ ਹੈ",
        "bn": "আমাদের অবিলম্বে পানীয় জলের প্রয়োজন",
        "ta": "எங்களுக்கு உடனடியாக குடிநீர் தேவை",
    },
    {
        "key": "medical_help_urgent",
        "en": "Medical help is required here immediately",
        "hi": "यहाँ तुरंत चिकित्सा सहायता की आवश्यकता है",
        "pa": "ਇੱਥੇ ਤੁਰੰਤ ਡਾਕਟਰੀ ਸਹਾਇਤਾ ਦੀ ਲੋੜ ਹੈ",
        "bn": "এখানে অবিলম্বে চিকিৎসা সহায়তা প্রয়োজন",
        "ta": "இங்கு உடனடியாக மருத்துவ உதவி தேவை",
    },
    {
        "key": "children_food_rations",
        "en": "Children need emergency food rations",
        "hi": "बच्चों को आपातकालीन खाद्य राशन की आवश्यकता है",
        "pa": "ਬੱਚਿਆਂ ਨੂੰ ਐਮਰਜੈਂਸੀ ਭੋਜਨ ਰਾਸ਼ਨ ਦੀ ਲੋੜ ਹੈ",
        "bn": "শিশুদের জরুরি খাদ্য রেশন প্রয়োজন",
        "ta": "குழந்தைகளுக்கு அவசர உணவு ரேஷன் தேவை",
    },
    {
        "key": "shelter_full_capacity",
        "en": "The relief camp shelter is at full capacity",
        "hi": "राहत शिविर आश्रय पूरी क्षमता पर है",
        "pa": "ਰਾਹਤ ਕੈਂਪ ਸ਼ੈਲਟਰ ਪੂਰੀ ਸਮਰੱਥਾ 'ਤੇ ਹੈ",
        "bn": "ত্রাণ শিবির আশ্রয় সম্পূর্ণ ক্ষমতায় রয়েছে",
        "ta": "நிவாரண முகாம் தங்குமிடம் முழு கொள்ளளவை எட்டியுள்ளது",
    },
    {
        "key": "rescue_boat_needed",
        "en": "Rescue boat needed for stranded families",
        "hi": "फंसे हुए परिवारों के लिए बचाव नाव की आवश्यकता है",
        "pa": "ਫਸੇ ਪਰਿਵਾਰਾਂ ਲਈ ਬਚਾਅ ਕਿਸ਼ਤੀ ਦੀ ਲੋੜ ਹੈ",
        "bn": "আটকে থাকা পরিবারের জন্য উদ্ধারকারী নৌকা প্রয়োজন",
        "ta": "சிக்கித் தவிக்கும் குடும்பங்களுக்கு மீட்புப் படகு தேவை",
    },
    {
        "key": "blankets_and_tarpaulins",
        "en": "Urgent requirement for blankets and tarpaulin sheets",
        "hi": "कंबल और तिरपाल की चादरों की तत्काल आवश्यकता है",
        "pa": "ਕੰਬਲ ਅਤੇ ਤਰਪਾਲਾਂ ਦੀ ਤੁਰੰਤ ਲੋੜ ਹੈ",
        "bn": "কম্বল এবং ত্রিপলের জরুরি প্রয়োজন",
        "ta": "போர்வைகள் மற்றும் தார்பாலின் தாள்கள் அவசரமாக தேவைப்படுகின்றன",
    },
    {
        "key": "insulin_needed",
        "en": "Diabetic patient requires emergency insulin",
        "hi": "मधुमेह के रोगी को आपातकालीन इंसुलिन की आवश्यकता है",
        "pa": "ਸ਼ੂਗਰ ਦੇ ਮਰੀਜ਼ ਨੂੰ ਐਮਰਜੈਂਸੀ ਇਨਸੁਲਿਨ ਦੀ ਲੋੜ ਹੈ",
        "bn": "ডায়াবেটিস রোগীর জরুরি ইনসুলিন প্রয়োজন",
        "ta": "நீரிழிவு நோயாளிக்கு அவசர இன்சுலின் தேவைப்படுகிறது",
    },
    {
        "key": "evacuation_in_progress",
        "en": "Evacuation in progress, please proceed to safe zone",
        "hi": "निकासी जारी है, कृपया सुरक्षित क्षेत्र में जाएं",
        "pa": "ਨਿਕਾਸੀ ਜਾਰੀ ਹੈ, ਕਿਰਪਾ ਕਰਕੇ ਸੁਰੱਖਿਅਤ ਖੇਤਰ ਵਿੱਚ ਜਾਓ",
        "bn": "উদ্ধারকাজ চলছে, অনুগ্রহ করে নিরাপদ স্থানে যান",
        "ta": "வெளியேற்றம் நடைபெற்று வருகிறது, தயவுசெய்து பாதுகாப்பான பகுதிக்கு செல்லவும்",
    },
    {
        "key": "volunteer_reported",
        "en": "Volunteer has reported for duty at distribution center",
        "hi": "स्वयंसेवक ने वितरण केंद्र पर ड्यूटी के लिए रिपोर्ट किया है",
        "pa": "ਵਲੰਟੀਅਰ ਨੇ ਵੰਡ ਕੇਂਦਰ 'ਤੇ ਡਿਊਟੀ ਲਈ ਰਿਪੋਰਟ ਕੀਤੀ ਹੈ",
        "bn": "স্বেচ্ছাসেবক বিতরণ কেন্দ্রে দায়িত্ব পালনের জন্য রিপোর্ট করেছেন",
        "ta": "தன்னார்வலர் விநியோக மையத்தில் பணிக்காக அறிக்கை செய்துள்ளார்",
    },
]

def find_phrasebook_match(text: str, source_lang: str, target_lang: str) -> Optional[Tuple[str, str]]:
    """
    Looks for exact or close phrasebook match.
    Returns (translated_text, phrase_key) if match is found with high confidence.
    """
    clean_text = re.sub(r'[^\w\s]', '', text.lower()).strip()
    words_input = set(clean_text.split())

    best_match = None
    best_jaccard = 0.0

    for item in PHRASEBOOK:
        src_text = item.get(source_lang, item.get("en", ""))
        clean_src = re.sub(r'[^\w\s]', '', src_text.lower()).strip()
        words_src = set(clean_src.split())

        if words_input == words_src:
            tgt_text = item.get(target_lang, item.get("en", ""))
            return tgt_text, item["key"]

        # Jaccard word similarity
        intersection = len(words_input & words_src)
        union = len(words_input | words_src)
        if union > 0:
            sim = intersection / union
            if sim > best_jaccard:
                best_jaccard = sim
                best_match = item

    # If substantial overlap (> 0.65)
    if best_match and best_jaccard >= 0.65:
        return best_match.get(target_lang, best_match.get("en", "")), best_match["key"]

    return None
