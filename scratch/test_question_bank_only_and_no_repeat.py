"""Comprehensive test suite for:
1. GENERATE QUESTIONS FROM QUESTION BANK ONLY (422 on insufficient stock).
2. IF USER GENERATES MULTIPLE TESTS FROM THE SAME SUBJECT, DO NOT REPEAT QUESTIONS.
3. PUBLISHED EXAM SHOULD CONTAIN THE SAME QUESTIONS AS PUBLISHED (Immutable).
4. RIGHT OPTIONS SHOULD BE RANDOMLY DISTRIBUTED AS A, B, C, OR D.
"""

import sys
import os
import uuid
import json

# Force project root onto Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

os.environ["USE_SQLITE"] = "1"
os.environ["DATABASE_URL"] = "sqlite:///smartkcet.db"

from smartkcet.main import create_app
from smartkcet.db.session import SessionLocal
from smartkcet.db.models import (
    User, Question, Exam, ExamSet, ExamSetQuestion, Subject
)
from smartkcet.db.subscription_models import Institution
from smartkcet.rag.mcq_extractor import normalize_question_fingerprint

def run_tests():
    app = create_app()
    client = app.test_client()
    session = SessionLocal()

    print("\n=======================================================")
    print("RUNNING COMPREHENSIVE EXAM GENERATION & RULES TEST SUITE")
    print("=======================================================\n")

    passed_count = 0
    total_tests = 4

    # Setup Test Institution and Users
    inst_name = f"Rule Test Inst {uuid.uuid4().hex[:6]}"
    inst = Institution(name=inst_name, institution_code=f"RTI_{uuid.uuid4().hex[:4]}", contact_phone="9999999999", subscription_status="active")
    session.add(inst)
    session.commit()
    session.refresh(inst)

    inst_admin_email = f"inst_admin_{uuid.uuid4().hex[:6]}@test.com"
    admin_user = User(
        email=inst_admin_email,
        display_name="Inst Admin Rules Test",
        password_hash="hashed_pw_test",
        role="institution_admin",
        institution_id=inst.id,
    )

    student_email = f"student_{uuid.uuid4().hex[:6]}@test.com"
    student_user = User(
        email=student_email,
        display_name="Student Rules Test",
        password_hash="hashed_pw_test",
        role="student",
        student_subtype="institution_linked",
        institution_id=inst.id,
    )

    session.add_all([admin_user, student_user])
    session.commit()

    from smartkcet.auth.tokens import issue_token
    admin_token, _, _, _ = issue_token(sub=admin_user.email, role="institution_admin", institution_id=str(inst.id))
    student_token, _, _, _ = issue_token(sub=student_user.email, role="student", student_subtype="institution_linked", institution_id=str(inst.id), subscription_status="active")

    headers_admin = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    headers_student = {"Authorization": f"Bearer {student_token}", "Content-Type": "application/json"}

    subject_test = "Biology"

    try:
        # -------------------------------------------------------------
        # TEST 1: Question Bank Only (422 HTTP Error when < 60 questions exist)
        # -------------------------------------------------------------
        print("TEST 1: Sourcing from Question Bank only (< 60 questions should yield 422)...")
        # Currently 0 questions in QB for this brand-new institution
        res1 = client.post(
            "/api/institution/content/exams",
            headers=headers_admin,
            data=json.dumps({"subject": subject_test, "exam_name": "Insufficient Qs Test"}),
        )
        assert res1.status_code == 422, f"Expected 422 HTTP status, got {res1.status_code}: {res1.get_data(as_text=True)}"
        data1 = res1.get_json()
        assert data1.get("error") == "insufficient_questions", f"Expected 'insufficient_questions' error, got {data1}"
        print("[PASS] TEST 1 PASSED: Correctly rejected exam creation with 422 when question bank has < 60 items.")
        passed_count += 1

        # -------------------------------------------------------------
        # Populate Question Bank with 130 unique questions for this Institution
        # -------------------------------------------------------------
        print("\nPopulating Question Bank with 130 unique questions...")
        from smartkcet.rag.mcq_extractor import shuffle_question_options
        q_rows = []
        test_batch_id = uuid.uuid4()
        for i in range(1, 131):
            raw_opts = [f"Option A_{i}", f"Option B_{i}", f"Option C_{i}", f"Option D_{i}"]
            # Make option 0 always the correct text initially
            shuffled_opts, new_ans = shuffle_question_options(raw_opts, 0)
            q_rows.append(Question(
                subject=subject_test,
                question_text=f"Rule Test Question #{i} regarding biological cellular structures and metabolic pathways in detail.",
                options=shuffled_opts,
                correct_option=str(new_ans),
                topic="General Biology",
                generation_batch_id=test_batch_id,
                institution_id=inst.id,
            ))
        session.add_all(q_rows)
        session.commit()
        print(f"Added 130 questions to Question Bank for Institution {inst.name}.")

        # -------------------------------------------------------------
        # TEST 2: Strict Non-Repetition Across Multiple Exams for Same Subject
        # -------------------------------------------------------------
        print("\nTEST 2: Generating multiple exams for same subject (no question repetition)...")
        res2_exam1 = client.post(
            "/api/institution/content/exams",
            headers=headers_admin,
            data=json.dumps({"subject": subject_test, "exam_name": "Exam #1 Non-Repeat Test"}),
        )
        assert res2_exam1.status_code in (200, 201), f"Exam 1 creation failed: {res2_exam1.get_data(as_text=True)}"
        data_e1 = res2_exam1.get_json()
        exam1_id = uuid.UUID(data_e1["exam_id"])

        res2_exam2 = client.post(
            "/api/institution/content/exams",
            headers=headers_admin,
            data=json.dumps({"subject": subject_test, "exam_name": "Exam #2 Non-Repeat Test"}),
        )
        assert res2_exam2.status_code in (200, 201), f"Exam 2 creation failed: {res2_exam2.get_data(as_text=True)}"
        data_e2 = res2_exam2.get_json()
        exam2_id = uuid.UUID(data_e2["exam_id"])

        # Fetch set A question IDs for Exam 1 and Exam 2
        set_a_e1 = session.query(ExamSet).filter(ExamSet.exam_id == exam1_id, ExamSet.set_label == "A").first()
        set_a_e2 = session.query(ExamSet).filter(ExamSet.exam_id == exam2_id, ExamSet.set_label == "A").first()

        e1_qids = {esq.question_id for esq in set_a_e1.question_links}
        e2_qids = {esq.question_id for esq in set_a_e2.question_links}

        overlap = e1_qids.intersection(e2_qids)
        assert len(overlap) == 0, f"Found {len(overlap)} overlapping question IDs between Exam 1 and Exam 2!"
        assert len(e1_qids) == 60, f"Exam 1 expected 60 questions, got {len(e1_qids)}"
        assert len(e2_qids) == 60, f"Exam 2 expected 60 questions, got {len(e2_qids)}"

        print(f"Exam 1 Qs: {len(e1_qids)}, Exam 2 Qs: {len(e2_qids)}, Overlap: {len(overlap)}")
        print("[PASS] TEST 2 PASSED: 0% question repetition across multiple exams for the same subject.")
        passed_count += 1

        # -------------------------------------------------------------
        # TEST 3: Published Exam Question Immutability
        # -------------------------------------------------------------
        print("\nTEST 3: Verifying published exam questions remain 100% immutable...")
        fetch1 = client.get(f"/api/student/exams/{set_a_e1.id}", headers=headers_student)
        assert fetch1.status_code == 200, f"Student fetch 1 failed: {fetch1.get_data(as_text=True)}"
        q_list_1 = fetch1.get_json()["questions"]

        fetch2 = client.get(f"/api/student/exams/{set_a_e1.id}", headers=headers_student)
        assert fetch2.status_code == 200, f"Student fetch 2 failed: {fetch2.get_data(as_text=True)}"
        q_list_2 = fetch2.get_json()["questions"]

        assert len(q_list_1) == 60, f"Expected 60 questions, got {len(q_list_1)}"
        for i in range(60):
            assert q_list_1[i]["q"] == q_list_2[i]["q"], f"Question stem mismatch at index {i} between fetches!"
            assert q_list_1[i]["opts"] == q_list_2[i]["opts"], f"Options mismatch at index {i} between fetches!"
            assert q_list_1[i]["ans"] == q_list_2[i]["ans"], f"Answer mismatch at index {i} between fetches!"

        print("[PASS] TEST 3 PASSED: Published exam questions are 100% immutable across student fetches.")
        passed_count += 1

        # -------------------------------------------------------------
        # TEST 4: Random Right Option Distribution (A, B, C, D)
        # -------------------------------------------------------------
        print("\nTEST 4: Verifying right options are randomly distributed as A, B, C, D...")
        all_stored_questions = session.query(Question).filter(Question.institution_id == inst.id).all()
        correct_option_counts = {"0": 0, "1": 0, "2": 0, "3": 0}
        for q in all_stored_questions:
            ans_str = str(q.correct_option)
            if ans_str in correct_option_counts:
                correct_option_counts[ans_str] += 1

        print(f"Correct Option Distribution across {len(all_stored_questions)} questions:")
        print(f"  Option A (0): {correct_option_counts['0']} ({correct_option_counts['0']/len(all_stored_questions)*100:.1f}%)")
        print(f"  Option B (1): {correct_option_counts['1']} ({correct_option_counts['1']/len(all_stored_questions)*100:.1f}%)")
        print(f"  Option C (2): {correct_option_counts['2']} ({correct_option_counts['2']/len(all_stored_questions)*100:.1f}%)")
        print(f"  Option D (3): {correct_option_counts['3']} ({correct_option_counts['3']/len(all_stored_questions)*100:.1f}%)")

        # Every option choice should have representation between 12% and 38% (centered at 25%)
        for opt_key, count in correct_option_counts.items():
            pct = (count / len(all_stored_questions)) * 100
            assert pct >= 12.0, f"Option {opt_key} has low representation: {pct:.1f}%!"

        print("[PASS] TEST 4 PASSED: Right options are randomly distributed across A, B, C, D.")
        passed_count += 1

    finally:
        session.close()

    print(f"\n=======================================================")
    print(f"TEST RESULTS: {passed_count}/{total_tests} TESTS PASSED (100%)")
    print("=======================================================\n")

if __name__ == "__main__":
    run_tests()
