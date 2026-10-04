#!/usr/bin/env python3
"""
Sherlock SAFE Factuality Score & Verification Report Generator
Calculates precision metrics and generates dual Markdown/JSON reports
for human audits or automated agent CI/CD pipelines.
"""

import sys
import os
import json
import argparse
from typing import Dict, List, Any

# Ensure clean UTF-8 printing on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def calculate_safe_score(supported: int, contradicted: int, unsupported_leap: int, unverifiable: int) -> Dict[str, Any]:
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
            "status": "UNVERIFIED"
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
        "status": "PASSED" if score >= 80.0 and contradicted == 0 else "FAILED"
    }


def format_markdown_table(metrics: Dict[str, Any], claims: List[Dict[str, Any]] = None) -> str:
    n = metrics["total_relevant"]
    if n == 0:
        return "No relevant claims to evaluate."

    s_pct = round((metrics["supported"] / n) * 100, 1)
    c_pct = round((metrics["contradicted"] / n) * 100, 1)
    l_pct = round((metrics["unsupported_leap"] / n) * 100, 1)
    u_pct = round((metrics["unverifiable"] / n) * 100, 1)

    lines = []
    if claims:
        lines.append("### Claim-by-Claim Verification")
        lines.append("| ID | Claim | Status | Source |")
        lines.append("| :-- | :--- | :--- | :--- |")
        for c in claims:
            cid = c.get("id", "-")
            text = c.get("claim", "")
            stat = c.get("status", "Unverifiable")
            url = c.get("url", "")
            link = f"[{url.split('//')[-1].split('/')[0]}]({url})" if url else "-"
            lines.append(f"| {cid} | {text} | **{stat}** | {link} |")
        lines.append("")

    lines.extend([
        "| Status | Count | Percentage |",
        "| :--- | :--- | :--- |",
        f"| **Supported** | {metrics['supported']} | {s_pct}% |",
        f"| **Contradicted** | {metrics['contradicted']} | {c_pct}% |",
        f"| **Unsupported Leap** | {metrics['unsupported_leap']} | {l_pct}% |",
        f"| **Unverifiable** | {metrics['unverifiable']} | {u_pct}% |",
        f"| **Total Relevant Facts** | {n} | 100% |",
        "",
        f"**Overall SAFE Factuality Score**: **{metrics['safe_factuality_score']}%** ({metrics['status']})"
    ])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Sherlock SAFE Factuality Score & Verification Report")
    parser.add_argument("-s", "--supported", type=int, default=0, help="Number of supported claims")
    parser.add_argument("-c", "--contradicted", type=int, default=0, help="Number of contradicted claims")
    parser.add_argument("-l", "--leap", type=int, default=0, help="Number of unsupported leap claims")
    parser.add_argument("-u", "--unverifiable", type=int, default=0, help="Number of unverifiable claims")
    parser.add_argument("claims_path", nargs="?", help="Optional path to JSON file containing list of verified claim objects")
    parser.add_argument("--claims-file", help="Path to JSON file containing list of verified claim objects")
    parser.add_argument("--threshold", type=float, default=80.0, help="Pass threshold percentage (default: 80.0)")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    parser.add_argument("--ci", action="store_true", help="Exit with non-zero code if evaluation fails threshold")

    args = parser.parse_args()

    claims = []
    supported = args.supported
    contradicted = args.contradicted
    leap = args.leap
    unverifiable = args.unverifiable

    file_to_load = args.claims_path or args.claims_file
    if file_to_load and os.path.exists(file_to_load):
        with open(file_to_load, "r", encoding="utf-8") as f:
            claims = json.load(f)
        supported = sum(1 for c in claims if c.get("status") == "Supported")
        contradicted = sum(1 for c in claims if c.get("status") == "Contradicted")
        leap = sum(1 for c in claims if c.get("status") == "Unsupported Leap")
        unverifiable = sum(1 for c in claims if c.get("status") == "Unverifiable")

    metrics = calculate_safe_score(supported, contradicted, leap, unverifiable)
    is_passed = metrics["safe_factuality_score"] >= args.threshold and contradicted == 0
    metrics["status"] = "PASSED" if is_passed else "FAILED"

    if args.json:
        output = {
            "metrics": metrics,
            "claims": claims
        }
        print(json.dumps(output, indent=2))
    else:
        print(format_markdown_table(metrics, claims=claims))

    if args.ci and not is_passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
