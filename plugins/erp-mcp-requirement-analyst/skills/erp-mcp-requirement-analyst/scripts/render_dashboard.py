#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "assets" / "dashboard_template.html"
FORBIDDEN_EXPORT = ["房源表", "房源导出", "房源明细导出", "新上房源导出", "在售房源导出", "在租房源导出", "房源历史表"]


def normalize(report):
    report.setdefault("meta", {})
    report.setdefault("queries", [])
    report.setdefault("definitions", {})
    report.setdefault("metrics", [])
    report.setdefault("datasets", {})
    report.setdefault("limitations", [])
    report.setdefault("export_recommendations", [])
    report.setdefault("filters", {})
    report["filters"].setdefault("scope_options", ["全公司"])
    report["filters"].setdefault("biz_options", report.get("meta", {}).get("biz_types") or ["全部"])
    report["filters"].setdefault("notice", "如果切换条件需要重新查询，页面会明确提示。")
    for m in report["metrics"]:
        if "value" not in m or m.get("value") is None or m.get("value") == "":
            m["missing"] = True
            m.setdefault("limitations", []).append("这个指标还没有取得可验证数据。")
        m.setdefault("formula", "")
        m.setdefault("business_formula", m.get("formula", ""))
        m.setdefault("drilldown", {"available": False, "dataset_id": "", "exact_reconciliation": False, "reason": ""})
    return report


def assert_no_forbidden_export(report):
    text = json.dumps(report.get("export_recommendations", []), ensure_ascii=False)
    bad = [x for x in FORBIDDEN_EXPORT if x in text]
    if bad:
        raise SystemExit("禁止在导出建议中出现房源类导出：" + "、".join(bad))


def main():
    ap = argparse.ArgumentParser(description="Render ERP MCP traceable interactive dashboard HTML.")
    ap.add_argument("report_json")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    report = normalize(json.loads(Path(args.report_json).read_text(encoding="utf-8")))
    assert_no_forbidden_export(report)
    title = report.get("meta", {}).get("title") or "ERP 数据看板"
    html = TEMPLATE.read_text(encoding="utf-8").replace("@@REPORT_TITLE@@", title).replace("@@REPORT_JSON@@", json.dumps(report, ensure_ascii=False))
    Path(args.out).write_text(html, encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
