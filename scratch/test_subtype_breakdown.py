import sys
import os
sys.path.insert(0, r"c:\Users\SHRIJA SANIL\Mr.E\backend")

from smartkcet.rag.mcq_extractor import (
    infer_question_subtype,
    apply_subject_subtype_breakdown,
    extract_or_generate_mcqs,
)

def test_subtypes():
    # Test Physics subtype inferencing
    q1 = "A car accelerates from rest at 2 m/s^2 for 10 s. Find distance."
    opts1 = ["50 m", "100 m", "150 m", "200 m"]
    st1 = infer_question_subtype(q1, opts1, "Physics")
    print(f"Physics Q1 Subtype: {st1}")
    assert st1 == "direct_formula"

    q2 = "Find the ratio of kinetic energy when velocity is doubled and mass is reduced by 50 percent."
    opts2 = ["1:2", "2:1", "1:4", "4:1"]
    st2 = infer_question_subtype(q2, opts2, "Physics")
    print(f"Physics Q2 Subtype: {st2}")
    assert st2 == "multi_step"

    q3 = "Lenz's law is a consequence of the law of conservation of:"
    opts3 = ["Charge", "Energy", "Mass", "Momentum"]
    st3 = infer_question_subtype(q3, opts3, "Physics")
    print(f"Physics Q3 Subtype: {st3}")
    assert st3 == "theory_definition"

    # Test Chemistry subtype inferencing
    q4 = "What is the molarity of a solution containing 5.85 g of NaCl in 500 mL water?"
    opts4 = ["0.1 M", "0.2 M", "0.5 M", "1.0 M"]
    st4 = infer_question_subtype(q4, opts4, "Chemistry")
    print(f"Chemistry Q4 Subtype: {st4}")
    assert st4 == "physical_numerical"

    q5 = "Which reagent distinguishes primary, secondary, and tertiary amines in the Hinsberg test?"
    opts5 = ["Benzenesulfonyl chloride", "Tollens reagent", "Lucas reagent", "Fehling solution"]
    st5 = infer_question_subtype(q5, opts5, "Chemistry")
    print(f"Chemistry Q5 Subtype: {st5}")
    assert st5 == "fact_reaction"

    # Test breakdown ratios for Physics (60 questions)
    phy_qs = extract_or_generate_mcqs("", topic="Physics", min_questions=60)
    print(f"Total Physics MCQs returned: {len(phy_qs)}")
    st_counts = {}
    for q in phy_qs:
        st = q.get("subtype", "unknown")
        st_counts[st] = st_counts.get(st, 0) + 1
    print(f"Physics Subtype Breakdown for 60 questions: {st_counts}")

    # Test breakdown ratios for Chemistry (60 questions)
    chem_qs = extract_or_generate_mcqs("", topic="Chemistry", min_questions=60)
    print(f"Total Chemistry MCQs returned: {len(chem_qs)}")
    chem_counts = {}
    for q in chem_qs:
        st = q.get("subtype", "unknown")
        chem_counts[st] = chem_counts.get(st, 0) + 1
    print(f"Chemistry Subtype Breakdown for 60 questions: {chem_counts}")

    print("ALL SUBTYPE TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_subtypes()
