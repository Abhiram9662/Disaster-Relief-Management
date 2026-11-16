"""
Unit tests for the Hybrid Logical Clock, CRDT state, and Delta Synchronization Protocol.
"""

from app.sync.crdt_state import HybridLogicalClock, GrowOnlyCounter
from app.sync.delta_protocol import delta_protocol
from app.models.schemas import Volunteer
from app.models.database import db

def test_hybrid_logical_clock_monotonicity():
    hlc_node1 = HybridLogicalClock("node-1")
    t1 = hlc_node1.now()
    t2 = hlc_node1.now()
    assert t2 >= t1

    hlc_node2 = HybridLogicalClock("node-2")
    t3 = hlc_node2.update(t2)
    assert t3 >= t2

def test_grow_only_counter():
    counter = GrowOnlyCounter()
    counter.increment("camp-01", 3)
    counter.increment("camp-02", 2)
    assert counter.value() == 5

    # Merge remote counts
    counter.merge({"camp-01": 5, "camp-02": 1, "camp-03": 4})
    # max(3,5) + max(2,1) + 4 = 5 + 2 + 4 = 11
    assert counter.value() == 11

def test_delta_sync_export_and_compression():
    # Insert a dummy record
    vol = Volunteer(
        id="vol-sync-test",
        name="Sync Test Vol",
        skills=["logistics"],
        languages=["en"],
        latitude=31.22,
        longitude=75.77,
        start_time=8.0,
        end_time=18.0,
        hlc_timestamp=1700000000001
    )
    db.upsert_volunteer(vol)

    res = delta_protocol.export_delta(from_hlc=0)
    assert "delta" in res
    assert res["raw_size_bytes"] > 0
    assert res["compressed_size_bytes"] > 0
    # Compression must yield a positive ratio
    assert res["compression_ratio"] >= 1.0

def test_low_bandwidth_benchmarks_table3():
    bench = delta_protocol.benchmark_payload_sizes(num_needs=100, num_changed=10)
    assert bench["sms_registration_bytes"] == 54  # Exactly matching Section 6.1 & Table 3!
    assert bench["full_sync_raw_bytes"] > bench["full_sync_compressed_bytes"]
    assert bench["delta_sync_raw_bytes"] > bench["delta_sync_compressed_bytes"]
    assert bench["delta_sync_raw_bytes"] < bench["full_sync_raw_bytes"]
