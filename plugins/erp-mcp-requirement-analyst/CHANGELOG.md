# Changelog

## 2.2.6 - 2026-07-15

- Add bundled local `erp_dashboard_proxy` MCP server for WorkBuddy MCP Apps Widget shells when this repository does not contain the remote ERP MCP server source.
- Provide real Widget tools: `showErpDashboard`, `queryErpDashboardData`, and `getErpMetricDetails`.
- Add deterministic query gating so business MCP calls and raw business JSON writes fail before customer confirmation.
- Add static and realtime Widget shell rendering, with ordinary HTML fallback clearly labeled as copy-back-to-chat rather than realtime ERP querying.
- Strengthen dashboard validation against fragile DOM selectors that break metric updates after filter changes.

## 2.2.4 - 2026-07-15

- Prefer bundled capability references, TSV field matrix, export whitelist, and scenario templates for the first requirement page; inspect live MCP only when local references are insufficient or after confirmation.
- Add top dashboard filters for keyword, region, business district, and community/project, and pass those filters to realtime Widget queries.
- Make metrics with available detail clickable: embedded detail rows open locally, and realtime Widgets can call a detail tool to refresh the detail area.

## 2.2.3 - 2026-07-15

- Make fast-first choice pages the actual workflow, not just a display cleanup.
- For known/common scenarios, defer ERP connector waiting and tool checks until after the customer confirms choices or clicks `确认后读取 ERP`.
- Prevent MCP preflight from blocking the first customer-visible question page.

## 2.2.2 - 2026-07-15

- Hide internal setup chatter such as skill loading, reference reading, tool exploration, and English progress text from customers.
- Add a screenshot-style audit rule: exploratory `queryRptData` and `listHouseByCondition` calls are not allowed before the customer sees and confirms the preview/query shell.
- Require known scenarios to use local templates immediately instead of live data probes.

## 2.2.1 - 2026-07-15

- Enforce preview-first behavior for slow ERP reports: show a requirement preview or MCP Apps Widget shell before any full data pull.
- Require a visible customer action such as `确认后读取 ERP` before heavy MCP calls, pagination, raw JSON writes, or final dashboard generation.
- Clarify that the 5-minute fallback may prepare a recommended query shell only, not silently start all-company ERP reads.
- Update realtime dashboard template wording so preview mode clearly says ERP data is read only after confirmation.

## 2.2.0 - 2026-07-15

- Prefer WorkBuddy native MCP Apps Widget for interactive ERP dashboards that need page-internal realtime querying.
- Add safe fallback rules for ordinary `file:///` HTML pages that cannot call ERP MCP directly.
- Add validation rules to keep ERP URL, Authorization headers, Bearer tokens, and session credentials out of generated HTML.

## 2.1.4 - 2026-07-15

- Add a hard pre-confirmation gate that allows only connector checks, intent classification, and local reference/template reading before the first customer confirmation.
- Forbid ERP business-data tools, sample pulls, pagination, JSON writes, and aggregate computation before the customer answers or the 5-minute recommended fallback is applied.
- Update the house new-listing + listing-average-price case so it asks required choices before probing live ERP data.

## 2.1.3 - 2026-07-15

- Use modal-style requirement confirmation HTML.
- Require automatic opening or a clear fallback link for confirmation pages.
- Force stop-and-wait behavior after required questions or layout previews.
- Add a 5-minute recommended-default fallback with mandatory final-page notice.

## 2.1.2 - 2026-07-15

- Expand terse average-price options with short explanations.
- Add optional final table-export choice.
- Add lightweight layout preview for long-running dashboards.
- Add performance rules that do not remove necessary questions.

## 2.1.1 - 2026-07-15

- Add required parenthetical explanations for semi-professional customer-facing terms.
- Auto-expand average-price option labels in generated pages.

## 2.1.0 - 2026-07-15

- Improve customer-facing wording and remove confusing visible technical terms.
- Add ERP MCP connector preflight workflow.
- Add non-secret MCP configuration template for plugin-level setup.

## 2.0.0 - 2026-07-15

- Initial GitHub marketplace release for WorkBuddy and Codex.
- Package V2 ERP MCP requirement analyst skill.
- Add WorkBuddy and Codex plugin metadata.
