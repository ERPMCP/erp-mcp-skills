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
        {"id": "time", "label": "统计月份", "type": "select", "options": ["上月", "本月", "自定义月份"]},
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
                {"value": "erp_report", "label": "按系统报表统计", "description": "适合先看系统报表里的汇总数。", "support": "系统能查，但统计方式需要说明"},
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
            "title": "本次数据如何统计",
            "body": "新上房源数量按你选择的月份统计。挂牌均价根据现在仍被系统标记为“新上”的房源计算，所以它是当前参考价，不一定完全等于所选月份新录入房源的均价。系统支持的导出表里没有房源表，因此不会建议你导出房源表。",
            "technical": "数量通常来自系统月度新增房源统计；均价通常来自当前房源列表中新上房源的挂牌单价。两者不一定对应同一批房源。"
        }
    ]
}


BAD_TIME_WORDS = ("时间口径", "日期口径")
BAD_TIME_OPTION_PARTS = ("数量=上月", "均价=本月", "queryRptData", "isNew", "unitPrice")


def normalize_customer_language(config):
    """Remove internal jargon from the visible questionnaire."""
    normalized_filters = []
    for f in config.get("base_filters", []):
        label = f.get("label", "")
        options = f.get("options", [])
        joined = " ".join(str(x) for x in options)
        is_bad_time_filter = label in BAD_TIME_WORDS or any(part in joined for part in BAD_TIME_OPTION_PARTS)
        if is_bad_time_filter:
            config.setdefault("info_cards", []).append({
                "title": "本次数据如何统计",
                "body": "新上房源数量按你选择的月份统计。挂牌均价根据现在仍被系统标记为“新上”的房源计算，所以它是当前参考价，不一定完全等于所选月份新录入房源的均价。",
                "technical": "原页面里的“数量=上月；均价=本月”属于内部说明，不应该作为客户选择项展示。"
            })
            continue
        if label in ("查看时间", "查询时间"):
            f["label"] = "统计月份"
        f["options"] = [str(o).replace("自定义时间", "自定义月份") for o in options]
        normalized_filters.append(f)
    config["base_filters"] = normalized_filters

    for q in config.get("questions", []):
        if q.get("title") in BAD_TIME_WORDS:
            q["title"] = "这个数字按哪个日期统计？"
        for opt in q.get("options", []):
            for part in BAD_TIME_OPTION_PARTS:
                if part in opt.get("label", ""):
                    opt["label"] = "按系统当前可查询的方式统计"
                    opt["description"] = "系统当前只有这一种可行统计方式，具体说明会显示在说明卡里。"
    return config


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
        config = json.loads(Path(args.config).read_text(encoding="utf-8-sig"))
    config = normalize_customer_language(config)
    config = prune_questions(config)
    html = TEMPLATE.read_text(encoding="utf-8").replace("@@WIZARD_JSON@@", json.dumps(config, ensure_ascii=False))
    Path(args.out).write_text(html, encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
