"""
Delta Synchronization Protocol & Low-Bandwidth Compression (Section 4.2, 4.3, Table 3):
- Delta extraction since last acknowledged HLC
- zlib level 9 payload compression
- Merge protocol with conflict resolution
"""

import json
import zlib
from typing import Dict, Any, List, Tuple
from app.models.database import db
from app.models.schemas import Volunteer, Need, AssignmentProposal, SyncDelta
from app.sync.crdt_state import HybridLogicalClock
from app.config import config

hlc = HybridLogicalClock(config.node_id)

class DeltaSyncProtocol:
    def export_delta(self, from_hlc: int = 0) -> Dict[str, Any]:
        """Exports changes that occurred after from_hlc."""
        current_hlc = hlc.now()
        logs = db.get_sync_deltas(from_hlc)

        vols = []
        needs = []
        assignments = []

        seen_vols = set()
        seen_needs = set()
        seen_asgns = set()

        for log in reversed(logs):
            entity_type = log["entity_type"]
            entity_id = log["entity_id"]
            payload = json.loads(log["payload"])

            if entity_type == "volunteer" and entity_id not in seen_vols:
                seen_vols.add(entity_id)
                vols.append(payload)
            elif entity_type == "need" and entity_id not in seen_needs:
                seen_needs.add(entity_id)
                needs.append(payload)
            elif entity_type == "assignment" and entity_id not in seen_asgns:
                seen_asgns.add(entity_id)
                assignments.append(payload)

        # Get counters
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT counter_key, node_id, value FROM crdt_counters WHERE hlc_timestamp > ?", (from_hlc,))
            counter_rows = cursor.fetchall()
            counters = {f"{r['counter_key']}@{r['node_id']}": r["value"] for r in counter_rows}

        delta_obj = {
            "node_id": config.node_id,
            "from_hlc": from_hlc,
            "to_hlc": current_hlc,
            "volunteers": vols,
            "needs": needs,
            "assignments": assignments,
            "counters": counters
        }

        raw_json = json.dumps(delta_obj, separators=(',', ':'))
        raw_bytes = raw_json.encode('utf-8')
        compressed_bytes = zlib.compress(raw_bytes, level=9)

        return {
            "delta": delta_obj,
            "raw_size_bytes": len(raw_bytes),
            "compressed_size_bytes": len(compressed_bytes),
            "compression_ratio": round(len(raw_bytes) / max(1, len(compressed_bytes)), 2)
        }

    def import_delta(self, delta_obj: Dict[str, Any]) -> Dict[str, Any]:
        """Applies incoming delta updates using Last-Writer-Wins."""
        remote_to_hlc = delta_obj.get("to_hlc", 0)
        hlc.update(remote_to_hlc)

        applied_vols = 0
        applied_needs = 0
        applied_asgns = 0

        for v_dict in delta_obj.get("volunteers", []):
            try:
                v = Volunteer(**v_dict)
                if db.upsert_volunteer(v):
                    applied_vols += 1
            except Exception:
                pass

        for n_dict in delta_obj.get("needs", []):
            try:
                n = Need(**n_dict)
                if db.upsert_need(n):
                    applied_needs += 1
            except Exception:
                pass

        for a_dict in delta_obj.get("assignments", []):
            try:
                a = AssignmentProposal(**a_dict)
                db.save_assignment(a, node_id=delta_obj.get("node_id", "remote"), hlc=remote_to_hlc)
                applied_asgns += 1
            except Exception:
                pass

        # Merge counters
        with db.get_connection() as conn:
            cursor = conn.cursor()
            for key_node, val in delta_obj.get("counters", {}).items():
                if "@" in key_node:
                    ckey, nid = key_node.split("@", 1)
                    cursor.execute("""
                    INSERT INTO crdt_counters (counter_key, node_id, value, hlc_timestamp)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(counter_key, node_id) DO UPDATE SET
                        value = MAX(crdt_counters.value, excluded.value),
                        hlc_timestamp = excluded.hlc_timestamp;
                    """, (ckey, nid, val, remote_to_hlc))
            conn.commit()

        return {
            "status": "success",
            "applied_volunteers": applied_vols,
            "applied_needs": applied_needs,
            "applied_assignments": applied_asgns,
            "current_node_hlc": hlc.now()
        }

    def benchmark_payload_sizes(self, num_needs: int = 100, num_changed: int = 10) -> Dict[str, Any]:
        """
        Measures payload sizes corresponding directly to Table 3 in the paper.
        """
        # 1. SMS registration payload: "REG|Manya S|MED,TRN|hi,pa,en|31.2240,75.7708|0800-1800"
        sms_text = "REG|Manya S|MED,TRN|hi,pa,en|31.2240,75.7708|0800-1800"
        sms_raw_size = len(sms_text.encode('utf-8'))

        # 2. Full sync of 100 need records (JSON)
        sample_needs = []
        for i in range(num_needs):
            sample_needs.append({
                "id": f"need-{i:03d}",
                "title": f"Disaster Relief Need #{i} - Emergency Shelter Distribution",
                "category": ["medical", "logistics", "translation", "distribution"][i % 4],
                "latitude": round(31.2240 + (i % 10) * 0.01, 4),
                "longitude": round(75.7708 + (i // 10) * 0.01, 4),
                "required_language": ["hi", "pa", "en", "bn", "ta"][i % 5],
                "start_time": 8.0,
                "end_time": 18.0,
                "required_head_count": (i % 3) + 1,
                "urgency": (i % 4) + 1,
                "status": "open",
                "filled_slots": 0,
                "hlc_timestamp": 1700000000000 + i,
                "node_id": "camp-node-01"
            })

        full_json = json.dumps(sample_needs, separators=(',', ':')).encode('utf-8')
        full_compressed = zlib.compress(full_json, level=9)

        # 3. Delta sync of 10 changed records
        delta_needs = sample_needs[:num_changed]
        delta_json = json.dumps(delta_needs, separators=(',', ':')).encode('utf-8')
        delta_compressed = zlib.compress(delta_json, level=9)

        return {
            "sms_registration_bytes": sms_raw_size,
            "full_sync_raw_bytes": len(full_json),
            "full_sync_compressed_bytes": len(full_compressed),
            "delta_sync_raw_bytes": len(delta_json),
            "delta_sync_compressed_bytes": len(delta_compressed)
        }

delta_protocol = DeltaSyncProtocol()
