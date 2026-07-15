#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WHITELIST = ROOT / "references" / "export_whitelist.json"

RULES = [
    {
        "terms": ["在职", "人员", "人均", "开单率", "岗位", "职能", "分母", "零开单", "组织", "层级"],
        "export": "人员信息导出",
        "sheet": "汇总、人员列表",
        "fields": ["运营", "大区", "片区", "门店", "分组", "职能", "姓名", "工号", "在职/离职或冻结状态", "入职时间"],
        "reason": "系统目前不能直接取得完整人员名单和在职人数，需要用人员信息表补充分母。",
    },
    {
        "terms": ["签约门店", "签约小组", "房源方", "客源方", "结单日期", "录入时间", "合同明细", "交易性质", "押金", "抵押"],
        "export": "合同信息导出",
        "sheet": "合同信息",
        "fields": ["合同类型", "合同编号", "签约日期", "结单日期", "录入时间", "签约门店", "签约小组", "房源方/客源方组织字段"],
        "reason": "合同信息表可以补充更细的合同日期和组织归属。",
    },
    {
        "terms": ["已实收业绩", "业绩小组", "业绩门店", "分配比例", "分配业绩", "业绩归属"],
        "export": "业绩明细导出",
        "sheet": "业绩分配",
        "fields": ["合同类型", "合同编号", "签约日期", "分配人", "业绩门店", "业绩小组", "分配比例", "分配业绩", "已实收佣金", "已实收业绩"],
        "reason": "这类字段通常需要业绩分配表补充。",
    },
    {
        "terms": ["付款", "退款", "付款方式", "付款人"],
        "export": "付款明细导出",
        "sheet": "默认工作表",
        "fields": ["合同类型", "合同编号", "签约时间", "类型", "项目", "状态", "金额", "付款方式", "付款人", "付款日期"],
        "reason": "付款明细表适合复核付款和退款记录。",
    },
    {
        "terms": ["实收", "票据", "佣金来源", "支付日期", "收款"],
        "export": "实收明细导出",
        "sheet": "默认工作表",
        "fields": ["合同类型", "合同编号", "签约时间", "项目", "状态", "签约门店", "签约小组", "签约人", "佣金来源", "支付金额", "支付日期", "票据号码"],
        "reason": "实收明细表适合复核收款、来源和票据。",
    },
]

FORBIDDEN_TERMS = ["房源表", "房源导出", "房源明细", "新上房源导出", "在售房源导出", "在租房源导出", "房源历史表"]
HOUSE_TERMS = ["新上房源", "挂牌均价", "挂牌均单价", "房源录入", "房源新上日期", "房源名单"]


def load_whitelist():
    data = json.loads(WHITELIST.read_text(encoding="utf-8"))
    return {x["table"]: set(x.get("sheets", [])) for x in data.get("allowed", [])}, data.get("forbidden_recommendations", [])


def validate_allowed(recommendations):
    allowed, forbidden = load_whitelist()
    errors = []
    for rec in recommendations:
        text = json.dumps(rec, ensure_ascii=False)
        if any(term in text for term in forbidden + FORBIDDEN_TERMS):
            errors.append(f"禁止建议导出房源类表格：{text}")
        if rec["export"] not in allowed:
            errors.append(f"导出表不在白名单：{rec['export']}")
    if errors:
        raise ValueError("\n".join(errors))


def recommend(text):
    if any(t in text for t in HOUSE_TERMS):
        return [{
            "export": "不建议导出表格",
            "sheet": "无",
            "fields": [],
            "reason": "系统支持的导出表里没有房源表。可以先查月度新增房源数量，再用当前房源列表计算当前新上房源的参考均价；如果必须要严格的历史新上明细，建议产品新增房源新上日期或历史明细接口。",
            "no_export": True,
        }]
    hits = []
    for rule in RULES:
        if any(t in text for t in rule["terms"]):
            hits.append(rule)
    validate_allowed([h for h in hits if not h.get("no_export")])
    return hits


def main():
    ap = argparse.ArgumentParser(description="Recommend minimum allowed ERP exports. Never recommends house exports.")
    ap.add_argument("request")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    hits = recommend(args.request)
    if args.json:
        print(json.dumps(hits, ensure_ascii=False, indent=2))
        return
    if not hits:
        print("没有命中固定导出规则。请查询字段矩阵；只能推荐白名单内表格，不能推荐房源表。")
        return
    for item in hits:
        if item.get("no_export"):
            print(item["reason"])
            continue
        print(f"需要补充：{item['export']} / {item['sheet']}")
        print(f"建议字段：{'、'.join(item['fields'])}")
        print(f"原因：{item['reason']}\n")


if __name__ == "__main__":
    main()
