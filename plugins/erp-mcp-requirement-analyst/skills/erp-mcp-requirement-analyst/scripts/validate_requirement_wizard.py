#!/usr/bin/env python3
import argparse
import re
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description="Static validation for requirement wizard HTML.")
    ap.add_argument("html")
    args = ap.parse_args()
    text = Path(args.html).read_text(encoding="utf-8")
    problems = []
    for token in ["@@WIZARD_JSON@@", "@@REPORT_JSON@@", "@@REPORT_TITLE@@"]:
        if token in text:
            problems.append(f"placeholder remains: {token}")
    if re.search(r"{{\s*[\w. -]+\s*}}", text) or "{%" in text or "%}" in text:
        problems.append("suspicious template syntax remains")
    for required in ["confirm", "fallback", "questions", "progressText", "baseFilters"]:
        if required not in text:
            problems.append(f"missing required element/script id: {required}")
    if "position:fixed" in text.replace(" ", "").lower():
        problems.append("fixed overlay style found")
    if "http://" in text or "https://" in text:
        problems.append("external network reference found")
    if problems:
        print("\n".join(problems))
        raise SystemExit(1)
    print("OK")


if __name__ == "__main__":
    main()
