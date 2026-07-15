#!/usr/bin/env python3
"""Local MCP Apps proxy for ERP dashboard shells.

The repository does not contain the remote ERP MCP server source. This local
server gives WorkBuddy a real MCP Apps Widget entry point and defers all data
reads until the user clicks the Widget query button. It never exposes ERP
tokens to browser JavaScript.
"""

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import date, timedelta

WIDGET_URI = "ui://erp/dashboard"
SERVER_NAME = "erp-dashboard-proxy"
SERVER_VERSION = "2.2.7"


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


def tool(name, description, schema, attach_widget=False):
    data = {
        "name": name,
        "description": description,
        "inputSchema": schema,
    }
    if attach_widget:
        data["_meta"] = {"ui": {"resourceUri": WIDGET_URI}}
    return data


def tools_list():
    obj = {"type": "object", "additionalProperties": True, "properties": {}}
    return [
        tool(
            "showErpDashboard",
            "打开 ERP 实时查询 Widget 壳。只展示筛选项和确认按钮，不预取 ERP 数据。",
            obj,
            attach_widget=True,
        ),
        tool(
            "queryErpDashboardData",
            "在用户点击 Widget 查询按钮后，按当前条件读取 ERP 数据并返回结构化结果。",
            obj,
        ),
        tool(
            "getErpMetricDetails",
            "在用户点击数字后读取同口径明细。未配置上游 ERP 或缺少明细工具时返回限制说明。",
            obj,
        ),
    ]


def widget_html():
    # Keep the Widget self-contained and token-free. The browser calls this MCP
    # server through the WorkBuddy host bridge; credentials stay in this process.
    return """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ERP 实时查询</title>
  <style>
    :root{color-scheme:light dark;--blue:#007aff;--bg:#f5f5f7;--card:rgba(255,255,255,.86);--text:#1d1d1f;--muted:#6e6e73;--line:rgba(0,0,0,.08)}
    @media(prefers-color-scheme:dark){:root{--bg:#101012;--card:rgba(35,35,39,.86);--text:#f5f5f7;--muted:#a1a1a6;--line:rgba(255,255,255,.12)}}
    *{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
    main{max-width:1100px;margin:auto;padding:28px} h1{font-size:28px;margin:0 0 8px;letter-spacing:0} p{margin:0;color:var(--muted);line-height:1.65}
    .grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:18px 0}.metrics{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
    .card{border:1px solid var(--line);background:var(--card);border-radius:18px;padding:16px;box-shadow:0 14px 40px rgba(0,0,0,.08);backdrop-filter:blur(18px)}
    label{display:block;color:var(--muted);font-size:12px;margin-bottom:8px} select,input{width:100%;height:38px;border:1px solid var(--line);border-radius:10px;background:transparent;color:var(--text);padding:0 10px}
    .value{margin-top:10px;color:var(--blue);font-size:24px;font-weight:750}.actions{display:flex;gap:10px;margin-top:18px;flex-wrap:wrap}button{height:44px;border:0;border-radius:12px;background:var(--blue);color:white;padding:0 18px;font-weight:650;cursor:pointer}.secondary{background:transparent;color:var(--blue);border:1px solid rgba(0,122,255,.35)}
    #status{margin-top:12px;color:var(--muted);min-height:24px}.detail{margin-top:14px;max-height:260px;overflow:auto;white-space:pre-wrap}
    @media(max-width:820px){main{padding:18px}.grid,.metrics{grid-template-columns:1fr}}
  </style>
</head>
<body>
<main>
  <section>
    <h1>ERP 实时查询入口</h1>
    <p>这个页面先让你确认条件。点击“开始查询”后，WorkBuddy 才会通过 MCP 读取 ERP 数据。</p>
  </section>
  <section class="grid">
    <div class="card"><label>统计月份</label><select id="month"><option>上月</option><option>本月</option></select></div>
    <div class="card"><label>查看范围</label><select id="scope"><option>先选择部门或门店</option><option>全公司</option></select></div>
    <div class="card"><label>业务类型</label><select id="businessType"><option>买卖房源</option><option>租赁房源</option><option>买卖和租赁都看</option></select></div>
    <div class="card"><label>挂牌均价</label><select id="priceMethod"><option>两种都展示（同时给出两套算法结果，方便对比）</option><option>每套房等权均价（每套房都算 1 套）</option><option>按面积计算整体均价（大面积房源影响更大）</option></select></div>
  </section>
  <section class="metrics">
    <div class="card"><label>新上房源数量</label><div class="value" id="count">确认后查询</div></div>
    <div class="card"><label>当前新上房源参考均价</label><div class="value" id="price">确认后查询</div></div>
    <div class="card"><label>明细</label><div class="value" id="detailCount">确认后查询</div></div>
  </section>
  <section class="card" style="margin-top:12px"><p>新上房源数量按你选择的月份统计。挂牌均价根据现在仍被系统标记为“新上”的房源计算，所以这两个数字不一定来自同一批房源。系统支持的导出表里没有房源表，因此不会建议导出房源表。</p></section>
  <div class="actions"><button id="run">开始查询</button><button class="secondary" id="copy">复制条件</button></div>
  <div id="status">等待你点击开始查询。</div>
  <div class="card detail" id="details">当前没有读取任何 ERP 业务数据。</div>
</main>
<script>
function filters(){return{month:month.value,scope:scope.value,businessType:businessType.value,priceMethod:priceMethod.value,scenario:"house_new_listing_price"}}
function appHost(){return window.app||window.openai}
function show(data){
  const m=(data&&data.metrics)||{};
  count.textContent=m.newListingCount?.display||"暂无可验证数据";
  price.textContent=m.referencePrice?.display||"暂无可验证数据";
  detailCount.textContent=m.detailRows?.display||"暂无可验证数据";
  details.textContent=data?.message||data?.limitation||"查询已返回，但没有可展示的明细。";
}
run.onclick=async()=>{
  const host=appHost();
  if(!host||typeof host.callServerTool!=="function"){status.textContent="当前没有检测到 WorkBuddy 实时查询桥。";return}
  status.textContent="正在读取 ERP 数据...";
  try{const res=await host.callServerTool({name:"queryErpDashboardData",arguments:filters()});show(res.structuredContent||res);status.textContent="查询完成。"}
  catch(e){status.textContent="查询失败："+(e&&e.message?e.message:String(e));details.textContent="没有显示假数字。请检查 ERP 连接、权限或后台聚合工具。"}
};
copy.onclick=async()=>{const text=JSON.stringify(filters(),null,2);try{await navigator.clipboard.writeText(text);status.textContent="已复制当前条件。"}catch{details.textContent=text;status.textContent="请手动复制明细区内容。"}};
</script>
</body>
</html>"""


def resource_payload():
    return {
        "contents": [
            {
                "uri": WIDGET_URI,
                "mimeType": "text/html;profile=mcp-app",
                "text": widget_html(),
            }
        ]
    }


def text_result(text, structured=None, attach_widget=False):
    data = {"content": [{"type": "text", "text": text}], "structuredContent": structured or {}}
    if attach_widget:
        data["_meta"] = {"ui": {"resourceUri": WIDGET_URI}}
    return data


def parse_month(label):
    today = date.today()
    first_this_month = today.replace(day=1)
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
    return os.environ.get("ERP_MCP_URL", "").strip()


def upstream_token():
    token = os.environ.get("ERP_MCP_TOKEN", "").strip()
    if token.startswith("Bearer "):
        token = token[7:].strip()
    return token


def call_upstream_tool(name, arguments):
    url = upstream_url()
    token = upstream_token()
    if not url or not token:
        raise RuntimeError("插件还没有配置 ERP MCP 地址或 Token。")
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    }
    raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=raw,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "Authorization": f"Bearer {token}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            text = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"远程 ERP MCP 返回 {exc.code}: {detail[:500]}")
    except Exception as exc:
        raise RuntimeError(f"无法连接远程 ERP MCP: {exc}")
    if text.startswith("data:"):
        parts = [line[5:].strip() for line in text.splitlines() if line.startswith("data:")]
        text = parts[-1] if parts else text
    data = json.loads(text)
    if "error" in data:
        raise RuntimeError(str(data["error"]))
    return data.get("result", data)


def extract_jsonish(value):
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in ("structuredContent", "data", "result", "items", "rows"):
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


def display_money(value):
    if value is None:
        return "暂无可验证数据"
    return f"{value:,.0f} 元/㎡"


def query_dashboard(args):
    start, end, month_label = parse_month(args.get("month", "上月"))
    biz_ui = args.get("businessType", "买卖房源")
    if "租赁" in biz_ui:
        rpt_biz = "租房"
        house_biz = "rent"
    else:
        rpt_biz = "买卖"
        house_biz = "sell"

    structured = {
        "phase": "QUERY_RUNNING",
        "filters": {**args, "startDate": start, "endDate": end, "monthLabel": month_label},
        "metrics": {
            "newListingCount": {"display": "暂无可验证数据"},
            "referencePrice": {"display": "暂无可验证数据"},
            "detailRows": {"display": "暂无可验证数据"},
        },
        "message": "",
        "limitation": "",
    }
    try:
        rpt = call_upstream_tool(
            "queryRptData",
            {"query": {"bizType": rpt_biz, "startDate": start, "endDate": end, "indexName": "新增房源·套"}},
        )
        rpt_rows = extract_jsonish(rpt) or []
        values = [to_number(row.get("indexValue")) for row in rpt_rows if isinstance(row, dict)]
        values = [v for v in values if v is not None]
        if values:
            structured["metrics"]["newListingCount"] = {"value": sum(values), "display": f"{sum(values):,.0f} 套"}
    except Exception as exc:
        structured["limitation"] = f"月度新增房源数量暂时没有查到：{exc}"

    try:
        houses = call_upstream_tool("listHouseByCondition", {"bizType": house_biz, "current": 1, "size": 100, "isNew": "是"})
        rows = extract_jsonish(houses) or []
        if isinstance(rows, dict):
            rows = rows.get("records") or rows.get("list") or rows.get("items") or []
        prices = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            for key in ("unitPrice", "unit_price", "挂牌单价", "单价"):
                n = to_number(row.get(key))
                if n is not None:
                    prices.append(n)
                    break
        if prices:
            avg = sum(prices) / len(prices)
            structured["metrics"]["referencePrice"] = {"value": avg, "display": display_money(avg)}
        structured["metrics"]["detailRows"] = {"value": len(rows), "display": f"{len(rows)} 条"}
        structured["message"] = "查询已完成。新上房源数量按所选月份统计，挂牌均价按当前仍标记为新上的房源计算。"
    except Exception as exc:
        msg = f"当前新上房源参考均价暂时没有查到：{exc}"
        structured["limitation"] = (structured.get("limitation") + "\n" + msg).strip()
        structured["message"] = "没有显示假数字。远程 ERP MCP 可能需要补充稳定的聚合工具 queryErpDashboardData。"

    structured["phase"] = "QUERY_COMPLETE" if structured["message"] else "QUERY_FAILED"
    return text_result(structured.get("message") or structured.get("limitation"), structured)


def metric_details(args):
    structured = {
        "phase": "QUERY_FAILED",
        "metricId": args.get("metricId", ""),
        "message": "当前代理没有稳定的同口径明细工具，不能伪造明细。请让 ERP MCP 后台提供 getErpMetricDetails 或对应明细查询。",
        "rows": [],
    }
    return text_result(structured["message"], structured)


def handle_call(msg):
    method = msg.get("method")
    params = msg.get("params") or {}
    if method == "initialize":
        result(
            msg,
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}, "resources": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            },
        )
    elif method == "tools/list":
        result(msg, {"tools": tools_list()})
    elif method == "resources/list":
        result(msg, {"resources": [{"uri": WIDGET_URI, "name": "ERP 实时查询 Widget", "mimeType": "text/html;profile=mcp-app"}]})
    elif method == "resources/read":
        if params.get("uri") != WIDGET_URI:
            error(msg, -32004, "resource not found")
        else:
            result(msg, resource_payload())
    elif method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        if name == "showErpDashboard":
            result(msg, text_result("已准备好 ERP 实时查询入口。", {"phase": "PREVIEW_SHOWN"}, attach_widget=True))
        elif name == "queryErpDashboardData":
            result(msg, query_dashboard(args))
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
