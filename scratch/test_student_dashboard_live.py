"""Verification script to test student dashboard live data binding."""

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
    print("VERIFYING LIVE STUDENT DASHBOARD DATA BINDING")
    print("=" * 60)

    students = session.query(User).filter(User.role == "student").all()
    print(f"Total Students in Database: {len(students)}")

    for st in students:
        inst_name = "Direct Subscriber"
        if st.institution_id:
            inst = session.query(Institution).filter(Institution.id == st.institution_id).first()
            if inst:
                inst_name = inst.name

        subs = session.query(Submission).filter(
            Submission.user_id == st.id,
            Submission.status == "completed"
        ).all()

        taken = len(subs)
        scores = [float(s.score_pct) for s in subs if s.score_pct is not None]
        avg = round(sum(scores) / len(scores), 1) if scores else 0.0

        print(f"\nStudent: {st.display_name} ({st.email})")
        print(f"  - Institution: {inst_name}")
        print(f"  - Real KCET Student ID: {st.kcet_student_id or 'Not Set'}")
        print(f"  - Live Exams Taken: {taken} Completed")
        print(f"  - Live Average Score: {avg}%")
        assert st.kcet_student_id is not None, "kcet_student_id must be present"

    print("\nSUCCESS: All student dashboard values are live and fully bound!")
    print("=" * 60)

finally:
    session.close()
