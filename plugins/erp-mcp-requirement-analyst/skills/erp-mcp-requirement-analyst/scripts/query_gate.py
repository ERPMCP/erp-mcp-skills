#!/usr/bin/env python3
"""Deterministic two-tier gate for fast ERP summaries and lazy details."""

import argparse
import fnmatch
import json
from datetime import datetime, timezone
from pathlib import Path

PHASE_COLLECTING = "COLLECTING_OPTIONS"
PHASE_READY_SUMMARY = "READY_FOR_SUMMARY"
PHASE_SUMMARY_RUNNING = "SUMMARY_RUNNING"
PHASE_SUMMARY_READY = "SUMMARY_READY"
PHASE_DETAIL_AUTHORIZED = "DETAIL_AUTHORIZED"
PHASE_DETAIL_RUNNING = "DETAIL_RUNNING"
PHASE_DETAIL_READY = "DETAIL_READY"
PHASE_FAILED = "QUERY_FAILED"

SUMMARY_TOOLS = {
    "queryRptData",
    "showErpDashboard",
    "queryErpDashboardSummary",
    "calculateErpSummaryMetric",
}

FILTER_TOOLS = {
    "getErpDashboardFilterOptions",
}

DETAIL_TOOLS = {
    "queryContractFinanceData",
    "listHouseByCondition",
    "getHouseByHouseNo",
    "getSectionMarketBaseInfo",
    "getSectionMarketData",
    "listHotSection",
    "getErpMetricDetails",
}

SUMMARY_JSON_PATTERNS = ["summary_*.json", "metric_*.json", "rpt_summary_*.json"]
DETAIL_JSON_PATTERNS = [
    "prices.json",
    "houses_*.json",
    "contracts_*.json",
    "finance_*.json",
    "payments_*.json",
    "performance_*.json",
    "details_*.json",
    "*_detail.json",
]

SUMMARY_BLOCK = "客户尚未确认统计定义，禁止读取ERP汇总数据。"
DETAIL_BLOCK = "客户尚未点击蓝色数字或查看明细，禁止读取ERP明细数据。"


def now():
    return datetime.now(timezone.utc).isoformat()


def default_state(scenario="", query=""):
    return {
        "phase": PHASE_COLLECTING,
        "scenario": scenario,
        "query": query,
        "definition_confirmed": False,
        "summary_ready": False,
        "detail_authorized": False,
        "selected_options": {},
        "summary_tool_calls": [],
        "filter_tool_calls": [],
        "detail_tool_calls": [],
        "summary_json_writes": [],
        "detail_json_writes": [],
        "preview_writes": [],
        "events": [{"at": now(), "event": "init", "phase": PHASE_COLLECTING}],
    }


def read_state(path):
    p = Path(path)
    if not p.exists():
        raise SystemExit(f"state file not found: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def write_state(path, state):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def print_json(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


def query_class(tool, explicit=""):
    if explicit:
        return explicit
    if tool in SUMMARY_TOOLS:
        return "summary"
    if tool in FILTER_TOOLS:
        return "filter_options"
    if tool in DETAIL_TOOLS:
        return "detail"
    return "other"


def summary_allowed(state):
    return state.get("phase") in {
        PHASE_READY_SUMMARY,
        PHASE_SUMMARY_RUNNING,
        PHASE_SUMMARY_READY,
        PHASE_DETAIL_READY,
    }


def filters_allowed(state):
    return state.get("phase") in {PHASE_SUMMARY_READY, PHASE_DETAIL_READY}


def detail_allowed(state):
    return state.get("phase") in {PHASE_DETAIL_AUTHORIZED, PHASE_DETAIL_RUNNING}


def cmd_init(args):
    state = default_state(args.scenario, args.query)
    write_state(args.state, state)
    print_json(state)


def cmd_choose(args):
    state = read_state(args.state)
    state.setdefault("selected_options", {})[args.key] = args.value
    state["phase"] = PHASE_COLLECTING
    state.setdefault("events", []).append(
        {"at": now(), "event": "choose_option", "key": args.key, "phase": PHASE_COLLECTING}
    )
    write_state(args.state, state)
    print_json(state)


def cmd_confirm_definition(args):
    state = read_state(args.state)
    if not state.get("selected_options") and not args.allow_defaults:
        raise SystemExit("at least one explicit option or --allow-defaults is required")
    state["phase"] = PHASE_READY_SUMMARY
    state["definition_confirmed"] = True
    state.setdefault("events", []).append(
        {"at": now(), "event": "definition_confirmed", "source": args.source, "phase": PHASE_READY_SUMMARY}
    )
    write_state(args.state, state)
    print_json(state)


def cmd_guard(args):
    state = read_state(args.state)
    kind = query_class(args.tool, args.kind)
    record = {"at": now(), "tool": args.tool, "output": args.output}

    if kind == "summary":
        if not summary_allowed(state):
            print(SUMMARY_BLOCK)
            raise SystemExit(2)
        state["phase"] = PHASE_SUMMARY_RUNNING
        state.setdefault("summary_tool_calls", []).append(record)
    elif kind == "filter_options":
        if not filters_allowed(state):
            print(SUMMARY_BLOCK)
            raise SystemExit(2)
        state.setdefault("filter_tool_calls", []).append(record)
    elif kind == "detail":
        if not detail_allowed(state):
            print(DETAIL_BLOCK)
            raise SystemExit(2)
        state["phase"] = PHASE_DETAIL_RUNNING
        state.setdefault("detail_tool_calls", []).append(record)
    else:
        state.setdefault("events", []).append(
            {"at": now(), "event": "other_tool", "tool": args.tool, "phase": state.get("phase")}
        )

    if kind != "other":
        state.setdefault("events", []).append(
            {"at": now(), "event": f"{kind}_tool_allowed", "tool": args.tool, "phase": state.get("phase")}
        )
    write_state(args.state, state)
    print_json(state)


def cmd_summary_ready(args):
    state = read_state(args.state)
    if state.get("phase") not in {PHASE_SUMMARY_RUNNING, PHASE_SUMMARY_READY}:
        raise SystemExit("summary can only complete after a summary query")
    state["phase"] = PHASE_SUMMARY_READY
    state["summary_ready"] = True
    state.setdefault("events", []).append(
        {"at": now(), "event": "summary_ready", "phase": PHASE_SUMMARY_READY}
    )
    write_state(args.state, state)
    print_json(state)


def cmd_authorize_detail(args):
    state = read_state(args.state)
    if state.get("phase") not in {PHASE_SUMMARY_READY, PHASE_DETAIL_READY}:
        raise SystemExit("details can only be authorized after a summary is visible")
    state["phase"] = PHASE_DETAIL_AUTHORIZED
    state["detail_authorized"] = True
    state["detail_metric_id"] = args.metric_id
    state.setdefault("events", []).append(
        {
            "at": now(),
            "event": "detail_authorized",
            "source": args.source,
            "metric_id": args.metric_id,
            "phase": PHASE_DETAIL_AUTHORIZED,
        }
    )
    write_state(args.state, state)
    print_json(state)


def cmd_detail_ready(args):
    state = read_state(args.state)
    if state.get("phase") not in {PHASE_DETAIL_RUNNING, PHASE_DETAIL_READY}:
        raise SystemExit("detail can only complete after a detail query")
    state["phase"] = PHASE_DETAIL_READY
    state["detail_authorized"] = False
    state.setdefault("events", []).append(
        {"at": now(), "event": "detail_ready", "phase": PHASE_DETAIL_READY}
    )
    write_state(args.state, state)
    print_json(state)


def classify_json(path, kind):
    if kind != "other":
        return kind
    name = Path(path).name
    if any(fnmatch.fnmatch(name, pattern) for pattern in DETAIL_JSON_PATTERNS):
        return "detail"
    if any(fnmatch.fnmatch(name, pattern) for pattern in SUMMARY_JSON_PATTERNS):
        return "summary"
    return "other"


def cmd_write_json(args):
    state = read_state(args.state)
    kind = classify_json(args.path, args.kind)
    record = {"at": now(), "path": args.path, "kind": kind}
    if kind == "summary":
        if not summary_allowed(state):
            print(SUMMARY_BLOCK)
            raise SystemExit(2)
        state.setdefault("summary_json_writes", []).append(record)
    elif kind == "detail":
        if not detail_allowed(state):
            print(DETAIL_BLOCK)
            raise SystemExit(2)
        state.setdefault("detail_json_writes", []).append(record)
    else:
        state.setdefault("preview_writes", []).append(record)
    state.setdefault("events", []).append(
        {"at": now(), "event": "json_write_allowed", **record, "phase": state.get("phase")}
    )
    write_state(args.state, state)
    print_json(state)


def cmd_fail(args):
    state = read_state(args.state)
    state["phase"] = PHASE_FAILED
    state["error"] = args.reason
    state.setdefault("events", []).append(
        {"at": now(), "event": "fail", "reason": args.reason, "phase": PHASE_FAILED}
    )
    write_state(args.state, state)
    print_json(state)


def cmd_status(args):
    print_json(read_state(args.state))


def main():
    ap = argparse.ArgumentParser(description="Gate ERP summary and detail queries separately.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init")
    p.add_argument("--state", required=True)
    p.add_argument("--scenario", default="")
    p.add_argument("--query", default="")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("choose")
    p.add_argument("--state", required=True)
    p.add_argument("--key", required=True)
    p.add_argument("--value", required=True)
    p.set_defaults(func=cmd_choose)

    p = sub.add_parser("confirm-definition")
    p.add_argument("--state", required=True)
    p.add_argument("--source", choices=["widget", "native_card", "chat", "html"], required=True)
    p.add_argument("--allow-defaults", action="store_true")
    p.set_defaults(func=cmd_confirm_definition)

    p = sub.add_parser("guard")
    p.add_argument("--state", required=True)
    p.add_argument("--tool", required=True)
    p.add_argument("--output", default="")
    p.add_argument("--kind", choices=["summary", "filter_options", "detail", "other"], default="")
    p.set_defaults(func=cmd_guard)

    p = sub.add_parser("summary-ready")
    p.add_argument("--state", required=True)
    p.set_defaults(func=cmd_summary_ready)

    p = sub.add_parser("authorize-detail")
    p.add_argument("--state", required=True)
    p.add_argument("--source", choices=["metric_click", "detail_button", "chat"], required=True)
    p.add_argument("--metric-id", required=True)
    p.set_defaults(func=cmd_authorize_detail)

    p = sub.add_parser("detail-ready")
    p.add_argument("--state", required=True)
    p.set_defaults(func=cmd_detail_ready)

    p = sub.add_parser("write-json")
    p.add_argument("--state", required=True)
    p.add_argument("--path", required=True)
    p.add_argument("--kind", choices=["preview", "summary", "detail", "other"], default="other")
    p.set_defaults(func=cmd_write_json)

    p = sub.add_parser("fail")
    p.add_argument("--state", required=True)
    p.add_argument("--reason", default="")
    p.set_defaults(func=cmd_fail)

    p = sub.add_parser("status")
    p.add_argument("--state", required=True)
    p.set_defaults(func=cmd_status)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
