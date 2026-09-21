"""Verification script to test MCQ generation, blueprint allocation, and 60-question set guarantees."""

import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from smartkcet.admin.exams import QUESTIONS_PER_SET, SET_LABELS
from smartkcet.rag.blueprint import allocate_blueprint_questions

print(f"OK: QUESTIONS_PER_SET constant = {QUESTIONS_PER_SET}")
assert QUESTIONS_PER_SET == 60, f"Expected 60, got {QUESTIONS_PER_SET}"

# Test dummy blueprint allocation for 60 questions
dummy_questions = []
for i in range(100):
    class DummyQ:
        def __init__(self, qid, text, topic, subject):
            self.id = qid
            self.question_text = text
            self.topic = topic
            self.subject = subject
    dummy_questions.append(DummyQ(i, f"Question {i} about Physics topic", "Current Electricity", "Physics"))

allocated = allocate_blueprint_questions(
    available_questions=dummy_questions,
    subject="Physics",
    uploaded_topics=None,
    total_questions=60
)

print(f"OK: Allocated questions count for Physics = {len(allocated)}")
assert len(allocated) == 60, f"Expected 60 questions, got {len(allocated)}"

print("SUCCESS: All 60-question set logic verified successfully!")
