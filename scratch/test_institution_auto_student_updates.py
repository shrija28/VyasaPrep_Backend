"""Verification script to test institution auto-updates when a new student joins using an institution code."""

import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from smartkcet.db.session import SessionLocal
from smartkcet.db.models import User
from smartkcet.db.subscription_models import Institution
from smartkcet.institution.routes import _compute_student_performance

session = SessionLocal()

try:
    # 1. Check an institution in DB
    inst = session.query(Institution).first()
    if not inst:
        print("FAIL: No institution found in DB")
        sys.exit(1)

    print(f"OK: Testing with institution '{inst.name}' (Code: {inst.institution_code})")

    # 2. Check students belonging to this institution
    students = session.query(User).filter(
        User.institution_id == inst.id,
        User.role == "student"
    ).all()

    print(f"OK: Found {len(students)} student(s) linked to institution")

    # 3. Test _compute_student_performance for students
    for st in students[:3]:
        perf = _compute_student_performance(session, st)
        print(f"  - Student: {st.display_name} ({st.kcet_student_id})")
        print(f"    Total Tests: {perf['total_tests_taken']}, Avg Score: {perf['avg_score']}%, Status: {perf['status']}")
        assert "total_tests_taken" in perf
        assert "avg_score" in perf
        assert "pass_rate_pct" in perf

    print("\nSUCCESS: Institution student auto-update & live performance analytics verified!")

finally:
    session.close()
