"""
Conflict-Free Replicated Data Types (CRDT-lite) - Section 4.2:
- Hybrid Logical Clock (HLC)
- Per-field Last-Writer-Wins (LWW) registers
- Grow-only counter (G-Counter) per node for capacity & filled slots
"""

import time
from typing import Dict, Any, Tuple

class HybridLogicalClock:
    """
    Hybrid Logical Clock (HLC) implementation ensuring monotonic time
    across distributed camp nodes and intermittent offline links.
    """
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.logical_time: int = 0
        self.counter: int = 0

    def now(self) -> int:
        pt = int(time.time() * 1000)
        if pt > self.logical_time:
            self.logical_time = pt
            self.counter = 0
        else:
            self.counter += 1
        # Encode physical time (high 48 bits) + counter (low 16 bits)
        return (self.logical_time << 16) | (self.counter & 0xFFFF)

    def update(self, remote_hlc: int) -> int:
        pt = int(time.time() * 1000)
        remote_pt = remote_hlc >> 16
        remote_cnt = remote_hlc & 0xFFFF

        max_pt = max(pt, self.logical_time, remote_pt)
        if max_pt == self.logical_time == remote_pt:
            self.counter = max(self.counter, remote_cnt) + 1
        elif max_pt == self.logical_time:
            self.counter += 1
        elif max_pt == remote_pt:
            self.counter = remote_cnt + 1
        else:
            self.counter = 0
        self.logical_time = max_pt
        return (self.logical_time << 16) | (self.counter & 0xFFFF)

class GrowOnlyCounter:
    """Grow-only counter where each node maintains its own independent slot count."""
    def __init__(self):
        self.node_counts: Dict[str, int] = {}

    def increment(self, node_id: str, delta: int = 1):
        self.node_counts[node_id] = self.node_counts.get(node_id, 0) + delta

    def value(self) -> int:
        return sum(self.node_counts.values())

    def merge(self, remote_counts: Dict[str, int]):
        for node_id, count in remote_counts.items():
            self.node_counts[node_id] = max(self.node_counts.get(node_id, 0), count)
