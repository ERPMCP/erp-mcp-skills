---
name: erp-mcp-requirement-analyst
description: Clarify vague Fangzaixian/ERP MCP reporting requests, route them to real erp MCP data or allowed system exports, forbid fabricated ERP data and unsupported house-export suggestions, and produce plain-Chinese interactive Apple-style HTML dashboards. Use for ERP statistics, contracts, opening rate, house/customer/source metrics, finance, performance allocation, people/org hierarchy, field availability, export guidance, WorkBuddy customer-facing MCP reports, or any request needing ERP data口径澄清 and clickable results.
---

# ERP MCP Requirement Analyst

Use this skill as a strict customer-facing workflow for ERP MCP reporting. The customer is often non-technical, so explain in plain Chinese, ask only questions that change the result, query real data, and present the final answer as an interactive HTML page.

## Highest Priority Rules

- NEVER invent ERP data: no fake contract numbers, people, departments, amounts, dates, rows, or totals.
- Treat screenshots as unverified UI references, never as data truth.
- Every number must have source, query/filter conditions, date rule, formula, numerator/denominator, dedupe key, raw/clean/deduped counts, limitations, and drilldown status.
- All formal query/calculation results MUST generate self-contained interactive HTML. Chat should only give a short completion note, the HTML link, and serious limitations.
- The HTML must offer real interaction where possible: time, scope, business type, search/filter, detail drilldown, metric explanation, and export buttons if data exists.
- Do not show fake 0. Missing data, JS errors, or failed loading must display `等待查询`, `暂无可验证数据`, or `加载失败`.
- Do not expose technical jargon in the main UI. Put tool names, field names, JSON, and formulas in a collapsed `数据来源与技术说明` section.
- NEVER recommend exporting a house/property table. The supported export list has no house export. Do not suggest `房源表`, `新上房源表`, `房源明细导出`, `在售房源导出`, or any invented house export.
- Do not call MCP-visible people `公司总人数` or `全员`. Headcount/opening-rate denominators require personnel export, or must be labeled `系统能看到的业务人员`.
- Do not interpret unknown status codes. Show raw values and say the meaning is not公开.
- Do not treat `finishStatus`, `status`, or `assignStatus` as contract approval status. If approval status is requested, explain current data cannot reliably filter it.
- Current known erp MCP is read-only. Do not claim to modify, approve, settle, create, or delete ERP records.

## Resource Map

Read only what is needed:

- `references/erp_mcp_capabilities.txt`: MCP tools, params, observed fields, limits, and date-risk notes.
- `references/erp_export_field_matrix.tsv`: fast field support matrix. Search with `scripts/lookup_field.py`.
- `references/erp_export_field_guide.txt`: export-table field guide, join keys, anti-duplication, scenario guidance.
- `references/export_whitelist.json`: the only export tables that may be recommended.
- `references/house_export_forbidden.md`: hard rule for house/new-listing scenarios.
- `references/final_html_interaction_rules.md`: final HTML, filters, opening, and no-fake-0 requirements.
- `references/plain_language_rules.md`: customer-facing wording rules.
- `references/house_new_listing_price_case.md`: standard case for `上月新上房源数量 + 挂牌均价`.
- `assets/requirement_wizard_template.html`: first-round Apple-style clickable requirement page.
- `assets/dashboard_template.html`: final interactive dashboard template.
- `scripts/recommend_export.py`: export recommendation with whitelist enforcement.
- `scripts/render_requirement_wizard.py`: render first-round requirement page.
- `scripts/render_dashboard.py`: render final dashboard.
- `scripts/validate_report_data.py`, `scripts/validate_dashboard.py`: validate data and HTML.

Source priority: live MCP response, uploaded files, MCP capability TXT, TSV matrix, field guide TXT, then XLSX audit copy.

## Allowed Export Tables Only

Only recommend these exports: 付款明细导出, 合同信息导出, 实收明细导出, 业绩明细导出（应收应付、业绩分配）, 人员信息导出（汇总、人员列表）.

If a field is needed but only a house export would solve it, do NOT recommend export. Say in plain Chinese that current system cannot provide that historical house detail through supported exports, then suggest a product/API enhancement.

## Core Workflow

1. Classify the request: statistics, contract detail, finance, performance allocation, staff/org, house listing, section market, field support, dashboard.
2. Extract known date range, date rule, business type, metric, role attribution, scope, denominator, and output requirement.
3. Ask only critical questions that change the number. If only one valid method remains, show an information card instead of a pointless choice.
4. Prefer a clickable Apple-style HTML questionnaire when critical choices remain.
5. Inspect live MCP schema first when available; otherwise use references and field matrix.
6. Plan data sources, dedupe keys, join keys, privacy masking, and export gaps.
7. Query real MCP data. Split date ranges over 31 days where required.
8. Normalize data while preserving text IDs and front zeros. Never default missing metric values to 0.
9. Aggregate one-to-many child tables before joining; never join raw receivable, allocation, actual-income, and payment rows directly.
10. Reconcile official statistics and detail data; if they differ, show both, do not force a match.
11. Render final HTML and validate it. Try to open it; only say `已自动打开` if actually opened.
12. Return a short chat summary with the HTML path and key limitation.

## Plain Chinese UI Rules

Use customer-friendly terms in main UI: `系统可以直接查`, `系统能查，但统计方式需要说明`, `需要补充一张系统表格`, `这个数字是按哪个日期统计`, `查看这个数字对应的明细`, `每平方米挂牌价`.

Tool names such as `queryRptData`, `listHouseByCondition`, `queryContractFinanceData`, `isNew`, `unitPrice`, `bizType`, `schema`, or `JSON` belong only in collapsed technical details.

## First-Round Requirement HTML

Generate a requirement page when user intent is vague and decisions affect the result. Include compact base filters, 2-5 critical questions at most, full-card clickable options, support status in plain Chinese, allowed export requirements, copy/JSON fallback, and a summary that does not cover options.

For organization filters, show levels only if real data supports them: 全公司、运营、大区、片区、门店、分组、个人. If no org data exists, show only `全公司` and explain that organization structure has not been loaded.

## Final HTML Dashboard Rules

Every final result HTML must include title, generated time, current filters, metric cards, detail/empty state, limitations, next steps, collapsed data source, clickable blue numbers only for exact drilldown, and metric explanation for non-drillable values.

Separate `应用筛选` for loaded data from `按此条件重新查询` for conditions requiring a new MCP call. Never show controls that do not work.

## Tool Routing

Use `queryRptData` for official aggregate statistics such as 新增房源·套、新增客源·个、带看、跟进、分享、访问、通话、合同应收、合同实收、合同成交单量·份、分边量·份.

Use `queryContractFinanceData` for 合同明细、业绩分配、实收明细、应收应付、付款明细.

Use house tools only through MCP: `listHouseByCondition` and `getHouseByHouseNo`. Never recommend a house export if historical house fields are missing.

Use section tools for market data: `getSectionMarketBaseInfo`, `getSectionMarketData`, `listHotSection`.

## Standard Metric Rules

Contract key: use `合同类型 + trim(合同编号)`, preserving leading zeros, letters, and hyphens.

Opening rate: formula must show denominator source. Personnel denominator requires personnel export unless user accepts `系统能看到的业务人员`.

House new listing quantity and listing average price must be split into two numbers: 月度新增房源数量 and 当前新上房源挂牌均价. Explain that the second is a current reference, not strict last-month new-listing average. Do not recommend a house export.

## Export Guidance

When a needed field is missing, search the field matrix, check `export_whitelist.json`, and recommend only whitelist tables. If the solution would require a forbidden house export, explain limitation and suggest product/API enhancement.

## Validation Expectations

Before final delivery, run report data validation and HTML validation when relevant. Check no placeholder tokens, no fake zero for missing metrics, no forbidden house-export recommendation, no empty dropdowns, no main UI technical jargon, and no fixed summary overlay blocking choices. If browser automation is unavailable, say only `已完成静态校验`.

## Final Chat Pattern

Use a short final note: `已生成交互 HTML：<file>`, plus only severe limitations. Do not paste full tables or long technical explanations in chat.