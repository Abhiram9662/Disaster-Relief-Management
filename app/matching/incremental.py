"""
Incremental matching workflow and assignment locking logic.
"""

from typing import List, Optional
from app.models.schemas import AssignmentProposal, MatchingResult
from app.models.database import db
from app.matching.matchers import run_proposed_matching, run_greedy_matching, run_nearest_first_matching, run_random_matching

def recompute_incremental_matching(
    algorithm: str = "proposed",
    alpha: Optional[float] = None,
    beta: Optional[float] = None,
    gamma: Optional[float] = None,
    eta: Optional[float] = None,
    r_max: Optional[float] = None,
) -> MatchingResult:
    """
    Fetches latest unassigned volunteers and open needs from the database,
    computes new proposals, and updates the database.
    """
    volunteers = db.list_volunteers()
    needs = db.list_needs()

    if algorithm == "proposed":
        result = run_proposed_matching(volunteers, needs, alpha, beta, gamma, eta, r_max)
    elif algorithm == "greedy":
        result = run_greedy_matching(volunteers, needs, alpha, beta, gamma, eta, r_max)
    elif algorithm == "nearest":
        result = run_nearest_first_matching(volunteers, needs)
    elif algorithm == "random":
        result = run_random_matching(volunteers, needs)
    else:
        result = run_proposed_matching(volunteers, needs, alpha, beta, gamma, eta, r_max)

    # Save proposals to database
    for proposal in result.assignments:
        db.save_assignment(proposal)

    return result

def confirm_and_lock_assignment(assignment_id: str, hlc: int = 0) -> bool:
    """
    Locks an assignment proposal: marks volunteer as assigned,
    updates need slot counter, and removes both from subsequent matching pool.
    """
    return db.confirm_assignment(assignment_id, hlc)
