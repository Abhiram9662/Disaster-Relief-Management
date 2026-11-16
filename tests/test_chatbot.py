"""
Unit tests for the chatbot dialogue FSM and FAQ retrieval engine.
"""

from app.chatbot.dialogue_fsm import dialogue_manager
from app.chatbot.faq_engine import faq_engine
from app.models.database import db

def test_faq_retrieval():
    # Camp query
    res_camp = faq_engine.query("Where is Camp Alpha located?", target_lang="en")
    assert res_camp["matched"] is True
    assert "Camp Alpha" in res_camp["answer"]
    assert res_camp["type"] == "camp"

    # Supplies query
    res_sup = faq_engine.query("What supplies are available at Central Depot?", target_lang="en")
    assert res_sup["matched"] is True
    assert res_sup["type"] == "supply"

    # Schedules query
    res_sch = faq_engine.query("When is the water tanker arriving?", target_lang="en")
    assert res_sch["matched"] is True

def test_volunteer_registration_fsm():
    sess_id = "test-fsm-vol-reg"

    # Turn 1: Start registration
    r1 = dialogue_manager.process_message(sess_id, "I want to register as a volunteer", user_role="volunteer")
    assert "full name" in r1["bot_reply_source_lang"].lower()

    # Turn 2: Name
    r2 = dialogue_manager.process_message(sess_id, "Abhiram Ramaprasad")
    assert "skills" in r2["bot_reply_source_lang"].lower()

    # Turn 3: Skills
    r3 = dialogue_manager.process_message(sess_id, "medical and translation")
    assert "languages" in r3["bot_reply_source_lang"].lower()

    # Turn 4: Languages
    r4 = dialogue_manager.process_message(sess_id, "English, Hindi, Punjabi")
    assert "located" in r4["bot_reply_source_lang"].lower()

    # Turn 5: Location
    r5 = dialogue_manager.process_message(sess_id, "31.2240, 75.7708")
    assert "availability" in r5["bot_reply_source_lang"].lower()

    # Turn 6: Availability
    r6 = dialogue_manager.process_message(sess_id, "08:00 to 18:00")
    assert "confirm" in r6["bot_reply_source_lang"].lower()

    # Turn 7: Confirm
    r7 = dialogue_manager.process_message(sess_id, "YES")
    assert "confirmed" in r7["bot_reply_source_lang"].lower()
    assert "vol-" in r7["bot_reply_source_lang"]

def test_need_reporting_fsm():
    sess_id = "test-fsm-need-rep"

    r1 = dialogue_manager.process_message(sess_id, "Report need for disaster relief", user_role="coordinator")
    assert "title" in r1["bot_reply_source_lang"].lower() or "assistance" in r1["bot_reply_source_lang"].lower()

    r2 = dialogue_manager.process_message(sess_id, "Emergency Triage at Sector 2")
    assert "category" in r2["bot_reply_source_lang"].lower()

    r3 = dialogue_manager.process_message(sess_id, "medical")
    assert "volunteers" in r3["bot_reply_source_lang"].lower()

    r4 = dialogue_manager.process_message(sess_id, "2")
    assert "urgency" in r4["bot_reply_source_lang"].lower()

    r5 = dialogue_manager.process_message(sess_id, "4")
    assert "location" in r5["bot_reply_source_lang"].lower()

    r6 = dialogue_manager.process_message(sess_id, "31.2850, 75.6500")
    assert "time window" in r6["bot_reply_source_lang"].lower()

    r7 = dialogue_manager.process_message(sess_id, "09:00 - 15:00")
    assert "confirm" in r7["bot_reply_source_lang"].lower()

    r8 = dialogue_manager.process_message(sess_id, "YES")
    assert "broadcast" in r8["bot_reply_source_lang"].lower()
    assert "need-" in r8["bot_reply_source_lang"]
