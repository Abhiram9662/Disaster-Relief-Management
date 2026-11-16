"""
Unit tests for the compact SMS Grammar parser and gateway responses.
"""

from app.chatbot.sms_gateway import sms_gateway
from app.models.schemas import SMSMessageIn

def test_sms_volunteer_registration_exact_54_bytes():
    # Exact example from Section 6.1 and Table 3:
    # "REG|Manya S|MED,TRN|hi,pa,en|31.2240,75.7708|0800-1800"
    sms_text = "REG|Manya S|MED,TRN|hi,pa,en|31.2240,75.7708|0800-1800"
    assert len(sms_text) == 54
    assert len(sms_text.encode('utf-8')) == 54

    sms_in = SMSMessageIn(sender="+919876543210", message=sms_text)
    out = sms_gateway.process_sms(sms_in)

    assert out.success is True
    assert out.parsed_type == "REG"
    assert out.payload_size_bytes == 54
    assert "OK REG:" in out.response_sms
    assert "Manya S" in out.response_sms

def test_sms_need_reporting():
    sms_text = "NEED|Water Shortage|DST|2|4|31.2240,75.7708|0800-1800|hi"
    sms_in = SMSMessageIn(sender="+919876543210", message=sms_text)
    out = sms_gateway.process_sms(sms_in)

    assert out.success is True
    assert out.parsed_type == "NEED"
    assert "OK NEED:" in out.response_sms
    assert "Urg:4" in out.response_sms

def test_sms_status_query():
    # Query non-existent ID
    sms_in = SMSMessageIn(sender="+919876543210", message="STATUS|vol-nonexistent")
    out = sms_gateway.process_sms(sms_in)
    assert out.success is False
    assert "ERR:" in out.response_sms
