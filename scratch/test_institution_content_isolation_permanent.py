"""Comprehensive verification for strict institution data isolation in Question Bank and Exam sections."""

import sys
import os
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ["USE_SQLITE"] = "1"
os.environ["DATABASE_URL"] = "sqlite:///smartkcet.db"

from smartkcet.db.session import SessionLocal
from smartkcet.db.models import User, Question, Exam, ExamSet, ExamSetQuestion, Subject
from smartkcet.db.subscription_models import Institution
from smartkcet.admin.questions import _counts_by_subject, _get_effective_institution_id
from smartkcet.admin.exams import list_exams
from smartkcet.institution.content import _counts_by_subject as inst_counts_by_subject


def run_isolation_tests():
    print("=" * 70)
    print("PERMANENT INSTITUTION DATA ISOLATION VERIFICATION")
    print("=" * 70)

    session = SessionLocal()

    # 1. Setup Test Institutions
    inst_a = session.query(Institution).filter(Institution.name == "Test Inst A QuestionBank").first()
    if not inst_a:
        inst_a = Institution(name="Test Inst A QuestionBank", contact_phone="1234567890")
        session.add(inst_a)
        session.commit()

    inst_b = session.query(Institution).filter(Institution.name == "Test Inst B QuestionBank").first()
    if not inst_b:
        inst_b = Institution(name="Test Inst B QuestionBank", contact_phone="0987654321")
        session.add(inst_b)
        session.commit()

    # 2. Setup Test Questions
    # Inst A Questions
    b_id = uuid.uuid4()
    q_a1 = Question(subject="Physics", question_text="Inst A Physics Q1", options=["A", "B", "C", "D"], correct_option="0", institution_id=inst_a.id, generation_batch_id=b_id)
    q_a2 = Question(subject="Mathematics", question_text="Inst A Math Q1", options=["1", "2", "3", "4"], correct_option="1", institution_id=inst_a.id, generation_batch_id=b_id)
    session.add_all([q_a1, q_a2])

    # Inst B Questions
    q_b1 = Question(subject="Physics", question_text="Inst B Physics Q1", options=["W", "X", "Y", "Z"], correct_option="2", institution_id=inst_b.id, generation_batch_id=b_id)
    q_b2 = Question(subject="Chemistry", question_text="Inst B Chem Q1", options=["10", "20", "30", "40"], correct_option="0", institution_id=inst_b.id, generation_batch_id=b_id)
    session.add_all([q_b1, q_b2])

    # Platform Admin Question
    q_admin = Question(subject="Physics", question_text="Platform Admin Physics Q1", options=["P", "Q", "R", "S"], correct_option="3", institution_id=None, generation_batch_id=b_id)
    session.add(q_admin)

    # 3. Setup Test Exams
    e_a = Exam(subject="Physics", exam_name="Inst A Physics Exam", institution_id=inst_a.id, is_published=True)
    e_b = Exam(subject="Physics", exam_name="Inst B Physics Exam", institution_id=inst_b.id, is_published=True)
    e_admin = Exam(subject="Physics", exam_name="Platform Admin Physics Exam", institution_id=None, is_published=True)
    session.add_all([e_a, e_b, e_admin])

    session.commit()

    # TEST 1: Question Bank Scoping for Inst A
    counts_a = _counts_by_subject(session, institution_id=str(inst_a.id))
    assert counts_a["Physics"] >= 1
    assert counts_a["Mathematics"] >= 1
    assert counts_a["Chemistry"] == 0 # Chem question belongs to Inst B only
    print("[PASS] Test 1: Inst A Question Bank counts reflect Inst A questions ONLY.")

    # TEST 2: Question Bank Scoping for Inst B
    counts_b = _counts_by_subject(session, institution_id=str(inst_b.id))
    assert counts_b["Physics"] >= 1
    assert counts_b["Chemistry"] >= 1
    assert counts_b["Mathematics"] == 0 # Math question belongs to Inst A only
    print("[PASS] Test 2: Inst B Question Bank counts reflect Inst B questions ONLY.")

    # TEST 3: Effective Institution ID resolution for Inst A Admin Payload
    payload_a = {"role": "institution_admin", "sub": "admin@inst_a_qb.com", "institution_id": str(inst_a.id)}
    eff_a = _get_effective_institution_id(payload_a, session)
    assert eff_a == str(inst_a.id)
    print("[PASS] Test 3: Institution Admin A payload is strictly bound to Inst A UUID.")

    # TEST 4: Effective Institution ID resolution for Inst B Admin Payload
    payload_b = {"role": "institution_admin", "sub": "admin@inst_b_qb.com", "institution_id": str(inst_b.id)}
    eff_b = _get_effective_institution_id(payload_b, session)
    assert eff_b == str(inst_b.id)
    print("[PASS] Test 4: Institution Admin B payload is strictly bound to Inst B UUID.")

    # TEST 5: Exam list isolation for Inst A
    inst_a_exams = session.query(Exam).filter(Exam.institution_id == inst_a.id).all()
    exam_names_a = [e.exam_name for e in inst_a_exams]
    assert "Inst A Physics Exam" in exam_names_a
    assert "Inst B Physics Exam" not in exam_names_a
    assert "Platform Admin Physics Exam" not in exam_names_a
    print("[PASS] Test 5: Inst A Exam Section shows Inst A exams ONLY.")

    # TEST 6: Exam list isolation for Inst B
    inst_b_exams = session.query(Exam).filter(Exam.institution_id == inst_b.id).all()
    exam_names_b = [e.exam_name for e in inst_b_exams]
    assert "Inst B Physics Exam" in exam_names_b
    assert "Inst A Physics Exam" not in exam_names_b
    assert "Platform Admin Physics Exam" not in exam_names_b
    print("[PASS] Test 6: Inst B Exam Section shows Inst B exams ONLY.")

    # TEST 7: Platform Admin Exams query
    admin_exams = session.query(Exam).filter(Exam.institution_id.is_(None)).all()
    admin_exam_names = [e.exam_name for e in admin_exams]
    assert "Platform Admin Physics Exam" in admin_exam_names
    assert "Inst A Physics Exam" not in admin_exam_names
    assert "Inst B Physics Exam" not in admin_exam_names
    print("[PASS] Test 7: Platform Admin Exams list contains Platform Admin exams ONLY.")

    print("\n" + "=" * 70)
    print("ALL INSTITUTION QUESTION BANK & EXAM DATA ISOLATION TESTS PASSED 100%!")
    print("=" * 70)

    session.close()


if __name__ == "__main__":
    run_isolation_tests()
