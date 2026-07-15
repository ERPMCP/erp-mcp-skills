#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable


def run(args, expect_ok=True):
    p = subprocess.run([PY, *map(str, args)], cwd=ROOT, text=True, capture_output=True)
    if expect_ok and p.returncode != 0:
        print(p.stdout)
        print(p.stderr)
        raise SystemExit(p.returncode)
    if not expect_ok and p.returncode == 0:
        print("expected failure but command passed", args)
        raise SystemExit(1)
    if p.stdout:
        print(p.stdout.strip())
    return p


def main():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        route_path = td / "fast-route.json"
        route_wizard_config = td / "fast-route-wizard.json"
        route = run([
            ROOT / "scripts" / "fast_route.py",
            "--query", "查询上月新上房源数量和挂牌均价，可以按多个层级筛选",
            "--out", route_path,
            "--wizard-config-out", route_wizard_config,
        ])
        route_data = json.loads(route_path.read_text(encoding="utf-8"))
        if not route_data.get("matched") or route_data.get("scenario_id") != "house_new_listing_price":
            raise SystemExit("fast route did not match the standard house scenario")
        if route_data.get("read_files") != [
            "references/fast_scenario_router.json",
            "references/house_new_listing_price_fast.json",
        ]:
            raise SystemExit("fast route read more than the router and one small template")
        pre = route_data.get("pre_confirmation", {})
        if pre.get("call_erp_business_tools") or pre.get("read_full_capability_guide") or pre.get("inspect_live_schema"):
            raise SystemExit("fast route enables ERP or broad reference reads before confirmation")
        if pre.get("action") != "render_requirement_wizard_and_wait" or not pre.get("halt_after_render"):
            raise SystemExit("fast route does not stop after rendering the confirmation page")
        if any(word in pre.get("customer_progress", "").lower() for word in ("loading", "reading", "schema", "probe", "i'll")):
            raise SystemExit("fast route leaked English/internal progress text")
        after = route_data.get("after_confirmation", [])
        if "query_real_erp_data" not in after or after.index("query_real_erp_data") < after.index("check_erp_connector"):
            raise SystemExit("fast route does not defer ERP querying until after connector checks")

        wizard = td / "wizard.html"
        run([ROOT / "scripts" / "render_requirement_wizard.py", "--config", route_wizard_config, "--out", wizard])
        run([ROOT / "scripts" / "validate_requirement_wizard.py", wizard])

        report = {
            "meta": {"title": "结构测试", "generated_at": "2026-07-14T00:00:00+08:00", "date_range": {"start": "2026-07-01", "end": "2026-07-31", "label": "2026年7月"}, "date_basis": "签约日期", "biz_types": ["全部"], "scope": "全公司", "plain_summary": "这是结构测试，不包含真实业务数字。", "provisional": True},
            "filters": {"time_options": ["2026年7月"], "scope_options": ["全公司"], "biz_options": ["全部"], "requires_requery": True},
            "queries": [{"id": "q1", "source_type": "mcp", "tool": "queryContractFinanceData", "type": "合同明细", "params": {}, "raw_count": 2, "clean_count": 2, "notes": []}],
            "definitions": {"contract_key": "合同类型|合同编号", "attribution": "签约人", "denominator_rule": "测试", "exclusions": []},
            "metrics": [{"id": "contracts", "label": "合同数", "value": 2, "unit": "份", "formula": "按合同类型+合同编号去重", "business_formula": "按合同类型和合同编号去重后计算", "source_query_ids": ["q1"], "record_count": 2, "drilldown": {"available": True, "mode": "embedded", "dataset_id": "contracts", "exact_reconciliation": True, "reason": ""}, "limitations": []}],
            "datasets": {"contracts": [{"合同类型": "测试合同", "合同编号": "TEST-001"}, {"合同类型": "测试合同", "合同编号": "TEST-002"}]},
            "reconciliation": [],
            "limitations": ["结构测试数据，非真实 ERP 数据"],
            "export_recommendations": [],
            "business_explanation": "页面优先说业务结论，技术信息放在折叠区。"
        }
        report_path = td / "report.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
        html = td / "dashboard.html"
        run([ROOT / "scripts" / "validate_report_data.py", report_path])
        run([ROOT / "scripts" / "render_dashboard.py", report_path, "--out", html])
        run([ROOT / "scripts" / "validate_dashboard.py", html])
        run([ROOT / "scripts" / "lookup_field.py", "合同编号", "--limit", "1"])
        run([ROOT / "scripts" / "recommend_export.py", "按业绩小组统计已实收业绩"])
        house = run([ROOT / "scripts" / "recommend_export.py", "查询上月新上房源数量和挂牌均价"])
        if "请导出房源表" in house.stdout or "需要补充：房源" in house.stdout or "房源明细导出" in house.stdout:
            raise SystemExit("house export recommendation leaked")
        bad = dict(report)
        bad["export_recommendations"] = ["请导出房源表"]
        bad_path = td / "bad.json"
        bad_path.write_text(json.dumps(bad, ensure_ascii=False), encoding="utf-8")
        run([ROOT / "scripts" / "render_dashboard.py", bad_path, "--out", td / "bad.html"], expect_ok=False)
    print("SELF_TEST_OK_V2")


if __name__ == "__main__":
    main()

