#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def normalize(report):
    report.setdefault("meta", {})
    report.setdefault("queries", [])
    report.setdefault("definitions", {})
    report.setdefault("metrics", [])
    report.setdefault("datasets", {})
    report.setdefault("reconciliation", [])
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
        m.setdefault("drilldown", {"available": False, "dataset_id": "", "exact_reconciliation": False, "reason": ""})
        m.setdefault("formula", "")
        m.setdefault("business_formula", m.get("formula", ""))
    return report


def main():
    ap = argparse.ArgumentParser(description="Normalize ERP report JSON without converting missing values to 0.")
    ap.add_argument("input")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    report = json.loads(Path(args.input).read_text(encoding="utf-8"))
    Path(args.out).write_text(json.dumps(normalize(report), ensure_ascii=False, indent=2), encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
