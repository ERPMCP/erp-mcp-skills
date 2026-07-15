#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

FORBIDDEN_EXPORT = ["房源表", "房源导出", "房源明细导出", "新上房源导出", "在售房源导出", "在租房源导出", "房源历史表"]


def main():
    ap = argparse.ArgumentParser(description="Validate ERP MCP report JSON provenance and V2 rules.")
    ap.add_argument("json_file")
    args = ap.parse_args()
    report = json.loads(Path(args.json_file).read_text(encoding="utf-8"))
    problems = []
    for key in ["meta", "queries", "definitions", "metrics", "datasets"]:
        if key not in report:
            problems.append(f"missing top-level key: {key}")
    export_text = json.dumps(report.get("export_recommendations", []), ensure_ascii=False)
    if any(t in export_text for t in FORBIDDEN_EXPORT):
        problems.append("forbidden house-export recommendation found")
    for i, metric in enumerate(report.get("metrics", []), 1):
        for key in ["id", "label", "formula"]:
            if key not in metric:
                problems.append(f"metric {i} missing {key}")
        if metric.get("missing") and (metric.get("value") == 0 or metric.get("value") == "0"):
            problems.append(f"metric {metric.get('id')} is missing but value is fake 0")
        drill = metric.get("drilldown", {})
        if drill.get("available") and drill.get("exact_reconciliation"):
            dsid = drill.get("dataset_id")
            rows = report.get("datasets", {}).get(dsid)
            if rows is None:
                problems.append(f"metric {metric.get('id')} points to missing dataset {dsid}")
            elif isinstance(metric.get("value"), int) and len(rows) != metric["value"]:
                problems.append(f"metric {metric.get('id')} value {metric['value']} != drilldown rows {len(rows)}")
        if not metric.get("source_query_ids") and not metric.get("limitations") and not metric.get("missing"):
            problems.append(f"metric {metric.get('id')} has no source_query_ids or limitation")
    for q in report.get("queries", []):
        if q.get("source_type") == "mcp" and not q.get("tool"):
            problems.append("mcp query missing tool")
        if "raw_count" not in q:
            problems.append(f"query {q.get('id', '')} missing raw_count")
    if problems:
        print("\n".join(problems))
        raise SystemExit(1)
    print("OK")


if __name__ == "__main__":
    main()
