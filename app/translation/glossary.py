"""
Relief-domain glossary of constrained terms across Indian languages and English:
Medical supplies, relief goods, camp codes, logistics entities.
"""

from typing import Dict, List, Optional, Tuple

RELIEF_GLOSSARY: Dict[str, Dict[str, str]] = {
    "drinking water": {
        "en": "drinking water",
        "hi": "पीने का पानी",
        "pa": "ਪੀਣ ਵਾਲਾ ਪਾਣੀ",
        "bn": "পানীয় জল",
        "ta": "குடிநீர்",
    },
    "water purification tablets": {
        "en": "water purification tablets",
        "hi": "पानी शुद्धिकरण की गोलियां",
        "pa": "ਪਾਣੀ ਸ਼ੁੱਧੀਕਰਨ ਗੋਲੀਆਂ",
        "bn": "জল বিশুদ্ধকরণ ট্যাবলেট",
        "ta": "நீர் சுத்திகரிப்பு மாத்திரைகள்",
    },
    "ors packets": {
        "en": "ORS packets",
        "hi": "ओआरएस पैकेट",
        "pa": "ਓਆਰਐਸ ਪੈਕੇਟ",
        "bn": "ওআরএস প্যাকেট",
        "ta": "ORS பாக்கெட்டுகள்",
    },
    "paracetamol": {
        "en": "paracetamol",
        "hi": "पैरासिटामोल",
        "pa": "ਪੈਰਾਸੀਟਾਮੋਲ",
        "bn": "প্যারাসিটামল",
        "ta": "பாராசிட்டமால்",
    },
    "first aid kit": {
        "en": "first aid kit",
        "hi": "प्राथमिक चिकित्सा किट",
        "pa": "ਮੁੱਢਲੀ ਸਹਾਇਤਾ ਕਿੱਟ",
        "bn": "প্রাথমিক চিকিৎসা কিট",
        "ta": "முதலுதவி பெட்டி",
    },
    "sterile bandages": {
        "en": "sterile bandages",
        "hi": "रोगाणुरहित पट्टियां",
        "pa": "ਸਟੀਰਾਈਲ ਪੱਟੀਆਂ",
        "bn": "জীবাণুমুক্ত ব্যান্ডেজ",
        "ta": "மலட்டு கட்டுகள்",
    },
    "insulin": {
        "en": "insulin",
        "hi": "इंसुलिन",
        "pa": "ਇਨਸੁਲਿਨ",
        "bn": "ইনসুলিন",
        "ta": "இன்சுலின்",
    },
    "baby food": {
        "en": "baby food",
        "hi": "शिशु आहार",
        "pa": "ਬੱਚਿਆਂ ਦਾ ਖਾਣਾ",
        "bn": "শিশুখাদ্য",
        "ta": "குழந்தை உணவு",
    },
    "dry rations": {
        "en": "dry rations",
        "hi": "सूखा राशन",
        "pa": "ਸੁੱਕਾ ਰਾਸ਼ਨ",
        "bn": "শুকনো রেশন",
        "ta": "உலர் உணவுப் பொருட்கள்",
    },
    "tarpaulin sheets": {
        "en": "tarpaulin sheets",
        "hi": "तिरपाल की चादरें",
        "pa": "ਤਰਪਾਲਾਂ",
        "bn": "ত্রিপল",
        "ta": "தார்பாலின் தாள்கள்",
    },
    "blankets": {
        "en": "blankets",
        "hi": "कंबल",
        "pa": "ਕੰਬਲ",
        "bn": "কম্বল",
        "ta": "போர்வைகள்",
    },
    "camp alpha": {
        "en": "Camp Alpha",
        "hi": "कैंप अल्फा",
        "pa": "ਕੈਂਪ ਅਲਫਾ",
        "bn": "ক্যাম্প আলফা",
        "ta": "முகாம் ஆல்பா",
    },
    "camp beta": {
        "en": "Camp Beta",
        "hi": "कैंप बीटा",
        "pa": "ਕੈਂਪ ਬੀਟਾ",
        "bn": "ক্যাম্প বিটা",
        "ta": "முகாம் பீட்டா",
    },
    "camp gamma": {
        "en": "Camp Gamma",
        "hi": "कैंप गामा",
        "pa": "ਕੈਂਪ ਗਾਮਾ",
        "bn": "ক্যাম্প গামা",
        "ta": "முகாம் காமா",
    },
    "medical volunteer": {
        "en": "medical volunteer",
        "hi": "चिकित्सा स्वयंसेवक",
        "pa": "ਡਾਕਟਰੀ ਵਲੰਟੀਅਰ",
        "bn": "চিকিৎসা স্বেচ্ছাসেবক",
        "ta": "மருத்துவ தன்னார்வலர்",
    },
    "rescue boat": {
        "en": "rescue boat",
        "hi": "बचाव नाव",
        "pa": "ਬਚਾਅ ਕਿਸ਼ਤੀ",
        "bn": "উদ্ধারকারী নৌকা",
        "ta": "மீட்பு படகு",
    },
}

def find_glossary_terms(text: str) -> List[str]:
    """Finds glossary terms present in text."""
    lower_text = text.lower()
    matched = []
    for term, trans_dict in RELIEF_GLOSSARY.items():
        if term in lower_text:
            matched.append(term)
            continue
        # Also check target language representations
        for lang, val in trans_dict.items():
            if val.lower() in lower_text:
                matched.append(term)
                break
    return list(set(matched))

def apply_glossary_constraints(text: str, source_lang: str, target_lang: str) -> Tuple[str, List[str]]:
    """Applies constrained terminology replacement from glossary."""
    matched = []
    res = text
    for term, trans in RELIEF_GLOSSARY.items():
        src_val = trans.get(source_lang, term)
        tgt_val = trans.get(target_lang, term)
        if src_val.lower() in res.lower():
            # Case-insensitive replacement
            import re
            pattern = re.compile(re.escape(src_val), re.IGNORECASE)
            res = pattern.sub(tgt_val, res)
            matched.append(term)
    return res, matched
