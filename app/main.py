"""
FastAPI Backend Application (Section 4.3):
Multilingual Coordination Chatbot for Disaster Relief NGOs and Volunteers
Project ID: CSEAIML2026-P22
Authors: Gandam Ram Charan Tej-12408114, Manya Sharma-12407126, Abhiram Ramaprasad-12407909
Institution: Lovely Professional University, Phagwara, Punjab, India
"""

import time
import uuid
from typing import List, Optional, Dict, Any
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from app.config import config, DB_PATH
from app.models.schemas import (
    Volunteer, VolunteerCreate,
    Need, NeedCreate,
    AssignmentProposal,
    MatchingRequest, MatchingResult,
    SMSMessageIn, SMSMessageOut,
    ChatRequest, ChatResponse,
    SyncDelta
)
from app.models.database import db
from app.matching.matchers import (
    run_proposed_matching,
    run_greedy_matching,
    run_nearest_first_matching,
    run_random_matching
)
from app.matching.incremental import recompute_incremental_matching, confirm_and_lock_assignment
from app.translation.engine import translator, detect_language
from app.translation.glossary import RELIEF_GLOSSARY
from app.translation.phrasebook import PHRASEBOOK
from app.chatbot.dialogue_fsm import dialogue_manager
from app.chatbot.faq_engine import faq_engine
from app.chatbot.sms_gateway import sms_gateway
from app.sync.delta_protocol import delta_protocol
from app.sync.crdt_state import HybridLogicalClock
from app.simulation.benchmark_runner import (
    run_matching_benchmark,
    run_low_bandwidth_benchmark,
    run_translation_benchmark
)
from app.simulation.scenario_generator import generate_scenario

app = FastAPI(
    title="Multilingual Disaster Relief Coordination Platform",
    description="Skill- and Proximity-Aware Matching, Real-Time Translation, and Offline-Friendly Operation (CSEAIML2026-P22)",
    version="1.0.0"
)

# Enable CORS for local-first testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

hlc = HybridLogicalClock(config.node_id)

# --- System & Info ---

@app.get("/api/info")
def get_info():
    return {
        "title": "Multilingual Coordination Chatbot for Disaster Relief NGOs and Volunteers",
        "project_id": "CSEAIML2026-P22",
        "authors": [
            "Gandam Ram Charan Tej (12408114)",
            "Manya Sharma (12407126)",
            "Abhiram Ramaprasad (12407909)"
        ],
        "institution": "Lovely Professional University, Phagwara, Punjab, India",
        "node_id": config.node_id,
        "database": str(DB_PATH),
        "status": "online",
        "current_hlc": hlc.now(),
        "default_weights": {
            "alpha_skill": config.alpha,
            "beta_proximity": config.beta,
            "gamma_availability": config.gamma,
            "eta_language": config.eta,
            "r_max_km": config.r_max_km,
            "delta_km": config.delta_km
        }
    }

# --- Volunteer Endpoints ---

@app.post("/api/volunteers", response_model=Volunteer)
def create_volunteer(payload: VolunteerCreate):
    vol_id = f"vol-{uuid.uuid4().hex[:6]}"
    vol = Volunteer(
        id=vol_id,
        name=payload.name,
        skills=payload.skills,
        languages=payload.languages,
        latitude=payload.latitude,
        longitude=payload.longitude,
        start_time=payload.start_time,
        end_time=payload.end_time,
        status="available",
        hlc_timestamp=hlc.now(),
        node_id=config.node_id
    )
    db.upsert_volunteer(vol)
    return vol

@app.get("/api/volunteers", response_model=List[Volunteer])
def list_volunteers(status: Optional[str] = None):
    return db.list_volunteers(status=status)

@app.get("/api/volunteers/{vol_id}", response_model=Volunteer)
def get_volunteer(vol_id: str):
    vol = db.get_volunteer(vol_id)
    if not vol:
        raise HTTPException(status_code=404, detail="Volunteer not found")
    return vol

# --- Need Endpoints ---

@app.post("/api/needs", response_model=Need)
def create_need(payload: NeedCreate):
    need_id = f"need-{uuid.uuid4().hex[:6]}"
    need = Need(
        id=need_id,
        title=payload.title,
        category=payload.category,
        latitude=payload.latitude,
        longitude=payload.longitude,
        required_language=payload.required_language,
        start_time=payload.start_time,
        end_time=payload.end_time,
        required_head_count=payload.required_head_count,
        urgency=payload.urgency,
        status="open",
        filled_slots=0,
        hlc_timestamp=hlc.now(),
        node_id=config.node_id
    )
    db.upsert_need(need)
    return need

@app.get("/api/needs", response_model=List[Need])
def list_needs(status: Optional[str] = None):
    return db.list_needs(status=status)

@app.get("/api/needs/{need_id}", response_model=Need)
def get_need(need_id: str):
    need = db.get_need(need_id)
    if not need:
        raise HTTPException(status_code=404, detail="Need not found")
    return need

# --- Matching Endpoints ---

@app.post("/api/match", response_model=MatchingResult)
def run_matching(req: MatchingRequest):
    volunteers = db.list_volunteers()
    needs = db.list_needs()

    algo = req.algorithm.lower()
    if algo == "proposed":
        res = run_proposed_matching(volunteers, needs, req.alpha, req.beta, req.gamma, req.eta, req.r_max_km)
    elif algo == "greedy":
        res = run_greedy_matching(volunteers, needs, req.alpha, req.beta, req.gamma, req.eta, req.r_max_km)
    elif algo == "nearest":
        res = run_nearest_first_matching(volunteers, needs)
    elif algo == "random":
        res = run_random_matching(volunteers, needs)
    else:
        res = run_proposed_matching(volunteers, needs, req.alpha, req.beta, req.gamma, req.eta, req.r_max_km)

    # Save generated proposals to database
    for p in res.assignments:
        db.save_assignment(p, node_id=config.node_id, hlc=hlc.now())

    return res

@app.get("/api/assignments", response_model=List[AssignmentProposal])
def list_assignments(status: Optional[str] = None):
    return db.list_assignments(status=status)

@app.post("/api/assignments/{assignment_id}/confirm")
def confirm_assignment(assignment_id: str):
    success = confirm_and_lock_assignment(assignment_id, hlc=hlc.now())
    if not success:
        raise HTTPException(status_code=400, detail="Assignment confirmation failed or assignment ID not found.")
    return {"status": "confirmed", "assignment_id": assignment_id}

# --- Translation Endpoints ---

@app.post("/api/translate")
def translate_message(
    text: str = Body(..., embed=True),
    source_lang: Optional[str] = Body("auto", embed=True),
    target_lang: str = Body("hi", embed=True)
):
    return translator.translate(text, source_lang=source_lang, target_lang=target_lang)

@app.get("/api/glossary")
def get_glossary():
    return RELIEF_GLOSSARY

@app.get("/api/phrasebook")
def get_phrasebook():
    return PHRASEBOOK

# --- Chatbot & FAQ Endpoints ---

@app.post("/api/chat", response_model=ChatResponse)
def chat_message(req: ChatRequest):
    res = dialogue_manager.process_message(
        session_id=req.session_id,
        user_text=req.message,
        user_role=req.user_role,
        target_lang=req.target_language
    )
    return ChatResponse(**res)

@app.post("/api/faq")
def query_faq(query: str = Body(..., embed=True), target_lang: str = Body("en", embed=True)):
    return faq_engine.query(query, target_lang=target_lang)

# --- SMS Gateway Endpoints ---

@app.post("/api/sms", response_model=SMSMessageOut)
def receive_sms(sms_in: SMSMessageIn):
    return sms_gateway.process_sms(sms_in)

# --- Low-Bandwidth Synchronization Endpoints ---

@app.get("/api/sync/delta")
def export_sync_delta(from_hlc: int = Query(0)):
    return delta_protocol.export_delta(from_hlc=from_hlc)

@app.post("/api/sync/delta")
def import_sync_delta(delta_payload: Dict[str, Any] = Body(...)):
    return delta_protocol.import_delta(delta_payload)

@app.get("/api/sync/benchmark")
def low_bandwidth_benchmark():
    return run_low_bandwidth_benchmark()

# --- Dashboard Summary & Map Data ---

@app.get("/api/dashboard/summary")
def get_dashboard_summary():
    vols = db.list_volunteers()
    needs = db.list_needs()
    asgns = db.list_assignments()

    categories = ["medical", "logistics", "translation", "distribution"]
    cat_summary = {}
    for c in categories:
        cat_summary[c] = {
            "volunteers_available": sum(1 for v in vols if c in v.skills and v.status == "available"),
            "needs_open": sum(1 for n in needs if n.category == c and n.status == "open"),
            "slots_required": sum(n.required_head_count for n in needs if n.category == c),
            "slots_filled": sum(n.filled_slots for n in needs if n.category == c)
        }

    total_slots = sum(n.required_head_count for n in needs)
    total_filled = sum(n.filled_slots for n in needs)

    return {
        "node_id": config.node_id,
        "total_volunteers": len(vols),
        "available_volunteers": sum(1 for v in vols if v.status == "available"),
        "assigned_volunteers": sum(1 for v in vols if v.status == "assigned"),
        "total_needs": len(needs),
        "open_needs": sum(1 for n in needs if n.status == "open"),
        "filled_needs": sum(1 for n in needs if n.status == "filled"),
        "total_slots": total_slots,
        "filled_slots": total_filled,
        "coverage_rate": round((total_filled / max(1, total_slots)) * 100.0, 1),
        "critical_needs_count": sum(1 for n in needs if n.urgency == 4 and n.status != "filled"),
        "category_breakdown": cat_summary,
        "confirmed_assignments": sum(1 for a in asgns if a.status == "confirmed"),
        "proposed_assignments": sum(1 for a in asgns if a.status == "proposed")
    }

@app.get("/api/dashboard/map")
def get_map_data():
    vols = db.list_volunteers()
    needs = db.list_needs()
    camps = faq_engine.camps
    supplies = faq_engine.supplies

    return {
        "volunteers": [
            {
                "id": v.id, "name": v.name, "skills": v.skills, "status": v.status,
                "lat": v.latitude, "lon": v.longitude, "hours": f"{v.start_time}-{v.end_time}"
            } for v in vols
        ],
        "needs": [
            {
                "id": n.id, "title": n.title, "category": n.category, "urgency": n.urgency,
                "status": n.status, "slots": f"{n.filled_slots}/{n.required_head_count}",
                "lat": n.latitude, "lon": n.longitude
            } for n in needs
        ],
        "camps": [
            {
                "id": c["camp_id"], "name": c["name"], "lat": c["latitude"], "lon": c["longitude"],
                "occupancy": f"{c['current_occupancy']}/{c['capacity']}"
            } for c in camps
        ],
        "supplies": [
            {
                "id": s["point_id"], "name": s["name"], "lat": s["latitude"], "lon": s["longitude"]
            } for s in supplies
        ]
    }

# --- Simulation Seed & Full Evaluation ---

@app.post("/api/simulation/seed-demo")
def seed_demo_data(scenario: str = Query("S1", enum=["S1", "S2", "S3"])):
    """Populates database with synthetic scenario data for interactive demonstration."""
    db.clear_all()
    vols, needs = generate_scenario(scenario, seed=42)
    for v in vols:
        db.upsert_volunteer(v)
    for n in needs:
        db.upsert_need(n)
    return {
        "status": "seeded",
        "scenario": scenario,
        "volunteers_count": len(vols),
        "needs_count": len(needs),
        "total_slots": sum(n.required_head_count for n in needs)
    }

@app.get("/api/simulation/run-benchmarks")
def run_all_benchmarks(seeds: int = Query(5, description="Number of seeds (use 30 for full paper reproduction)")):
    """Executes matching benchmark, low bandwidth analysis, and translation evaluation."""
    matching_res = run_matching_benchmark(num_seeds=seeds)
    bandwidth_res = run_low_bandwidth_benchmark()
    trans_res = run_translation_benchmark()

    return {
        "table2_matching": matching_res["table2"],
        "table3_bandwidth": bandwidth_res,
        "table4_translation": trans_res
    }

# --- Serve Web / PWA Client ---

web_dir = Path(__file__).resolve().parent / "web"
app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")

@app.get("/")
def serve_dashboard():
    index_file = web_dir / "index.html"
    return FileResponse(str(index_file))

@app.get("/sw.js")
def serve_service_worker():
    sw_file = web_dir / "sw.js"
    return FileResponse(str(sw_file), media_type="application/javascript")

@app.get("/manifest.json")
def serve_manifest():
    mf_file = web_dir / "manifest.json"
    return FileResponse(str(mf_file), media_type="application/manifest+json")
