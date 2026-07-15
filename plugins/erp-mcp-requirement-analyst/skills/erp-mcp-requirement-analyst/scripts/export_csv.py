#!/usr/bin/env python3
import argparse
import csv
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description="Export one dataset from report JSON to UTF-8-SIG CSV.")
    ap.add_argument("report_json")
    ap.add_argument("dataset_id")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    report = json.loads(Path(args.report_json).read_text(encoding="utf-8"))
    rows = report.get("datasets", {}).get(args.dataset_id, [])
    if not rows:
        Path(args.out).write_text("", encoding="utf-8-sig")
        print(args.out)
        return
    fields = list(dict.fromkeys(k for row in rows for k in row.keys()))
    with Path(args.out).open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(args.out)


if __name__ == "__main__":
    main()
