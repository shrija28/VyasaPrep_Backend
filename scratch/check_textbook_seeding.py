import sys
import os
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from smartkcet.rag.textbook_sync import list_all_supabase_textbooks, stream_textbook_from_supabase
from smartkcet.db.session import SessionLocal
from smartkcet.db.models import IndexedFile

def check_seeding():
    print("=== CHECKING TEXTBOOK SEEDING STATUS IN BACKEND ===")
    
    # 1. Supabase Storage check
    books_by_subject = list_all_supabase_textbooks()
    total_supabase_books = sum(len(v) for v in books_by_subject.values())
    
    print("\n--- 1. SUPABASE STORAGE ('vyasaprep-textbook' BUCKET) ---")
    print(f"Total Textbooks Found in Supabase Storage: {total_supabase_books}")
    for subject, books in books_by_subject.items():
        print(f" - {subject}: {len(books)} books")
        if books:
            sample = books[0]
            size = sample.get('size_bytes') or sample.get('size', 0)
            print(f"   Sample: {sample.get('filename')} ({size} bytes)")

    # 2. Database IndexedFile table check
    db = SessionLocal()
    db_indexed_files = db.query(IndexedFile).all()
    print("\n--- 2. DATABASE 'IndexedFile' TABLE RECORDS ---")
    print(f"Total IndexedFile Records in PostgreSQL Database: {len(db_indexed_files)}")
    
    file_type_counts = {}
    for f in db_indexed_files:
        file_type_counts[f.file_type] = file_type_counts.get(f.file_type, 0) + 1
        
    print(f"File Type Breakdown: {file_type_counts}")
    print("\nFirst 10 DB IndexedFile Records:")
    for f in db_indexed_files[:10]:
        scope = "Admin/Global" if f.institution_id is None else f"Institution ({f.institution_id})"
        print(f" - ID: {f.id} | Name: {f.filename} | Subject: {f.subject} | Type: {f.file_type} | Chunks: {f.chunk_count} | Scope: {scope}")

    # 3. Direct In-Memory Streaming Test
    print("\n--- 3. SUPABASE STREAMING TEST ---")
    sample_path = None
    for s, b_list in books_by_subject.items():
        if b_list:
            sample_path = b_list[0].get('remote_path') or b_list[0].get('filename')
            break
            
    if sample_path:
        res = stream_textbook_from_supabase(sample_path)
        if res:
            stream, name, size = res
            print(f"SUCCESS: Streamed '{name}' directly from Supabase Storage in-memory ({size} bytes).")
        else:
            print(f"FAILED to stream sample textbook '{sample_path}' from Supabase.")
    else:
        print("No sample file path found in Supabase bucket.")

if __name__ == "__main__":
    check_seeding()
