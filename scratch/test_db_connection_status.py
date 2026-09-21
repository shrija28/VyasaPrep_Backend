from sqlalchemy import text
from smartkcet.db.session import SessionLocal
from smartkcet.db.models import User, Question, Exam, Submission
from smartkcet.db.subscription_models import Institution, Subscription

def test_db_status():
    print("=== TESTING DATABASE CONNECTION ===")
    session = SessionLocal()
    try:
        # Test raw connection query
        res = session.execute(text("SELECT version();")).scalar()
        print(f"Status: CONNECTED")
        print(f"Database Version: {res}")

        # Count records across core tables
        user_count = session.query(User).count()
        inst_count = session.query(Institution).count()
        q_count = session.query(Question).count()
        exam_count = session.query(Exam).count()
        subm_count = session.query(Submission).count()
        sub_count = session.query(Subscription).count()

        print("\n--- ACTIVE TABLE RECORD COUNTS ---")
        print(f"Users: {user_count}")
        print(f"Institutions: {inst_count}")
        print(f"Questions: {q_count}")
        print(f"Exams: {exam_count}")
        print(f"Submissions (Attempts): {subm_count}")
        print(f"Subscriptions: {sub_count}")

    except Exception as e:
        print(f"Status: ERROR ({e})")
    finally:
        session.close()

if __name__ == "__main__":
    test_db_status()
