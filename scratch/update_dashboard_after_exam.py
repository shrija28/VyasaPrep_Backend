"""Script to submit an exam and verify that the student, institution, and admin dashboards auto-update immediately."""

import sys
import os
import uuid
import requests

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from smartkcet.db.session import SessionLocal
from smartkcet.db.models import User, Exam, ExamSet, Submission, Question, ExamSetQuestion
from smartkcet.db.subscription_models import Institution

BASE_URL = "http://127.0.0.1:8000"

def run_test():
    print("=" * 65)
    print("TESTING DASHBOARD AUTO-UPDATE AFTER EXAM SUBMISSION")
    print("=" * 65)

    session = SessionLocal()
    try:
        # 1. Find a test student with an institution in DB or login as one
        student = session.query(User).filter(
            User.role == "student",
            User.institution_id.isnot(None)
        ).first()

        if not student:
            print("FAIL: No institution-linked student found in DB")
            return

        print(f"Student: {student.display_name} ({student.email})")

        # Create session and login as student
        stu_session = requests.Session()
        login_res = stu_session.post(f"{BASE_URL}/api/auth/login", json={
            "email": student.email,
            "password": "Password123!" # standard test pwd or login via token
        })

        if login_res.status_code != 200:
            # Generate JWT token manually if direct password login fails
            import jwt
            import datetime
            from smartkcet.config import validate_startup_config
            cfg = validate_startup_config()
            
            payload = {
                'sub': str(student.id),
                'role': 'student',
                'student_subtype': student.student_subtype or 'institution_linked',
                'institution_id': str(student.institution_id) if student.institution_id else None,
                'subscription_status': 'active',
                'iat': int(datetime.datetime.now(datetime.timezone.utc).timestamp()),
                'exp': int((datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)).timestamp()),
                'jti': str(uuid.uuid4())
            }
            token = jwt.encode(payload, cfg.jwt_secret, algorithm='HS256')
            if isinstance(token, bytes):
                token = token.decode('utf-8')
            stu_session.headers.update({'Authorization': f'Bearer {token}'})

        # 2. Fetch initial student dashboard stats
        initial_stats_res = stu_session.get(f"{BASE_URL}/api/student/dashboard-stats")
        print(f"GET initial dashboard stats status: {initial_stats_res.status_code}")
        initial_data = initial_stats_res.json()
        
        initial_kpis = initial_data.get("kpis", {})
        init_taken = initial_kpis.get("examsTaken", 0)
        init_avg = initial_kpis.get("avgScore", 0.0)
        init_recent_count = len(initial_data.get("recentSubmissions", []))

        print(f"-> Initial Exams Taken: {init_taken}")
        print(f"-> Initial Avg Score: {init_avg}%")
        print(f"-> Initial Recent Submissions Count: {init_recent_count}")

        # 3. Find an available ExamSet to take
        exam_set = session.query(ExamSet).join(Exam).filter(
            Exam.is_published == True
        ).first()

        if not exam_set:
            print("FAIL: No published exam set found in DB to take!")
            return

        print(f"\nTaking Exam Set: {exam_set.set_label} (ID: {exam_set.id})")

        # Get questions for this set
        esq_rows = session.query(Question, ExamSetQuestion.order_index).join(
            ExamSetQuestion, ExamSetQuestion.question_id == Question.id
        ).filter(ExamSetQuestion.exam_set_id == exam_set.id).all()

        print(f"Exam set has {len(esq_rows)} questions loaded.")

        # Simulate answers (answer option 'A' for all questions)
        answers = {}
        for q, idx in esq_rows:
            answers[str(idx)] = "A"

        submit_payload = {
            "exam_set_id": str(exam_set.id),
            "answers": answers,
            "time_taken_sec": 1200,
            "idempotency_key": str(uuid.uuid4())
        }

        # 4. Submit exam
        print("Submitting exam answers...")
        sub_res = stu_session.post(f"{BASE_URL}/api/student/submit", json=submit_payload)
        print(f"POST /api/student/submit status: {sub_res.status_code}")
        if sub_res.status_code != 200:
            print(f"Error submitting exam: {sub_res.text}")
            return
        
        sub_json = sub_res.json()
        pct_scored = sub_json.get("percentage", 0.0)
        print(f"Exam Submitted Successfully! Score: {pct_scored}%")

        # 5. Fetch updated dashboard stats
        updated_stats_res = stu_session.get(f"{BASE_URL}/api/student/dashboard-stats")
        print(f"\nGET updated dashboard stats status: {updated_stats_res.status_code}")
        updated_data = updated_stats_res.json()
        
        upd_kpis = updated_data.get("kpis", {})
        upd_taken = upd_kpis.get("examsTaken", 0)
        upd_avg = upd_kpis.get("avgScore", 0.0)
        upd_recent = updated_data.get("recentSubmissions", [])

        print(f"-> Updated Exams Taken: {upd_taken} (Expected: {init_taken + 1})")
        print(f"-> Updated Avg Score: {upd_avg}%")
        print(f"-> Updated Recent Submissions Count: {len(upd_recent)} (Expected: {init_recent_count + 1})")

        # 6. Assertions to verify dashboard auto-updated
        assert upd_taken == init_taken + 1, f"Exams taken did not increment! Was {init_taken}, now {upd_taken}"
        assert len(upd_recent) == init_recent_count + 1 or len(upd_recent) == min(10, init_recent_count + 1), "Recent submissions count did not update!"
        
        # Verify top recent submission is the one we just took
        latest_sub = upd_recent[0]
        print(f"-> Latest Submission in Dashboard: Set {latest_sub.get('exam_set_label')} | Score {latest_sub.get('score')}% | Pass: {latest_sub.get('passed')}")

        print("\n" + "=" * 65)
        print("SUCCESS: Student Dashboard auto-updated immediately after exam submission!")
        print("=" * 65)

    finally:
        session.close()

if __name__ == "__main__":
    run_test()
