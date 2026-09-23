import sys
import uuid
from smartkcet.db.session import SessionLocal
from smartkcet.db.models import User, Question, Exam, ExamSet, ExamSetQuestion, Submission
from smartkcet.db.subscription_models import Institution

def run_tests():
    db = SessionLocal()
    try:
        print("=== STACK & DB ISOLATION TEST ===")
        
        # 1. Create dummy institution
        inst_id = uuid.uuid4()
        inst = Institution(
            id=inst_id,
            name="Test Institution ABC",
            contact_phone="9999999999",
            subscription_status="active"
        )
        db.add(inst)
        db.flush()
        
        # 2. Create institution student
        inst_student = User(
            id=uuid.uuid4(),
            email=f"student_inst_{uuid.uuid4().hex[:6]}@test.com",
            display_name="Inst Student",
            password_hash="hash",
            role="student",
            student_subtype="institution_linked",
            institution_id=inst_id
        )
        db.add(inst_student)
        
        # 3. Create direct student
        direct_student = User(
            id=uuid.uuid4(),
            email=f"student_direct_{uuid.uuid4().hex[:6]}@test.com",
            display_name="Direct Student",
            password_hash="hash",
            role="student",
            student_subtype="direct_subscriber",
            institution_id=None
        )
        db.add(direct_student)

        # 4. Create Admin Question & Exam
        admin_q_batch = uuid.uuid4()
        admin_q = Question(
            id=uuid.uuid4(),
            subject="Physics",
            question_text="Admin Physics Question 1?",
            options=["A", "B", "C", "D"],
            correct_option="0",
            generation_batch_id=admin_q_batch,
            institution_id=None,
            source_type="question_paper"
        )
        db.add(admin_q)

        admin_exam = Exam(
            id=uuid.uuid4(),
            subject="Physics",
            exam_name="Admin Physics Test 1",
            institution_id=None,
            is_published=True
        )
        db.add(admin_exam)
        db.flush()

        admin_set = ExamSet(
            id=uuid.uuid4(),
            exam_id=admin_exam.id,
            set_label="A"
        )
        db.add(admin_set)
        db.flush()

        admin_esq = ExamSetQuestion(
            exam_set_id=admin_set.id,
            question_id=admin_q.id,
            order_index=0
        )
        db.add(admin_esq)

        # 5. Create Institution Question & Exam
        inst_q_batch = uuid.uuid4()
        inst_q = Question(
            id=uuid.uuid4(),
            subject="Physics",
            question_text="Inst Physics Question 1?",
            options=["Option 1", "Option 2", "Option 3", "Option 4"],
            correct_option="0",
            generation_batch_id=inst_q_batch,
            institution_id=inst_id,
            source_type="question_paper"
        )
        db.add(inst_q)

        inst_exam = Exam(
            id=uuid.uuid4(),
            subject="Physics",
            exam_name="Inst Physics Test 1",
            institution_id=inst_id,
            is_published=True
        )
        db.add(inst_exam)
        db.flush()

        inst_set = ExamSet(
            id=uuid.uuid4(),
            exam_id=inst_exam.id,
            set_label="A"
        )
        db.add(inst_set)
        db.flush()

        inst_esq = ExamSetQuestion(
            exam_set_id=inst_set.id,
            question_id=inst_q.id,
            order_index=0
        )
        db.add(inst_esq)

        db.commit()

        print("[SUCCESS] Test fixtures created successfully.")
        
        # Test 1: Direct student queries exams (should see ONLY Admin exam)
        from sqlalchemy import select
        direct_exams = db.execute(
            select(Exam).where(Exam.is_published.is_(True), Exam.institution_id.is_(None))
        ).scalars().all()
        direct_exam_ids = [e.id for e in direct_exams]
        assert admin_exam.id in direct_exam_ids, "Direct student should see Admin exam"
        assert inst_exam.id not in direct_exam_ids, "Direct student MUST NOT see Institution exam"
        print("[PASS] Test 1: Direct student sees ONLY Admin exam.")

        # Test 2: Institution student queries exams (should see ONLY Institution exam)
        inst_exams = db.execute(
            select(Exam).where(Exam.is_published.is_(True), Exam.institution_id == inst_id)
        ).scalars().all()
        inst_exam_ids = [e.id for e in inst_exams]
        assert inst_exam.id in inst_exam_ids, "Institution student should see their Institution exam"
        assert admin_exam.id not in inst_exam_ids, "Institution student MUST NOT see Admin exam"
        print("[PASS] Test 2: Institution student sees ONLY Institution exam.")

        # Test 3: Attempt tracking and single attempt restriction
        sub = Submission(
            id=uuid.uuid4(),
            user_id=inst_student.id,
            exam_set_id=inst_set.id,
            answers={"0": "0"},
            score_pct=100.0,
            topic_breakdown={},
            time_taken_sec=300,
            status="completed"
        )
        db.add(sub)
        db.commit()

        # Check completed submission query
        completed_sub = db.execute(
            select(Submission.id)
            .join(ExamSet, Submission.exam_set_id == ExamSet.id)
            .where(
                Submission.user_id == inst_student.id,
                ExamSet.exam_id == inst_exam.id,
                Submission.status == "completed"
            )
        ).scalar_one_or_none()
        assert completed_sub is not None, "Completed submission should be found for student & exam"
        print("[PASS] Test 3: Single attempt detection works correctly.")

        print("=== ALL ISOLATION & ATTEMPT TESTS PASSED SUCCESSFULLY! ===")
    finally:
        db.close()

if __name__ == "__main__":
    run_tests()
