# Changelog

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
