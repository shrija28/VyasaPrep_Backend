import requests
import jwt
import datetime
import uuid
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from smartkcet.db.session import SessionLocal
from smartkcet.db.models import User, ExamSet, Exam, Question, ExamSetQuestion
from smartkcet.config import validate_startup_config
from smartkcet.submissions.scoring import _is_correct_answer
from smartkcet.rag.mcq_extractor import shuffle_options_for_set_label

session = SessionLocal()

es_b = session.query(ExamSet).filter(ExamSet.set_label == "B").first()
exam = session.get(Exam, es_b.exam_id)

eqs = session.query(Question, ExamSetQuestion.order_index).join(
    ExamSetQuestion, ExamSetQuestion.question_id == Question.id
).filter(
    ExamSetQuestion.exam_set_id == es_b.id
).order_by(ExamSetQuestion.order_index.asc()).all()

print(f"Set B ID: {es_b.id} | Total Questions: {len(eqs)}")

for idx, (q, order_idx) in enumerate(eqs):
    shuffled_opts, new_ans = shuffle_options_for_set_label(q.options or [], q.correct_option, "B")
    
    wrong_given = "0" if new_ans != "0" else "1"
    is_corr = _is_correct_answer(wrong_given, new_ans, shuffled_opts)

    if is_corr:
        print(f"\n[BUG FOUND] Question {idx} (Order {order_idx}):")
        print(f"  Q Text: {q.question_text[:60]}")
        print(f"  Orig Correct: {q.correct_option!r}")
        print(f"  Orig Opts: {q.options}")
        print(f"  Shuffled Opts: {shuffled_opts}")
        print(f"  Shuffled new_ans: {new_ans!r}")
        print(f"  Wrong Given Tested: {wrong_given!r}")
        print(f"  _is_correct_answer result: {is_corr}")

session.close()
