"""Leaderboard service — queries, computes, and ranks students.

Implements design.md §6 (Leaderboard_Service) with support for
subject-filtered ranking (REQ-11.7).

The service:
1. Queries the database for all students' submission stats (optionally
   filtered by subject).
2. Computes cohort stats (max_attempts, max_std_dev) from the eligible pool.
3. Applies the eligibility filter (is_eligible from score.py).
4. Computes composite scores for eligible students.
5. Ranks them using the rank.py module.
6. When a subject filter is provided, only considers submissions for that
   subject and excludes students with zero submissions in that subject.
7. Returns the ranked list.

Requirements covered: REQ-11.1, REQ-11.2, REQ-11.3, REQ-11.7.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from smartkcet.db.models import Exam, ExamSet, Subject, Submission, User
from smartkcet.leaderboard.rank import RankedEntry, assign_ranks
from smartkcet.leaderboard.score import (
    CohortStats,
    StudentStats,
    compute_composite,
    is_eligible,
)


def _std_dev(scores: List[float])-> float:
    """Compute the population standard deviation of *scores*.

    Returns 0.0 when the list has fewer than 2 elements.
    """
    if len(scores) < 2:
        return 0.0
    mean = sum(scores) / len(scores)
    variance = sum((s - mean) ** 2 for s in scores) / len(scores)
    return math.sqrt(variance)


def _gather_student_stats(session: Session, subject: Optional[str] = None, institution_id: Optional[Any] = None)-> Dict[str, StudentStats]:
    """Query the database and build per-student stats.

    When *institution_id* is provided, stats are strictly isolated to students
    and exams belonging to that institution.
    When *institution_id* is None, stats are strictly isolated to independent students and platform-wide exams.
    """
    query = (
        session.query(
            Submission.user_id,
            Submission.score_pct,
        )
        .join(ExamSet, Submission.exam_set_id == ExamSet.id)
        .join(Exam, ExamSet.exam_id == Exam.id)
        .join(User, Submission.user_id == User.id)
        .filter(Submission.status == "completed")
    )

    if institution_id is not None:
        query = query.filter(User.institution_id == institution_id, Exam.institution_id == institution_id)
    else:
        query = query.filter(User.institution_id.is_(None), Exam.institution_id.is_(None))

    if subject is not None:
        query = query.filter(Exam.subject == subject)

    rows = query.all()

    # Group scores by user_id
    user_scores: Dict[str, List[float]] = {}
    for row in rows:
        uid = str(row.user_id)
        if uid not in user_scores:
            user_scores[uid] = []
        user_scores[uid].append(row.score_pct)

    # Also get overall stats (unfiltered) for eligibility check
    overall_stats: Dict[str, tuple] = {}
    if subject is not None:
        overall_query = (
            session.query(
                Submission.user_id,
                func.count(Submission.id).label("count"),
                func.avg(Submission.score_pct).label("avg"),
            )
            .filter(Submission.status == "completed")
            .group_by(Submission.user_id)
        )
        for row in overall_query.all():
            overall_stats[str(row.user_id)] = (row.count, float(row.avg))
    else:
        for uid, scores in user_scores.items():
            overall_stats[uid] = (len(scores), sum(scores) / len(scores))

    # Build StudentStats for each user that has submissions
    result: Dict[str, StudentStats] = {}
    for uid, scores in user_scores.items():
        avg_score = sum(scores) / len(scores) if scores else 0.0
        attempt_count = len(scores)

        overall_count, overall_avg = overall_stats.get(uid, (attempt_count, avg_score))

        result[uid] = StudentStats(
            average_score=avg_score,
            attempt_count=attempt_count,
            scores=scores,
            submission_count=int(overall_count),
            overall_average_score=float(overall_avg),
        )

    return result


def _get_user_info(session: Session, user_ids: List[str])-> Dict[str, tuple]:
    """Fetch display_name and kcet_student_id for the given user IDs.

    Returns a dict mapping user_id (str) to (display_name, kcet_student_id).
    """
    if not user_ids:
        return {}

    from uuid import UUID

    uuid_ids = [UUID(uid) for uid in user_ids]
    users = (
        session.query(User.id, User.display_name, User.kcet_student_id)
        .filter(User.id.in_(uuid_ids))
        .all()
    )
    return {
        str(u.id): (u.display_name, u.kcet_student_id or "")
        for u in users
    }


def get_leaderboard(session: Session, subject: Optional[str] = None, institution_id: Optional[Any] = None)-> List[RankedEntry]:
    """Compute and return the ranked leaderboard.

    Args:
        session: SQLAlchemy session for DB queries.
        subject: Optional subject filter.
        institution_id: Optional institution filter for strict institution leaderboard isolation.

    Returns:
        A list of RankedEntry objects sorted by rank (ascending).
    """
    if subject is not None:
        valid_subjects = {s.value for s in Subject}
        if subject not in valid_subjects:
            return []

    all_stats = _gather_student_stats(session, subject=subject, institution_id=institution_id)

    if not all_stats:
        return []

    # Step 2 & 3: Filter to eligible students
    eligible_stats: Dict[str, StudentStats] = {
        uid: stats
        for uid, stats in all_stats.items()
        if is_eligible(stats)
    }

    if not eligible_stats:
        return []

    # Step 4: Compute cohort stats from the eligible pool
    max_attempts = max(s.attempt_count for s in eligible_stats.values())
    all_std_devs = [_std_dev(s.scores) for s in eligible_stats.values()]
    max_std_dev = max(all_std_devs) if all_std_devs else 0.0

    cohort_stats = CohortStats(
        max_attempts_in_cohort=max_attempts,
        max_std_dev_in_cohort=max_std_dev,
    )

    # Step 5: Compute composite scores and build ranked entries
    user_ids = list(eligible_stats.keys())
    user_info = _get_user_info(session, user_ids)

    entries: List[RankedEntry] = []
    for uid, stats in eligible_stats.items():
        composite = compute_composite(stats, cohort_stats)
        display_name, kcet_id = user_info.get(uid, ("", ""))
        entries.append(
            RankedEntry(
                student_id=uid,
                composite_score=composite,
                display_name=display_name,
                kcet_student_id=kcet_id,
                average_score=stats.average_score,
                attempt_count=stats.attempt_count,
            )
        )

    # Step 6: Rank using rank.py module
    ranked = assign_ranks(entries)

    return ranked


__all__ = [
    "get_leaderboard",
]
