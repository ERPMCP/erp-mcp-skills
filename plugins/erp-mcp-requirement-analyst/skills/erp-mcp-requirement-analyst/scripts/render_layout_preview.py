#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


DEFAULT_PREVIEW = {
    "title": "ERP 数据看板排版预览",
    "goal": "确认页面结构后再开始完整查询",
    "filters": ["统计月份", "查看范围", "业务类型"],
    "metrics": ["新上房源数量", "挂牌均价（当前挂牌单价的平均值）"],
    "detail_sections": ["指标说明", "明细（组成这个数字的具体记录）", "导出本次结果", "数据来源与技术说明"],
    "notes": [
        "这是排版预览，不包含真实业务数据。",
        "确认后再调用 ERP 查询正式数据，并生成可点击的最终页面。",
    ],
}


def _items(values):
    return "\n".join(f"<li>{escape(str(v))}</li>" for v in values)


def escape(text):
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render(config):
    title = escape(config.get("title") or DEFAULT_PREVIEW["title"])
    goal = escape(config.get("goal") or DEFAULT_PREVIEW["goal"])
    filters = config.get("filters") or DEFAULT_PREVIEW["filters"]
    metrics = config.get("metrics") or DEFAULT_PREVIEW["metrics"]
    sections = config.get("detail_sections") or DEFAULT_PREVIEW["detail_sections"]
    notes = config.get("notes") or DEFAULT_PREVIEW["notes"]
    metric_cards = "\n".join(
        f"""
        <article class="metric">
          <span>{escape(str(label))}</span>
          <strong>等待查询</strong>
          <p>客户确认排版后再写入真实数据。</p>
        </article>
        """
        for label in metrics
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    :root {{ color-scheme: light; --blue:#1677ff; --text:#111827; --muted:#667085; --bg:#f5f7fb; --card:#fff; }}
    * {{ box-sizing: border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--text); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",sans-serif; }}
    main {{ max-width:1120px; margin:0 auto; padding:32px 20px 48px; }}
    header {{ display:flex; justify-content:space-between; gap:20px; align-items:flex-end; margin-bottom:22px; }}
    h1 {{ margin:0; font-size:30px; letter-spacing:0; }}
    p {{ color:var(--muted); line-height:1.7; }}
    .badge {{ display:inline-flex; align-items:center; border-radius:999px; padding:8px 12px; color:var(--blue); background:#eaf2ff; font-weight:700; }}
    .grid {{ display:grid; grid-template-columns: 1.1fr .9fr; gap:18px; }}
    .card, .metric {{ background:var(--card); border:1px solid #e6eaf0; border-radius:18px; box-shadow:0 18px 40px rgba(15,23,42,.06); }}
    .card {{ padding:22px; }}
    .metrics {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); gap:14px; }}
    .metric {{ padding:20px; min-height:150px; }}
    .metric span {{ color:var(--muted); font-weight:700; }}
    .metric strong {{ display:block; margin:14px 0 8px; font-size:32px; }}
    ul {{ margin:12px 0 0; padding-left:22px; line-height:1.8; }}
    .actions {{ display:flex; flex-wrap:wrap; gap:12px; margin-top:18px; }}
    button {{ border:0; border-radius:12px; padding:12px 16px; font-weight:800; cursor:pointer; }}
    .primary {{ background:var(--blue); color:white; }}
    .secondary {{ background:#eef2f7; color:#273142; }}
    .notice {{ margin-top:18px; padding:14px 16px; border-radius:14px; background:#fff8e6; color:#7a4d00; }}
    @media (max-width:760px) {{ .grid, header {{ display:block; }} h1 {{ font-size:24px; }} }}
  </style>
</head>
<body>
<main>
  <header>
    <div>
      <span class="badge">排版预览</span>
      <h1>{title}</h1>
      <p>{goal}</p>
    </div>
  </header>
  <section class="grid">
    <div class="card">
      <h2>顶部筛选区</h2>
      <p>正式页面会把这些条件放在页面顶部，方便客户查看当前统计范围。</p>
      <ul>{_items(filters)}</ul>
      <div class="notice">本页不含真实数据，不会把缺失值显示成 0。</div>
    </div>
    <div class="card">
      <h2>说明区</h2>
      <ul>{_items(notes)}</ul>
    </div>
  </section>
  <section class="card" style="margin-top:18px">
    <h2>核心指标区</h2>
    <div class="metrics">{metric_cards}</div>
  </section>
  <section class="card" style="margin-top:18px">
      <h2>下方明细区</h2>
      <ul>{_items(sections)}</ul>
      <p>正式页面会根据客户选择决定是否显示导出按钮。导出只包含本次已经查询并校验过的数据。</p>
      <div class="actions">
      <button class="primary" onclick="copyDecision('确认排版，继续查询正式数据')">确认排版，继续查询</button>
      <button class="secondary" onclick="copyDecision('需要调整排版后再查询')">需要调整排版</button>
    </div>
  </section>
</main>
<script>
function copyDecision(text) {{
  const msg = "页面排版预览选择：" + text;
  navigator.clipboard?.writeText(msg).then(() => alert("已复制选择结果，请回到对话粘贴。")).catch(() => alert(msg));
}}
</script>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser(description="Render a lightweight layout preview before long ERP queries.")
    ap.add_argument("--config")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    config = DEFAULT_PREVIEW
    if args.config:
        config = json.loads(Path(args.config).read_text(encoding="utf-8-sig"))
    Path(args.out).write_text(render(config), encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
