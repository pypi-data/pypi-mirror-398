#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for eval_num_interval method
"""

import numpy as np
from modeleval import ModelEval

def test_eval_num_interval():
    """Test eval_num_interval method with sample data"""

    # Create sample data with specific patterns for testing
    np.random.seed(42)
    y_probs = np.random.uniform(0, 1, 50)  # 50 random probabilities
    y_test = np.random.randint(0, 2, 50)   # 50 random binary labels

    # Test with default interval (10)
    print("=== Testing eval_num_interval with interval=10 ===")
    result = ModelEval.eval_num_interval(y_probs, y_test, interval=10)

    print(f"Total samples: {len(y_probs)}")
    print(f"y_probs range: [{y_probs.min():.3f}, {y_probs.max():.3f}]")
    print(f"Total positive samples in y_test: {np.sum(y_test == 1)}")

    print("\nInterval analysis (sorted by probability descending):")
    print("Prob Range\t\tPositives\tCumulative\tRatio")
    print("-" * 60)
    for min_prob, max_prob, count_ones, cumulative_count in result:
        ratio = count_ones / (cumulative_count - (cumulative_count - min(10, cumulative_count))) if cumulative_count > 0 else 0
        current_batch_size = min(10, cumulative_count - (cumulative_count - min(10, cumulative_count)))
        print(f"[{min_prob:.3f}, {max_prob:.3f}]\t\t{count_ones}\t\t{cumulative_count}\t\t{ratio:.3f}")

    # Verify the counts add up
    total_positives = sum(count_ones for _, _, count_ones, _ in result)
    print(f"\nVerification:")
    print(f"Sum of positives ({total_positives}) == Total positives ({np.sum(y_test == 1)}): {total_positives == np.sum(y_test == 1)}")
    print(f"Last cumulative count ({result[-1][3] if result else 0}) == Total samples ({len(y_test)}): {result[-1][3] if result else 0 == len(y_test)}")

    # Test with different interval size
    print("\n=== Testing with interval=15 ===")
    result2 = ModelEval.eval_num_interval(y_probs, y_test, interval=15)
    print("Prob Range\t\tPositives\tCumulative\tRatio")
    print("-" * 60)
    for min_prob, max_prob, count_ones, cumulative_count in result2:
        current_batch_size = min(15, cumulative_count - (cumulative_count - min(15, cumulative_count)))
        ratio = count_ones / current_batch_size if current_batch_size > 0 else 0
        print(f"[{min_prob:.3f}, {max_prob:.3f}]\t\t{count_ones}\t\t{cumulative_count}\t\t{ratio:.3f}")

    # Test with specific example for easier verification
    print("\n=== Testing with specific example ===")
    # Create a controlled example where we know the expected results
    y_probs_specific = np.array([0.95, 0.90, 0.85, 0.80, 0.75, 0.70, 0.65, 0.60, 0.55, 0.50,
                                 0.45, 0.40, 0.35, 0.30, 0.25, 0.20, 0.15, 0.10, 0.05, 0.01])
    y_test_specific = np.array([1, 1, 1, 1, 0, 1, 0, 1, 1, 0,
                                0, 1, 0, 0, 1, 0, 0, 1, 0, 0])

    result3 = ModelEval.eval_num_interval(y_probs_specific, y_test_specific, interval=5)
    print("Specific example with interval=5:")
    print("y_probs (sorted):", np.sort(y_probs_specific)[::-1])
    print("y_test (corresponding):", y_test_specific[np.argsort(y_probs_specific)[::-1]])
    print("\nResult:")
    print("Prob Range\t\tPositives\tCumulative\tRatio")
    print("-" * 60)
    for min_prob, max_prob, count_ones, cumulative_count in result3:
        current_batch_size = min(5, cumulative_count - (cumulative_count - min(5, cumulative_count)))
        ratio = count_ones / current_batch_size if current_batch_size > 0 else 0
        print(f"[{min_prob:.2f}, {max_prob:.2f}]\t\t{count_ones}\t\t{cumulative_count}\t\t{ratio:.3f}")

    # Verify cumulative values
    print("\n=== Verification of cumulative values ===")
    expected_cumulative = [5, 10, 15, 20]
    actual_cumulative = [item[3] for item in result3]
    is_correct = actual_cumulative == expected_cumulative
    print(f"Cumulative values correct: {is_correct}")
    print(f"Expected: {expected_cumulative}")
    print(f"Actual: {actual_cumulative}")

    # Test edge case: interval larger than data size
    print("\n=== Testing edge case: interval > data size ===")
    y_probs_small = np.array([0.8, 0.6, 0.4])
    y_test_small = np.array([1, 0, 1])
    result4 = ModelEval.eval_num_interval(y_probs_small, y_test_small, interval=10)
    print(f"Small dataset (interval=10): {result4}")

    # Test with interval=1 (individual samples)
    print("\n=== Testing with interval=1 (individual analysis) ===")
    result5 = ModelEval.eval_num_interval(y_probs_specific[:5], y_test_specific[:5], interval=1)
    print("Individual analysis (first 5 samples):")
    print("Prob Range\t\tPositives\tCumulative")
    print("-" * 50)
    for min_prob, max_prob, count_ones, cumulative_count in result5:
        print(f"[{min_prob:.2f}, {max_prob:.2f}]\t\t{count_ones}\t\t{cumulative_count}")

if __name__ == "__main__":
    test_eval_num_interval()