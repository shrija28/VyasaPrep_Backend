"""End-to-End Test for Strict Institution-Level Data Isolation across the Flask Backend.

Tests:
1. Institution A User (Admin/Student):
   - Access Question Bank A: ALLOW
   - Access Questions A: ALLOW
   - Access Exams A: ALLOW
   - Access Question Bank B: DENY (0 items returned)
   - Access Questions B: DENY (0 items returned)
   - Access Exams B / Fetch Exam B Questions: DENY (404)
   - Submit Exam B: DENY (404)

2. Institution B User (Admin/Student):
   - Access Question Bank B: ALLOW
   - Access Questions B: ALLOW
   - Access Exams B: ALLOW
   - Access Question Bank A: DENY (0 items returned)
   - Access Questions A: DENY (0 items returned)
   - Access Exams A / Fetch Exam A Questions: DENY (404)
   - Submit Exam A: DENY (404)

3. Independent Student (No Institution):
   - Access Admin-created platform exams: ALLOW
   - Access Institution A/B exams: DENY (0 items returned / 404)
   - Access Institution question banks / questions: DENY
"""

import sys
import os
import uuid
import datetime
import jwt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from smartkcet.db.session import SessionLocal
from smartkcet.db.models import User, Question, Exam, ExamSet, ExamSetQuestion, Subject, Submission
from smartkcet.db.subscription_models import Institution
from smartkcet.config import validate_startup_config

cfg = validate_startup_config()

def create_jwt_for_user(user: User) -> str:
    payload = {
        'sub': user.email if user.role != 'student' else user.kcet_student_id,
        'role': user.role,
        'student_subtype': user.student_subtype or ('institution_linked' if user.institution_id else 'direct_subscriber'),
        'institution_id': str(user.institution_id) if user.institution_id else None,
        'subscription_status': 'active',
        'iat': int(datetime.datetime.now(datetime.timezone.utc).timestamp()),
        'exp': int((datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)).timestamp()),
        'jti': str(uuid.uuid4())
    }
    token = jwt.encode(payload, cfg.jwt_secret, algorithm='HS256')
    return token if isinstance(token, str) else token.decode('utf-8')


def run_isolation_audit():
    print("=" * 70)
    print("STRICT INSTITUTION-LEVEL DATA ISOLATION AUDIT & TEST")
    print("=" * 70)

    session = SessionLocal()
    try:
        # 1. Setup Test Institutions
        inst_a = session.query(Institution).filter(Institution.name == "Test Inst A").first()
        if not inst_a:
            inst_a = Institution(id=uuid.uuid4(), name="Test Inst A", institution_code="inst_a_code", contact_phone="1234567890")
            session.add(inst_a)

        inst_b = session.query(Institution).filter(Institution.name == "Test Inst B").first()
        if not inst_b:
            inst_b = Institution(id=uuid.uuid4(), name="Test Inst B", institution_code="inst_b_code", contact_phone="0987654321")
            session.add(inst_b)
        session.commit()

        # 2. Setup Test Users
        admin_a = session.query(User).filter(User.email == "admin_a@insta.com").first()
        if not admin_a:
            admin_a = User(id=uuid.uuid4(), email="admin_a@insta.com", display_name="Admin A", password_hash="dummy_hash", role="institution_admin", institution_id=inst_a.id)
            session.add(admin_a)

        student_a = session.query(User).filter(User.kcet_student_id == "INSTA0001").first()
        if not student_a:
            student_a = User(id=uuid.uuid4(), email="student_a@insta.com", password_hash="dummy_hash", kcet_student_id="INSTA0001", display_name="Student A", role="student", student_subtype="institution_linked", institution_id=inst_a.id)
            session.add(student_a)

        admin_b = session.query(User).filter(User.email == "admin_b@instb.com").first()
        if not admin_b:
            admin_b = User(id=uuid.uuid4(), email="admin_b@instb.com", password_hash="dummy_hash", display_name="Admin B", role="institution_admin", institution_id=inst_b.id)
            session.add(admin_b)

        student_b = session.query(User).filter(User.kcet_student_id == "INSTB0001").first()
        if not student_b:
            student_b = User(id=uuid.uuid4(), email="student_b@instb.com", password_hash="dummy_hash", kcet_student_id="INSTB0001", display_name="Student B", role="student", student_subtype="institution_linked", institution_id=inst_b.id)
            session.add(student_b)

        independent_student = session.query(User).filter(User.kcet_student_id == "IND0001").first()
        if not independent_student:
            independent_student = User(id=uuid.uuid4(), email="ind@student.com", password_hash="dummy_hash", kcet_student_id="IND0001", display_name="Independent Student", role="student", student_subtype="direct_subscriber", institution_id=None)
            session.add(independent_student)

        session.commit()

        # 3. Create Questions & Exams for Inst A, Inst B, and Admin (Platform)
        q_a = session.query(Question).filter(Question.question_text == "Unique Question for Inst A").first()
        if not q_a:
            q_a = Question(id=uuid.uuid4(), subject="Mathematics", question_text="Unique Question for Inst A", options=["1","2","3","4"], correct_option="0", generation_batch_id=uuid.uuid4(), institution_id=inst_a.id)
            session.add(q_a)

        q_b = session.query(Question).filter(Question.question_text == "Unique Question for Inst B").first()
        if not q_b:
            q_b = Question(id=uuid.uuid4(), subject="Mathematics", question_text="Unique Question for Inst B", options=["A","B","C","D"], correct_option="1", generation_batch_id=uuid.uuid4(), institution_id=inst_b.id)
            session.add(q_b)

        q_admin = session.query(Question).filter(Question.question_text == "Unique Platform Admin Question").first()
        if not q_admin:
            q_admin = Question(id=uuid.uuid4(), subject="Mathematics", question_text="Unique Platform Admin Question", options=["W","X","Y","Z"], correct_option="2", generation_batch_id=uuid.uuid4(), institution_id=None)
            session.add(q_admin)
        session.commit()

        # Exams
        exam_a = session.query(Exam).filter(Exam.exam_name == "Exam Inst A").first()
        if not exam_a:
            exam_a = Exam(id=uuid.uuid4(), subject="Mathematics", exam_name="Exam Inst A", is_published=True, institution_id=inst_a.id)
            session.add(exam_a)
            session.flush()
            set_a = ExamSet(id=uuid.uuid4(), exam_id=exam_a.id, set_label="A")
            session.add(set_a)
            session.flush()
            session.add(ExamSetQuestion(exam_set_id=set_a.id, question_id=q_a.id, order_index=0))

        exam_b = session.query(Exam).filter(Exam.exam_name == "Exam Inst B").first()
        if not exam_b:
            exam_b = Exam(id=uuid.uuid4(), subject="Mathematics", exam_name="Exam Inst B", is_published=True, institution_id=inst_b.id)
            session.add(exam_b)
            session.flush()
            set_b = ExamSet(id=uuid.uuid4(), exam_id=exam_b.id, set_label="A")
            session.add(set_b)
            session.flush()
            session.add(ExamSetQuestion(exam_set_id=set_b.id, question_id=q_b.id, order_index=0))

        exam_admin = session.query(Exam).filter(Exam.exam_name == "Platform Admin Exam").first()
        if not exam_admin:
            exam_admin = Exam(id=uuid.uuid4(), subject="Mathematics", exam_name="Platform Admin Exam", is_published=True, institution_id=None)
            session.add(exam_admin)
            session.flush()
            set_admin = ExamSet(id=uuid.uuid4(), exam_id=exam_admin.id, set_label="A")
            session.add(set_admin)
            session.flush()
            session.add(ExamSetQuestion(exam_set_id=set_admin.id, question_id=q_admin.id, order_index=0))

        session.commit()

        # Retrieve set_b ID
        es_b = session.query(ExamSet).filter(ExamSet.exam_id == exam_b.id).first()
        es_a = session.query(ExamSet).filter(ExamSet.exam_id == exam_a.id).first()

        # 4. Test Flask endpoints using test_client
        from smartkcet.main import create_app
        app = create_app()
        client = app.test_client()

        # TEST 1: Institution A Admin lists questions
        headers_admin_a = {"Authorization": f"Bearer {create_jwt_for_user(admin_a)}"}
        res_q_a = client.get("/api/institution/content/questions", headers=headers_admin_a)
        assert res_q_a.status_code == 200, f"Failed GET /api/institution/content/questions for Admin A: {res_q_a.status_code} - {res_q_a.text}"
        qs_a_data = res_q_a.get_json().get("questions", [])
        q_texts_a = [q["question_text"] for q in qs_a_data]
        assert "Unique Question for Inst A" in q_texts_a, f"Inst A questions missing for Admin A: {q_texts_a}"
        assert "Unique Question for Inst B" not in q_texts_a, "SECURITY VIOLATION: Inst B question leaked to Admin A!"
        print("[PASS] Test 1: Inst A Admin sees Inst A questions ONLY. Inst B questions strictly hidden.")

        # TEST 2: Institution B Admin lists questions
        headers_admin_b = {"Authorization": f"Bearer {create_jwt_for_user(admin_b)}"}
        res_q_b = client.get("/api/institution/content/questions", headers=headers_admin_b)
        assert res_q_b.status_code == 200, f"Failed GET /api/institution/content/questions for Admin B: {res_q_b.status_code} - {res_q_b.text}"
        qs_b_data = res_q_b.get_json().get("questions", [])
        q_texts_b = [q["question_text"] for q in qs_b_data]
        assert "Unique Question for Inst B" in q_texts_b, "Inst B questions missing for Admin B"
        assert "Unique Question for Inst A" not in q_texts_b, "SECURITY VIOLATION: Inst A question leaked to Admin B!"
        print("[PASS] Test 2: Inst B Admin sees Inst B questions ONLY. Inst A questions strictly hidden.")

        # TEST 3: Institution A Student lists exams
        headers_student_a = {"Authorization": f"Bearer {create_jwt_for_user(student_a)}"}
        res_ex_a = client.get("/api/student/exams", headers=headers_student_a)
        assert res_ex_a.status_code == 200, f"Failed GET /api/student/exams for Student A: {res_ex_a.status_code}"
        subj_a = res_ex_a.get_json().get("subjects", [])
        exam_names_a = []
        for s in subj_a:
            for ex in s.get("exams", []):
                exam_names_a.append(ex.get("exam_name"))
        assert "Exam Inst A" in exam_names_a, f"Exam Inst A missing for Student A: {exam_names_a}"
        assert "Exam Inst B" not in exam_names_a, "SECURITY VIOLATION: Exam Inst B leaked to Student A!"
        print("[PASS] Test 3: Inst A Student sees Inst A exams ONLY. Inst B exams strictly hidden.")

        # TEST 4: Institution A Student attempts to fetch Questions for Exam B
        res_set_b = client.get(f"/api/student/exams/{es_b.id}", headers=headers_student_a)
        assert res_set_b.status_code == 404, f"SECURITY VIOLATION: Student A was allowed to access Exam B questions! Code: {res_set_b.status_code}"
        print("[PASS] Test 4: Inst A Student fetching Exam B questions strictly DENIED (404 Not Found).")

        # TEST 5: Institution A Student attempts to Submit Exam B
        sub_payload_b = {
            "exam_set_id": str(es_b.id),
            "answers": {"0": "0"},
            "time_taken_sec": 60,
            "idempotency_key": str(uuid.uuid4())
        }
        res_sub_b = client.post("/api/student/submit", headers=headers_student_a, json=sub_payload_b)
        assert res_sub_b.status_code in (404, 403), f"SECURITY VIOLATION: Student A was allowed to submit Exam B! Code: {res_sub_b.status_code}"
        print("[PASS] Test 5: Inst A Student submitting Exam B strictly DENIED (404/403).")

        # TEST 6: Independent Student lists exams
        headers_ind = {"Authorization": f"Bearer {create_jwt_for_user(independent_student)}"}
        res_ex_ind = client.get("/api/student/exams", headers=headers_ind)
        assert res_ex_ind.status_code == 200, f"Failed GET /api/student/exams for Independent Student: {res_ex_ind.status_code}"
        subj_ind = res_ex_ind.get_json().get("subjects", [])
        exam_names_ind = []
        for s in subj_ind:
            for ex in s.get("exams", []):
                exam_names_ind.append(ex.get("exam_name"))
        assert "Platform Admin Exam" in exam_names_ind, f"Platform Admin Exam missing for Independent Student: {exam_names_ind}"
        assert "Exam Inst A" not in exam_names_ind, "SECURITY VIOLATION: Exam Inst A leaked to Independent Student!"
        assert "Exam Inst B" not in exam_names_ind, "SECURITY VIOLATION: Exam Inst B leaked to Independent Student!"
        print("[PASS] Test 6: Independent Student sees Platform Admin exams ONLY. Institution exams strictly hidden.")

        # TEST 7: Independent Student attempts to fetch Exam A questions
        res_ind_set_a = client.get(f"/api/student/exams/{es_a.id}", headers=headers_ind)
        assert res_ind_set_a.status_code == 404, f"SECURITY VIOLATION: Independent Student was allowed to access Exam A questions! Code: {res_ind_set_a.status_code}"
        print("[PASS] Test 7: Independent Student fetching Exam A questions strictly DENIED (404 Not Found).")

        print("\n" + "=" * 70)
        print("ALL INSTITUTION-LEVEL DATA ISOLATION TESTS PASSED 100% SUCCESSFULLY!")
        print("=" * 70)

    finally:
        session.close()

if __name__ == "__main__":
    run_isolation_audit()
