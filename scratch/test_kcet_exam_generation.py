"""Verification script to test KCET distribution and concept deduplication across Physics, Chemistry, and Mathematics."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from smartkcet.rag.mcq_extractor import extract_or_generate_mcqs, extract_concept_fingerprint, normalize_question_fingerprint

def safe_print(text):
    print(text.encode('ascii', errors='replace').decode('ascii'))

def test_subject_generation(subject_name: str):
    print(f"\n========================================================")
    print(f"Testing KCET Exam Generation for {subject_name} (60 questions)")
    print(f"========================================================")
    
    questions = extract_or_generate_mcqs("", topic=subject_name, min_questions=60)
    print(f"Total questions generated: {len(questions)}")
    assert len(questions) == 60, f"Expected 60 questions, got {len(questions)}"
    
    # Check 1: Text fingerprint deduplication
    fps = [normalize_question_fingerprint(q["q"]) for q in questions]
    unique_fps = set(fps)
    print(f"Unique text fingerprints: {len(unique_fps)} / 60")
    assert len(unique_fps) == 60, "Duplicate question text stems found!"
    
    # Check 2: Concept-level formula deduplication
    concepts = [extract_concept_fingerprint(q["q"]) for q in questions]
    unique_concepts = set(concepts)
    print(f"Unique concept archetypes: {len(unique_concepts)} / 60")
    
    # Find any repeated concepts
    concept_counts = {}
    for c in concepts:
        concept_counts[c] = concept_counts.get(c, 0) + 1
    
    duplicates = {c: count for c, count in concept_counts.items() if count > 1}
    if duplicates:
        print("WARNING: Repeated concepts detected:", duplicates)
        for c in duplicates:
            print(f"Concept '{c}' questions:")
            for q in questions:
                if extract_concept_fingerprint(q["q"]) == c:
                    safe_print(f" - {q['q']}")
    else:
        print("SUCCESS: 0 repetitive concept numericals! All 60 questions test completely distinct formulas/concepts!")

    # Check 3: Subtype distribution versatility
    subtypes = {}
    for q in questions:
        st = q.get("subtype", "unknown")
        subtypes[st] = subtypes.get(st, 0) + 1
    print("Subtype Breakdown:", subtypes)
    
    # Print sample first 5 questions
    print("\nSample first 5 questions:")
    for i, q in enumerate(questions[:5], 1):
        safe_print(f"Q{i} [{q.get('subtype')} | {q.get('topic')}]: {q['q']}")
        safe_print(f"   Opts: {q['opts']}")
        safe_print(f"   Correct: Option {q['ans']}")

if __name__ == "__main__":
    test_subject_generation("Physics")
    test_subject_generation("Chemistry")
    test_subject_generation("Mathematics")
