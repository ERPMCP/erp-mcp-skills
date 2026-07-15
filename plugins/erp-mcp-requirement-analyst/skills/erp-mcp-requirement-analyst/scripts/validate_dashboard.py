#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path

FORBIDDEN_EXPORT = ["房源表", "房源导出", "房源明细导出", "新上房源导出", "在售房源导出", "在租房源导出", "房源历史表"]
TECH_TERMS_MAIN = ["queryRptData", "listHouseByCondition", "queryContractFinanceData", "isNew=", "unitPrice", "bizType", "schema", "JSON lineage", "MCP直接支持", "MCP支持但口径需说明"]
FORBIDDEN_SECRET_MARKERS = ["Authorization", "Bearer ", "erp_mcp_token", "access_token", "api_key"]


def main():
    ap = argparse.ArgumentParser(description="Static validation for rendered ERP dashboard HTML.")
    ap.add_argument("html")
    args = ap.parse_args()
    text = Path(args.html).read_text(encoding="utf-8")
    problems = []
    for token in ["@@REPORT_JSON@@", "@@REPORT_TITLE@@", "@@WIZARD_JSON@@"]:
        if token in text:
            problems.append(f"placeholder remains: {token}")
    if re.search(r"{{\s*[\w. -]+\s*}}", text) or "{%" in text or "%}" in text:
        problems.append("suspicious template syntax remains")
    if "position:fixed" in text.replace(" ", "").lower():
        problems.append("fixed overlay style found; summary may cover content")
    match = re.search(r'<script id="report-data" type="application/json">(.*?)</script>', text, re.S)
    if not match:
        problems.append("missing embedded report JSON")
        report = {}
    else:
        try:
            report = json.loads(match.group(1))
        except Exception as exc:
            problems.append(f"report JSON parse failed: {exc}")
            report = {}
    report_text = json.dumps(report, ensure_ascii=False)
    if any(term in report_text for term in FORBIDDEN_EXPORT):
        problems.append("forbidden house-export recommendation found")
    for m in report.get("metrics", []):
        if m.get("missing") and (m.get("value") == 0 or m.get("value") == "0"):
            problems.append(f"missing metric displays fake 0: {m.get('id')}")
        d = m.get("drilldown", {})
        if d.get("available") and d.get("exact_reconciliation") and d.get("dataset_id") not in report.get("datasets", {}):
            problems.append(f"metric {m.get('id')} has missing drilldown dataset")
    filters = report.get("filters", {})
    for key in ["scope_options", "biz_options"]:
        if key in filters and isinstance(filters[key], list) and len(filters[key]) == 0:
            problems.append(f"empty filter options: {key}")
    ids = re.findall(r'id="([^"]+)"', text)
    dupes = sorted({x for x in ids if ids.count(x) > 1})
    if dupes:
        problems.append(f"duplicate ids: {', '.join(dupes)}")
    if "http://" in text or "https://" in text:
        problems.append("external network reference found")
    for marker in FORBIDDEN_SECRET_MARKERS:
        if marker in text:
            problems.append(f"possible secret/auth marker found in HTML: {marker}")
    if "按此条件重新查询" in text and "callServerTool" not in text:
        problems.append("requery wording found without realtime bridge support")
    if problems:
        print("\n".join(problems))
        raise SystemExit(1)
    print("OK")


if __name__ == "__main__":
    main()
