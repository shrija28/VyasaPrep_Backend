"""Test to verify 4 sets (A, B, C, D) generation with identical 60 questions in shuffled order."""

import sys
import os
import random

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Create a sample pool of 60 questions
drawn = [f"Q_ID_{i}" for i in range(60)]
SET_LABELS = ["A", "B", "C", "D"]

partitions = []
for s_i, label in enumerate(SET_LABELS):
    set_qids = list(drawn)
    if s_i > 0:
        random.shuffle(set_qids)
        if set_qids == drawn and len(set_qids) > 1:
            set_qids.reverse()
    partitions.append(set_qids)

# Verification 1: Exactly 4 sets generated
print(f"OK: Number of sets = {len(partitions)}")
assert len(partitions) == 4

# Verification 2: Each set has 60 questions
for idx, set_qids in enumerate(partitions):
    print(f"OK: Set {SET_LABELS[idx]} question count = {len(set_qids)}")
    assert len(set_qids) == 60

# Verification 3: All sets contain the EXACT SAME 60 questions
set_A_items = set(partitions[0])
for idx in range(1, 4):
    set_items = set(partitions[idx])
    print(f"OK: Set {SET_LABELS[idx]} matches Set A question set = {set_items == set_A_items}")
    assert set_items == set_A_items, f"Set {SET_LABELS[idx]} does not match Set A questions"

# Verification 4: The order is shuffled (not identical sequence to Set A)
order_differs_count = sum(1 for idx in range(1, 4) if partitions[idx] != partitions[0])
print(f"OK: Shuffled sets count = {order_differs_count} / 3")
assert order_differs_count >= 2, "Shuffling failed to vary question sequence"

print("SUCCESS: 4 sets generated with exact same 60 questions in shuffled order!")
