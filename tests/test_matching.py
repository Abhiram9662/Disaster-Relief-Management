"""
Unit tests for the matching engine, compatibility scoring, and feasibility constraints.
"""

import pytest
from app.models.schemas import Volunteer, Need, Slot
from app.matching.scoring import calculate_distance, is_feasible, compute_compatibility_score, expand_need_to_slots
from app.matching.matchers import run_proposed_matching, run_greedy_matching, run_nearest_first_matching, run_random_matching
from app.simulation.scenario_generator import generate_scenario

def test_distance_calculation():
    # Euclidean simulation distance
    d1 = calculate_distance(10.0, 10.0, 10.0, 10.0)
    assert d1 == 0.0

    d2 = calculate_distance(0.0, 0.0, 3.0, 4.0)
    assert abs(d2 - 5.0) < 1e-4

    # Haversine distance
    d_geo = calculate_distance(31.2240, 75.7708, 31.2850, 75.6500)
    assert 10.0 < d_geo < 25.0

def test_feasibility_constraints():
    v = Volunteer(
        id="vol-test",
        name="Test Volunteer",
        skills=["medical"],
        languages=["hi", "en"],
        latitude=10.0,
        longitude=10.0,
        start_time=8.0,
        end_time=18.0
    )

    # 1. Feasible slot
    s_feasible = Slot(
        slot_id="s1", need_id="n1", category="medical",
        latitude=12.0, longitude=12.0, required_language="hi",
        start_time=9.0, end_time=15.0, urgency=3
    )
    feasible, dist, overlap = is_feasible(v, s_feasible, r_max=25.0)
    assert feasible is True
    assert overlap == 6.0

    # 2. Skill mismatch
    s_wrong_skill = Slot(
        slot_id="s2", need_id="n2", category="logistics",
        latitude=12.0, longitude=12.0, required_language="hi",
        start_time=9.0, end_time=15.0, urgency=3
    )
    feasible, _, _ = is_feasible(v, s_wrong_skill, r_max=25.0)
    assert feasible is False

    # 3. Distance > R_max
    s_too_far = Slot(
        slot_id="s3", need_id="n3", category="medical",
        latitude=40.0, longitude=40.0, required_language="hi",
        start_time=9.0, end_time=15.0, urgency=3
    )
    feasible, dist, _ = is_feasible(v, s_too_far, r_max=25.0)
    assert feasible is False
    assert dist > 25.0

    # 4. No time overlap
    s_no_overlap = Slot(
        slot_id="s4", need_id="n4", category="medical",
        latitude=12.0, longitude=12.0, required_language="hi",
        start_time=19.0, end_time=22.0, urgency=3
    )
    feasible, _, overlap = is_feasible(v, s_no_overlap, r_max=25.0)
    assert feasible is False
    assert overlap == 0.0

def test_compatibility_scoring_formula():
    v = Volunteer(
        id="vol-test", name="Test", skills=["medical"], languages=["hi"],
        latitude=10.0, longitude=10.0, start_time=8.0, end_time=18.0
    )
    s = Slot(
        slot_id="s1", need_id="n1", category="medical",
        latitude=10.0, longitude=10.0, required_language="hi",
        start_time=8.0, end_time=18.0, urgency=4
    )
    # Distance = 0 -> P = exp(0) = 1.0
    # S = 1.0, P = 1.0, A = 1.0, L = 1.0
    # w(v,n) = 4 * (0.4*1 + 0.3*1 + 0.2*1 + 0.1*1) = 4 * 1.0 = 4.0
    score, feasible, breakdown = compute_compatibility_score(v, s)
    assert feasible is True
    assert abs(score - 4.0) < 1e-4
    assert breakdown.skill_match == 1.0
    assert abs(breakdown.proximity - 1.0) < 1e-4
    assert breakdown.availability_coverage == 1.0
    assert breakdown.language_match == 1.0

def test_matchers_comparison():
    vols, needs = generate_scenario("S1", seed=42)
    res_proposed = run_proposed_matching(vols, needs)
    res_greedy = run_greedy_matching(vols, needs)
    res_nearest = run_nearest_first_matching(vols, needs)
    res_random = run_random_matching(vols, needs, seed=42)

    # Proposed and Greedy must have 100% skill precision (only feasible assignments)
    assert res_proposed.skill_precision_percent == 100.0
    assert res_greedy.skill_precision_percent == 100.0

    # Proposed global optimization achieves >= greedy total utility
    assert res_proposed.total_utility >= res_greedy.total_utility - 1e-4

    # Nearest and random ignore skills so their skill precision is much lower
    assert res_nearest.skill_precision_percent < 60.0
    assert res_random.skill_precision_percent < 60.0

    # Proposed qualified coverage is higher than nearest and random
    assert res_proposed.qualified_coverage_percent > res_nearest.qualified_coverage_percent
    assert res_proposed.qualified_coverage_percent > res_random.qualified_coverage_percent
