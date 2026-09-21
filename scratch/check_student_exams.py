import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    print("=== 1. ALL EXAMS IN DATABASE ===")
    exams = conn.execute(text("""
        SELECT e.id, e.exam_name, e.subject, e.is_published, e.institution_id, i.name as inst_name
        FROM exams e
        LEFT JOIN institutions i ON e.institution_id = i.id
        ORDER BY e.created_at DESC
    """)).fetchall()
    
    print(f"Total exams: {len(exams)}")
    for ex in exams:
        print(f"  • ID: {ex[0]} | Name: '{ex[1]}' | Subj: {ex[2]} | Published: {ex[3]} | Inst: {ex[5]} ({ex[4]})")

    print("\n=== 2. PUBLISHED EXAMS (is_published = True) ===")
    pub_exams = [ex for ex in exams if ex[3] is True]
    print(f"Published count: {len(pub_exams)}")
    for ex in pub_exams:
        print(f"  • Name: '{ex[1]}' | Subj: {ex[2]} | Inst: {ex[5]}")

    print("\n=== 3. UNPUBLISHED / DRAFT EXAMS (is_published = False) ===")
    unpub_exams = [ex for ex in exams if ex[3] is False]
    print(f"Unpublished count: {len(unpub_exams)}")
    for ex in unpub_exams:
        print(f"  • Name: '{ex[1]}' | Subj: {ex[2]} | Inst: {ex[5]}")

    print("\n=== 4. EXAMS PER INSTITUTION ===")
    inst_counts = conn.execute(text("""
        SELECT i.name, COUNT(e.id) as total, COUNT(CASE WHEN e.is_published THEN 1 END) as published
        FROM exams e
        LEFT JOIN institutions i ON e.institution_id = i.id
        GROUP BY i.name
    """)).fetchall()
    for row in inst_counts:
        print(f"  • Institution: {row[0] or 'Platform-Wide (Admin)'} => Total Exams: {row[1]}, Published: {row[2]}")
