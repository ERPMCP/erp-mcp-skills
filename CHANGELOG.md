# Changelog

## 2.2.6 - 2026-07-15

- Add a local `erp_dashboard_proxy` MCP server so WorkBuddy can open an MCP Apps Widget shell instead of a dead `file:///` page when realtime querying is requested.
- Add `showErpDashboard`, `queryErpDashboardData`, and `getErpMetricDetails` proxy tools. The Widget calls these tools only after the customer clicks `开始查询`.
- Add a deterministic query gate that blocks ERP business tools and raw business JSON writes before customer confirmation.
- Add a Widget shell renderer with separate realtime Widget mode and honest static fallback mode.
- Add tests proving zero ERP business calls and zero raw business JSON writes before confirmation, and proving that static HTML does not pretend to call MCP.

## 2.2.5 - 2026-07-15

- Add a deterministic fast scenario router for the first customer-visible screen.
- Route the common "last month's new listings + listing average price" request directly to a small local requirement template, without reading the full MCP capability guide or calling ERP tools.
- Require the first round to render the confirmation page and stop; ERP connector checks, live schema inspection, and real ERP data reads start only after customer confirmation.
- Add automated assertions for the zero-query first round, two-file read limit, Chinese-only customer progress, stop-after-render behavior, and post-confirmation ERP start.
- Align WorkBuddy/Codex marketplace metadata, plugin manifests, README, and changelog at version 2.2.5.

## 2.2.0 - 2026-07-15

- Make MCP Apps Widget the preferred output for ERP dashboards that need realtime interaction, including time, organization scope, business type, refresh, and drilldown.
- Add dedicated MCP Apps realtime dashboard rules and require agents to check for a host/widget bridge before generating page-internal ERP query buttons.
- Update the dashboard template so it uses a secure `callServerTool` bridge only when available, and clearly falls back to copy-back-to-chat behavior for ordinary local HTML pages.
- Forbid embedding ERP URLs, Authorization headers, Bearer tokens, or access tokens inside generated HTML.
- Clarify that ordinary `file:///dashboard.html` pages can do local filtering only and must not pretend to directly connect to ERP MCP.

## 2.1.4 - 2026-07-15

- Add a hard pre-confirmation gate: before the first customer question card, requirement wizard, or layout preview is shown and answered, the agent may only check ERP connector availability and read local references/templates.
- Explicitly forbid `queryRptData`, `queryContractFinanceData`, `listHouseByCondition`, `getHouseByHouseNo`, section market tools, sample pulls, pagination, JSON writes, and aggregate computation before customer confirmation.
- Update the house new-listing + listing-average-price scenario so it asks required choices first instead of probing live ERP data shape first.
- Clarify that ERP MCP preflight is only a connection check, not permission to start business-data queries.

## 2.1.3 - 2026-07-15

- Make requirement confirmation pages look like modal popups instead of ordinary pages.
- Require the agent to open confirmation/preview pages when possible and stop until the customer answers.
- Strengthen WorkBuddy flow rules so required questions and layout previews cannot be bypassed by continued background querying.
- Add a 5-minute no-confirmation fallback that uses recommended choices and requires a visible final-page notice.

## 2.1.2 - 2026-07-15

- Expand terse average-price options such as `两种都展示`, `每套等权`, and `面积加权` with customer-friendly explanations.
- Add a non-required export preference entry so customers can choose whether the final page includes table export.
- Add a lightweight layout-preview step for long-running reports before full MCP pulls and final HTML generation.
- Add performance rules that preserve all necessary requirement questions while avoiding premature large queries and noisy raw-data output.

## 2.1.1 - 2026-07-15

- Add required parenthetical explanations for semi-professional customer-facing terms.
- Enforce Chinese customer-facing progress and option text.
- Auto-expand terms such as `每套房等权均价` and `按面积加权均价` in generated HTML.

## 2.1.0 - 2026-07-15

- Improve customer-facing wording and remove confusing visible terms such as `时间口径`.
- Remove fake-choice dropdowns like `数量=上月;均价=本月`; show a plain explanation card instead.
- Add ERP MCP preflight rules: check connector availability before rendering query pages or dashboards.
- Add a non-secret ERP MCP configuration template for plugin-level connection setup.

## 2.0.0 - 2026-07-15

- Publish `erp-mcp-requirement-analyst` as a GitHub plugin marketplace package.
- Add WorkBuddy-compatible marketplace metadata.
- Add Codex-compatible plugin manifest and marketplace metadata.
- Include V2 ERP MCP rules:
  - final interactive HTML report requirement;
  - no fabricated data;
  - no unsupported house/property export recommendation;
  - plain-Chinese customer-facing explanations;
  - drill-down and metric-source rules.
