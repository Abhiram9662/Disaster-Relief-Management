"""
Compact SMS Grammar Gateway (Section 4.2 & Table 3):
Parses feature phone SMS messages into structured records and generates concise responses.
Standard registration example:
REG|Manya S|MED,TRN|hi,pa,en|31.2240,75.7708|0800-1800 (54 characters)
"""

import time
import uuid
from typing import Dict, Any, Tuple, Optional
from app.models.schemas import Volunteer, Need, SMSMessageIn, SMSMessageOut
from app.models.database import db
from app.chatbot.dialogue_fsm import parse_location, parse_time_window

SKILL_ABBREVIATIONS = {
    "MED": "medical",
    "LOG": "logistics",
    "TRN": "translation",
    "DST": "distribution",
    "MEDICAL": "medical",
    "LOGISTICS": "logistics",
    "TRANSLATION": "translation",
    "DISTRIBUTION": "distribution"
}

REVERSE_SKILLS = {
    "medical": "MED",
    "logistics": "LOG",
    "translation": "TRN",
    "distribution": "DST"
}

class SMSGateway:
    def process_sms(self, sms_in: SMSMessageIn) -> SMSMessageOut:
        raw = sms_in.message.strip()
        payload_size = len(raw.encode('utf-8'))
        parts = [p.strip() for p in raw.split("|")]
        cmd = parts[0].upper() if parts else ""

        if cmd == "REG":
            return self._handle_registration(parts, sms_in.sender, payload_size)
        elif cmd == "NEED":
            return self._handle_need(parts, sms_in.sender, payload_size)
        elif cmd == "STATUS":
            return self._handle_status(parts, payload_size)
        elif cmd == "CONFIRM":
            return self._handle_confirm(parts, payload_size)
        elif cmd in ["HELP", "INFO"]:
            return SMSMessageOut(
                success=True,
                parsed_type="HELP",
                response_sms="Syntax: REG|Name|MED,TRN|hi,en|lat,lon|0800-1800 OR NEED|Title|MED|1|3|lat,lon|0900-1500|hi OR STATUS|ID",
                payload_size_bytes=payload_size,
                data=None
            )
        else:
            return SMSMessageOut(
                success=False,
                parsed_type="UNKNOWN",
                response_sms="Invalid command. Send HELP for valid SMS syntax.",
                payload_size_bytes=payload_size,
                data=None
            )

    def _handle_registration(self, parts: list[str], sender: str, payload_size: int) -> SMSMessageOut:
        # REG|name|skills|languages|lat,lon|window
        # e.g., REG|Manya S|MED,TRN|hi,pa,en|31.2240,75.7708|0800-1800
        if len(parts) < 6:
            return SMSMessageOut(
                success=False,
                parsed_type="REG",
                response_sms="ERR: Incomplete REG format. Use: REG|Name|Skills|Langs|Lat,Lon|Start-End",
                payload_size_bytes=payload_size
            )

        name = parts[1]
        skills_raw = parts[2].split(",")
        skills = [SKILL_ABBREVIATIONS.get(s.strip().upper(), s.strip().lower()) for s in skills_raw if s.strip()]
        if not skills:
            skills = ["distribution"]

        languages = [l.strip().lower() for l in parts[3].split(",") if l.strip()]
        if not languages:
            languages = ["en"]

        lat, lon = parse_location(parts[4])
        start_h, end_h = parse_time_window(parts[5])

        vol_id = f"vol-{uuid.uuid4().hex[:6]}"
        vol = Volunteer(
            id=vol_id,
            name=name,
            skills=skills,
            languages=languages,
            latitude=lat,
            longitude=lon,
            start_time=start_h,
            end_time=end_h,
            status="available",
            hlc_timestamp=int(time.time() * 1000)
        )
        db.upsert_volunteer(vol)

        reply = f"OK REG:{vol_id} {name} Sk:{','.join([REVERSE_SKILLS.get(k, k) for k in skills])} Ready"
        return SMSMessageOut(
            success=True,
            parsed_type="REG",
            response_sms=reply,
            payload_size_bytes=payload_size,
            data=vol.model_dump()
        )

    def _handle_need(self, parts: list[str], sender: str, payload_size: int) -> SMSMessageOut:
        # NEED|title|category|count|urgency|lat,lon|window|lang
        # e.g., NEED|Water Shortage|DST|2|4|31.2240,75.7708|0800-1800|hi
        if len(parts) < 7:
            return SMSMessageOut(
                success=False,
                parsed_type="NEED",
                response_sms="ERR: Incomplete NEED. Format: NEED|Title|Cat|Count|Urg|Lat,Lon|Window|[Lang]",
                payload_size_bytes=payload_size
            )

        title = parts[1]
        cat = SKILL_ABBREVIATIONS.get(parts[2].strip().upper(), parts[2].strip().lower())
        count = int(parts[3]) if parts[3].isdigit() else 1
        urgency = int(parts[4]) if parts[4].isdigit() else 3
        urgency = max(1, min(4, urgency))
        lat, lon = parse_location(parts[5])
        start_h, end_h = parse_time_window(parts[6])
        req_lang = parts[7].strip().lower() if len(parts) > 7 and parts[7].strip() else "hi"

        need_id = f"need-{uuid.uuid4().hex[:6]}"
        need = Need(
            id=need_id,
            title=title,
            category=cat,
            latitude=lat,
            longitude=lon,
            required_language=req_lang,
            start_time=start_h,
            end_time=end_h,
            required_head_count=count,
            urgency=urgency,
            status="open",
            filled_slots=0,
            hlc_timestamp=int(time.time() * 1000)
        )
        db.upsert_need(need)

        reply = f"OK NEED:{need_id} Cat:{cat} Req:{count} Urg:{urgency} Broadcasted"
        return SMSMessageOut(
            success=True,
            parsed_type="NEED",
            response_sms=reply,
            payload_size_bytes=payload_size,
            data=need.model_dump()
        )

    def _handle_status(self, parts: list[str], payload_size: int) -> SMSMessageOut:
        if len(parts) < 2:
            return SMSMessageOut(
                success=False,
                parsed_type="STATUS",
                response_sms="ERR: Specify ID: STATUS|vol-xxx OR STATUS|need-xxx",
                payload_size_bytes=payload_size
            )

        target_id = parts[1].strip()
        if target_id.startswith("vol-"):
            vol = db.get_volunteer(target_id)
            if not vol:
                return SMSMessageOut(success=False, parsed_type="STATUS", response_sms="ERR: Vol not found", payload_size_bytes=payload_size)
            reply = f"VOL:{vol.id} Status:{vol.status} Slot:{vol.assigned_slot_id or 'None'}"
            return SMSMessageOut(success=True, parsed_type="STATUS", response_sms=reply, payload_size_bytes=payload_size, data=vol.model_dump())
        else:
            need = db.get_need(target_id)
            if not need:
                return SMSMessageOut(success=False, parsed_type="STATUS", response_sms="ERR: Need not found", payload_size_bytes=payload_size)
            reply = f"NEED:{need.id} Status:{need.status} Filled:{need.filled_slots}/{need.required_head_count}"
            return SMSMessageOut(success=True, parsed_type="STATUS", response_sms=reply, payload_size_bytes=payload_size, data=need.model_dump())

    def _handle_confirm(self, parts: list[str], payload_size: int) -> SMSMessageOut:
        # CONFIRM|assignment_id
        if len(parts) < 2:
            return SMSMessageOut(success=False, parsed_type="CONFIRM", response_sms="ERR: CONFIRM|assignment_id", payload_size_bytes=payload_size)
        asgn_id = parts[1].strip()
        success = db.confirm_assignment(asgn_id, hlc=int(time.time() * 1000))
        if success:
            return SMSMessageOut(success=True, parsed_type="CONFIRM", response_sms=f"OK ASSIGN:{asgn_id} Locked", payload_size_bytes=payload_size)
        return SMSMessageOut(success=False, parsed_type="CONFIRM", response_sms=f"ERR: ASSIGN:{asgn_id} Failed", payload_size_bytes=payload_size)

sms_gateway = SMSGateway()
