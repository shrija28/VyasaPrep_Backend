import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from smartkcet.rag.mcq_extractor import generate_fallback_mcqs

def test_physics_blueprint():
    print("=== TESTING PHYSICS BLUEPRINT QUESTION GENERATION ===")
    questions = generate_fallback_mcqs("", topic="Physics", max_questions=60)
    print(f"Total Questions Generated: {len(questions)}")
    
    counts = {}
    for q in questions:
        sub = q.get("subtype", "unknown")
        counts[sub] = counts.get(sub, 0) + 1
        
    print(f"Physics Subtype Breakdown (Target: 60 questions):")
    for sub, count in counts.items():
        pct = (count / len(questions)) * 100
        print(f" - {sub}: {count} questions ({pct:.1f}%)")
        
    calc_count = counts.get("direct_formula", 0) + counts.get("multi_step", 0)
    calc_pct = (calc_count / len(questions)) * 100
    print(f"Total Physics Calculations: {calc_count} / {len(questions)} ({calc_pct:.1f}%)")
    assert 50.0 <= calc_pct <= 60.0, f"Physics calculations ({calc_pct}%) outside target 50-60%!"
    print("SUCCESS: Physics blueprint target verified!")

def test_chemistry_blueprint():
    print("\n=== TESTING CHEMISTRY BLUEPRINT QUESTION GENERATION ===")
    questions = generate_fallback_mcqs("", topic="Chemistry", max_questions=60)
    print(f"Total Questions Generated: {len(questions)}")
    
    counts = {}
    for q in questions:
        sub = q.get("subtype", "unknown")
        counts[sub] = counts.get(sub, 0) + 1
        
    print(f"Chemistry Subtype Breakdown (Target: 60 questions):")
    for sub, count in counts.items():
        pct = (count / len(questions)) * 100
        print(f" - {sub}: {count} questions ({pct:.1f}%)")
        
    num_count = counts.get("physical_numerical", 0)
    num_pct = (num_count / len(questions)) * 100
    print(f"Total Chemistry Numericals: {num_count} / {len(questions)} ({num_pct:.1f}%)")
    assert 5 <= num_count <= 8, f"Chemistry numericals ({num_count}) outside target 5 to 8 questions!"
    print("SUCCESS: Chemistry blueprint target verified!")

if __name__ == "__main__":
    test_physics_blueprint()
    test_chemistry_blueprint()
