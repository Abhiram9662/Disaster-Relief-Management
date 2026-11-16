"""
Safety-critical content preservation check (Section 4.2 & Section 5.2):
Verifies that numbers, units, and place names are preserved across translation.
"""

import re
from typing import List, Tuple, Set

# Script numerals mapping
NUMERAL_MAP = {
    # Devanagari
    '०': '0', '१': '1', '२': '2', '३': '3', '४': '4', '५': '5', '६': '6', '७': '7', '८': '8', '९': '9',
    # Gurmukhi
    '੦': '0', '੧': '1', '੨': '2', '੩': '3', '੪': '4', '੫': '5', '੬': '6', '੭': '7', '੮': '8', '੯': '9',
    # Bengali
    '০': '0', '১': '1', '২': '2', '৩': '3', '৪': '4', '৫': '5', '৬': '6', '৭': '7', '৮': '8', '৯': '9',
    # Tamil
    '௦': '0', '௧': '1', '௨': '2', '௩': '3', '௪': '4', '௫': '5', '௬': '6', '௭': '7', '௮': '8', '௯': '9',
}

UNIT_SYNONYMS = {
    "kg": ["kg", "kilogram", "kilograms", "किग्रा", "किलो", "ਕਿਲੋ", "কেজি", "கிலோ"],
    "liter": ["l", "liter", "liters", "litre", "litres", "लीटर", "ਲਿਟਰ", "লিটার", "லிட்டர்"],
    "packet": ["packet", "packets", "pkt", "pkts", "पैकेट", "ਪੈਕੇਟ", "প্যাকেট", "பாக்கெட்"],
    "box": ["box", "boxes", "डिब्बे", "ਬਕਸੇ", "বাক্স", "பெட்டி"],
    "tablet": ["tablet", "tablets", "tab", "tabs", "गोली", "गोलियां", "ਗੋਲੀਆਂ", "ট্যাবলেট", "மாத்திரை"],
    "km": ["km", "kilometer", "kilometers", "किमी", "ਕਿਲੋਮੀਟਰ", "কিমি", "கிமீ"],
    "people": ["people", "persons", "লোক", "মানুষ", "लोग", "ਵਿਅਕਤੀ", "மக்கள்"],
}

KNOWN_LOCATIONS = [
    "Camp Alpha", "Camp Beta", "Camp Gamma",
    "Sector 1", "Sector 2", "Sector 3", "Sector 4",
    "Phagwara", "Jalandhar", "Ludhiana", "Amritsar",
    "Civil Hospital", "Community Center", "Main Shelter", "Railway Station"
]

LOCATION_TRANSLATIONS = {
    "camp alpha": ["camp alpha", "कैंप अल्फा", "ਕੈਂਪ ਅਲਫਾ", "ক্যাম্প আলফা", "முகாம் ஆல்பா"],
    "camp beta": ["camp beta", "कैंप बीटा", "ਕੈਂਪ ਬੀਟਾ", "ক্যাম্প বিটা", "முகாம் பீட்டா"],
    "camp gamma": ["camp gamma", "कैंप गामा", "ਕੈਂਪ ਗਾਮਾ", "ক্যাম্প গামা", "முகாம் காமா"],
    "sector 1": ["sector 1", "सेक्टर 1", "ਸੈਕਟਰ 1", "সেক্টর 1"],
    "sector 2": ["sector 2", "सेक्टर 2", "ਸੈਕਟਰ 2", "সেক্টর 2"],
    "sector 3": ["sector 3", "सेक्टर 3", "ਸੈਕਟਰ 3", "সেক্টর 3"],
    "sector 4": ["sector 4", "सेक्टर 4", "ਸੈਕਟਰ 4", "সেক্টর 4"],
    "phagwara": ["phagwara", "फगवाड़ा", "ਫਗਵਾੜਾ", "ফাগওয়ারা"],
    "jalandhar": ["jalandhar", "जालंधर", "ਜਲੰਧਰ", "জলন্ধর"],
    "civil hospital": ["civil hospital", "सिविल अस्पताल", "ਸਿਵਲ ਹਸਪਤਾਲ", "সিভিল হাসপাতাল"],
}

def normalize_digits(text: str) -> str:
    """Converts script-specific numerals into standard ASCII digits."""
    res = []
    for ch in text:
        res.append(NUMERAL_MAP.get(ch, ch))
    return "".join(res)

def extract_numbers(text: str) -> Set[str]:
    """Extracts all numeric tokens from text."""
    normalized = normalize_digits(text)
    numbers = re.findall(r'\b\d+(?:\.\d+)?\b', normalized)
    return set(numbers)

def extract_units(text: str) -> Set[str]:
    """Extracts recognized measurement units."""
    lower = text.lower()
    found_units = set()
    for canonical_unit, synonyms in UNIT_SYNONYMS.items():
        for syn in synonyms:
            # Word boundary check
            pattern = rf'(?:\b|\d){re.escape(syn.lower())}(?:\b|\d|[^\w])'
            if re.search(pattern, lower):
                found_units.add(canonical_unit)
                break
    return found_units

def extract_places(text: str) -> Set[str]:
    """Extracts known relief places, camp codes, and sector identifiers."""
    lower = text.lower()
    found_places = set()
    for loc in KNOWN_LOCATIONS:
        if loc.lower() in lower:
            found_places.add(loc)
    return found_places

def verify_critical_preservation(source_text: str, target_text: str) -> Tuple[bool, float, List[str]]:
    """
    Checks if numbers, units, and place names in source_text are preserved in target_text.
    Returns:
    - passed: bool (True if all critical entities preserved)
    - preservation_rate: float in [0.0, 1.0]
    - missing_entities: List[str] of items lost in translation
    """
    src_nums = extract_numbers(source_text)
    tgt_nums = extract_numbers(target_text)

    src_units = extract_units(source_text)
    tgt_units = extract_units(target_text)

    src_places = extract_places(source_text)
    tgt_places = extract_places(target_text)

    missing = []
    total_entities = len(src_nums) + len(src_units) + len(src_places)

    if total_entities == 0:
        return True, 1.0, []

    preserved_count = 0

    for num in src_nums:
        if num in tgt_nums:
            preserved_count += 1
        else:
            missing.append(f"Number '{num}'")

    for unit in src_units:
        if unit in tgt_units:
            preserved_count += 1
        else:
            missing.append(f"Unit '{unit}'")

    for place in src_places:
        place_low = place.lower()
        translations = LOCATION_TRANSLATIONS.get(place_low, [place_low])
        # Check if any translation or original name is present in target text
        if any(tr.lower() in target_text.lower() for tr in translations) or any(p in target_text.lower() for p in place_low.split()):
            preserved_count += 1
        else:
            missing.append(f"Place '{place}'")

    rate = preserved_count / total_entities
    passed = (len(missing) == 0)

    return passed, rate, missing
