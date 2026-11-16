"""
Pydantic data schemas representing the entities described in Section 3 of the paper.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class VolunteerBase(BaseModel):
    name: str = Field(..., description="Volunteer full name")
    skills: List[str] = Field(..., description="Subset of {medical, logistics, translation, distribution}")
    languages: List[str] = Field(..., description="Languages spoken from {en, hi, pa, bn, ta}")
    latitude: float = Field(..., description="Geographical latitude or coordinate")
    longitude: float = Field(..., description="Geographical longitude or coordinate")
    start_time: float = Field(..., description="Start hour of availability [0-24]")
    end_time: float = Field(..., description="End hour of availability [0-24]")

class VolunteerCreate(VolunteerBase):
    pass

class Volunteer(VolunteerBase):
    id: str = Field(..., description="Unique volunteer ID e.g. vol-001")
    status: str = Field(default="available", description="available | assigned | inactive")
    assigned_slot_id: Optional[str] = None
    assigned_need_id: Optional[str] = None
    hlc_timestamp: int = Field(default=0, description="Hybrid Logical Clock timestamp")
    node_id: str = Field(default="camp-node-01")

class NeedBase(BaseModel):
    title: str = Field(..., description="Short title or description of relief need")
    category: str = Field(..., description="medical | logistics | translation | distribution")
    latitude: float = Field(..., description="Geographical latitude or coordinate")
    longitude: float = Field(..., description="Geographical longitude or coordinate")
    required_language: str = Field(default="hi", description="Required language")
    start_time: float = Field(..., description="Need start hour [0-24]")
    end_time: float = Field(..., description="Need end hour [0-24]")
    required_head_count: int = Field(default=1, ge=1, le=10, description="r_n: number of volunteer slots needed")
    urgency: int = Field(default=3, ge=1, le=4, description="u_n in {1,2,3,4}: 1=Low, 2=Medium, 3=High, 4=Critical")

class NeedCreate(NeedBase):
    pass

class Need(NeedBase):
    id: str = Field(..., description="Unique need ID e.g. need-001")
    status: str = Field(default="open", description="open | partially_filled | filled | closed")
    filled_slots: int = Field(default=0)
    hlc_timestamp: int = Field(default=0)
    node_id: str = Field(default="camp-node-01")

class Slot(BaseModel):
    slot_id: str = Field(..., description="Slot ID e.g. need-001_s0")
    need_id: str = Field(..., description="Parent need ID")
    category: str
    latitude: float
    longitude: float
    required_language: str
    start_time: float
    end_time: float
    urgency: int
    assigned_volunteer_id: Optional[str] = None
    is_locked: bool = Field(default=False)

class CompatibilityBreakdown(BaseModel):
    skill_match: float
    proximity: float
    distance_km: float
    availability_coverage: float
    overlap_hours: float
    language_match: float
    raw_compatibility: float
    urgency_multiplier: int
    final_score: float

class AssignmentProposal(BaseModel):
    assignment_id: str
    volunteer_id: str
    volunteer_name: str
    need_id: str
    slot_id: str
    category: str
    score: float
    feasibility: bool = True
    breakdown: Optional[CompatibilityBreakdown] = None
    status: str = Field(default="proposed", description="proposed | confirmed | rejected")

class MatchingRequest(BaseModel):
    algorithm: str = Field(default="proposed", description="proposed | greedy | nearest | random")
    alpha: Optional[float] = None
    beta: Optional[float] = None
    gamma: Optional[float] = None
    eta: Optional[float] = None
    r_max_km: Optional[float] = None

class MatchingResult(BaseModel):
    algorithm: str
    total_volunteers: int
    total_slots: int
    assignments: List[AssignmentProposal]
    qualified_coverage_percent: float
    skill_precision_percent: float
    mean_distance_km: float
    total_utility: float
    runtime_ms: float

class SMSMessageIn(BaseModel):
    sender: str = Field(..., description="Sender phone number")
    message: str = Field(..., description="Raw SMS text")

class SMSMessageOut(BaseModel):
    success: bool
    parsed_type: str
    response_sms: str
    payload_size_bytes: int
    data: Optional[Dict[str, Any]] = None

class ChatRequest(BaseModel):
    session_id: str = Field(default="session-default")
    user_role: str = Field(default="volunteer", description="volunteer | coordinator | community")
    source_language: str = Field(default="en")
    target_language: str = Field(default="hi")
    message: str

class ChatResponse(BaseModel):
    session_id: str
    original_text: str
    detected_language: str
    target_language: str
    translated_text: str
    intent: str
    bot_reply_source_lang: str
    bot_reply_target_lang: str
    dialogue_state: Optional[Dict[str, Any]] = None
    glossary_terms: List[str] = []
    preservation_checked: bool = True
    preservation_passed: bool = True
    used_phrasebook: bool = False
    flagged_for_human_review: bool = False

class SyncDelta(BaseModel):
    node_id: str
    from_hlc: int
    to_hlc: int
    volunteers: List[Volunteer] = []
    needs: List[Need] = []
    assignments: List[AssignmentProposal] = []
    counters: Dict[str, int] = {}
