#!/usr/bin/env python3
import argparse
import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MATRIX = ROOT / "references" / "erp_export_field_matrix.tsv"


def load_rows(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def search(rows, keyword: str):
    keyword = keyword.lower().strip()
    if not keyword:
        return []
    out = []
    for row in rows:
        hay = "\n".join(str(v) for v in row.values()).lower()
        if keyword in hay:
            out.append(row)
    return out


def main():
    ap = argparse.ArgumentParser(description="Search ERP MCP/export field matrix.")
    ap.add_argument("keyword", help="Field or business term to search.")
    ap.add_argument("--matrix", default=str(DEFAULT_MATRIX))
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    rows = search(load_rows(Path(args.matrix)), args.keyword)[: args.limit]
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return
    if not rows:
        print("未找到匹配字段。")
        return
    for i, row in enumerate(rows, 1):
        name = row.get("原始字段名") or row.get("标准字段名") or row.get("字段名称") or row.get("字段") or row.get("field") or ""
        table = row.get("导出表") or row.get("表格名称") or row.get("table") or ""
        sheet = row.get("工作表/模块") or row.get("Sheet") or ""
        support = row.get("MCP支持程度") or row.get("MCP支持情况") or row.get("支持情况") or row.get("support") or ""
        mcp = row.get("MCP工具/类型") or row.get("MCP对应字段/指标") or ""
        note = row.get("推荐处理方式") or row.get("关联键/补充说明") or row.get("说明") or row.get("备注") or row.get("notes") or ""
        print(f"{i}. {table} / {sheet} / {name} / {support}")
        if mcp:
            print(f"   MCP：{mcp}")
        if note:
            print(f"   {note}")


if __name__ == "__main__":
    main()
