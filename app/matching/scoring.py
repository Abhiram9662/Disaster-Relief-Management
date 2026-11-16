"""
Compatibility score and feasibility constraints as defined in Section 3 and 4.2:
- Skill match S in [0, 1]
- Proximity P = exp(-d / delta) with delta = 10 km
- Availability coverage A = min(1, overlap / need_duration)
- Language compatibility L in {0, 1}
- Urgency-weighted compatibility score:
  w(v,n) = u_n * (alpha*S + beta*P + gamma*A + eta*L)
  alpha=0.4, beta=0.3, gamma=0.2, eta=0.1
"""

import math
from typing import Tuple, List, Optional
from app.config import config
from app.models.schemas import Volunteer, Need, Slot, CompatibilityBreakdown

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes distance in km.
    If coordinates are within [0, 50], treats them as direct Euclidean km coordinates (simulation mode).
    Otherwise, computes standard Haversine distance from geographical lat/long.
    """
    if 0.0 <= lat1 <= 50.0 and 0.0 <= lat2 <= 50.0 and 0.0 <= lon1 <= 50.0 and 0.0 <= lon2 <= 50.0:
        return math.sqrt((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2)

    # Haversine formula
    r = 6371.0  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c

def expand_need_to_slots(need: Need) -> List[Slot]:
    """Expands need n into r_n independent assignment slots."""
    slots = []
    for i in range(need.required_head_count):
        slots.append(Slot(
            slot_id=f"{need.id}_s{i}",
            need_id=need.id,
            category=need.category,
            latitude=need.latitude,
            longitude=need.longitude,
            required_language=need.required_language,
            start_time=need.start_time,
            end_time=need.end_time,
            urgency=need.urgency,
            assigned_volunteer_id=None,
            is_locked=False
        ))
    return slots

def is_feasible(v: Volunteer, s: Slot, r_max: Optional[float] = None) -> Tuple[bool, float, float]:
    """
    Checks feasibility constraints (Section 3):
    (a) c_n in K_v (volunteer has required skill)
    (b) d(v, n) <= R_max (distance within max travel radius)
    (c) Availability and need windows overlap: max(s_v, s_n) < min(e_v, e_n)
    Returns (feasible, distance_km, overlap_hours).
    """
    max_radius = r_max if r_max is not None else config.r_max_km

    # (a) Skill check
    if s.category not in v.skills:
        dist = calculate_distance(v.latitude, v.longitude, s.latitude, s.longitude)
        return False, dist, 0.0

    # (b) Distance check
    dist = calculate_distance(v.latitude, v.longitude, s.latitude, s.longitude)
    if dist > max_radius:
        return False, dist, 0.0

    # (c) Availability overlap check
    overlap_start = max(v.start_time, s.start_time)
    overlap_end = min(v.end_time, s.end_time)
    overlap_duration = max(0.0, overlap_end - overlap_start)
    if overlap_duration <= 0.0:
        return False, dist, 0.0

    return True, dist, overlap_duration

def compute_compatibility_score(
    v: Volunteer,
    s: Slot,
    alpha: Optional[float] = None,
    beta: Optional[float] = None,
    gamma: Optional[float] = None,
    eta: Optional[float] = None,
    delta: Optional[float] = None,
    r_max: Optional[float] = None,
) -> Tuple[float, bool, CompatibilityBreakdown]:
    """
    Computes w(v,n) = u_n * (alpha*S + beta*P + gamma*A + eta*L)
    Returns (score, feasible, breakdown).
    """
    a_w = alpha if alpha is not None else config.alpha
    b_w = beta if beta is not None else config.beta
    g_w = gamma if gamma is not None else config.gamma
    e_w = eta if eta is not None else config.eta
    d_scale = delta if delta is not None else config.delta_km

    feasible, dist, overlap_hours = is_feasible(v, s, r_max)

    # S: Skill match
    s_val = 1.0 if s.category in v.skills else 0.0

    # P: Proximity decay exp(-d / delta)
    p_val = math.exp(-dist / d_scale)

    # A: Availability coverage (overlap divided by need duration, capped at 1.0)
    need_duration = max(0.001, s.end_time - s.start_time)
    a_val = min(1.0, max(0.0, overlap_hours / need_duration))

    # L: Language compatibility (1 if volunteer speaks required language)
    l_val = 1.0 if s.required_language in v.languages else 0.0

    raw_compatibility = (a_w * s_val + b_w * p_val + g_w * a_val + e_w * l_val)
    final_score = s.urgency * raw_compatibility if feasible else 0.0

    breakdown = CompatibilityBreakdown(
        skill_match=s_val,
        proximity=p_val,
        distance_km=dist,
        availability_coverage=a_val,
        overlap_hours=overlap_hours,
        language_match=l_val,
        raw_compatibility=raw_compatibility,
        urgency_multiplier=s.urgency,
        final_score=final_score
    )

    return final_score, feasible, breakdown
