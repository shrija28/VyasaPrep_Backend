import sys
sys.path.insert(0, ".")

from smartkcet.rag.textbook_sync import list_supabase_textbooks, get_textbook_stream
from smartkcet.db.session import SessionLocal
from smartkcet.db.models import IndexedFile

def test_textbook_status():
    print("=== TESTING TEXTBOOK SEEDING & STREAMING STATUS ===")

    # 1. Supabase Storage Bucket Test
    try:
        files = list_supabase_textbooks()
        print(f"1. Supabase Storage Bucket ('vyasaprep-textbook'): {len(files)} PDFs available")
        if files:
            print(f"   Sample PDFs: {[f['name'] for f in files[:3]]}")
    except Exception as e:
        print(f"1. Supabase Storage error: {e}")

    # 2. Database IndexedFile Table Test
    session = SessionLocal()
    try:
        idx_count = session.query(IndexedFile).count()
        print(f"2. Database IndexedFile table: {idx_count} indexed textbook records")
        sample_files = session.query(IndexedFile).limit(3).all()
        for f in sample_files:
            print(f"   - {f.filename} | Subject: {f.subject} | InstID: {f.institution_id}")
    except Exception as e:
        print(f"2. Database IndexedFile error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    test_textbook_status()
