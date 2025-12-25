#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for eval_num_byinterval method
"""

import numpy as np
from modeleval import ModelEval

def test_eval_num_byinterval():
    """Test eval_num_byinterval method with sample data"""

    # Create sample data
    np.random.seed(42)
    y_probs = np.random.uniform(0, 1, 100)  # 100 random probabilities between 0 and 1
    y_test = np.random.randint(0, 2, 100)   # 100 random binary labels (0 or 1)

    # Test with default interval (0.1)
    print("=== Testing eval_num_byinterval with interval=0.1 ===")
    result = ModelEval.eval_num_byinterval(y_probs, y_test, interval=0.1)

    print(f"Number of intervals: {len(result)}")
    print(f"y_probs range: [{y_probs.min():.3f}, {y_probs.max():.3f}]")
    print(f"Total positive samples in y_test: {np.sum(y_test == 1)}")

    print("\nInterval analysis (sorted by count_ones descending):")
    print("Interval Range\t\tPositives\tTotal\tRatio")
    print("-" * 65)
    for min_val, max_val, count_ones, count_total in result:
        ratio = count_ones / count_total if count_total > 0 else 0
        print(f"[{min_val:.3f}, {max_val:.3f})\t\t{count_ones}\t\t{count_total}\t{ratio:.3f}")

    # Verify the counts add up
    total_positives = sum(count_ones for _, _, count_ones, _ in result)
    total_samples = sum(count_total for _, _, _, count_total in result)
    print(f"\nVerification:")
    print(f"Sum of positives ({total_positives}) == Total positives ({np.sum(y_test == 1)}): {total_positives == np.sum(y_test == 1)}")
    print(f"Sum of total samples ({total_samples}) == Total samples ({len(y_test)}): {total_samples == len(y_test)}")

    # Test with different interval size
    print("\n=== Testing with interval=0.2 ===")
    result2 = ModelEval.eval_num_byinterval(y_probs, y_test, interval=0.2)
    print(f"Number of intervals: {len(result2)}")
    print("Interval Range\t\tPositives\tTotal\tRatio")
    print("-" * 65)
    for min_val, max_val, count_ones, count_total in result2:
        ratio = count_ones / count_total if count_total > 0 else 0
        print(f"[{min_val:.3f}, {max_val:.3f})\t\t{count_ones}\t\t{count_total}\t{ratio:.3f}")

    # Test edge case: all probabilities are the same
    print("\n=== Testing edge case: all probabilities equal ===")
    y_probs_same = np.full(50, 0.5)
    y_test_mixed = np.random.randint(0, 2, 50)
    result3 = ModelEval.eval_num_byinterval(y_probs_same, y_test_mixed, interval=0.1)
    print(f"Result for equal probabilities: {result3}")

    # Test with specific example
    print("\n=== Testing with specific example ===")
    y_probs_specific = np.array([0.1, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95])
    y_test_specific = np.array([0, 1, 0, 1, 1, 0, 1, 0, 1, 1])

    result4 = ModelEval.eval_num_byinterval(y_probs_specific, y_test_specific, interval=0.2)
    print("Specific example with interval=0.2:")
    print("y_probs:", y_probs_specific)
    print("y_test :", y_test_specific)
    print("Result (sorted by count_ones descending):")
    print("Interval Range\t\tPositives\tTotal\tRatio")
    print("-" * 65)
    for min_val, max_val, count_ones, count_total in result4:
        ratio = count_ones / count_total if count_total > 0 else 0
        print(f"[{min_val:.1f}, {max_val:.1f})\t\t{count_ones}\t\t{count_total}\t{ratio:.3f}")

    # Test sorting verification
    print("\n=== Verification of descending sort ===")
    counts_ones = [item[2] for item in result4]
    is_sorted = all(counts_ones[i] >= counts_ones[i+1] for i in range(len(counts_ones)-1))
    print(f"Results sorted by count_ones in descending order: {is_sorted}")

if __name__ == "__main__":
    test_eval_num_byinterval()