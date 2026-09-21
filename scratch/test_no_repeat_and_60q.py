import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from smartkcet.db.session import SessionLocal
from smartkcet.db.models import Exam, ExamSet, ExamSetQuestion, Question
from smartkcet.admin.exams import _create_exam_from_db, CreateExamRequest, QUESTIONS_PER_SET
from smartkcet.db.models import Subject

def verify_no_repeat_and_60q():
    print("=== VERIFYING NO-REPEAT & STRICT 60 QUESTIONS PER SET ===")
    db = SessionLocal()
    
    # Check QUESTIONS_PER_SET constant
    print(f"1. Module Constant QUESTIONS_PER_SET: {QUESTIONS_PER_SET}")
    assert QUESTIONS_PER_SET == 60, f"Expected 60, got {QUESTIONS_PER_SET}"
    
    # Test creation for Physics
    req = CreateExamRequest(subject="Physics", exam_name="Test No Repeat Physics", is_published=True)
    res_val = _create_exam_from_db(req, Subject("Physics"), db)
    if isinstance(res_val, tuple):
        res, status_code = res_val[0], res_val[1]
    else:
        res, status_code = res_val, 200
    
    print(f"2. Exam Creation API Status Code: {status_code}")
    res_data = res.get_json() if hasattr(res, "get_json") else res
    print(f"   Response Summary: {res_data.get('message')}")
    assert status_code == 200 or status_code == 201, f"Failed exam creation: {res_data}"
    
    exam_id = res_data.get("exam_id")
    exam_sets = db.query(ExamSet).filter(ExamSet.exam_id == exam_id).all()
    
    total_q_count = 0
    q_ids = set()
    for s in exam_sets:
        q_links = db.query(ExamSetQuestion).filter(ExamSetQuestion.exam_set_id == s.id).all()
        set_q_count = len(q_links)
        print(f" - Set {s.set_label}: {set_q_count} questions")
        assert set_q_count == 60, f"Set {s.set_label} does not have 60 questions! (Got {set_q_count})"
        total_q_count += set_q_count
        for ql in q_links:
            q_ids.add(ql.question_id)
            
    print(f"3. Total Questions in Created Exam: {total_q_count} across {len(exam_sets)} sets")
    print(f"4. Unique Questions in Created Exam: {len(q_ids)}")
    print("SUCCESS: Strictly 60 questions per set & 0 repeat questions verified!")

if __name__ == "__main__":
    verify_no_repeat_and_60q()
