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


def test_skill_contract():
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    allow_line = next((line for line in skill.splitlines() if line.startswith("allowed-tools:")), "")
    expected = "allowed-tools: AskUserQuestion, mcp__erp_dashboard_proxy__showErpDashboard"
    if allow_line != expected:
        raise SystemExit(f"first-turn tool allowlist changed: {allow_line}")
    for forbidden in ("Read", "Write", "Bash", "mcp__erp__"):
        if forbidden in allow_line:
            raise SystemExit(f"forbidden first-turn tool leaked into allowlist: {forbidden}")
    for required in (
        "快速模式 2.4",
        "新房业务（新增数量可查；当前挂牌均价查不到）",
        "全部业务（新增数量可查；挂牌均价不能用同一种方式合并）",
        "按面积计算均价（推荐）：先算每套房单价，再按面积大小综合；大面积房源影响更大，适合看市场均价。",
        "按套数简单平均：每套房都算一票；小房子和大房子影响一样，适合快速粗略核对。",
        "After asking any question, stop the turn",
        "Never translate an unavailable request into a nearby available field",
        "按公司部门和人员看",
        "按房源所在位置看",
        "never create `data.py`",
    ):
        if required not in skill:
            raise SystemExit(f"skill contract missing: {required}")
    if "鏂颁" in skill or "�" in skill:
        raise SystemExit("SKILL.md contains broken Chinese encoding")

    removed = [
        ROOT / "references" / "house_new_listing_price_case.md",
        ROOT / "references" / "fast_scenario_router.json",
        ROOT / "references" / "house_new_listing_count_fast.json",
        ROOT / "references" / "house_new_listing_price_fast.json",
        ROOT / "scripts" / "fast_route.py",
        ROOT / "scripts" / "query_gate.py",
        ROOT / "assets" / "requirement_wizard_template.html",
        ROOT / "scripts" / "render_requirement_wizard.py",
    ]
    existing = [str(path.relative_to(ROOT)) for path in removed if path.exists()]
    if existing:
        raise SystemExit(f"obsolete slow-path files still exist: {existing}")

    agent_text = (ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
    if 'value: "erp"' in agent_text:
        raise SystemExit("agent metadata still asks WorkBuddy to load the direct ERP server")


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
    summary = proxy.monthly_summary(
        {
            "month": "上月",
            "businessType": "sell",
            "scenario": "house_new_listing_price",
            "includeReferencePrice": True,
            "priceMethod": "equal_weight",
        }
    )
    if [name for name, _ in calls] != ["queryRptData"]:
        raise SystemExit("initial result used anything other than the aggregate path")
    if summary["metrics"]["primary"]["value"] != 200 or summary["technical"]["detailRowsFetched"] != 0:
        raise SystemExit("aggregate path did not return 200 without display details")
    if summary["metrics"]["primary"]["drilldown"]["available"]:
        raise SystemExit("monthly aggregate was falsely marked drillable")
    if summary["secondaryMetric"]["status"] != "waiting_for_user":
        raise SystemExit("price calculation started before the page button click")
    if summary["filterOptions"]["departments"] != ["一店", "二店"]:
        raise SystemExit("aggregate rows did not provide compact filter options")

    calls.clear()

    def fake_current(name, arguments, timeout=30):
        calls.append((name, arguments))
        return {"structuredContent": {"data": {"total": 40, "records": [{"houseNo": "H-1"}]}}}

    proxy.call_upstream_tool = fake_current
    current = proxy.current_listing_summary(
        {
            "metricId": "currentNewListingCount",
            "businessType": "sell",
            "zoneName": "中心商圈",
            "includeReferencePrice": True,
        }
    )
    if calls[0][0] != "listHouseByCondition" or calls[0][1].get("size") != 1:
        raise SystemExit("location summary did not request only the pagination total")
    if current["metrics"]["primary"]["value"] != 40 or current["technical"]["detailRowsFetched"] != 0:
        raise SystemExit("location summary did not keep detail rows lazy")
    if current["secondaryMetric"]["status"] != "waiting_for_user":
        raise SystemExit("location filter started price calculation without a click")

    calls.clear()
    blocked_price = proxy.listing_price_summary({"businessType": "sell"})
    if calls or not blocked_price.get("isError"):
        raise SystemExit("price calculation ran without the calculate button action")

    def fake_price(name, arguments, timeout=30):
        calls.append((name, arguments))
        return {
            "structuredContent": {
                "data": {
                    "total": 2,
                    "records": [
                        {"unitPrice": 10000, "area": 100},
                        {"unitPrice": 20000, "area": 200},
                    ],
                }
            }
        }

    proxy.call_upstream_tool = fake_price
    equal = proxy.listing_price_summary(
        {"businessType": "sell", "priceMethod": "equal_weight", "userAction": "calculate_price"}
    )["structuredContent"]["secondaryMetric"]
    if equal["value"] != 15000 or equal["technical"]["detailRowsFetchedForDisplay"] != 0:
        raise SystemExit("equal-weight price calculation is wrong or exposed detail rows")
    weighted = proxy.listing_price_summary(
        {"businessType": "sell", "priceMethod": "area_weighted", "userAction": "calculate_price"}
    )["structuredContent"]["secondaryMetric"]
    if round(weighted["value"], 2) != 16666.67:
        raise SystemExit("area-weighted price calculation is wrong")

    source = (PLUGIN_ROOT / "mcp_servers" / "erp_dashboard_proxy.py").read_text(encoding="utf-8")
    if "unit_prices = []" in source:
        raise SystemExit("price calculation still retains one value per house instead of running totals")

    calls.clear()

    def fake_locations(name, arguments, timeout=30):
        calls.append((name, arguments))
        return {
            "structuredContent": {
                "data": {
                    "total": 3,
                    "records": [
                        {"districtName": "东区", "zoneName": "中心商圈", "sectionName": "甲小区"},
                        {"districtName": "东区", "zoneName": "中心商圈", "sectionName": "乙小区"},
                        {"districtName": "西区", "zoneName": "新城商圈", "sectionName": "丙小区"},
                    ],
                }
            }
        }

    proxy.call_upstream_tool = fake_locations
    blocked_options = proxy.location_filter_options({"businessType": "sell"})
    if calls or not blocked_options.get("isError"):
        raise SystemExit("location dropdown options loaded before the customer opened that view")
    options = proxy.location_filter_options(
        {"businessType": "sell", "userAction": "load_filter_options"}
    )["structuredContent"]
    if not options["filterOptions"]["complete"] or len(options["filterOptions"]["locations"]) != 3:
        raise SystemExit("location fields were not converted into complete dropdown options")
    if options["technical"]["detailRowsFetchedForDisplay"] != 0:
        raise SystemExit("location option loading exposed property detail rows")

    calls.clear()
    proxy.call_upstream_tool = fake_current
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
    expected = {
        "showErpDashboard",
        "queryErpDashboardSummary",
        "getErpDashboardFilterOptions",
        "queryErpDashboardSecondaryMetric",
        "getErpMetricDetails",
    }
    if expected - names:
        raise SystemExit(f"proxy MCP tools missing: {expected - names}")
    by_name = {tool["name"]: tool for tool in replies[1]["result"]["tools"]}
    if by_name["showErpDashboard"].get("_meta", {}).get("ui", {}).get("visibility") != ["model"]:
        raise SystemExit("initial dashboard tool is not model-visible")
    for name in expected - {"showErpDashboard"}:
        if by_name[name].get("_meta", {}).get("ui", {}).get("visibility") != ["app"]:
            raise SystemExit(f"page-only tool leaked to the model: {name}")

    resource = replies[2]["result"]["contents"][0]
    html = resource.get("text", "")
    if resource.get("mimeType") != "text/html;profile=mcp-app":
        raise SystemExit("Widget resource has the wrong MCP Apps MIME type")
    for required in (
        "callServerTool",
        "queryErpDashboardSummary",
        "queryErpDashboardSecondaryMetric",
        "getErpMetricDetails",
        "按公司部门和人员看",
        "按房源所在位置看",
        "getErpDashboardFilterOptions",
    ):
        if required not in html:
            raise SystemExit(f"built Widget is stale or incomplete: {required}")
    script_start = html.find("<script>")
    script_end = html.rfind("</script>")
    if script_start < 0 or script_end <= script_start:
        raise SystemExit("built Widget does not contain one complete inline script")
    bundled_script = html[script_start + len("<script>") : script_end]
    if "<!doctype html>" in bundled_script.lower() or "/*__APP_JS__*/" in bundled_script:
        raise SystemExit("Widget template was injected into its own JavaScript bundle")

    source = (PLUGIN_ROOT / "mcp_servers" / "widget" / "src" / "main.js").read_text(encoding="utf-8")
    for required in ("new App", "app.ontoolinput", "app.ontoolresult", "app.connect()"):
        if required not in source:
            raise SystemExit(f"official MCP Apps lifecycle missing: {required}")
    for forbidden in ("window.app", "window.openai", "queryErpDashboardData", "鏂颁"):
        if forbidden in source:
            raise SystemExit(f"legacy or broken Widget content remains: {forbidden}")
    template = (PLUGIN_ROOT / "mcp_servers" / "widget" / "src" / "index.html").read_text(encoding="utf-8")
    for field in ("deptName", "userName", "districtName", "zoneName", "sectionLike"):
        if f'<select id="{field}"' not in template or f'<input id="{field}"' in template:
            raise SystemExit(f"enumerable ERP filter is not a dropdown: {field}")


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
    test_skill_contract()
    test_proxy_logic()
    test_proxy_protocol()
    with tempfile.TemporaryDirectory() as directory:
        temp_dir = Path(directory)
        test_static_report(temp_dir)
        run([ROOT / "scripts" / "lookup_field.py", "合同编号", "--limit", "1"])
        house = run([ROOT / "scripts" / "recommend_export.py", "查询上月新上房源数量和挂牌均价"])
        if "请导出房源表" in house.stdout or "需要补充：房源" in house.stdout or "房源明细导出" in house.stdout:
            raise SystemExit("house export recommendation leaked")
    print("SELF_TEST_OK_V4")


if __name__ == "__main__":
    main()
