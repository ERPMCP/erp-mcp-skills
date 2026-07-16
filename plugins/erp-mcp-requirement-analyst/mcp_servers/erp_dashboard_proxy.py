#!/usr/bin/env python3
"""Local MCP Apps proxy: quick ERP summaries, lazy filters, click-only details."""

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import date, timedelta
from pathlib import Path

WIDGET_URI = "ui://erp/dashboard"
SERVER_NAME = "erp-dashboard-proxy"
SERVER_VERSION = "2.4.3"
PROTOCOL_VERSION = "2025-06-18"
WIDGET_PATH = Path(__file__).resolve().parent / "widget" / "dist" / "index.html"

SESSION_ID = ""
SESSION_INITIALIZED = False
REQUEST_ID = 0
LAST_FILTER_OPTIONS = {"departments": [], "people": []}
LAST_LOCATION_OPTIONS = {"locations": [], "complete": False, "businessType": ""}


def read_message():
    headers = {}
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            return None
        if line in (b"\r\n", b"\n"):
            break
        key, value = line.decode("ascii", errors="ignore").split(":", 1)
        headers[key.lower()] = value.strip()
    length = int(headers.get("content-length", "0"))
    if length <= 0:
        return None
    return json.loads(sys.stdin.buffer.read(length).decode("utf-8"))


def write_message(payload):
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    sys.stdout.buffer.write(f"Content-Length: {len(raw)}\r\n\r\n".encode("ascii") + raw)
    sys.stdout.buffer.flush()


def result(msg, data):
    write_message({"jsonrpc": "2.0", "id": msg.get("id"), "result": data})


def error(msg, code, message):
    write_message({"jsonrpc": "2.0", "id": msg.get("id"), "error": {"code": code, "message": message}})


def tool(name, description, schema, *, widget=False, visibility=None):
    data = {"name": name, "description": description, "inputSchema": schema}
    ui = {}
    if widget:
        ui["resourceUri"] = WIDGET_URI
    if visibility:
        ui["visibility"] = visibility
    if ui:
        data["_meta"] = {"ui": ui}
    return data


FILTER_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "scenario": {"type": "string"},
        "metricId": {
            "type": "string",
            "enum": ["monthlyNewListingCount", "currentNewListingCount"],
            "default": "monthlyNewListingCount",
        },
        "month": {"type": "string", "default": "上月"},
        "startDate": {"type": "string"},
        "endDate": {"type": "string"},
        "businessType": {"type": "string", "default": "sell"},
        "includeReferencePrice": {"type": "boolean", "default": False},
        "priceMethod": {
            "type": "string",
            "enum": ["equal_weight", "area_weighted"],
            "default": "equal_weight",
        },
        "filterMode": {
            "type": "string",
            "enum": ["both", "organization", "location", "none"],
            "default": "both",
        },
        "deptName": {"type": "string"},
        "userName": {"type": "string"},
        "districtName": {"type": "string"},
        "zoneName": {"type": "string"},
        "sectionLike": {"type": "string"},
    },
}


def tools_list():
    detail_schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["metricId", "userAction"],
        "properties": {
            **FILTER_SCHEMA["properties"],
            "userAction": {"type": "string", "enum": ["metric_click", "load_more"]},
            "page": {"type": "integer", "minimum": 1, "default": 1},
            "pageSize": {"type": "integer", "minimum": 1, "maximum": 50, "default": 20},
        },
    }
    price_schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["userAction"],
        "properties": {
            **FILTER_SCHEMA["properties"],
            "userAction": {"type": "string", "enum": ["calculate_price"]},
        },
    }
    option_schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "filterKind": {"type": "string", "enum": ["organization", "location"], "default": "organization"},
            "businessType": {"type": "string", "default": "sell"},
            "userAction": {"type": "string", "enum": ["load_filter_options"]},
        },
    }
    return [
        tool(
            "showErpDashboard",
            "客户确认统计定义后使用。优先读取现成汇总；没有现成数字时执行最小字段计算，并打开实时看板。不会预取展示明细。",
            FILTER_SCHEMA,
            widget=True,
            visibility=["model"],
        ),
        tool(
            "queryErpDashboardSummary",
            "看板筛选按钮使用。刷新一个逻辑汇总结果；必要时可重新计算，但不返回数字背后的展示明细。",
            FILTER_SCHEMA,
            visibility=["app"],
        ),
        tool(
            "getErpDashboardFilterOptions",
            "返回下拉框选项。公司部门和人员复用汇总结果；房源位置仅在用户打开该查看方式后读取并去重区域、商圈和小区，不返回房源明细。",
            option_schema,
            visibility=["app"],
        ),
        tool(
            "queryErpDashboardSecondaryMetric",
            "仅在用户点击计算挂牌均价后，读取计算所需字段并返回均价；不返回或保存逐套房源。",
            price_schema,
            visibility=["app"],
        ),
        tool(
            "getErpMetricDetails",
            "仅在用户点击蓝色数字或加载更多时读取一页同口径明细。",
            detail_schema,
            visibility=["app"],
        ),
    ]


def load_widget_html():
    if not WIDGET_PATH.exists():
        return """<!doctype html><html lang=\"zh-CN\"><meta charset=\"utf-8\"><title>ERP 实时看板</title><body><main><h1>实时看板资源尚未构建</h1><p>请运行 Widget 构建脚本后重新加载插件。没有显示任何假数据。</p></main></body></html>"""
    return WIDGET_PATH.read_text(encoding="utf-8")


def resource_payload():
    return {
        "contents": [
            {
                "uri": WIDGET_URI,
                "mimeType": "text/html;profile=mcp-app",
                "text": load_widget_html(),
                "_meta": {"ui": {"csp": {"connectDomains": [], "resourceDomains": []}}},
            }
        ]
    }


def text_result(text, structured=None, *, attach_widget=False, is_error=False):
    data = {
        "content": [{"type": "text", "text": text}],
        "structuredContent": structured or {},
    }
    if attach_widget:
        data["_meta"] = {"ui": {"resourceUri": WIDGET_URI}}
    if is_error:
        data["isError"] = True
    return data


def parse_month(args):
    explicit_start = str(args.get("startDate") or "").strip()
    explicit_end = str(args.get("endDate") or "").strip()
    if explicit_start and explicit_end:
        return explicit_start, explicit_end, f"{explicit_start} 至 {explicit_end}"

    today = date.today()
    first_this_month = today.replace(day=1)
    label = str(args.get("month") or "上月")
    if label == "上月":
        end = first_this_month - timedelta(days=1)
        start = end.replace(day=1)
    else:
        start = first_this_month
        if start.month == 12:
            end = start.replace(year=start.year + 1, month=1) - timedelta(days=1)
        else:
            end = start.replace(month=start.month + 1) - timedelta(days=1)
    return start.isoformat(), end.isoformat(), f"{start.year}年{start.month}月"


def upstream_url():
    return os.environ.get("ERP_MCP_URL", "https://portal.fangline.cn/mcp").strip()


def upstream_token():
    token = (
        os.environ.get("ERP_MCP_TOKEN", "").strip()
        or os.environ.get("FANGLINE_MCP_TOKEN", "").strip()
    )
    return token[7:].strip() if token.startswith("Bearer ") else token


def parse_http_payload(text):
    text = text.strip()
    if not text:
        return {}
    if text.startswith("data:") or "\ndata:" in text:
        candidates = []
        for line in text.splitlines():
            if line.startswith("data:"):
                raw = line[5:].strip()
                if raw and raw != "[DONE]":
                    candidates.append(raw)
        for raw in reversed(candidates):
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                continue
    return json.loads(text)


def post_upstream(payload, *, timeout=30):
    global SESSION_ID
    url = upstream_url()
    token = upstream_token()
    if not url or not token:
        raise RuntimeError("插件还没有配置 ERP MCP 地址或 Token。")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Authorization": f"Bearer {token}",
        "MCP-Protocol-Version": PROTOCOL_VERSION,
    }
    if SESSION_ID:
        headers["Mcp-Session-Id"] = SESSION_ID
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=raw, method="POST", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            SESSION_ID = resp.headers.get("Mcp-Session-Id", SESSION_ID)
            return parse_http_payload(resp.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"远程 ERP MCP 返回 {exc.code}: {detail[:500]}")
    except Exception as exc:
        raise RuntimeError(f"无法连接远程 ERP MCP: {exc}")


def ensure_upstream_session():
    global REQUEST_ID, SESSION_INITIALIZED
    if SESSION_INITIALIZED:
        return
    REQUEST_ID += 1
    init = post_upstream(
        {
            "jsonrpc": "2.0",
            "id": REQUEST_ID,
            "method": "initialize",
            "params": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            },
        }
    )
    if init.get("error"):
        raise RuntimeError(str(init["error"]))
    post_upstream({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}, timeout=10)
    SESSION_INITIALIZED = True


def call_upstream_tool(name, arguments, *, timeout=30):
    global REQUEST_ID
    ensure_upstream_session()
    REQUEST_ID += 1
    data = post_upstream(
        {
            "jsonrpc": "2.0",
            "id": REQUEST_ID,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        },
        timeout=timeout,
    )
    if data.get("error"):
        raise RuntimeError(str(data["error"]))
    return data.get("result", data)


def extract_jsonish(value):
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in ("structuredContent", "data", "result"):
            if key in value:
                got = extract_jsonish(value[key])
                if got is not None:
                    return got
        content = value.get("content")
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and isinstance(item.get("text"), str):
                    try:
                        got = extract_jsonish(json.loads(item["text"]))
                        if got is not None:
                            return got
                    except Exception:
                        pass
        for key in ("rows", "records", "list", "items"):
            if isinstance(value.get(key), list):
                return value[key]
    return None


def extract_total(value):
    if isinstance(value, dict):
        for key in ("total", "totalCount", "totalElements"):
            number = to_number(value.get(key))
            if number is not None:
                return int(number)
        for key in ("structuredContent", "data", "result", "page"):
            if key in value:
                got = extract_total(value[key])
                if got is not None:
                    return got
        content = value.get("content")
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and isinstance(item.get("text"), str):
                    try:
                        got = extract_total(json.loads(item["text"]))
                        if got is not None:
                            return got
                    except Exception:
                        pass
    return None


def to_number(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace(",", "").replace("元/㎡", "").replace("元", "").replace("㎡", "").strip()
    try:
        return float(text)
    except ValueError:
        return None


def business_values(value):
    text = str(value or "sell").lower()
    if text in {"rent", "租赁", "租房", "租赁房源"}:
        return "租赁", "rent", "租赁房源"
    if text in {"new_house", "new", "新房", "新房业务"}:
        return "新房", "sell", "新房业务"
    if text in {"all", "全部", "全部业务"}:
        return "全部", "sell", "全部业务"
    return "买卖", "sell", "买卖房源"


def clean_option(value):
    text = str(value or "").strip()
    return text if text and text not in {"null", "None", "-"} else ""


def waiting_price_metric(args):
    requested = bool(args.get("includeReferencePrice")) or args.get("scenario") == "house_new_listing_price"
    return {
        "requested": requested,
        "id": "currentNewListingAveragePrice",
        "label": "当前新上房源挂牌均价",
        "status": "waiting_for_user",
        "display": "点击后计算",
        "priceMethod": args.get("priceMethod", "equal_weight"),
        "message": "先显示新增数量；点击计算后才读取价格和面积字段。",
    }


def monthly_summary(args):
    global LAST_FILTER_OPTIONS
    start, end, month_label = parse_month(args)
    rpt_biz, _, business_label = business_values(args.get("businessType"))
    query = {
        "bizType": rpt_biz,
        "startDate": start,
        "endDate": end,
        "indexName": "新增房源·套",
    }
    dept = clean_option(args.get("deptName"))
    user = clean_option(args.get("userName"))
    if dept:
        query["deptName"] = dept
    if user:
        query["userName"] = user

    raw = call_upstream_tool("queryRptData", {"query": query}, timeout=25)
    rows = extract_jsonish(raw)
    if not isinstance(rows, list):
        raise RuntimeError("统计接口没有返回可识别的汇总行。")
    values = [to_number(row.get("indexValue")) for row in rows if isinstance(row, dict)]
    values = [value for value in values if value is not None]
    if not values:
        raise RuntimeError("统计接口没有返回可验证的新增房源数字。")

    departments = sorted({clean_option(row.get("deptName")) for row in rows if isinstance(row, dict)})
    people = sorted({clean_option(row.get("userName")) for row in rows if isinstance(row, dict)})
    LAST_FILTER_OPTIONS = {
        "departments": [item for item in departments if item][:200],
        "people": [item for item in people if item][:300],
    }
    value = sum(values)
    return {
        "phase": "SUMMARY_READY",
        "view": "organization",
        "filters": {
            "metricId": "monthlyNewListingCount",
            "month": args.get("month", "上月"),
            "startDate": start,
            "endDate": end,
            "monthLabel": month_label,
            "businessType": args.get("businessType", "sell"),
            "businessLabel": business_label,
            "deptName": dept,
            "userName": user,
            "scenario": args.get("scenario", "house_new_listing_count"),
            "includeReferencePrice": bool(args.get("includeReferencePrice")),
            "priceMethod": args.get("priceMethod", "equal_weight"),
            "filterMode": args.get("filterMode", "both"),
        },
        "filterOptions": LAST_FILTER_OPTIONS,
        "secondaryMetric": waiting_price_metric(args),
        "metrics": {
            "primary": {
                "id": "monthlyNewListingCount",
                "label": f"{month_label}新上房源数量",
                "value": value,
                "display": f"{value:,.0f} 套",
                "drilldown": {
                    "available": False,
                    "reason": "当前官方统计只返回汇总数字，没有同一月份、同一统计方式的逐套房源明细。",
                },
            }
        },
        "message": "核心数字已按官方统计读取完成。页面没有预取逐套房源。",
        "plainRule": "这个数字按所选月份、业务类型和部门/人员统计。",
        "technical": {
            "source": "queryRptData",
            "indexName": "新增房源·套",
            "aggregateRows": len(rows),
            "detailRowsFetched": 0,
        },
    }


def current_listing_summary(args):
    _, house_biz, business_label = business_values(args.get("businessType"))
    if house_biz not in {"sell", "rent"}:
        raise RuntimeError("当前新上房源位置筛选只支持买卖或租赁房源。")
    query = {"bizType": house_biz, "current": 1, "size": 1, "isNew": "是"}
    for key in ("districtName", "zoneName", "sectionLike"):
        value = clean_option(args.get(key))
        if value:
            query[key] = value
    raw = call_upstream_tool("listHouseByCondition", query, timeout=25)
    total = extract_total(raw)
    rows = extract_jsonish(raw)
    if total is None and isinstance(rows, list) and not rows:
        total = 0
    if total is None:
        raise RuntimeError("房源列表返回中没有可验证的总套数，不能用首屏条数冒充总数。")
    filters = {key: args.get(key, "") for key in FILTER_SCHEMA["properties"]}
    filters.update({"metricId": "currentNewListingCount", "businessLabel": business_label})
    return {
        "phase": "SUMMARY_READY",
        "view": "location",
        "filters": filters,
        "filterOptions": LAST_FILTER_OPTIONS,
        "secondaryMetric": waiting_price_metric(args),
        "metrics": {
            "primary": {
                "id": "currentNewListingCount",
                "label": "当前新上房源数量",
                "value": total,
                "display": f"{total:,.0f} 套",
                "drilldown": {"available": True, "reason": "点击后按当前条件读取第一页房源明细。"},
            }
        },
        "message": "当前新上房源总数已查询完成，只读取了分页总数，没有预取完整列表。",
        "plainRule": "这是目前仍被系统标记为“新上”的房源，不是所选月份的历史新增房源。",
        "technical": {"source": "listHouseByCondition", "pageSize": 1, "detailRowsFetched": 0},
    }


def query_summary(args):
    try:
        if args.get("metricId") == "currentNewListingCount":
            return text_result("当前新上房源汇总已返回。", current_listing_summary(args))
        return text_result("月度新增房源汇总已返回。", monthly_summary(args))
    except Exception as exc:
        structured = {
            "phase": "QUERY_FAILED",
            "filters": args,
            "metrics": {"primary": {"display": "查询失败", "drilldown": {"available": False}}},
            "message": "暂时没有查到可验证的数字。",
            "limitation": str(exc),
        }
        return text_result(structured["message"], structured, is_error=True)


def row_number(row, aliases):
    for key in aliases:
        number = to_number(row.get(key))
        if number is not None:
            return number
    return None


def listing_price_summary(args):
    if args.get("userAction") != "calculate_price":
        return text_result(
            "挂牌均价必须由页面中的计算按钮触发。",
            {"phase": "QUERY_FAILED", "secondaryMetric": {"status": "blocked"}},
            is_error=True,
        )

    _, house_biz, business_label = business_values(args.get("businessType"))
    if house_biz not in {"sell", "rent"}:
        return text_result(
            "当前挂牌均价只支持买卖或租赁房源。",
            {"phase": "QUERY_FAILED", "secondaryMetric": {"status": "unavailable"}},
            is_error=True,
        )

    method = args.get("priceMethod") or "equal_weight"
    page = 1
    page_size = 200
    total = None
    processed = 0
    valid_price_count = 0
    unit_price_sum = 0.0
    weighted_numerator = 0.0
    weighted_denominator = 0.0

    try:
        while page <= 50:
            query = {"bizType": house_biz, "current": page, "size": page_size, "isNew": "是"}
            for key in ("districtName", "zoneName", "sectionLike"):
                value = clean_option(args.get(key))
                if value:
                    query[key] = value
            raw = call_upstream_tool("listHouseByCondition", query, timeout=60)
            rows = extract_jsonish(raw)
            rows = rows if isinstance(rows, list) else []
            if total is None:
                total = extract_total(raw)

            for row in rows:
                if not isinstance(row, dict):
                    continue
                area = row_number(row, ("area", "buildArea", "acreage", "面积", "建筑面积"))
                unit_price = row_number(row, ("unitPrice", "unit_price", "挂牌单价", "单价"))
                if unit_price is None and area and area > 0:
                    price = row_number(row, ("price", "totalPrice", "挂牌价", "总价", "租金"))
                    if price is not None:
                        unit_price = price * (10000 if house_biz == "sell" else 1) / area
                if unit_price is None or unit_price <= 0:
                    continue
                valid_price_count += 1
                unit_price_sum += unit_price
                if area and area > 0:
                    weighted_numerator += unit_price * area
                    weighted_denominator += area

            processed += len(rows)
            if not rows or len(rows) < page_size or (total is not None and processed >= total):
                break
            page += 1

        if total is not None and processed < total:
            raise RuntimeError("房源页数超过安全上限，未完成全部计算，因此不展示不完整均价。")
        if valid_price_count == 0:
            raise RuntimeError("没有取得可用于计算挂牌均价的有效价格字段。")

        if method == "area_weighted":
            if weighted_denominator <= 0:
                raise RuntimeError("当前结果缺少有效面积，无法按面积计算挂牌均价。")
            value = weighted_numerator / weighted_denominator
            rule = "每套房按面积影响最终均价。"
        else:
            value = unit_price_sum / valid_price_count
            rule = "每套有效房源都算 1 套。"

        return text_result(
            "挂牌均价计算完成。",
            {
                "phase": "SUMMARY_READY",
                "secondaryMetric": {
                    "requested": True,
                    "id": "currentNewListingAveragePrice",
                    "label": "当前新上房源挂牌均价",
                    "status": "ready",
                    "value": value,
                    "display": f"{value:,.0f} 元/㎡",
                    "sampleCount": valid_price_count,
                    "priceMethod": method,
                    "plainRule": rule,
                    "message": "只返回计算结果，没有返回或保存逐套房源。",
                    "technical": {
                        "pagesRead": page,
                        "calculationRows": processed,
                        "detailRowsFetchedForDisplay": 0,
                        "businessLabel": business_label,
                    },
                },
            },
        )
    except Exception as exc:
        return text_result(
            "挂牌均价计算失败，没有显示假数字。",
            {
                "phase": "QUERY_FAILED",
                "secondaryMetric": {
                    "requested": True,
                    "status": "failed",
                    "display": "计算失败",
                    "message": str(exc),
                },
            },
            is_error=True,
        )


HOUSE_FIELD_ALIASES = {
    "房源编号": ("houseNo", "house_no", "房源编号"),
    "小区": ("sectionName", "section", "小区"),
    "区域": ("districtName", "区域"),
    "商圈": ("zoneName", "商圈"),
    "总价或租金": ("price", "总价", "租金"),
    "面积": ("area", "面积"),
    "户型": ("rooms", "houseLayout", "户型"),
    "楼层": ("floor", "楼层"),
    "装修": ("decoration", "装修"),
    "朝向": ("towards", "朝向"),
}


def safe_house_row(row):
    cleaned = {}
    for label, aliases in HOUSE_FIELD_ALIASES.items():
        for key in aliases:
            value = row.get(key)
            if value not in (None, ""):
                cleaned[label] = value
                break
    return cleaned


def metric_details(args):
    if args.get("userAction") not in {"metric_click", "load_more"}:
        return text_result(
            "明细查询必须由用户点击数字或加载更多触发。",
            {"phase": "QUERY_FAILED", "rows": []},
            is_error=True,
        )
    if args.get("metricId") != "currentNewListingCount":
        return text_result(
            "这个月度汇总数字目前没有同一统计方式的逐套明细，不能伪造钻取。",
            {"phase": "DETAIL_READY", "rows": [], "drilldownAvailable": False},
        )
    page = max(1, int(args.get("page") or 1))
    size = min(50, max(1, int(args.get("pageSize") or 20)))
    _, house_biz, _ = business_values(args.get("businessType"))
    query = {"bizType": house_biz, "current": page, "size": size, "isNew": "是"}
    for key in ("districtName", "zoneName", "sectionLike"):
        value = clean_option(args.get(key))
        if value:
            query[key] = value
    try:
        raw = call_upstream_tool("listHouseByCondition", query, timeout=45)
        rows = extract_jsonish(raw)
        rows = rows if isinstance(rows, list) else []
        total = extract_total(raw)
        safe_rows = [safe_house_row(row) for row in rows if isinstance(row, dict)]
        return text_result(
            f"已读取第 {page} 页明细。",
            {
                "phase": "DETAIL_READY",
                "metricId": "currentNewListingCount",
                "page": page,
                "pageSize": size,
                "total": total,
                "rows": safe_rows,
                "hasMore": bool(total is not None and page * size < total),
            },
        )
    except Exception as exc:
        return text_result(
            "明细查询失败，没有显示假数据。",
            {"phase": "QUERY_FAILED", "rows": [], "limitation": str(exc)},
            is_error=True,
        )


def row_text(row, aliases):
    for key in aliases:
        value = clean_option(row.get(key))
        if value:
            return value
    return ""


def location_filter_options(args):
    global LAST_LOCATION_OPTIONS
    if args.get("userAction") != "load_filter_options":
        return text_result(
            "房源位置下拉选项必须在用户打开该查看方式后加载。",
            {"phase": "QUERY_FAILED", "filterOptions": {"locations": []}},
            is_error=True,
        )

    _, house_biz, business_label = business_values(args.get("businessType"))
    if house_biz not in {"sell", "rent"}:
        return text_result(
            "房源位置筛选只支持买卖或租赁房源。",
            {"phase": "QUERY_FAILED", "filterOptions": {"locations": []}},
            is_error=True,
        )
    if LAST_LOCATION_OPTIONS.get("complete") and LAST_LOCATION_OPTIONS.get("businessType") == house_biz:
        return text_result(
            "已返回房源位置下拉选项。",
            {"phase": "FILTER_OPTIONS_READY", "filterOptions": LAST_LOCATION_OPTIONS, "detailRowsFetchedForDisplay": 0},
        )

    page = 1
    page_size = 200
    processed = 0
    total = None
    locations = set()
    try:
        while page <= 50:
            raw = call_upstream_tool(
                "listHouseByCondition",
                {"bizType": house_biz, "current": page, "size": page_size, "isNew": "是"},
                timeout=60,
            )
            rows = extract_jsonish(raw)
            rows = rows if isinstance(rows, list) else []
            if total is None:
                total = extract_total(raw)
            for row in rows:
                if not isinstance(row, dict):
                    continue
                district = row_text(row, ("districtName", "district", "区域"))
                zone = row_text(row, ("zoneName", "zone", "businessArea", "商圈", "板块"))
                section = row_text(row, ("sectionName", "section", "communityName", "小区"))
                if district or zone or section:
                    locations.add((district, zone, section))
            processed += len(rows)
            if not rows or len(rows) < page_size or (total is not None and processed >= total):
                break
            page += 1

        if total is not None and processed < total:
            raise RuntimeError("房源位置选项超过安全读取上限，不能把不完整列表冒充完整下拉框。")
        location_rows = [
            {"district": district, "zone": zone, "section": section}
            for district, zone, section in sorted(locations)
        ]
        LAST_LOCATION_OPTIONS = {
            "locations": location_rows,
            "complete": True,
            "businessType": house_biz,
            "businessLabel": business_label,
        }
        return text_result(
            "房源位置下拉选项已加载。",
            {
                "phase": "FILTER_OPTIONS_READY",
                "filterOptions": LAST_LOCATION_OPTIONS,
                "technical": {"calculationRows": processed, "detailRowsFetchedForDisplay": 0},
            },
        )
    except Exception as exc:
        return text_result(
            "暂时无法完整加载房源位置下拉选项。",
            {
                "phase": "QUERY_FAILED",
                "filterOptions": {"locations": [], "complete": False},
                "limitation": str(exc),
            },
            is_error=True,
        )


def filter_options(args):
    if args.get("filterKind") == "location":
        return location_filter_options(args)
    return text_result(
        "已返回最近一次汇总中的可选部门和人员。",
        {"phase": "SUMMARY_READY", "filterOptions": LAST_FILTER_OPTIONS, "detailRowsFetched": 0},
    )


def handle_call(msg):
    method = msg.get("method")
    params = msg.get("params") or {}
    if method == "initialize":
        result(
            msg,
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}, "resources": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            },
        )
    elif method == "tools/list":
        result(msg, {"tools": tools_list()})
    elif method == "resources/list":
        result(msg, {"resources": [{"uri": WIDGET_URI, "name": "ERP 实时看板", "mimeType": "text/html;profile=mcp-app"}]})
    elif method == "resources/read":
        result(msg, resource_payload()) if params.get("uri") == WIDGET_URI else error(msg, -32004, "resource not found")
    elif method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        if name == "showErpDashboard":
            summary = query_summary(args)
            summary["_meta"] = {"ui": {"resourceUri": WIDGET_URI}}
            result(msg, summary)
        elif name == "queryErpDashboardSummary":
            result(msg, query_summary(args))
        elif name == "getErpDashboardFilterOptions":
            result(msg, filter_options(args))
        elif name == "queryErpDashboardSecondaryMetric":
            result(msg, listing_price_summary(args))
        elif name == "getErpMetricDetails":
            result(msg, metric_details(args))
        else:
            error(msg, -32602, f"unknown tool: {name}")
    elif method == "ping":
        result(msg, {})
    elif method and method.startswith("notifications/"):
        return
    else:
        error(msg, -32601, f"unknown method: {method}")


def main():
    while True:
        msg = read_message()
        if msg is None:
            break
        if "id" not in msg and str(msg.get("method", "")).startswith("notifications/"):
            continue
        try:
            handle_call(msg)
        except Exception as exc:
            error(msg, -32000, str(exc))


if __name__ == "__main__":
    main()
