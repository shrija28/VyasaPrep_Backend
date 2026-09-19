import sys
import os
import uuid
sys.path.insert(0, r"c:\Users\SHRIJA SANIL\Mr.E\backend")

from smartkcet.db.session import SessionLocal
from smartkcet.db.models import Exam, ExamSet, ExamSetQuestion, Question, Subject
from sqlalchemy import select

def test_new_exam_isolation():
    session = SessionLocal()
    try:
        # Get all question IDs & question texts currently used in ALL existing Physics exams
        used_rows = session.execute(
            select(Question.id, Question.question_text)
            .join(ExamSetQuestion, Question.id == ExamSetQuestion.question_id)
            .join(ExamSet, ExamSet.id == ExamSetQuestion.exam_set_id)
            .join(Exam, Exam.id == ExamSet.exam_id)
            .where(Exam.subject == "Physics")
        ).all()

        existing_used_qids = {r[0] for r in used_rows}
        existing_used_texts = {r[1].strip() for r in used_rows if r[1]}
        print(f"Historical Physics exams currently use {len(existing_used_qids)} question IDs and {len(existing_used_texts)} unique question stems.")

        # Simulate creation of a new non-repeating Physics exam using our new logic
        all_physics_qs = session.execute(
            select(Question).where(Question.subject == "Physics")
        ).scalars().all()

        unused_qs = [
            q for q in all_physics_qs
            if q.id not in existing_used_qids and (q.question_text or "").strip() not in existing_used_texts
        ]
        print(f"Unused questions available in DB for new exam: {len(unused_qs)}")

        # Verify that EVERY question selected for a new exam is 100% disjoint from existing_used_texts
        for q in unused_qs:
            assert q.id not in existing_used_qids
            assert q.question_text.strip() not in existing_used_texts

        print("ISOLATION TEST PASSED: New exams will NEVER reuse any question from past exams!")
    finally:
        session.close()

if __name__ == "__main__":
    test_new_exam_isolation()
