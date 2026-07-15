#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "assets" / "requirement_wizard_template.html"

DEFAULT_CONFIG = {
    "goal": "ERP 数据需求",
    "storageKey": "erp_mcp_requirement_selection_v2",
    "base_filters": [
        {"id": "time", "label": "查看时间", "type": "select", "options": ["上月", "本月", "自定义时间"]},
        {"id": "scope", "label": "查看范围", "type": "select", "options": ["全公司"]},
        {"id": "biz", "label": "业务类型", "type": "select", "options": ["全部", "买卖", "租赁", "新房"]}
    ],
    "questions": [
        {
            "id": "date_basis",
            "title": "这个数字按哪个日期统计？",
            "required": True,
            "options": [
                {"value": "contract_date", "label": "按签约日期", "description": "适合看某段时间签了哪些合同。", "support": "系统可以直接查", "recommended": True},
                {"value": "erp_report", "label": "按 ERP 月度统计", "description": "适合先看系统报表里的官方汇总数。", "support": "系统能查，但统计方式需要说明"},
                {"value": "finish_time", "label": "按结单日期", "description": "适合看某段时间完成结单的合同。", "support": "系统能查，但要核对结果"},
                {"value": "create_time", "label": "按录入时间", "description": "适合看房源或客户是什么时候录入的。", "support": "需要补充合同表", "export_required": True, "notes": "通常需要合同信息导出。"}
            ]
        },
        {
            "id": "attribution",
            "title": "开单按谁来算？",
            "required": True,
            "options": [
                {"value": "signer", "label": "按签约人", "description": "合同由谁签约，就记在谁名下。", "support": "系统可以直接查", "recommended": True},
                {"value": "allocation_user", "label": "按业绩分配人", "description": "适合看实际业绩归属，一份合同可能分给多人。", "support": "系统可以直接查"},
                {"value": "house_user", "label": "按房源方经纪人", "description": "开单记在负责房源的一方。", "support": "系统可以直接查"},
                {"value": "cust_user", "label": "按客源方经纪人", "description": "开单记在负责客户的一方。", "support": "系统可以直接查"}
            ]
        },
        {
            "id": "denominator",
            "title": "人员总数按谁来算？",
            "required": True,
            "options": [
                {"value": "personnel_export_active", "label": "统计期结束时仍在职", "description": "适合正式计算人均和开单率。", "support": "需要补充人员表", "export_required": True, "recommended": True, "notes": "需要人员信息导出。"},
                {"value": "personnel_export_period", "label": "这段时间内曾经在职", "description": "月中入职或离职的人也会计入。", "support": "需要补充人员表", "export_required": True, "notes": "需要人员信息导出。"},
                {"value": "mcp_visible", "label": "先按系统能看到的人快速预览", "description": "速度快，但不能叫公司全员。没有业务记录的人可能看不到。", "support": "可以先预览"}
            ]
        }
    ],
    "info_cards": [
        {
            "title": "房源类数据的说明",
            "body": "上月新增房源的总套数可以按月份统计；但系统目前不能拉出一份“上月新录入房源的完整名单”。当前房源列表里的“新上”只是房源现在仍处于新上状态，所以用这些房源计算出来的均价只能作为当前新上房源的参考。系统没有房源表导出功能，因此不会建议你导出房源表。"
        }
    ]
}


def prune_questions(config):
    kept = []
    for q in config.get("questions", []):
        options = q.get("options", [])
        feasible = [o for o in options if "系统目前做不到" not in o.get("support", "")]
        if len(feasible) <= 1:
            card = {"title": q.get("title", "系统当前只能这样处理"), "body": (feasible[0].get("description") if feasible else "系统当前没有可用方案。")}
            config.setdefault("info_cards", []).append(card)
        else:
            kept.append(q)
    config["questions"] = kept
    return config


def main():
    ap = argparse.ArgumentParser(description="Render Apple-style ERP requirement wizard in plain Chinese.")
    ap.add_argument("--config")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    config = DEFAULT_CONFIG
    if args.config:
        config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    config = prune_questions(config)
    html = TEMPLATE.read_text(encoding="utf-8").replace("@@WIZARD_JSON@@", json.dumps(config, ensure_ascii=False))
    Path(args.out).write_text(html, encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
