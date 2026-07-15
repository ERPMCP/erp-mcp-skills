#!/usr/bin/env python3
"""Deterministic guard for the preview-first ERP workflow.

This script does not call ERP. It records the report phase and blocks accidental
business-data reads or raw JSON writes before the customer confirms the preview.
"""

import argparse
import fnmatch
import json
from datetime import datetime, timezone
from pathlib import Path

PHASE_PREVIEW = "PREVIEW_PENDING"
PHASE_CONFIRMED = "QUERY_CONFIRMED"
PHASE_RUNNING = "QUERY_RUNNING"
PHASE_COMPLETE = "QUERY_COMPLETE"
PHASE_FAILED = "QUERY_FAILED"

BUSINESS_TOOLS = {
    "queryRptData",
    "queryContractFinanceData",
    "listHouseByCondition",
    "getHouseByHouseNo",
    "getSectionMarketBaseInfo",
    "getSectionMarketData",
    "listHotSection",
    "queryErpDashboardData",
    "getErpMetricDetails",
}

BUSINESS_JSON_PATTERNS = [
    "prices.json",
    "counts_*.json",
    "houses_*.json",
    "contracts_*.json",
    "rpt_*.json",
    "finance_*.json",
    "payments_*.json",
    "performance_*.json",
    "*_business.json",
]

BLOCK_MESSAGE = "客户尚未确认预览，禁止读取ERP数据。"


def now():
    return datetime.now(timezone.utc).isoformat()


def default_state(scenario="", query=""):
    return {
        "phase": PHASE_PREVIEW,
        "confirmed": False,
        "query_started": False,
        "scenario": scenario,
        "query": query,
        "confirmation_source": None,
        "business_tool_calls": [],
        "business_json_writes": [],
        "preview_writes": [],
        "events": [{"at": now(), "event": "init", "phase": PHASE_PREVIEW}],
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


def can_read_business(state):
    return state.get("phase") in {PHASE_CONFIRMED, PHASE_RUNNING}


def is_business_json(path, kind):
    if kind == "business":
        return True
    name = Path(path).name
    return any(fnmatch.fnmatch(name, pattern) for pattern in BUSINESS_JSON_PATTERNS)


def print_json(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_init(args):
    state = default_state(args.scenario, args.query)
    write_state(args.state, state)
    print_json(state)


def cmd_confirm(args):
    state = read_state(args.state)
    if state.get("phase") == PHASE_COMPLETE:
        raise SystemExit("query is already complete")
    state["phase"] = PHASE_CONFIRMED
    state["confirmed"] = True
    state["confirmation_source"] = args.source
    state.setdefault("events", []).append({"at": now(), "event": "confirm", "source": args.source, "phase": PHASE_CONFIRMED})
    write_state(args.state, state)
    print_json(state)


def cmd_guard(args):
    state = read_state(args.state)
    business = args.business or args.tool in BUSINESS_TOOLS
    if business and not can_read_business(state):
        print(BLOCK_MESSAGE)
        raise SystemExit(2)
    if business:
        state["phase"] = PHASE_RUNNING
        state["query_started"] = True
        state.setdefault("business_tool_calls", []).append({"at": now(), "tool": args.tool, "output": args.output})
        state.setdefault("events", []).append({"at": now(), "event": "business_tool_allowed", "tool": args.tool, "phase": PHASE_RUNNING})
    else:
        state.setdefault("events", []).append({"at": now(), "event": "non_business_tool", "tool": args.tool, "phase": state.get("phase")})
    write_state(args.state, state)
    print_json(state)


def cmd_write_json(args):
    state = read_state(args.state)
    business = is_business_json(args.path, args.kind)
    if business and not can_read_business(state):
        print(BLOCK_MESSAGE)
        raise SystemExit(2)
    record = {"at": now(), "path": args.path, "kind": "business" if business else args.kind}
    if business:
        state.setdefault("business_json_writes", []).append(record)
    else:
        state.setdefault("preview_writes", []).append(record)
    state.setdefault("events", []).append({"at": now(), "event": "json_write_allowed", **record, "phase": state.get("phase")})
    write_state(args.state, state)
    print_json(state)


def cmd_complete(args):
    state = read_state(args.state)
    state["phase"] = PHASE_COMPLETE
    state.setdefault("events", []).append({"at": now(), "event": "complete", "phase": PHASE_COMPLETE})
    write_state(args.state, state)
    print_json(state)


def cmd_fail(args):
    state = read_state(args.state)
    state["phase"] = PHASE_FAILED
    state["error"] = args.reason
    state.setdefault("events", []).append({"at": now(), "event": "fail", "reason": args.reason, "phase": PHASE_FAILED})
    write_state(args.state, state)
    print_json(state)


def cmd_status(args):
    print_json(read_state(args.state))


def main():
    ap = argparse.ArgumentParser(description="Gate ERP business queries until customer confirmation.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init")
    p.add_argument("--state", required=True)
    p.add_argument("--scenario", default="")
    p.add_argument("--query", default="")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("confirm")
    p.add_argument("--state", required=True)
    p.add_argument("--source", choices=["widget", "native_card", "chat"], required=True)
    p.set_defaults(func=cmd_confirm)

    p = sub.add_parser("guard")
    p.add_argument("--state", required=True)
    p.add_argument("--tool", required=True)
    p.add_argument("--output", default="")
    p.add_argument("--business", action="store_true")
    p.set_defaults(func=cmd_guard)

    p = sub.add_parser("write-json")
    p.add_argument("--state", required=True)
    p.add_argument("--path", required=True)
    p.add_argument("--kind", choices=["preview", "business", "other"], default="other")
    p.set_defaults(func=cmd_write_json)

    p = sub.add_parser("complete")
    p.add_argument("--state", required=True)
    p.set_defaults(func=cmd_complete)

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
