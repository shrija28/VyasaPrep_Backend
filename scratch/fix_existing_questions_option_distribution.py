"""Script to randomize correct option placements for pre-existing DB questions
and ensure option distribution across A, B, C, D is balanced in smartkcet.db.
"""

import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

os.environ["USE_SQLITE"] = "1"
os.environ["DATABASE_URL"] = "sqlite:///smartkcet.db"

from smartkcet.db.session import SessionLocal
from smartkcet.db.models import Question
from smartkcet.rag.mcq_extractor import shuffle_question_options

def fix_db_questions():
    session = SessionLocal()
    try:
        questions = session.query(Question).all()
        print(f"Inspecting {len(questions)} pre-existing questions in smartkcet.db...")
        updated = 0
        for q in questions:
            if isinstance(q.options, list) and len(q.options) == 4:
                shuffled_opts, new_ans = shuffle_question_options(q.options, q.correct_option)
                q.options = shuffled_opts
                q.correct_option = str(new_ans)
                updated += 1
        session.commit()
        print(f"Successfully randomized option placement for {updated} questions in smartkcet.db.")

        # Recount distribution
        counts = {"0": 0, "1": 0, "2": 0, "3": 0}
        for q in session.query(Question).all():
            ans_str = str(q.correct_option)
            if ans_str in counts:
                counts[ans_str] += 1
        print("Updated Correct Option Distribution in DB:")
        print(f"  Option A (0): {counts['0']}")
        print(f"  Option B (1): {counts['1']}")
        print(f"  Option C (2): {counts['2']}")
        print(f"  Option D (3): {counts['3']}")
    finally:
        session.close()

if __name__ == "__main__":
    fix_db_questions()
