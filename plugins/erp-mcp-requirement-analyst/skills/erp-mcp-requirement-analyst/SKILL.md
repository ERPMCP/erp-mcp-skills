---
name: erp-mcp-requirement-analyst
description: Clarify vague ERP MCP questions, return verified aggregate numbers quickly, and provide a customer-friendly MCP Apps dashboard that re-queries summaries in place and loads detail rows only after an explicit click. Use for ERP statistics, contracts, opening rate, house/customer/source metrics, finance, performance, staff or organization analysis, field availability, export guidance, WorkBuddy reports, filters, drilldown, or clickable ERP results.
---

# ERP MCP Requirement Analyst

Serve nontechnical ERP customers in plain Chinese. Optimize for time-to-first-answer without weakening metric definitions or inventing data.

## Non-Negotiable Rules

- Never fabricate a number, row, person, department, contract, house, amount, date, or fallback example.
- Treat screenshots as UI references, not data sources.
- Never recommend exporting a house/property table. Supported exports do not include one.
- Never put an ERP URL, Token, Authorization header, or session credential in HTML or browser JavaScript.
- Use a real MCP Apps Widget for page-internal ERP queries. A `file:///` page is only an honest read-only fallback.
- Keep tool names, parameters, formulas, and raw field names inside a collapsed technical section.
- Show missing or failed values as `暂无可验证数据` or `查询失败`, never as fake `0`.
- Do not narrate internal work such as reading skills, probing schemas, or fetching pages.

## Fast Answer Contract

Use four layers. Never collapse them into one large query.

### Layer 1: Confirm the definition

Before ERP reads, ask only questions that can change the number. Ask at most 1-3 questions in one native WorkBuddy card or compact Apple-style confirmation page.

For `上月新上房源数量`, usually confirm only:

1. business type: 买卖、租赁、新房、全部;
2. initial scope if the customer named one; otherwise use 全公司汇总 and expose department/person filters in the result Widget.

Do not ask about sorting, export, page decoration, detail columns, or every possible filter before the first number. Those belong in the Widget.

For known scenarios, run `scripts/fast_route.py` and read only the returned small scenario file. Do not read the full capability guide or inspect live business data before showing the question.

### Layer 2: Return one verified summary quickly

After the customer confirms the definition, immediately call the bundled proxy tool `showErpDashboard` with the confirmed filters.

Choose the cheapest valid calculation strategy for the requested metric:

1. `direct_aggregate`: use an existing ERP aggregate metric when it exactly matches;
2. `server_calculation`: use an ERP/MCP server-side calculation tool when available;
3. `derived_summary`: fetch only the fields required by the formula, calculate the number in the proxy, and discard display rows;
4. `not_available`: explain the missing fields or allowed export needed; never guess.

Do not force every metric into one official aggregate call. Some metrics have no ready-made number and must be recalculated. The hard rule is to avoid fetching full display details before the number, not to limit every calculation to one upstream call.

`showErpDashboard` must:

- use one direct aggregate call when an exact aggregate exists, such as `queryRptData` for `新增房源·套`;
- otherwise run the smallest valid derived calculation plan, requesting only formula fields and only as many pages as the calculation truly needs;
- return the number and attach the MCP Apps Widget in the same tool result;
- return only the calculated result, calculation status, and small filter-option lists;
- never call `listHouseByCondition`, `queryContractFinanceData`, `getHouseByHouseNo`, or paginate detail rows for the initial number.

The last restriction applies only when those tools are not required to calculate the requested metric. When a derived metric genuinely needs one of them, request a minimal field set if the tool supports projection, aggregate rows immediately, do not retain or render full records, and mark `detailRowsFetchedForDisplay=0`.

The first result page should therefore show the verified number as soon as calculation finishes, not wait for a polished detail table. If a derived calculation takes longer, open the Widget immediately with `正在计算核心数字` and update that card when the calculation returns. If calculation fails, show an honest error state and retry control.

### Layer 3: Re-query summaries inside the Widget

Changing month, business type, department, person, region, business district, or community must remain inside the Widget. The page calls `queryErpDashboardSummary` through the official MCP Apps host bridge.

- A summary refresh returns only the aggregate number and supported filter options.
- Do not fetch rows behind the number during a filter refresh.
- Load organization option names from aggregate rows when available; do not invent hierarchy levels.
- For monthly official new-listing counts, department/person filters are supported through `queryRptData`.
- Geographic filters belong to the separate `当前新上房源` view because the current house-list tool has region/business-district filters but no historical new-listing date. Never present that result as `上月新增房源`.
- Hide or disable a filter when the current metric cannot support it honestly.

### Layer 4: Fetch details only on demand

Make a number blue and clickable only when an exact same-definition detail query exists.

- Clicking a blue number calls `getErpMetricDetails`.
- Fetch the first page only, default 20 rows and maximum 50.
- Fetch another page only after `加载更多` or a new page click.
- Do not preload, pre-count by enumeration, or write all detail rows in the background.
- If exact detail is unavailable, keep the number non-blue and open a short metric explanation instead.
- `queryRptData` returns aggregate rows, not individual house records. Therefore `月度新增房源数量` is not drillable unless the live ERP exposes an exact historical-detail tool.
- `当前新上房源` may be drillable through `listHouseByCondition`; label it clearly as current inventory, not the selected month's historical additions.

## Deterministic Query States

Use `scripts/query_gate.py`; prompt text alone is not sufficient.

1. `COLLECTING_OPTIONS`: ask definition questions; all ERP business reads are blocked.
2. `READY_FOR_SUMMARY`: the customer confirmed the definition; one logical summary task is allowed. That task may use one direct aggregate or the minimum calls required for a derived calculation.
3. `SUMMARY_RUNNING`: the aggregate query is running; detail tools remain blocked.
4. `SUMMARY_READY`: the verified number is visible in the Widget; summary refreshes and filter-option calls are allowed.
5. `DETAIL_AUTHORIZED`: a real metric click or explicit detail request occurred.
6. `DETAIL_RUNNING`: one paginated detail request is running.
7. `DETAIL_READY`: the requested detail page is visible.
8. `QUERY_FAILED`: show an honest failure state; do not substitute zero.

Choosing an option moves only toward `READY_FOR_SUMMARY`. It never authorizes detail reads. A summary query never authorizes detail reads. Only a real metric click or explicit `查看明细` action moves to `DETAIL_AUTHORIZED`.

Before every ERP call, guard its query class:

```text
summary: queryRptData, showErpDashboard, queryErpDashboardSummary, calculateErpSummaryMetric
filter_options: getErpDashboardFilterOptions
detail: listHouseByCondition, getHouseByHouseNo, queryContractFinanceData, getErpMetricDetails
```

Use `query_gate.py write-json --kind summary|detail` before writing business data. Summary permission must never allow detail files such as `houses_*.json` or `contracts_*.json`.

## MCP Apps Widget Requirements

Use the bundled local `erp_dashboard_proxy` because this repository does not contain the remote ERP server source.

The proxy exposes:

- `showErpDashboard`: run the initial summary strategy and attach `ui://erp/dashboard`;
- `queryErpDashboardSummary`: refresh one logical summary result from page filters;
- `getErpDashboardFilterOptions`: return small supported option lists only;
- `getErpMetricDetails`: fetch one detail page after a metric click.

The Widget must use the official MCP Apps `App` client, register `toolinput` and `toolresult` handlers before connecting, and call tools with `app.callServerTool(...)`. Do not use guessed globals such as `window.app` as the primary bridge.

Initial tool `structuredContent` must contain the confirmed filters and primary summary. The Widget renders it immediately. Subsequent calls update only the metric, option list, or detail region; do not regenerate the page.

## New Listing Example

Customer: `查询上月新上房源数量。`

Correct sequence:

1. Ask one compact question for business type if missing.
2. After confirmation, call `showErpDashboard` once.
3. The proxy calls `queryRptData` with `indexName=新增房源·套` and returns the aggregate.
4. The Widget opens with the verified number and department/person selectors derived from aggregate rows.
5. Selecting a department and clicking `刷新数字` calls `queryErpDashboardSummary`; it does not fetch house rows.
6. The monthly number is non-blue when exact historical detail is unavailable.
7. A separate `当前新上房源` view may accept region/business-district/community filters. It queries only a total first; clicking its blue total fetches the first detail page.

Forbidden sequence:

```text
ask question -> query all departments -> fetch 200 houses -> paginate -> calculate -> build page
```

## Data and Export Rules

- Prefer `queryRptData` for official aggregate statistics.
- Use `queryContractFinanceData` only when contract/finance details are explicitly requested or needed after a drilldown action.
- Use `listHouseByCondition` only for current house-list filters/details, not to reconstruct a historical monthly aggregate.
- Use contract key `合同类型 + trim(合同编号)`, preserving leading zeros, letters, and hyphens.
- Aggregate one-to-many child tables before joining.
- Show official-statistic/detail disagreements side by side; never delete rows to force a match.
- For headcount/opening-rate denominators, require personnel export or label the denominator `系统能看到的业务人员`.
- Only recommend tables in `references/export_whitelist.json`.

## Resource Routing

Read only what the request needs:

- Fast scenarios: `references/fast_scenario_router.json` through `scripts/fast_route.py`.
- MCP fields and limits: `references/erp_mcp_capabilities.txt`.
- Export fields: search `references/erp_export_field_matrix.tsv` with `scripts/lookup_field.py`.
- Export allowlist: `references/export_whitelist.json`.
- Plain-language UI: `references/plain_language_rules.md`.
- Widget behavior: `references/mcp_apps_widget_rules.md`.
- Speed and lazy detail: `references/performance_rules.md`.

## Validation

Before release, run `scripts/self_test.py` and the Skill Creator `quick_validate.py`.

Tests must prove:

- before definition confirmation, ERP business calls are zero;
- after confirmation, a direct-aggregate metric calls one aggregate and no detail tool;
- a derived metric reads only formula fields and never renders or writes display-detail rows before the number;
- summary refresh never calls a detail tool;
- initial Widget HTML contains no embedded ERP rows or credentials;
- detail calls occur only after a metric click and use bounded pagination;
- monthly official count is not falsely marked drillable;
- missing data never becomes zero;
- no house-export recommendation appears;
- the Widget uses the official MCP Apps client and receives initial `structuredContent`.

## Customer-Facing Completion

Keep chat short: `已按你确认的统计方式打开实时看板，核心数字已经显示。你可以直接在页面里换条件；只有点击蓝色数字时才会读取明细。`
