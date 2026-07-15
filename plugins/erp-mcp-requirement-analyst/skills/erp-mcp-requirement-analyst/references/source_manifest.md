# Source Manifest

Version: 2026-07-14-v2

This skill uses the V2 structured ERP MCP package.

Priority order:

1. Live erp MCP schema and actual tool response.
2. Uploaded customer file headers and rows.
3. `erp_mcp_capabilities.txt`.
4. `erp_export_field_matrix.tsv`.
5. `erp_export_field_guide.txt`.
6. `erp_export_field_matrix.xlsx`.

Runtime references:

- `erp_mcp_capabilities.txt`: MCP tools, params, limits, observed response fields.
- `erp_export_field_guide.txt`: detailed export-table field guide, join keys, anti-duplication rules, scenario guidance.
- `erp_export_field_matrix.tsv`: machine-readable field support matrix.
- `erp_export_field_matrix.xlsx`: human-maintained audit workbook.
- `export_whitelist.json`: the only export tables the skill may recommend.
- `house_export_forbidden.md`: hard rule forbidding house/property export suggestions.
- `final_html_interaction_rules.md`: final answer must be interactive HTML with real filters.
- `plain_language_rules.md`: customer-facing wording must avoid technical jargon.
- `house_new_listing_price_case.md`: standard case for new-listing count and listing average price.

Hard update notes:

- Do not add company names, real departments, people, screenshots, or sample business numbers to references.
- Do not recommend house/property exports. Supported exports are only the whitelist tables.
- Main customer HTML must use plain Chinese; technical fields belong in collapsed details.
