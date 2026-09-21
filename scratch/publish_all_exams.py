import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    print("--- UPDATING ALL EXAMS TO is_published = True ---")
    res = conn.execute(text("UPDATE exams SET is_published = True WHERE is_published = False OR is_published IS NULL"))
    conn.commit()
    print(f"Updated {res.rowcount} exams to is_published = True.")

    print("\n--- RE-QUERYING ALL EXAMS IN DATABASE ---")
    exams = conn.execute(text("""
        SELECT e.id, e.exam_name, e.subject, e.is_published, e.institution_id, i.name as inst_name
        FROM exams e
        LEFT JOIN institutions i ON e.institution_id = i.id
        ORDER BY e.created_at DESC
    """)).fetchall()
    
    print(f"Total exams: {len(exams)}")
    for ex in exams:
        print(f"  • ID: {ex[0]} | Name: '{ex[1]}' | Subj: {ex[2]} | Published: {ex[3]} | Inst: {ex[5]}")
