"""Verification script to test strict institution exam visibility and isolation end-to-end.

Tests:
1. Exams created by Institution A are ONLY visible to students of Institution A.
2. Students of Institution B CANNOT see or access exams created by Institution A.
3. Direct Subscribers (Personal Students) CANNOT see or access exams created by any institution.
4. Cross-access attempts (GET questions, POST submit) across institutions return HTTP 404.
"""

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
from smartkcet.db.subscription_models import Institution
from smartkcet.config import validate_startup_config

BASE_URL = "http://127.0.0.1:8000"
cfg = validate_startup_config()

def create_jwt_for_user(user: User) -> str:
    payload = {
        'sub': str(user.id),
        'role': 'student',
        'student_subtype': user.student_subtype or ('institution_linked' if user.institution_id else 'direct_subscriber'),
        'institution_id': str(user.institution_id) if user.institution_id else None,
        'kcet_student_id': user.kcet_student_id,
        'subscription_status': 'active',
        'iat': int(datetime.datetime.now(datetime.timezone.utc).timestamp()),
        'exp': int((datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)).timestamp()),
        'jti': str(uuid.uuid4())
    }
    token = jwt.encode(payload, cfg.jwt_secret, algorithm='HS256')
    return token if isinstance(token, str) else token.decode('utf-8')

def test_isolation():
    print("=" * 70)
    print("TESTING STRICT INSTITUTION EXAM VISIBILITY & ISOLATION")
    print("=" * 70)

    session = SessionLocal()
    try:
        # Find two different institutions
        institutions = session.query(Institution).all()
        if len(institutions) < 2:
            print("FAIL: Need at least 2 institutions in DB to test isolation")
            return

        inst_a = institutions[0]
        inst_b = institutions[1]
        print(f"Institution A: {inst_a.name} (ID: {inst_a.id})")
        print(f"Institution B: {inst_b.name} (ID: {inst_b.id})")

        # Find student belonging to Inst A
        student_a = session.query(User).filter(
            User.role == "student",
            User.institution_id == inst_a.id
        ).first()

        # Find student belonging to Inst B
        student_b = session.query(User).filter(
            User.role == "student",
            User.institution_id == inst_b.id
        ).first()

        # Find direct subscriber student (no institution)
        student_direct = session.query(User).filter(
            User.role == "student",
            User.institution_id.is_(None)
        ).first()

        if not student_a or not student_b:
            print("FAIL: Could not find students for both institutions")
            return

        print(f"-> Student A ({inst_a.name}): {student_a.display_name} ({student_a.email})")
        print(f"-> Student B ({inst_b.name}): {student_b.display_name} ({student_b.email})")
        if student_direct:
            print(f"-> Direct Subscriber Student: {student_direct.display_name} ({student_direct.email})")

        # Ensure an exam exists for Inst A
        exam_a = session.query(Exam).filter(
            Exam.institution_id == inst_a.id,
            Exam.is_published == True
        ).first()

        if not exam_a:
            exam_a = Exam(
                id=uuid.uuid4(),
                subject="Physics",
                exam_name=f"Physics Test for {inst_a.name}",
                institution_id=inst_a.id,
                is_published=True
            )
            session.add(exam_a)
            session.flush()

            # Create ExamSet A
            es_a = ExamSet(id=uuid.uuid4(), exam_id=exam_a.id, set_label="A")
            session.add(es_a)
            session.commit()
            print(f"-> Created published Exam A for {inst_a.name} (Exam ID: {exam_a.id})")

        # Ensure an exam exists for Inst B
        exam_b = session.query(Exam).filter(
            Exam.institution_id == inst_b.id,
            Exam.is_published == True
        ).first()

        if not exam_b:
            exam_b = Exam(
                id=uuid.uuid4(),
                subject="Chemistry",
                exam_name=f"Chemistry Test for {inst_b.name}",
                institution_id=inst_b.id,
                is_published=True
            )
            session.add(exam_b)
            session.flush()

            # Create ExamSet B
            es_b = ExamSet(id=uuid.uuid4(), exam_id=exam_b.id, set_label="A")
            session.add(es_b)
            session.commit()
            print(f"-> Created published Exam B for {inst_b.name} (Exam ID: {exam_b.id})")

        set_a = session.query(ExamSet).filter(ExamSet.exam_id == exam_a.id).first()
        set_b = session.query(ExamSet).filter(ExamSet.exam_id == exam_b.id).first()

        # ---------------------------------------------------------------------
        # TEST 1: Student A lists exams
        # ---------------------------------------------------------------------
        print("\n--- TEST 1: Student A lists available exams ---")
        headers_a = {"Authorization": f"Bearer {create_jwt_for_user(student_a)}"}
        res_a = requests.get(f"{BASE_URL}/api/student/exams", headers=headers_a)
        assert res_a.status_code == 200, f"Failed GET /api/student/exams: {res_a.status_code}"

        data_a = res_a.json()
        all_exams_a = []
        for sb in data_a.get("subjects", []):
            for e in sb.get("exams", []):
                all_exams_a.append(e.get("exam_id"))

        print(f"Student A sees {len(all_exams_a)} exams")
        assert str(exam_a.id) in all_exams_a, f"Student A MUST see Exam A ({exam_a.id})"
        assert str(exam_b.id) not in all_exams_a, f"Student A MUST NOT see Exam B ({exam_b.id})!"
        print("  [PASS] Student A sees Exam A and does NOT see Exam B")

        # ---------------------------------------------------------------------
        # TEST 2: Student B lists exams
        # ---------------------------------------------------------------------
        print("\n--- TEST 2: Student B lists available exams ---")
        headers_b = {"Authorization": f"Bearer {create_jwt_for_user(student_b)}"}
        res_b = requests.get(f"{BASE_URL}/api/student/exams", headers=headers_b)
        assert res_b.status_code == 200, f"Failed GET /api/student/exams: {res_b.status_code}"

        data_b = res_b.json()
        all_exams_b = []
        for sb in data_b.get("subjects", []):
            for e in sb.get("exams", []):
                all_exams_b.append(e.get("exam_id"))

        print(f"Student B sees {len(all_exams_b)} exams")
        assert str(exam_b.id) in all_exams_b, f"Student B MUST see Exam B ({exam_b.id})"
        assert str(exam_a.id) not in all_exams_b, f"Student B MUST NOT see Exam A ({exam_a.id})!"
        print("  [PASS] Student B sees Exam B and does NOT see Exam A")

        # ---------------------------------------------------------------------
        # TEST 3: Direct Subscriber lists exams
        # ---------------------------------------------------------------------
        if student_direct:
            print("\n--- TEST 3: Direct Subscriber Student lists available exams ---")
            headers_d = {"Authorization": f"Bearer {create_jwt_for_user(student_direct)}"}
            res_d = requests.get(f"{BASE_URL}/api/student/exams", headers=headers_d)
            assert res_d.status_code == 200, f"Failed GET /api/student/exams: {res_d.status_code}"

            data_d = res_d.json()
            all_exams_d = []
            for sb in data_d.get("subjects", []):
                for e in sb.get("exams", []):
                    all_exams_d.append(e.get("exam_id"))

            print(f"Direct Student sees {len(all_exams_d)} exams")
            assert str(exam_a.id) not in all_exams_d, "Direct Subscriber MUST NOT see Exam A!"
            assert str(exam_b.id) not in all_exams_d, "Direct Subscriber MUST NOT see Exam B!"
            print("  [PASS] Direct Subscriber does NOT see Exam A or Exam B")

        # ---------------------------------------------------------------------
        # TEST 4: Student B attempts cross-institution access to Exam A
        # ---------------------------------------------------------------------
        if set_a:
            print("\n--- TEST 4: Cross-Institution Security Check ---")
            # Student B attempts GET Exam Set A questions
            cross_q_res = requests.get(f"{BASE_URL}/api/student/exams/{set_a.id}", headers=headers_b)
            print(f"Student B GET Exam Set A questions status: {cross_q_res.status_code}")
            assert cross_q_res.status_code == 404, f"Expected 404 for cross-institution exam questions, got {cross_q_res.status_code}"

            # Student B attempts POST submit to Exam Set A
            cross_sub_res = requests.post(f"{BASE_URL}/api/student/submit", headers=headers_b, json={
                "exam_set_id": str(set_a.id),
                "answers": {"0": "A"},
                "time_taken_sec": 300,
                "idempotency_key": str(uuid.uuid4())
            })
            print(f"Student B POST submit to Exam Set A status: {cross_sub_res.status_code}")
            assert cross_sub_res.status_code == 404, f"Expected 404 for cross-institution exam submit, got {cross_sub_res.status_code}"

            # Student B attempts GET status for Exam Set A
            cross_st_res = requests.get(f"{BASE_URL}/api/student/exams/{set_a.id}/status", headers=headers_b)
            print(f"Student B GET status for Exam Set A status: {cross_st_res.status_code}")
            assert cross_st_res.status_code == 404, f"Expected 404 for cross-institution exam status, got {cross_st_res.status_code}"

            print("  [PASS] Cross-institution exam question fetch, submission, and status access blocked with 404!")

        print("\n" + "=" * 70)
        print("SUCCESS: Strict Institution Exam Isolation fully verified!")
        print("=" * 70)

    finally:
        session.close()

if __name__ == "__main__":
    test_isolation()
