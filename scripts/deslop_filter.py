#!/usr/bin/env python3
"""
Sherlock Anti-Slop Deterministic Filter
Zero-dependency heuristic cleaner and linter that purges AI conversational filler,
throat-clearing preambles, and mechanical buzzwords from text.
"""

import sys
import os
import re
import argparse
import json
from typing import Tuple, List, Dict

# Ensure clean UTF-8 printing on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BANNED_WORDS_MAP = {
    r"\bdelve\b": "examine",
    r"\bdelving into\b": "examining",
    r"\ba testament to\b": "evidence of",
    r"\btestament to\b": "evidence of",
    r"\btapestry\b": "structure",
    r"\brich tapestry\b": "system",
    r"\bbeacon of\b": "example of",
    r"\brich mosaic\b": "variety",
    r"\bnavigating the complexities of\b": "addressing",
    r"\bunpacking\b": "analyzing",
}

PREAMBLE_PATTERNS = [
    r"^(?:Sure|Certainly|Of course|I(?:'d| would) be happy to|Great question)[!,.]?\s*",
    r"^(?:In today's (?:fast-paced )?digital (?:landscape|world|age)[!,.]?\s*)",
    r"^(?:It(?:'s| is) (?:important|worth|crucial) to (?:note|remember|keep in mind) that\s*)",
    r"^(?:When it comes to [^,\n]+,\s*)",
    r"^(?:As an AI (?:language model|assistant)[!,.]?\s*)",
]

CONCLUSION_PATTERNS = [
    r"\n+(?:In conclusion|To summarize(?: the above)?|All in all|In summary)[^\n]*\n*",
    r"\n+I hope this (?:helps|information was useful)[^\n]*$",
    r"\n+Let me know if you have any (?:further )?questions[^\n]*$",
]


def deslop_text(text: str) -> Tuple[str, List[Dict[str, str]]]:
    """
    Cleans text by stripping throat-clearing openings, trailing filler,
    and replaces banned robotic buzzwords. Returns (cleaned_text, detected_issues).
    """
    cleaned = text.strip()
    issues = []

    # 1. Strip conversational preambles
    for pat in PREAMBLE_PATTERNS:
        match = re.search(pat, cleaned, flags=re.IGNORECASE)
        if match:
            matched_str = match.group(0).strip()
            issues.append({"type": "throat_clearing", "pattern": matched_str})
            cleaned = re.sub(pat, "", cleaned, count=1, flags=re.IGNORECASE).strip()

    # 2. Strip conversational conclusions and sign-offs
    for pat in CONCLUSION_PATTERNS:
        matches = list(re.finditer(pat, cleaned, flags=re.IGNORECASE))
        for m in matches:
            issues.append({"type": "trailing_filler", "pattern": m.group(0).strip()})
        cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE).strip()

    # 3. Detect and replace banned robotic tics
    for pat, replacement in BANNED_WORDS_MAP.items():
        if re.search(pat, cleaned, flags=re.IGNORECASE):
            matches = re.findall(pat, cleaned, flags=re.IGNORECASE)
            for m in matches:
                issues.append({"type": "banned_word", "word": m, "suggested": replacement})
            cleaned = re.sub(pat, replacement, cleaned, flags=re.IGNORECASE)

    # 4. Collapse excessive whitespace
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned, issues


def main():
    parser = argparse.ArgumentParser(description="Sherlock Anti-Slop Deterministic Filter")
    parser.add_argument("text", nargs="?", help="Raw text to clean or verify")
    parser.add_argument("--file", help="Path to file to process")
    parser.add_argument("--check-only", action="store_true", help="Exit code 1 if slop found, 0 if clean")
    parser.add_argument("--json", action="store_true", help="Output JSON results")
    args = parser.parse_args()

    content = ""
    if args.file and os.path.exists(args.file):
        with open(args.file, "r", encoding="utf-8") as f:
            content = f.read()
    elif args.text:
        content = args.text
    elif not sys.stdin.isatty():
        content = sys.stdin.read()
    else:
        parser.print_help()
        sys.exit(0)

    cleaned, issues = deslop_text(content)

    if args.json:
        result = {
            "is_clean": len(issues) == 0,
            "slop_count": len(issues),
            "issues": issues,
            "cleaned_text": cleaned
        }
        print(json.dumps(result, indent=2))
    elif args.check_only:
        if issues:
            print(f"[!] Slop detected ({len(issues)} issue(s)):", file=sys.stderr)
            for iss in issues:
                print(f"  - {iss}", file=sys.stderr)
            sys.exit(1)
        else:
            print("[✓] Text is 100% clean and free of AI slop.")
            sys.exit(0)
    else:
        print(cleaned)


if __name__ == "__main__":
    main()
