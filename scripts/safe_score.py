#!/usr/bin/env python3
"""
Sherlock SAFE Factuality Score Calculator
Calculates the SAFE precision metrics based on Google DeepMind's
Search-Augmented Factuality Evaluator framework.
"""

import sys
import json
import argparse


def calculate_safe_score(supported: int, contradicted: int, unsupported_leap: int, unverifiable: int) -> dict:
    total_relevant = supported + contradicted + unsupported_leap + unverifiable
    if total_relevant == 0:
        return {
            "total_relevant": 0,
            "supported": 0,
            "contradicted": 0,
            "unsupported_leap": 0,
            "unverifiable": 0,
            "safe_factuality_score": 0.0,
            "contradiction_rate": 0.0,
            "leap_rate": 0.0,
        }

    score = (supported / total_relevant) * 100.0
    contradiction_rate = (contradicted / total_relevant) * 100.0
    leap_rate = ((unsupported_leap + unverifiable) / total_relevant) * 100.0

    return {
        "total_relevant": total_relevant,
        "supported": supported,
        "contradicted": contradicted,
        "unsupported_leap": unsupported_leap,
        "unverifiable": unverifiable,
        "safe_factuality_score": round(score, 2),
        "contradiction_rate": round(contradiction_rate, 2),
        "leap_rate": round(leap_rate, 2),
    }


def format_markdown_table(metrics: dict) -> str:
    n = metrics["total_relevant"]
    if n == 0:
        return "No relevant claims to evaluate."

    s_pct = round((metrics["supported"] / n) * 100, 1)
    c_pct = round((metrics["contradicted"] / n) * 100, 1)
    l_pct = round((metrics["unsupported_leap"] / n) * 100, 1)
    u_pct = round((metrics["unverifiable"] / n) * 100, 1)

    table = [
        "| Status | Count | Percentage |",
        "| :--- | :--- | :--- |",
        f"| **Supported** | {metrics['supported']} | {s_pct}% |",
        f"| **Contradicted** | {metrics['contradicted']} | {c_pct}% |",
        f"| **Unsupported Leap** | {metrics['unsupported_leap']} | {l_pct}% |",
        f"| **Unverifiable** | {metrics['unverifiable']} | {u_pct}% |",
        f"| **Total Relevant Facts** | {n} | 100% |",
        "",
        f"**Overall SAFE Factuality Score**: **{metrics['safe_factuality_score']}%**",
    ]
    return "\n".join(table)


def main():
    parser = argparse.ArgumentParser(description="Calculate SAFE Factuality Score")
    parser.add_argument("-s", "--supported", type=int, default=0, help="Number of supported claims")
    parser.add_argument("-c", "--contradicted", type=int, default=0, help="Number of contradicted claims")
    parser.add_argument("-l", "--leap", type=int, default=0, help="Number of unsupported leap claims")
    parser.add_argument("-u", "--unverifiable", type=int, default=0, help="Number of unverifiable claims")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of markdown")

    args = parser.parse_args()

    metrics = calculate_safe_score(args.supported, args.contradicted, args.leap, args.unverifiable)

    if args.json:
        print(json.dumps(metrics, indent=2))
    else:
        print(format_markdown_table(metrics))


if __name__ == "__main__":
    main()
