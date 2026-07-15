#!/usr/bin/env python3
"""Route common ERP requests to a tiny local first-round template.

This script deliberately reads only fast_scenario_router.json and the matched
scenario template. It never reads the full capability guide and never calls MCP.
"""

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFERENCES = ROOT / "references"
ROUTER_PATH = REFERENCES / "fast_scenario_router.json"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def matches(query: str, scenario: dict) -> bool:
    text = query.lower().strip()
    groups = scenario.get("required_keyword_groups", [])
    if groups:
        return all(any(word.lower() in text for word in group) for group in groups)
    return any(word.lower() in text for word in scenario.get("keywords_any", []))


def route(query: str) -> dict:
    router = load_json(ROUTER_PATH)
    for scenario in router.get("scenarios", []):
        if not matches(query, scenario):
            continue
        template_path = REFERENCES / scenario["template"]
        template = load_json(template_path)
        return {
            "matched": True,
            "scenario_id": scenario["id"],
            "read_files": [
                "references/fast_scenario_router.json",
                f"references/{scenario['template']}"
            ],
            "template_path": f"references/{scenario['template']}",
            "wizard_config": template,
            "pre_confirmation": {
                "action": scenario["first_round_action"],
                "customer_progress": scenario["customer_progress"],
                "call_erp_business_tools": False,
                "read_full_capability_guide": False,
                "inspect_live_schema": False,
                "forbidden_erp_tools": scenario["forbidden_before_confirmation"],
                "halt_after_render": True
            },
            "after_confirmation": scenario["after_confirmation"]
        }
    return {
        "matched": False,
        "read_files": ["references/fast_scenario_router.json"],
        "next_action": "use_local_capability_references_then_render_requirement_wizard",
        "call_erp_business_tools": False
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Fast local router for ERP first-round requirement pages.")
    parser.add_argument("--query", required=True, help="Customer's ERP request in natural language.")
    parser.add_argument("--out", help="Optional route-result JSON output file.")
    parser.add_argument("--wizard-config-out", help="Write the matched small wizard config to this JSON file.")
    args = parser.parse_args()

    result = route(args.query)
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(payload + "\n", encoding="utf-8")
    if args.wizard_config_out and result.get("matched"):
        Path(args.wizard_config_out).write_text(
            json.dumps(result["wizard_config"], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
