"""Verification script to test score evaluation accuracy across Sets A, B, C, D."""

import sys
import os
import uuid
import datetime
import jwt
import requests

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from smartkcet.db.session import SessionLocal
from smartkcet.db.models import User, Exam, ExamSet, ExamSetQuestion, Question
from smartkcet.config import validate_startup_config

BASE_URL = "http://127.0.0.1:8000"
cfg = validate_startup_config()

def create_jwt_for_user(user: User) -> str:
    payload = {
        'sub': str(user.id),
        'role': 'student',
        'student_subtype': user.student_subtype or 'direct_subscriber',
        'kcet_student_id': user.kcet_student_id,
        'subscription_status': 'active',
        'iat': int(datetime.datetime.now(datetime.timezone.utc).timestamp()),
        'exp': int((datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)).timestamp()),
        'jti': str(uuid.uuid4())
    }
    token = jwt.encode(payload, cfg.jwt_secret, algorithm='HS256')
    return token if isinstance(token, str) else token.decode('utf-8')

def test_scoring():
    print("=" * 70)
    print("TESTING SCORE EVALUATION ACCURACY ACROSS ALL EXAM SETS (A, B, C, D)")
    print("=" * 70)

    session = SessionLocal()
    try:
        student = session.query(User).filter(User.role == "student").first()
        if not student:
            print("FAIL: No student found in DB")
            return

        published_exam = session.query(Exam).filter(Exam.is_published == True).first()
        if not published_exam:
            print("FAIL: No published exam found in DB")
            return

        if published_exam.institution_id:
            student.institution_id = published_exam.institution_id
            student.student_subtype = "institution_linked"
            session.commit()

        exam_sets = session.query(ExamSet).filter(
            ExamSet.exam_id == published_exam.id
        ).order_by(ExamSet.set_label.asc()).all()

        print(f"Testing Exam: '{published_exam.exam_name}' ({published_exam.subject})")
        print(f"Available Exam Sets: {[s.set_label for s in exam_sets]}")

        headers = {"Authorization": f"Bearer {create_jwt_for_user(student)}"}

        for es in exam_sets:
            set_label = es.set_label
            print(f"\n--- Testing Set {set_label} (ID: {es.id}) ---")

            # 1. Get questions for Set
            q_res = requests.get(f"{BASE_URL}/api/student/exams/{es.id}", headers=headers)
            assert q_res.status_code == 200, f"Failed GET questions for Set {set_label}: {q_res.status_code}"

            q_data = q_res.json()
            questions = q_data.get("questions", [])
            print(f"Set {set_label} delivered {len(questions)} questions")
            assert len(questions) > 0, "Set questions cannot be empty"

            # 2. Build 100% PERFECT answers map matching the delivered set's correct answers
            perfect_answers = {}
            for idx, q in enumerate(questions):
                perfect_answers[str(idx)] = str(q.get("ans"))

            # Submit 100% correct answers
            sub_payload = {
                "exam_set_id": str(es.id),
                "answers": perfect_answers,
                "time_taken_sec": 600,
                "idempotency_key": str(uuid.uuid4())
            }
            sub_res = requests.post(f"{BASE_URL}/api/student/submit", headers=headers, json=sub_payload)
            assert sub_res.status_code == 200, f"Failed submit for Set {set_label}: {sub_res.status_code} - {sub_res.text}"

            res_json = sub_res.json()
            pct = res_json.get("percentage", 0.0)
            correct = res_json.get("correct_count", 0)
            total = res_json.get("total_marks", len(questions))

            print(f"-> Set {set_label} Perfect Submission Score: {pct}% ({correct}/{total} correct)")
            assert pct == 100.0, f"Expected 100.0% for perfect submission on Set {set_label}, got {pct}%!"
            assert correct == total, f"Expected {total} correct, got {correct}!"
            print(f"  [PASS] Set {set_label} 100% perfect score evaluated accurately!")

            # 3. Test 0% score submission for Set B/C/D to confirm wrong answers are scored 0
            if set_label != "A":
                wrong_answers = {}
                for idx, q in enumerate(questions):
                    correct_idx = str(q.get("ans"))
                    # Pick an intentionally wrong option index
                    wrong_idx = "0" if correct_idx != "0" else "1"
                    wrong_answers[str(idx)] = wrong_idx

                sub_payload_wrong = {
                    "exam_set_id": str(es.id),
                    "answers": wrong_answers,
                    "time_taken_sec": 600,
                    "idempotency_key": str(uuid.uuid4())
                }
                sub_res_wrong = requests.post(f"{BASE_URL}/api/student/submit", headers=headers, json=sub_payload_wrong)
                assert sub_res_wrong.status_code == 200, f"Failed submit wrong answers for Set {set_label}"

                res_json_w = sub_res_wrong.json()
                pct_w = res_json_w.get("percentage", 0.0)
                print(f"-> Set {set_label} All-Wrong Submission Score: {pct_w}%")
                assert pct_w == 0.0, f"Expected 0.0% for all-wrong submission on Set {set_label}, got {pct_w}%!"
                print(f"  [PASS] Set {set_label} 0% wrong score evaluated accurately!")

        print("\n" + "=" * 70)
        print("SUCCESS: Score evaluation accuracy verified 100% across all exam sets!")
        print("=" * 70)

    finally:
        session.close()

if __name__ == "__main__":
    test_scoring()
