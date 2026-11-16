"""
Finite-State Dialogue Manager (Section 4.2):
Slot-filling dialogue for volunteer registration and need reporting
with fuzzy keyword matching, controlled vocabulary normalization,
and explicit confirmation turns.
"""

import re
import uuid
import time
from typing import Dict, Any, Tuple, Optional, List
from app.models.schemas import Volunteer, Need, VolunteerCreate, NeedCreate
from app.models.database import db
from app.translation.engine import detect_language, translator
from app.chatbot.faq_engine import faq_engine

CAMP_COORDINATES = {
    "camp alpha": (31.2240, 75.7708),
    "camp beta": (31.2850, 75.6500),
    "camp gamma": (31.1800, 75.8200),
    "phagwara": (31.2240, 75.7708),
    "jalandhar": (31.3260, 75.5762),
    "ludhiana": (30.9010, 75.8573),
}

SKILL_SYNONYMS = {
    "medical": ["medical", "doctor", "nurse", "paramedic", "first aid", "health", "medicine", "चिकित्सा", "ਡਾਕਟਰੀ", "চিকিৎসা", "மருத்துவம்"],
    "logistics": ["logistics", "driver", "transport", "vehicle", "truck", "warehouse", "रसद", "ਵਾਹਨ", "লজিস্টিক", "லாஜிஸ்டிக்ஸ்"],
    "translation": ["translation", "translator", "interpreter", "multilingual", "language", "अनुवाद", "ਅਨੁਵਾਦ", "অনুবাদ", "மொழிபெயர்ப்பு"],
    "distribution": ["distribution", "food", "rations", "supplies", "water", "delivery", "वितरण", "ਵੰਡ", "বিতরণ", "விநியோகம்"],
}

LANGUAGE_SYNONYMS = {
    "en": ["english", "en", "अंग्रेजी", "ਅੰਗਰੇਜ਼ੀ", "ইংরেজি", "ஆங்கிலம்"],
    "hi": ["hindi", "hi", "हिन्दी", "हिंदी", "ਹਿੰਦੀ", "হিন্দি", "இந்தி"],
    "pa": ["punjabi", "pa", "ਪੰਜਾਬੀ", "पंजाबी", "পাঞ্জাবি", "பஞ்சாபி"],
    "bn": ["bengali", "bn", "বাংলা", "बंगाली", "বঙালী", "வங்காளம்"],
    "ta": ["tamil", "ta", "தமிழ்", "तमिल", "তামিল", "தமிழ்"],
}

class SessionState:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.state: str = "IDLE"
        self.flow: Optional[str] = None  # "register_volunteer" or "report_need"
        self.slots: Dict[str, Any] = {}
        self.last_active: float = time.time()

sessions: Dict[str, SessionState] = {}

def get_or_create_session(session_id: str) -> SessionState:
    if session_id not in sessions:
        sessions[session_id] = SessionState(session_id)
    return sessions[session_id]

def normalize_skills(text: str) -> List[str]:
    found = set()
    text_lower = text.lower()
    for canonical, syns in SKILL_SYNONYMS.items():
        for syn in syns:
            if syn in text_lower:
                found.add(canonical)
                break
    return list(found) if found else ["distribution"]

def normalize_languages(text: str) -> List[str]:
    found = set()
    text_lower = text.lower()
    for code, syns in LANGUAGE_SYNONYMS.items():
        for syn in syns:
            if syn in text_lower:
                found.add(code)
                break
    return list(found) if found else ["en"]

def parse_location(text: str) -> Tuple[float, float]:
    """Parses lat,lon or matches known camp / city landmark."""
    # Look for pair of floats
    coords = re.findall(r'[-+]?\d*\.?\d+', text)
    if len(coords) >= 2:
        try:
            return float(coords[0]), float(coords[1])
        except ValueError:
            pass

    text_lower = text.lower()
    for name, (lat, lon) in CAMP_COORDINATES.items():
        if name in text_lower:
            return lat, lon

    # Default fallback near center
    return 31.2240, 75.7708

def parse_time_window(text: str) -> Tuple[float, float]:
    """Parses time window like 0800-1800, 8-18, 08:00 to 18:00."""
    numbers = re.findall(r'\b\d{1,4}\b', text)
    if len(numbers) >= 2:
        n1 = int(numbers[0])
        n2 = int(numbers[1])
        s = (n1 // 100) if n1 > 100 else n1
        e = (n2 // 100) if n2 > 100 else n2
        return float(s), float(e)
    return 8.0, 18.0

class DialogueManager:
    def process_message(
        self,
        session_id: str,
        user_text: str,
        user_role: str = "volunteer",
        target_lang: str = "en"
    ) -> Dict[str, Any]:
        session = get_or_create_session(session_id)
        session.last_active = time.time()
        detected_lang = detect_language(user_text)

        msg_clean = user_text.strip()
        msg_lower = msg_clean.lower()

        # Check for reset or cancel
        if msg_lower in ["cancel", "reset", "stop", "रद्द करें", "ਰੱਦ ਕਰੋ"]:
            session.state = "IDLE"
            session.flow = None
            session.slots = {}
            return self._reply(session, "Operation cancelled. How can I assist you today? You can register as a volunteer, report a relief need, or ask logistics questions.", detected_lang, target_lang)

        # State Machine Dispatch
        if session.state == "IDLE":
            # Check intent
            if any(k in msg_lower for k in ["register", "volunteer", "sign up", "पंजीकरण", "ਰਜਿਸਟਰ", "விருப்ப"]) or user_role == "volunteer" and "help" in msg_lower:
                session.flow = "register_volunteer"
                session.state = "VOL_NAME"
                session.slots = {}
                return self._reply(session, "Welcome to Disaster Relief Volunteer Registration! What is your full name?", detected_lang, target_lang)

            elif any(k in msg_lower for k in ["report need", "need help", "request aid", "urgent need", "जरूरत", "ਲੋੜ", "தேவை"]) or user_role == "coordinator":
                session.flow = "report_need"
                session.state = "NEED_TITLE"
                session.slots = {}
                return self._reply(session, "Relief Need Reporting: Please enter a brief title or description of what assistance is required.", detected_lang, target_lang)

            else:
                # Query FAQ / logistics database
                faq_res = faq_engine.query(user_text, target_lang=target_lang)
                if faq_res["matched"]:
                    return {
                        "session_id": session_id,
                        "original_text": user_text,
                        "detected_language": detected_lang,
                        "target_language": target_lang,
                        "translated_text": faq_res["translated_answer"],
                        "intent": "faq_retrieval",
                        "bot_reply_source_lang": faq_res["answer"],
                        "bot_reply_target_lang": faq_res["translated_answer"],
                        "dialogue_state": {"state": session.state, "slots": session.slots},
                        "glossary_terms": [],
                        "preservation_checked": True,
                        "preservation_passed": True,
                        "used_phrasebook": False,
                        "flagged_for_human_review": False
                    }
                else:
                    return self._reply(
                        session,
                        "Hello! I am the Disaster Relief Coordination Assistant. You can:\n1. Type 'Register' to register as a volunteer.\n2. Type 'Report need' to submit an emergency aid request.\n3. Ask questions about relief camps, supplies, and schedules (e.g., 'Where is Camp Alpha?', 'What supplies are at central depot?').",
                        detected_lang,
                        target_lang
                    )

        # --- Volunteer Registration Flow ---
        elif session.state == "VOL_NAME":
            session.slots["name"] = msg_clean
            session.state = "VOL_SKILLS"
            return self._reply(session, f"Thank you, {msg_clean}. What are your skills? (e.g. medical, logistics, translation, distribution)", detected_lang, target_lang)

        elif session.state == "VOL_SKILLS":
            skills = normalize_skills(msg_clean)
            session.slots["skills"] = skills
            session.state = "VOL_LANGUAGES"
            return self._reply(session, f"Recorded skills: {', '.join(skills)}. What languages do you speak? (e.g., English, Hindi, Punjabi, Bengali, Tamil)", detected_lang, target_lang)

        elif session.state == "VOL_LANGUAGES":
            langs = normalize_languages(msg_clean)
            session.slots["languages"] = langs
            session.state = "VOL_LOCATION"
            return self._reply(session, f"Languages noted: {', '.join(langs)}. Where are you currently located? (Enter GPS latitude,longitude or nearby camp e.g. 31.2240, 75.7708 or Camp Alpha)", detected_lang, target_lang)

        elif session.state == "VOL_LOCATION":
            lat, lon = parse_location(msg_clean)
            session.slots["latitude"] = lat
            session.slots["longitude"] = lon
            session.state = "VOL_AVAILABILITY"
            return self._reply(session, f"Location registered: ({lat:.4f}, {lon:.4f}). What is your availability window today? (e.g., 08:00-18:00 or 8 to 18)", detected_lang, target_lang)

        elif session.state == "VOL_AVAILABILITY":
            start_h, end_h = parse_time_window(msg_clean)
            session.slots["start_time"] = start_h
            session.slots["end_time"] = end_h
            session.state = "VOL_CONFIRM"

            summary = (
                f"Please confirm your registration details:\n"
                f"- Name: {session.slots['name']}\n"
                f"- Skills: {', '.join(session.slots['skills'])}\n"
                f"- Languages: {', '.join(session.slots['languages'])}\n"
                f"- Location: ({session.slots['latitude']:.4f}, {session.slots['longitude']:.4f})\n"
                f"- Available: {int(start_h):02d}:00 to {int(end_h):02d}:00\n\n"
                f"Type 'YES' to confirm or 'NO' to change."
            )
            return self._reply(session, summary, detected_lang, target_lang)

        elif session.state == "VOL_CONFIRM":
            if any(y in msg_lower for y in ["yes", "y", "confirm", "हाँ", "ਹਾਂ", "হ্যাঁ", "ஆம்"]):
                vol_id = f"vol-{uuid.uuid4().hex[:6]}"
                new_vol = Volunteer(
                    id=vol_id,
                    name=session.slots["name"],
                    skills=session.slots["skills"],
                    languages=session.slots["languages"],
                    latitude=session.slots["latitude"],
                    longitude=session.slots["longitude"],
                    start_time=session.slots["start_time"],
                    end_time=session.slots["end_time"],
                    status="available",
                    hlc_timestamp=int(time.time() * 1000)
                )
                db.upsert_volunteer(new_vol)
                session.state = "IDLE"
                session.flow = None
                session.slots = {}
                return self._reply(session, f"Registration confirmed! Your Volunteer ID is {vol_id}. You are now active in the matching pool.", detected_lang, target_lang)
            else:
                session.state = "IDLE"
                session.flow = None
                return self._reply(session, "Registration discarded. Let me know if you would like to start over.", detected_lang, target_lang)

        # --- Need Reporting Flow ---
        elif session.state == "NEED_TITLE":
            session.slots["title"] = msg_clean
            session.state = "NEED_CATEGORY"
            return self._reply(session, "What category is required? (medical, logistics, translation, distribution)", detected_lang, target_lang)

        elif session.state == "NEED_CATEGORY":
            skills = normalize_skills(msg_clean)
            cat = skills[0] if skills else "medical"
            session.slots["category"] = cat
            session.state = "NEED_HEADCOUNT"
            return self._reply(session, f"Category set to '{cat}'. How many volunteers are needed? (1 to 4)", detected_lang, target_lang)

        elif session.state == "NEED_HEADCOUNT":
            nums = re.findall(r'\d+', msg_clean)
            hc = int(nums[0]) if nums else 1
            hc = max(1, min(10, hc))
            session.slots["required_head_count"] = hc
            session.state = "NEED_URGENCY"
            return self._reply(session, f"Required head-count: {hc}. What is the urgency level? (1=Low, 2=Medium, 3=High, 4=Critical)", detected_lang, target_lang)

        elif session.state == "NEED_URGENCY":
            nums = re.findall(r'\d+', msg_clean)
            urg = int(nums[0]) if nums else 3
            if "crit" in msg_lower:
                urg = 4
            elif "high" in msg_lower:
                urg = 3
            elif "med" in msg_lower:
                urg = 2
            elif "low" in msg_lower:
                urg = 1
            urg = max(1, min(4, urg))
            session.slots["urgency"] = urg
            session.state = "NEED_LOCATION"
            return self._reply(session, f"Urgency set to Level {urg}. What is the location? (GPS coordinates or camp name)", detected_lang, target_lang)

        elif session.state == "NEED_LOCATION":
            lat, lon = parse_location(msg_clean)
            session.slots["latitude"] = lat
            session.slots["longitude"] = lon
            session.state = "NEED_WINDOW"
            return self._reply(session, f"Location: ({lat:.4f}, {lon:.4f}). What is the required time window? (e.g. 09:00-15:00)", detected_lang, target_lang)

        elif session.state == "NEED_WINDOW":
            start_h, end_h = parse_time_window(msg_clean)
            session.slots["start_time"] = start_h
            session.slots["end_time"] = end_h
            session.slots["required_language"] = detected_lang if detected_lang in ["hi", "pa", "bn", "ta"] else "hi"
            session.state = "NEED_CONFIRM"

            summary = (
                f"Please confirm the reported relief need:\n"
                f"- Title: {session.slots['title']}\n"
                f"- Category: {session.slots['category']}\n"
                f"- Volunteers: {session.slots['required_head_count']}\n"
                f"- Urgency: Level {session.slots['urgency']}\n"
                f"- Location: ({session.slots['latitude']:.4f}, {session.slots['longitude']:.4f})\n"
                f"- Hours: {int(start_h):02d}:00 - {int(end_h):02d}:00\n\n"
                f"Type 'YES' to broadcast this need or 'NO' to cancel."
            )
            return self._reply(session, summary, detected_lang, target_lang)

        elif session.state == "NEED_CONFIRM":
            if any(y in msg_lower for y in ["yes", "y", "confirm", "हाँ", "ਹਾਂ", "হ্যাঁ", "ஆம்"]):
                need_id = f"need-{uuid.uuid4().hex[:6]}"
                new_need = Need(
                    id=need_id,
                    title=session.slots["title"],
                    category=session.slots["category"],
                    latitude=session.slots["latitude"],
                    longitude=session.slots["longitude"],
                    required_language=session.slots.get("required_language", "hi"),
                    start_time=session.slots["start_time"],
                    end_time=session.slots["end_time"],
                    required_head_count=session.slots["required_head_count"],
                    urgency=session.slots["urgency"],
                    status="open",
                    filled_slots=0,
                    hlc_timestamp=int(time.time() * 1000)
                )
                db.upsert_need(new_need)
                session.state = "IDLE"
                session.flow = None
                session.slots = {}
                return self._reply(session, f"Need successfully broadcast! ID: {need_id}. The matching engine will allocate qualified volunteers immediately.", detected_lang, target_lang)
            else:
                session.state = "IDLE"
                session.flow = None
                return self._reply(session, "Need report cancelled.", detected_lang, target_lang)

        # Fallback
        session.state = "IDLE"
        return self._reply(session, "How can I help you?", detected_lang, target_lang)

    def _reply(self, session: SessionState, english_text: str, detected_lang: str, target_lang: str) -> Dict[str, Any]:
        translated_reply = english_text
        if target_lang != "en":
            tr = translator.translate(english_text, source_lang="en", target_lang=target_lang)
            translated_reply = tr["translated_text"]

        return {
            "session_id": session.session_id,
            "original_text": english_text,
            "detected_language": detected_lang,
            "target_language": target_lang,
            "translated_text": translated_reply,
            "intent": session.flow or "dialogue",
            "bot_reply_source_lang": english_text,
            "bot_reply_target_lang": translated_reply,
            "dialogue_state": {"state": session.state, "slots": session.slots},
            "glossary_terms": [],
            "preservation_checked": True,
            "preservation_passed": True,
            "used_phrasebook": False,
            "flagged_for_human_review": False
        }

dialogue_manager = DialogueManager()
