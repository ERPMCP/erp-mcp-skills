#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT.parents[1]
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


def mcp_roundtrip(script, messages):
    p = subprocess.Popen([PY, str(script)], cwd=PLUGIN_ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        replies = []
        for msg in messages:
            raw = json.dumps(msg, ensure_ascii=False).encode("utf-8")
            p.stdin.write(f"Content-Length: {len(raw)}\r\n\r\n".encode("ascii") + raw)
            p.stdin.flush()
            headers = {}
            while True:
                line = p.stdout.readline()
                if line in (b"\r\n", b"\n"):
                    break
                if not line:
                    raise SystemExit("proxy closed before response")
                key, value = line.decode("ascii").split(":", 1)
                headers[key.lower()] = value.strip()
            length = int(headers.get("content-length", "0"))
            replies.append(json.loads(p.stdout.read(length).decode("utf-8")))
        return replies
    finally:
        try:
            p.stdin.close()
        except Exception:
            pass
        p.terminate()
        p.wait(timeout=5)


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
        if "render_preview_or_widget_shell" not in after or "stop_until_start_query" not in after:
            raise SystemExit("fast route does not force preview before querying")
        if "after_start_query_query_real_erp_data" not in after:
            raise SystemExit("fast route does not defer ERP querying until start query")
        if after.index("after_start_query_query_real_erp_data") < after.index("stop_until_start_query"):
            raise SystemExit("fast route queries before the start-query stop point")

        wizard = td / "wizard.html"
        run([ROOT / "scripts" / "render_requirement_wizard.py", "--config", route_wizard_config, "--out", wizard])
        run([ROOT / "scripts" / "validate_requirement_wizard.py", wizard])

        state = td / "state.json"
        run([ROOT / "scripts" / "query_gate.py", "init", "--state", state, "--scenario", "house_new_listing_price", "--query", "查询上月新上房源数量和挂牌均价"])
        gate_data = json.loads(state.read_text(encoding="utf-8"))
        if gate_data.get("phase") != "COLLECTING_OPTIONS" or gate_data.get("business_tool_calls"):
            raise SystemExit("query gate did not start in COLLECTING_OPTIONS")
        blocked_tool = run([ROOT / "scripts" / "query_gate.py", "guard", "--state", state, "--tool", "queryRptData"], expect_ok=False)
        if "客户尚未点击开始查询" not in blocked_tool.stdout:
            raise SystemExit("query gate did not block business tool before confirmation")
        blocked_json = run([ROOT / "scripts" / "query_gate.py", "write-json", "--state", state, "--path", str(td / "prices.json"), "--kind", "business"], expect_ok=False)
        if "客户尚未点击开始查询" not in blocked_json.stdout:
            raise SystemExit("query gate did not block business JSON before confirmation")
        run([ROOT / "scripts" / "query_gate.py", "choose", "--state", state, "--key", "business_type", "--value", "sell"])
        gate_data = json.loads(state.read_text(encoding="utf-8"))
        if gate_data.get("phase") != "COLLECTING_OPTIONS" or gate_data.get("query_authorized"):
            raise SystemExit("choosing business type must not authorize query")
        blocked_after_choice = run([ROOT / "scripts" / "query_gate.py", "guard", "--state", state, "--tool", "listHouseByCondition"], expect_ok=False)
        if "客户尚未点击开始查询" not in blocked_after_choice.stdout:
            raise SystemExit("query gate allowed ERP probing after option selection")
        run([ROOT / "scripts" / "query_gate.py", "ready", "--state", state])
        gate_data = json.loads(state.read_text(encoding="utf-8"))
        if gate_data.get("phase") != "READY_FOR_PREVIEW":
            raise SystemExit("query gate did not enter READY_FOR_PREVIEW")
        blocked_ready = run([ROOT / "scripts" / "query_gate.py", "guard", "--state", state, "--tool", "queryRptData"], expect_ok=False)
        if "客户尚未点击开始查询" not in blocked_ready.stdout:
            raise SystemExit("query gate allowed ERP probing while ready for preview")
        widget_html = td / "widget.html"
        static_html = td / "static.html"
        run([ROOT / "scripts" / "render_widget_shell.py", "--config", route_wizard_config, "--out", widget_html, "--mode", "widget", "--state-id", str(state)])
        run([ROOT / "scripts" / "render_widget_shell.py", "--config", route_wizard_config, "--out", static_html, "--mode", "static", "--state-id", str(state)])
        widget_text = widget_html.read_text(encoding="utf-8")
        static_text = static_html.read_text(encoding="utf-8")
        if "确认后查询" not in widget_text or "queryErpDashboardData" not in widget_text or "callServerTool" not in widget_text:
            raise SystemExit("widget shell is not a realtime query entrance")
        if "确认后查询" not in static_text or "callServerTool" in static_text or "queryErpDashboardData" in static_text:
            raise SystemExit("static shell pretends to be realtime")
        run([ROOT / "scripts" / "query_gate.py", "preview-shown", "--state", state, "--source", "widget"])
        gate_data = json.loads(state.read_text(encoding="utf-8"))
        if gate_data.get("phase") != "PREVIEW_SHOWN" or gate_data.get("query_authorized"):
            raise SystemExit("preview display must not authorize query")
        blocked_preview = run([ROOT / "scripts" / "query_gate.py", "guard", "--state", state, "--tool", "queryRptData"], expect_ok=False)
        if "客户尚未点击开始查询" not in blocked_preview.stdout:
            raise SystemExit("query gate allowed ERP probing after preview display")
        run([ROOT / "scripts" / "query_gate.py", "authorize", "--state", state, "--source", "widget"])
        run([ROOT / "scripts" / "query_gate.py", "guard", "--state", state, "--tool", "queryErpDashboardData"])
        gate_data = json.loads(state.read_text(encoding="utf-8"))
        if gate_data.get("phase") != "QUERY_RUNNING" or not gate_data.get("business_tool_calls"):
            raise SystemExit("query gate did not allow business query after explicit start query")
        run([ROOT / "scripts" / "query_gate.py", "write-json", "--state", state, "--path", str(td / "counts_all.json"), "--kind", "business"])
        gate_data = json.loads(state.read_text(encoding="utf-8"))
        if not gate_data.get("business_json_writes"):
            raise SystemExit("query gate did not log business JSON after confirmation")

        proxy_script = PLUGIN_ROOT / "mcp_servers" / "erp_dashboard_proxy.py"
        replies = mcp_roundtrip(proxy_script, [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
            {"jsonrpc": "2.0", "id": 3, "method": "resources/read", "params": {"uri": "ui://erp/dashboard"}},
            {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "showErpDashboard", "arguments": {}}},
        ])
        tool_names = {t["name"] for t in replies[1]["result"]["tools"]}
        if {"showErpDashboard", "queryErpDashboardData", "getErpMetricDetails"} - tool_names:
            raise SystemExit("proxy MCP tools missing")
        widget_resource = replies[2]["result"]["contents"][0]
        if widget_resource.get("mimeType") != "text/html;profile=mcp-app" or "callServerTool" not in widget_resource.get("text", ""):
            raise SystemExit("proxy MCP widget resource is not a realtime MCP Apps widget")
        if replies[3]["result"].get("_meta", {}).get("ui", {}).get("resourceUri") != "ui://erp/dashboard":
            raise SystemExit("showErpDashboard did not attach widget resource")

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
        bad_js = td / "bad-js.html"
        bad_js.write_text('<script>function setMetric(id){const el=document.getElementById(id);el.querySelector(".value").innerHTML="1"}</script><script id="report-data" type="application/json">{"metrics":[],"datasets":{},"filters":{}}</script>', encoding="utf-8")
        run([ROOT / "scripts" / "validate_dashboard.py", bad_js], expect_ok=False)
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

