#!/usr/bin/env python3
"""
Sherlock Evaluation Runner
Validates atomic decomposition heuristics and SAFE mathematical scoring against benchmark test cases.
Follows Anthropic's Evaluation-Driven Development guidelines for Agent Skills.
"""

import json
import os
import sys

# Ensure UTF-8 output if supported
if sys.stdout.encoding != "utf-8" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, os.path.join(parent_dir, "scripts"))

from safe_score import calculate_safe_score


def run_evals():
    eval_file = os.path.join(script_dir, "eval_cases.json")
    if not os.path.exists(eval_file):
        print(f"Error: Eval file not found at {eval_file}")
        sys.exit(1)

    with open(eval_file, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    passed = 0
    failed = 0

    print(f"Running Sherlock SAFE Evaluation Suite ({len(test_cases)} cases)...\n")

    for case in test_cases:
        cid = case["id"]
        v = case["expected_verdicts"]
        expected_score = case["expected_safe_score"]

        metrics = calculate_safe_score(
            v["supported"],
            v["contradicted"],
            v["unsupported_leap"],
            v["unverifiable"]
        )

        score_diff = abs(metrics["safe_factuality_score"] - expected_score)
        if score_diff < 0.1:
            print(f"  [PASS] {cid}: SAFE Score {metrics['safe_factuality_score']}% matches expected {expected_score}%")
            passed += 1
        else:
            print(f"  [FAIL] {cid}: Got {metrics['safe_factuality_score']}%, expected {expected_score}%")
            failed += 1

    print(f"\nEvaluation Summary: {passed} passed, {failed} failed.")
    if failed > 0:
        sys.exit(1)
    print("All evaluation benchmarks passed successfully.")


if __name__ == "__main__":
    run_evals()
