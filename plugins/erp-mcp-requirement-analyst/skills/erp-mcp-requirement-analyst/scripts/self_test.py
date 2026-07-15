#!/usr/bin/env python3
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT.parents[1]
PY = sys.executable


def run(args, expect_ok=True):
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    process = subprocess.run(
        [PY, *map(str, args)],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        env=env,
    )
    if expect_ok and process.returncode != 0:
        print(process.stdout)
        print(process.stderr)
        raise SystemExit(process.returncode)
    if not expect_ok and process.returncode == 0:
        raise SystemExit(f"expected failure but command passed: {args}")
    return process


def mcp_roundtrip(script, messages):
    process = subprocess.Popen(
        [PY, str(script)],
        cwd=PLUGIN_ROOT,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        replies = []
        for message in messages:
            raw = json.dumps(message, ensure_ascii=False).encode("utf-8")
            process.stdin.write(f"Content-Length: {len(raw)}\r\n\r\n".encode("ascii") + raw)
            process.stdin.flush()
            headers = {}
            while True:
                line = process.stdout.readline()
                if line in (b"\r\n", b"\n"):
                    break
                if not line:
                    raise SystemExit("proxy closed before response")
                key, value = line.decode("ascii").split(":", 1)
                headers[key.lower()] = value.strip()
            replies.append(json.loads(process.stdout.read(int(headers["content-length"])).decode("utf-8")))
        return replies
    finally:
        if process.stdin:
            process.stdin.close()
        process.terminate()
        process.wait(timeout=5)


def load_proxy_module():
    path = PLUGIN_ROOT / "mcp_servers" / "erp_dashboard_proxy.py"
    spec = importlib.util.spec_from_file_location("erp_dashboard_proxy_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def assert_route(temp_dir, query, scenario, template):
    route_path = temp_dir / f"{scenario}.json"
    wizard_path = temp_dir / f"{scenario}-wizard.json"
    run(
        [
            ROOT / "scripts" / "fast_route.py",
            "--query",
            query,
            "--out",
            route_path,
            "--wizard-config-out",
            wizard_path,
        ]
    )
    route = json.loads(route_path.read_text(encoding="utf-8"))
    if route.get("scenario_id") != scenario:
        raise SystemExit(f"wrong route for {query}: {route.get('scenario_id')}")
    if route.get("read_files") != [
        "references/fast_scenario_router.json",
        f"references/{template}",
    ]:
        raise SystemExit("fast route read more than the router and one small template")
    pre = route.get("pre_confirmation", {})
    if pre.get("call_erp_business_tools") or pre.get("read_full_capability_guide") or pre.get("inspect_live_schema"):
        raise SystemExit("fast route enabled ERP or broad reference reads before confirmation")
    if pre.get("action") != "render_requirement_wizard_and_wait" or not pre.get("halt_after_render"):
        raise SystemExit("fast route did not stop for definition confirmation")
    after = route.get("after_confirmation", [])
    if "call_showErpDashboard_for_summary" not in after or "do_not_fetch_details_until_metric_click" not in after:
        raise SystemExit("fast route does not enforce quick summary followed by lazy detail")
    return wizard_path


def test_query_gate(temp_dir):
    gate = ROOT / "scripts" / "query_gate.py"
    state = temp_dir / "state.json"
    run([gate, "init", "--state", state, "--scenario", "house_new_listing_count", "--query", "查询上月新上房源数量"])
    data = json.loads(state.read_text(encoding="utf-8"))
    if data.get("phase") != "COLLECTING_OPTIONS":
        raise SystemExit("gate did not start in COLLECTING_OPTIONS")

    blocked = run([gate, "guard", "--state", state, "--tool", "queryRptData"], expect_ok=False)
    if "尚未确认统计定义" not in blocked.stdout:
        raise SystemExit("summary was not blocked before definition confirmation")
    blocked_detail = run([gate, "guard", "--state", state, "--tool", "listHouseByCondition"], expect_ok=False)
    if "尚未点击蓝色数字" not in blocked_detail.stdout:
        raise SystemExit("detail was not blocked before definition confirmation")

    run([gate, "choose", "--state", state, "--key", "business_type", "--value", "sell"])
    if json.loads(state.read_text(encoding="utf-8")).get("phase") != "COLLECTING_OPTIONS":
        raise SystemExit("choosing an option authorized a query")
    run([gate, "confirm-definition", "--state", state, "--source", "widget"])
    if json.loads(state.read_text(encoding="utf-8")).get("phase") != "READY_FOR_SUMMARY":
        raise SystemExit("definition confirmation did not enter READY_FOR_SUMMARY")

    run([gate, "guard", "--state", state, "--tool", "queryRptData"])
    run([gate, "guard", "--state", state, "--tool", "calculateErpSummaryMetric"])
    run([gate, "write-json", "--state", state, "--path", temp_dir / "summary_metric.json", "--kind", "summary"])
    blocked_during_summary = run([gate, "guard", "--state", state, "--tool", "listHouseByCondition"], expect_ok=False)
    if "尚未点击蓝色数字" not in blocked_during_summary.stdout:
        raise SystemExit("a derived summary accidentally authorized detail reads")
    run([gate, "summary-ready", "--state", state])
    run([gate, "guard", "--state", state, "--tool", "getErpDashboardFilterOptions"])
    run([gate, "guard", "--state", state, "--tool", "queryErpDashboardSummary"])
    run([gate, "summary-ready", "--state", state])

    blocked_json = run(
        [gate, "write-json", "--state", state, "--path", temp_dir / "houses_1.json", "--kind", "detail"],
        expect_ok=False,
    )
    if "尚未点击蓝色数字" not in blocked_json.stdout:
        raise SystemExit("detail JSON was not blocked before a metric click")
    run([gate, "authorize-detail", "--state", state, "--source", "metric_click", "--metric-id", "currentNewListingCount"])
    run([gate, "guard", "--state", state, "--tool", "getErpMetricDetails"])
    run([gate, "write-json", "--state", state, "--path", temp_dir / "houses_1.json", "--kind", "detail"])
    run([gate, "detail-ready", "--state", state])
    final = json.loads(state.read_text(encoding="utf-8"))
    if final.get("phase") != "DETAIL_READY" or len(final.get("detail_tool_calls", [])) != 1:
        raise SystemExit("detail click flow did not finish correctly")


def test_proxy_logic():
    proxy = load_proxy_module()
    calls = []

    def fake_monthly(name, arguments, timeout=30):
        calls.append((name, arguments))
        return {
            "structuredContent": {
                "rows": [
                    {"deptName": "一店", "userName": "甲", "indexValue": 120},
                    {"deptName": "二店", "userName": "乙", "indexValue": 80},
                ]
            }
        }

    proxy.call_upstream_tool = fake_monthly
    summary = proxy.monthly_summary({"month": "上月", "businessType": "sell"})
    if [name for name, _ in calls] != ["queryRptData"]:
        raise SystemExit("direct aggregate path called more than the aggregate tool")
    if summary["metrics"]["primary"]["value"] != 200 or summary["technical"]["detailRowsFetched"] != 0:
        raise SystemExit("direct aggregate path did not return 200 without detail rows")
    if summary["metrics"]["primary"]["drilldown"]["available"]:
        raise SystemExit("monthly aggregate was falsely marked drillable")
    if summary["filterOptions"]["departments"] != ["一店", "二店"]:
        raise SystemExit("aggregate rows did not provide compact filter options")

    calls.clear()

    def fake_current(name, arguments, timeout=30):
        calls.append((name, arguments))
        return {"structuredContent": {"data": {"total": 40, "records": [{"houseNo": "H-1"}]}}}

    proxy.call_upstream_tool = fake_current
    current = proxy.current_listing_summary({"metricId": "currentNewListingCount", "businessType": "sell", "zoneName": "中心商圈"})
    if calls[0][0] != "listHouseByCondition" or calls[0][1].get("size") != 1:
        raise SystemExit("location summary did not request only the pagination total")
    if current["metrics"]["primary"]["value"] != 40 or current["technical"]["detailRowsFetched"] != 0:
        raise SystemExit("location summary did not keep detail rows lazy")
    if not current["metrics"]["primary"]["drilldown"]["available"]:
        raise SystemExit("current listing total should be drillable")

    calls.clear()
    no_click = proxy.metric_details({"metricId": "currentNewListingCount"})
    if calls or not no_click.get("isError"):
        raise SystemExit("detail tool ran without a metric click")
    clicked = proxy.metric_details(
        {
            "metricId": "currentNewListingCount",
            "businessType": "sell",
            "userAction": "metric_click",
            "page": 1,
            "pageSize": 20,
        }
    )
    if calls[0][1].get("size") != 20 or len(clicked["structuredContent"]["rows"]) != 1:
        raise SystemExit("metric click did not fetch exactly one bounded detail page")


def test_proxy_protocol():
    proxy_script = PLUGIN_ROOT / "mcp_servers" / "erp_dashboard_proxy.py"
    replies = mcp_roundtrip(
        proxy_script,
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
            {"jsonrpc": "2.0", "id": 3, "method": "resources/read", "params": {"uri": "ui://erp/dashboard"}},
        ],
    )
    names = {tool["name"] for tool in replies[1]["result"]["tools"]}
    expected = {"showErpDashboard", "queryErpDashboardSummary", "getErpDashboardFilterOptions", "getErpMetricDetails"}
    if expected - names:
        raise SystemExit(f"proxy MCP tools missing: {expected - names}")
    resource = replies[2]["result"]["contents"][0]
    html = resource.get("text", "")
    if resource.get("mimeType") != "text/html;profile=mcp-app":
        raise SystemExit("Widget resource has the wrong MCP Apps MIME type")
    if "callServerTool" not in html or "queryErpDashboardSummary" not in html or "getErpMetricDetails" not in html:
        raise SystemExit("built Widget does not contain live summary and detail calls")

    source = (PLUGIN_ROOT / "mcp_servers" / "widget" / "src" / "main.js").read_text(encoding="utf-8")
    for required in ("new App", "app.ontoolinput", "app.ontoolresult", "app.connect()"):
        if required not in source:
            raise SystemExit(f"official MCP Apps lifecycle missing: {required}")
    for forbidden in ("window.app", "window.openai", "queryErpDashboardData"):
        if forbidden in source:
            raise SystemExit(f"legacy Widget bridge remains: {forbidden}")


def test_static_report(temp_dir):
    report = {
        "meta": {
            "title": "结构测试",
            "generated_at": "2026-07-15T00:00:00+08:00",
            "date_range": {"start": "2026-07-01", "end": "2026-07-31", "label": "2026年7月"},
            "date_basis": "系统统计时间",
            "biz_types": ["全部"],
            "scope": "全公司",
            "plain_summary": "这是结构测试，不包含真实业务数字。",
            "provisional": True,
        },
        "filters": {"time_options": ["2026年7月"], "scope_options": ["全公司"], "biz_options": ["全部"], "requires_requery": True},
        "queries": [{"id": "q1", "source_type": "mcp", "tool": "queryContractFinanceData", "type": "合同明细", "params": {}, "raw_count": 2, "clean_count": 2, "notes": []}],
        "definitions": {"contract_key": "合同类型|合同编号", "attribution": "签约人", "denominator_rule": "测试", "exclusions": []},
        "metrics": [{"id": "contracts", "label": "合同数", "value": 2, "unit": "份", "formula": "按合同类型+合同编号去重", "business_formula": "按合同类型和合同编号去重后计算", "source_query_ids": ["q1"], "record_count": 2, "drilldown": {"available": True, "mode": "embedded", "dataset_id": "contracts", "exact_reconciliation": True, "reason": ""}, "limitations": []}],
        "datasets": {"contracts": [{"合同类型": "测试合同", "合同编号": "TEST-001"}, {"合同类型": "测试合同", "合同编号": "TEST-002"}]},
        "reconciliation": [],
        "limitations": ["结构测试数据，非真实 ERP 数据"],
        "export_recommendations": [],
        "business_explanation": "页面优先说业务结论，技术信息放在折叠区。",
    }
    report_path = temp_dir / "report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
    html = temp_dir / "dashboard.html"
    run([ROOT / "scripts" / "validate_report_data.py", report_path])
    run([ROOT / "scripts" / "render_dashboard.py", report_path, "--out", html])
    run([ROOT / "scripts" / "validate_dashboard.py", html])
    text = html.read_text(encoding="utf-8")
    if "window.app" in text or "window.openai" in text or "queryErpDashboardData" in text:
        raise SystemExit("static fallback still pretends to be a live Widget")
    bad = dict(report)
    bad["export_recommendations"] = ["请导出房源表"]
    bad_path = temp_dir / "bad.json"
    bad_path.write_text(json.dumps(bad, ensure_ascii=False), encoding="utf-8")
    run([ROOT / "scripts" / "render_dashboard.py", bad_path, "--out", temp_dir / "bad.html"], expect_ok=False)


def main():
    with tempfile.TemporaryDirectory() as directory:
        temp_dir = Path(directory)
        count_wizard = assert_route(
            temp_dir,
            "查询上月新上房源数量",
            "house_new_listing_count",
            "house_new_listing_count_fast.json",
        )
        assert_route(
            temp_dir,
            "查询上月新上房源数量和挂牌均价",
            "house_new_listing_price",
            "house_new_listing_price_fast.json",
        )
        wizard = temp_dir / "wizard.html"
        run([ROOT / "scripts" / "render_requirement_wizard.py", "--config", count_wizard, "--out", wizard])
        run([ROOT / "scripts" / "validate_requirement_wizard.py", wizard])
        test_query_gate(temp_dir)
        test_proxy_logic()
        test_proxy_protocol()
        test_static_report(temp_dir)
        run([ROOT / "scripts" / "lookup_field.py", "合同编号", "--limit", "1"])
        house = run([ROOT / "scripts" / "recommend_export.py", "查询上月新上房源数量和挂牌均价"])
        if "请导出房源表" in house.stdout or "需要补充：房源" in house.stdout or "房源明细导出" in house.stdout:
            raise SystemExit("house export recommendation leaked")
    print("SELF_TEST_OK_V3")


if __name__ == "__main__":
    main()
