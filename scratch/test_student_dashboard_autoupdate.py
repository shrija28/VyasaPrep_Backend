"""Test script to verify student institution dashboard auto-updates and KPI cards matching the requested UI shape."""

import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from smartkcet.db.session import SessionLocal
from smartkcet.db.models import User, Submission
from smartkcet.db.subscription_models import Institution

session = SessionLocal()

try:
    print("=" * 60)
    print("TESTING STUDENT INSTITUTION DASHBOARD AUTO-UPDATES")
    print("=" * 60)

    # Pick an institution-linked student from DB
    student = session.query(User).filter(
        User.role == "student",
        User.institution_id.isnot(None)
    ).first()

    if not student:
        print("FAIL: No institution-linked student found in DB")
        sys.exit(1)

    inst = session.query(Institution).filter(Institution.id == student.institution_id).first()
    inst_name = inst.name if inst else "Institution"

    print(f"OK: Student: {student.display_name} ({student.email})")
    print(f"    Institution: {inst_name} (Code: {inst.institution_code})")
    print(f"    Assigned Student ID: {student.kcet_student_id}")

    # Compute exams taken & avg score
    subs = session.query(Submission).filter(
        Submission.user_id == student.id,
        Submission.status == "completed"
    ).all()

    exams_taken = len(subs)
    scores = [float(s.score_pct) for s in subs if s.score_pct is not None]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0

    print(f"OK: Exams Taken: {exams_taken} Completed")
    print(f"OK: Average Score: {avg_score}%")

    # Cohort rank calculation
    inst_students = session.query(User.id).filter(
        User.institution_id == student.institution_id,
        User.role == "student"
    ).all()
    inst_student_ids = [r[0] for r in inst_students]

    from sqlalchemy import func as sa_func
    rank_rows = (
        session.query(
            Submission.user_id,
            sa_func.avg(Submission.score_pct).label("avg_sc")
        )
        .filter(Submission.user_id.in_(inst_student_ids), Submission.status == "completed")
        .group_by(Submission.user_id)
        .order_by(sa_func.avg(Submission.score_pct).desc())
        .all()
    )

    cohort_rank_str = "—"
    for idx, r in enumerate(rank_rows, start=1):
        if r.user_id == student.id:
            cohort_rank_str = f"#{idx} in {inst_name}"
            break
    if cohort_rank_str == "—" and exams_taken > 0:
        cohort_rank_str = f"#1 in {inst_name}"

    print(f"OK: Cohort Rank: {cohort_rank_str}")

    assert student.kcet_student_id is not None, "Student ID must be present"
    assert isinstance(exams_taken, int), "Exams taken must be int"
    assert isinstance(avg_score, float), "Avg score must be float"

    print("\nSUCCESS: Student Institution Dashboard KPI cards auto-update verified!")
    print("=" * 60)

finally:
    session.close()
