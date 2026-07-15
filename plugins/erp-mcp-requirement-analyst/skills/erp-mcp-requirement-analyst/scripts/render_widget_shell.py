#!/usr/bin/env python3
import argparse
import html
import json
from pathlib import Path


def load_config(path):
    if not path:
        return {}
    return json.loads(Path(path).read_text(encoding="utf-8"))


def default_filters(config):
    questions = {q.get("id"): q for q in config.get("questions", [])}
    return {
        "scenario": "house_new_listing_price",
        "month": "上月",
        "scope": "先选择部门或门店" if "scope_mode" in questions else "全公司",
        "businessType": "买卖房源",
        "priceMethod": "两种都展示（同时给出两套算法结果，方便对比）",
    }


def render(config, mode, state_id):
    filters = default_filters(config)
    payload = json.dumps({"filters": filters, "stateId": state_id, "mode": mode}, ensure_ascii=False).replace("</", "<\\/")
    realtime = mode == "widget"
    action_label = "开始查询" if realtime else "复制条件，回到对话继续查询"
    bridge_note = (
        "这是 WorkBuddy 实时看板入口。点击开始查询后，页面会通过 WorkBuddy 安全调用 MCP 工具读取 ERP。"
        if realtime
        else "这是普通 HTML 预览页，不能自己连接 ERP。点击按钮会复制查询条件，请回到对话继续查询。"
    )
    script = WIDGET_SCRIPT if realtime else STATIC_SCRIPT
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ERP 查询预览</title>
  <style>
    :root {{ color-scheme: light dark; --blue:#007aff; --bg:#f5f5f7; --card:rgba(255,255,255,.82); --text:#1d1d1f; --muted:#6e6e73; --line:rgba(0,0,0,.08); }}
    @media (prefers-color-scheme: dark) {{ :root {{ --bg:#101012; --card:rgba(34,34,38,.82); --text:#f5f5f7; --muted:#a1a1a6; --line:rgba(255,255,255,.12); }} }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:var(--bg); color:var(--text); }}
    main {{ max-width:1120px; margin:0 auto; padding:28px; }}
    .hero {{ display:flex; justify-content:space-between; gap:20px; align-items:flex-start; margin-bottom:20px; }}
    h1 {{ margin:0 0 8px; font-size:28px; line-height:1.2; letter-spacing:0; }}
    p {{ margin:0; color:var(--muted); line-height:1.65; }}
    .pill {{ display:inline-flex; align-items:center; gap:8px; padding:8px 12px; border:1px solid var(--line); border-radius:999px; color:var(--muted); background:var(--card); white-space:nowrap; }}
    .grid {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; margin:18px 0; }}
    .card {{ border:1px solid var(--line); background:var(--card); backdrop-filter:blur(18px); border-radius:18px; padding:16px; box-shadow:0 14px 40px rgba(0,0,0,.08); }}
    label {{ display:block; font-size:12px; color:var(--muted); margin-bottom:8px; }}
    select,input {{ width:100%; height:38px; border-radius:10px; border:1px solid var(--line); background:transparent; color:var(--text); padding:0 10px; font:inherit; }}
    .metrics {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; }}
    .metric strong {{ display:block; font-size:13px; color:var(--muted); font-weight:500; }}
    .metric .value {{ margin-top:10px; font-size:24px; font-weight:700; color:var(--blue); }}
    .notice {{ margin:14px 0; border-left:4px solid var(--blue); }}
    button {{ height:44px; border:0; border-radius:12px; padding:0 18px; background:var(--blue); color:white; font-weight:650; cursor:pointer; }}
    button.secondary {{ background:transparent; color:var(--blue); border:1px solid rgba(0,122,255,.35); }}
    .actions {{ display:flex; gap:10px; flex-wrap:wrap; align-items:center; margin-top:18px; }}
    .status {{ min-height:24px; color:var(--muted); margin-top:12px; }}
    .details {{ margin-top:14px; max-height:260px; overflow:auto; border:1px solid var(--line); border-radius:12px; padding:12px; color:var(--muted); }}
    @media (max-width:820px) {{ main {{ padding:18px; }} .hero {{ display:block; }} .grid,.metrics {{ grid-template-columns:1fr; }} .pill {{ margin-top:12px; }} }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <div>
        <h1>ERP 查询预览</h1>
        <p>请先确认页面和查询条件。下面还没有读取 ERP 数据，所有数字都会在你点击按钮后再查询。</p>
      </div>
      <div class="pill">当前状态：确认后查询</div>
    </section>
    <section class="card notice">
      <p>{html.escape(bridge_note)}</p>
    </section>
    <section class="grid">
      <div class="card"><label>统计月份</label><select id="month"><option>上月</option><option>本月</option><option>自定义月份</option></select></div>
      <div class="card"><label>查看范围</label><select id="scope"><option>先选择部门或门店</option><option>全公司</option></select></div>
      <div class="card"><label>业务类型</label><select id="businessType"><option>买卖房源</option><option>租赁房源</option><option>买卖和租赁都看</option></select></div>
      <div class="card"><label>挂牌均价</label><select id="priceMethod"><option>两种都展示（同时给出两套算法结果，方便对比）</option><option>每套房等权均价（每套房都算 1 套）</option><option>按面积计算整体均价（大面积房源影响更大）</option></select></div>
    </section>
    <section class="metrics">
      <div class="card metric"><strong>新上房源数量</strong><div class="value" id="metric-count">确认后查询</div></div>
      <div class="card metric"><strong>当前新上房源参考均价</strong><div class="value" id="metric-price">确认后查询</div></div>
      <div class="card metric"><strong>可查看明细</strong><div class="value" id="metric-detail">确认后查询</div></div>
    </section>
    <section class="card notice">
      <p>新上房源数量按你选择的月份统计。挂牌均价根据现在仍被系统标记为“新上”的房源计算，所以这两个数字不一定来自同一批房源。系统支持的导出表里没有房源表，因此不会建议你导出房源表。</p>
    </section>
    <div class="actions">
      <button id="start">{html.escape(action_label)}</button>
      <button class="secondary" id="copy">复制当前条件</button>
    </div>
    <div class="status" id="status">等待你确认后再读取 ERP 数据。</div>
    <div class="details" id="details">明细区会在查询完成后显示。当前没有读取任何 ERP 业务数据。</div>
  </main>
  <script id="widget-shell-data" type="application/json">{payload}</script>
  <script>{script}</script>
</body>
</html>
"""


WIDGET_SCRIPT = r"""
const shell = JSON.parse(document.getElementById('widget-shell-data').textContent);
function filters(){
  return {
    scenario: shell.filters.scenario,
    month: document.getElementById('month').value,
    scope: document.getElementById('scope').value,
    businessType: document.getElementById('businessType').value,
    priceMethod: document.getElementById('priceMethod').value,
    stateId: shell.stateId
  };
}
function setStatus(text){ document.getElementById('status').textContent = text; }
function renderResult(result){
  const data = result && (result.structuredContent || result);
  const metrics = data.metrics || {};
  document.getElementById('metric-count').textContent = metrics.newListingCount?.display ?? '暂无可验证数据';
  document.getElementById('metric-price').textContent = metrics.referencePrice?.display ?? '暂无可验证数据';
  document.getElementById('metric-detail').textContent = metrics.detailRows?.display ?? '暂无可验证数据';
  document.getElementById('details').textContent = data.message || data.limitation || '查询已返回，但没有可展示的明细。';
}
async function startQuery(){
  const host = window.app || window.openai;
  if (!host || typeof host.callServerTool !== 'function') {
    setStatus('当前页面没有检测到 WorkBuddy 实时查询桥，请回到对话继续查询。');
    return;
  }
  setStatus('正在读取 ERP 数据...');
  try {
    const result = await host.callServerTool({ name: 'queryErpDashboardData', arguments: filters() });
    renderResult(result);
    setStatus('查询完成。');
  } catch (err) {
    setStatus('查询失败：' + (err && err.message ? err.message : String(err)));
    document.getElementById('details').textContent = '没有显示假数字。请检查 ERP 连接、权限或后台聚合工具。';
  }
}
async function copyFilters(){
  const text = JSON.stringify(filters(), null, 2);
  try { await navigator.clipboard.writeText(text); setStatus('已复制当前查询条件。'); }
  catch { document.getElementById('details').textContent = text; setStatus('浏览器不允许自动复制，请手动复制明细区内容。'); }
}
document.getElementById('start').addEventListener('click', startQuery);
document.getElementById('copy').addEventListener('click', copyFilters);
"""


STATIC_SCRIPT = r"""
const shell = JSON.parse(document.getElementById('widget-shell-data').textContent);
function filters(){
  return {
    scenario: shell.filters.scenario,
    month: document.getElementById('month').value,
    scope: document.getElementById('scope').value,
    businessType: document.getElementById('businessType').value,
    priceMethod: document.getElementById('priceMethod').value,
    stateId: shell.stateId
  };
}
function setStatus(text){ document.getElementById('status').textContent = text; }
async function copyFilters(){
  const text = '开始查询：' + JSON.stringify(filters(), null, 2);
  try { await navigator.clipboard.writeText(text); setStatus('已复制查询条件，请回到对话粘贴后继续。'); }
  catch { document.getElementById('details').textContent = text; setStatus('浏览器不允许自动复制，请手动复制明细区内容。'); }
}
document.getElementById('start').addEventListener('click', copyFilters);
document.getElementById('copy').addEventListener('click', copyFilters);
"""


def main():
    ap = argparse.ArgumentParser(description="Render a preview-first ERP MCP Apps Widget shell.")
    ap.add_argument("--config")
    ap.add_argument("--out", required=True)
    ap.add_argument("--mode", choices=["widget", "static"], default="widget")
    ap.add_argument("--state-id", default="")
    args = ap.parse_args()
    config = load_config(args.config)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(render(config, args.mode, args.state_id), encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
