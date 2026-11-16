"""
Implementation of the 4 Matching Algorithms compared in Section 5.2 and Table 2:
1. Proposed: Globally optimal min-cost assignment via LinearSumAssignment (Hungarian)
2. Constrained Greedy: Descending urgency, assigns best-scoring feasible volunteer
3. Nearest-first: Descending urgency, assigns closest unassigned volunteer (ignores constraints)
4. Random: Randomly assigns unassigned volunteers to slots without constraints
"""

import time
import random
import numpy as np
from typing import List, Dict, Tuple, Optional
from scipy.optimize import linear_sum_assignment

from app.models.schemas import Volunteer, Need, Slot, AssignmentProposal, MatchingResult, CompatibilityBreakdown
from app.matching.scoring import expand_need_to_slots, is_feasible, compute_compatibility_score, calculate_distance

def run_proposed_matching(
    volunteers: List[Volunteer],
    needs: List[Need],
    alpha: Optional[float] = None,
    beta: Optional[float] = None,
    gamma: Optional[float] = None,
    eta: Optional[float] = None,
    r_max: Optional[float] = None,
) -> MatchingResult:
    """
    Algorithm 1: MATCH(V, N) from Section 4.2
    Optimal min-cost rectangular assignment using scipy.optimize.linear_sum_assignment
    """
    start_time = time.perf_counter()

    # Filter out already assigned volunteers and needs
    active_volunteers = [v for v in volunteers if v.status != "assigned"]
    slots: List[Slot] = []
    for n in needs:
        if n.status != "filled":
            unfilled_slots = n.required_head_count - n.filled_slots
            if unfilled_slots > 0:
                for i in range(unfilled_slots):
                    slots.append(Slot(
                        slot_id=f"{n.id}_s{n.filled_slots + i}",
                        need_id=n.id,
                        category=n.category,
                        latitude=n.latitude,
                        longitude=n.longitude,
                        required_language=n.required_language,
                        start_time=n.start_time,
                        end_time=n.end_time,
                        urgency=n.urgency,
                        is_locked=False
                    ))

    n_v = len(active_volunteers)
    n_s = len(slots)

    if n_v == 0 or n_s == 0:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return MatchingResult(
            algorithm="proposed",
            total_volunteers=n_v,
            total_slots=n_s,
            assignments=[],
            qualified_coverage_percent=0.0,
            skill_precision_percent=100.0,
            mean_distance_km=0.0,
            total_utility=0.0,
            runtime_ms=elapsed_ms
        )

    # Cost matrix W[v, s]
    W = np.zeros((n_v, n_s), dtype=np.float64)
    feasibility_matrix = np.zeros((n_v, n_s), dtype=bool)
    breakdown_matrix: Dict[Tuple[int, int], CompatibilityBreakdown] = {}

    for vi, v in enumerate(active_volunteers):
        for si, s in enumerate(slots):
            score, feasible, breakdown = compute_compatibility_score(
                v, s, alpha=alpha, beta=beta, gamma=gamma, eta=eta, r_max=r_max
            )
            feasibility_matrix[vi, si] = feasible
            breakdown_matrix[(vi, si)] = breakdown
            if feasible:
                W[vi, si] = score
            else:
                W[vi, si] = 0.0

    # Solve rectangular LinearSumAssignment(-W)
    row_ind, col_ind = linear_sum_assignment(-W)

    assignments: List[AssignmentProposal] = []
    total_utility = 0.0
    distances = []
    qualified_count = 0
    skill_match_count = 0

    for r, c in zip(row_ind, col_ind):
        # Line 5: only return feasible assignments with positive weight
        if feasibility_matrix[r, c] and W[r, c] > 0.0:
            v = active_volunteers[r]
            s = slots[c]
            score = float(W[r, c])
            breakdown = breakdown_matrix[(r, c)]
            dist = breakdown.distance_km

            assignments.append(AssignmentProposal(
                assignment_id=f"asgn-{v.id}-{s.slot_id}",
                volunteer_id=v.id,
                volunteer_name=v.name,
                need_id=s.need_id,
                slot_id=s.slot_id,
                category=s.category,
                score=round(score, 4),
                feasibility=True,
                breakdown=breakdown,
                status="proposed"
            ))

            total_utility += score
            distances.append(dist)
            qualified_count += 1
            if s.category in v.skills:
                skill_match_count += 1

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    cov_pct = (qualified_count / n_s * 100.0) if n_s > 0 else 0.0
    prec_pct = (skill_match_count / len(assignments) * 100.0) if assignments else 100.0
    mean_dist = float(np.mean(distances)) if distances else 0.0

    return MatchingResult(
        algorithm="proposed",
        total_volunteers=n_v,
        total_slots=n_s,
        assignments=assignments,
        qualified_coverage_percent=round(cov_pct, 2),
        skill_precision_percent=round(prec_pct, 2),
        mean_distance_km=round(mean_dist, 2),
        total_utility=round(total_utility, 4),
        runtime_ms=round(elapsed_ms, 2)
    )

def run_greedy_matching(
    volunteers: List[Volunteer],
    needs: List[Need],
    alpha: Optional[float] = None,
    beta: Optional[float] = None,
    gamma: Optional[float] = None,
    eta: Optional[float] = None,
    r_max: Optional[float] = None,
) -> MatchingResult:
    """
    Constrained Greedy Matcher:
    Processes slots in descending urgency and assigns the best-scoring feasible volunteer.
    """
    start_time = time.perf_counter()

    active_volunteers = {v.id: v for v in volunteers if v.status != "assigned"}
    slots: List[Slot] = []
    for n in needs:
        if n.status != "filled":
            unfilled_slots = n.required_head_count - n.filled_slots
            for i in range(unfilled_slots):
                slots.append(Slot(
                    slot_id=f"{n.id}_s{n.filled_slots + i}",
                    need_id=n.id,
                    category=n.category,
                    latitude=n.latitude,
                    longitude=n.longitude,
                    required_language=n.required_language,
                    start_time=n.start_time,
                    end_time=n.end_time,
                    urgency=n.urgency,
                    is_locked=False
                ))

    # Sort slots descending by urgency
    slots.sort(key=lambda s: s.urgency, reverse=True)

    n_v = len(active_volunteers)
    n_s = len(slots)
    assignments: List[AssignmentProposal] = []
    total_utility = 0.0
    distances = []
    qualified_count = 0
    skill_match_count = 0

    assigned_vols = set()

    for s in slots:
        best_v = None
        best_score = -1.0
        best_breakdown = None

        for v_id, v in active_volunteers.items():
            if v_id in assigned_vols:
                continue
            score, feasible, breakdown = compute_compatibility_score(
                v, s, alpha=alpha, beta=beta, gamma=gamma, eta=eta, r_max=r_max
            )
            if feasible and score > best_score:
                best_score = score
                best_v = v
                best_breakdown = breakdown

        if best_v is not None and best_score > 0:
            assigned_vols.add(best_v.id)
            assignments.append(AssignmentProposal(
                assignment_id=f"asgn-{best_v.id}-{s.slot_id}",
                volunteer_id=best_v.id,
                volunteer_name=best_v.name,
                need_id=s.need_id,
                slot_id=s.slot_id,
                category=s.category,
                score=round(best_score, 4),
                feasibility=True,
                breakdown=best_breakdown,
                status="proposed"
            ))
            total_utility += best_score
            distances.append(best_breakdown.distance_km)
            qualified_count += 1
            if s.category in best_v.skills:
                skill_match_count += 1

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    cov_pct = (qualified_count / n_s * 100.0) if n_s > 0 else 0.0
    prec_pct = (skill_match_count / len(assignments) * 100.0) if assignments else 100.0
    mean_dist = float(np.mean(distances)) if distances else 0.0

    return MatchingResult(
        algorithm="greedy",
        total_volunteers=n_v,
        total_slots=n_s,
        assignments=assignments,
        qualified_coverage_percent=round(cov_pct, 2),
        skill_precision_percent=round(prec_pct, 2),
        mean_distance_km=round(mean_dist, 2),
        total_utility=round(total_utility, 4),
        runtime_ms=round(elapsed_ms, 2)
    )

def run_nearest_first_matching(
    volunteers: List[Volunteer],
    needs: List[Need],
) -> MatchingResult:
    """
    Nearest-first Matcher:
    Processes slots in descending urgency and assigns the closest unassigned volunteer,
    ignoring skills and availability.
    """
    start_time = time.perf_counter()

    active_volunteers = {v.id: v for v in volunteers if v.status != "assigned"}
    slots: List[Slot] = []
    for n in needs:
        if n.status != "filled":
            unfilled_slots = n.required_head_count - n.filled_slots
            for i in range(unfilled_slots):
                slots.append(Slot(
                    slot_id=f"{n.id}_s{n.filled_slots + i}",
                    need_id=n.id,
                    category=n.category,
                    latitude=n.latitude,
                    longitude=n.longitude,
                    required_language=n.required_language,
                    start_time=n.start_time,
                    end_time=n.end_time,
                    urgency=n.urgency,
                    is_locked=False
                ))

    slots.sort(key=lambda s: s.urgency, reverse=True)

    n_v = len(active_volunteers)
    n_s = len(slots)
    assignments: List[AssignmentProposal] = []
    total_utility = 0.0
    distances = []
    qualified_count = 0
    skill_match_count = 0

    assigned_vols = set()

    for s in slots:
        best_v = None
        min_dist = float("inf")

        for v_id, v in active_volunteers.items():
            if v_id in assigned_vols:
                continue
            d = calculate_distance(v.latitude, v.longitude, s.latitude, s.longitude)
            if d < min_dist:
                min_dist = d
                best_v = v

        if best_v is not None:
            assigned_vols.add(best_v.id)
            score, feasible, breakdown = compute_compatibility_score(best_v, s)
            assignments.append(AssignmentProposal(
                assignment_id=f"asgn-{best_v.id}-{s.slot_id}",
                volunteer_id=best_v.id,
                volunteer_name=best_v.name,
                need_id=s.need_id,
                slot_id=s.slot_id,
                category=s.category,
                score=round(score, 4),
                feasibility=feasible,
                breakdown=breakdown,
                status="proposed"
            ))
            distances.append(min_dist)
            if feasible:
                total_utility += score
                qualified_count += 1
            if s.category in best_v.skills:
                skill_match_count += 1

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    cov_pct = (qualified_count / n_s * 100.0) if n_s > 0 else 0.0
    prec_pct = (skill_match_count / len(assignments) * 100.0) if assignments else 0.0
    mean_dist = float(np.mean(distances)) if distances else 0.0

    return MatchingResult(
        algorithm="nearest",
        total_volunteers=n_v,
        total_slots=n_s,
        assignments=assignments,
        qualified_coverage_percent=round(cov_pct, 2),
        skill_precision_percent=round(prec_pct, 2),
        mean_distance_km=round(mean_dist, 2),
        total_utility=round(total_utility, 4),
        runtime_ms=round(elapsed_ms, 2)
    )

def run_random_matching(
    volunteers: List[Volunteer],
    needs: List[Need],
    seed: Optional[int] = None,
) -> MatchingResult:
    """
    Random Matcher:
    Assigns unassigned volunteers to slots uniformly at random without constraints.
    """
    start_time = time.perf_counter()
    rng = random.Random(seed)

    active_volunteers = [v for v in volunteers if v.status != "assigned"]
    rng.shuffle(active_volunteers)

    slots: List[Slot] = []
    for n in needs:
        if n.status != "filled":
            unfilled_slots = n.required_head_count - n.filled_slots
            for i in range(unfilled_slots):
                slots.append(Slot(
                    slot_id=f"{n.id}_s{n.filled_slots + i}",
                    need_id=n.id,
                    category=n.category,
                    latitude=n.latitude,
                    longitude=n.longitude,
                    required_language=n.required_language,
                    start_time=n.start_time,
                    end_time=n.end_time,
                    urgency=n.urgency,
                    is_locked=False
                ))

    rng.shuffle(slots)

    n_v = len(active_volunteers)
    n_s = len(slots)
    assignments: List[AssignmentProposal] = []
    total_utility = 0.0
    distances = []
    qualified_count = 0
    skill_match_count = 0

    num_pairs = min(n_v, n_s)
    for i in range(num_pairs):
        v = active_volunteers[i]
        s = slots[i]
        score, feasible, breakdown = compute_compatibility_score(v, s)
        dist = calculate_distance(v.latitude, v.longitude, s.latitude, s.longitude)
        assignments.append(AssignmentProposal(
            assignment_id=f"asgn-{v.id}-{s.slot_id}",
            volunteer_id=v.id,
            volunteer_name=v.name,
            need_id=s.need_id,
            slot_id=s.slot_id,
            category=s.category,
            score=round(score, 4),
            feasibility=feasible,
            breakdown=breakdown,
            status="proposed"
        ))
        distances.append(dist)
        if feasible:
            total_utility += score
            qualified_count += 1
        if s.category in v.skills:
            skill_match_count += 1

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    cov_pct = (qualified_count / n_s * 100.0) if n_s > 0 else 0.0
    prec_pct = (skill_match_count / len(assignments) * 100.0) if assignments else 0.0
    mean_dist = float(np.mean(distances)) if distances else 0.0

    return MatchingResult(
        algorithm="random",
        total_volunteers=n_v,
        total_slots=n_s,
        assignments=assignments,
        qualified_coverage_percent=round(cov_pct, 2),
        skill_precision_percent=round(prec_pct, 2),
        mean_distance_km=round(mean_dist, 2),
        total_utility=round(total_utility, 4),
        runtime_ms=round(elapsed_ms, 2)
    )
