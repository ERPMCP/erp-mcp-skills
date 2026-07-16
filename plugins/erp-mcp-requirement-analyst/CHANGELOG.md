# Changelog
## 2.4.3 - 2026-07-16

- Expand native popup labels for price methods and filter choices into full plain-Chinese explanations, so WorkBuddy cannot show only terse terms such as `面积加权` or `套数算术平均`.
- Mirror the updated Skill into the legacy local install folder that WorkBuddy was still loading during testing, removing the stale `house_new_listing_price_case.md` path from that install source.
## 2.4.2 - 2026-07-16

- Make the bundled dashboard proxy fall back to the existing `FANGLINE_MCP_TOKEN` environment variable and default ERP MCP URL, so local installs can load the Widget entry without copying secrets into config files.
- Document the local-install fix for cases where WorkBuddy kept loading an older `~/.codex/skills` copy and continued direct ERP probes before showing the fast question.
## 2.4.1 - 2026-07-16

- Add clearly labeled new-house and all-business choices to the count-plus-price question so unsupported price combinations remain visible and require explicit customer confirmation.

## 2.4.0 - 2026-07-15

- Restrict the Skill to `AskUserQuestion` and the bundled `showErpDashboard` entry tool so WorkBuddy cannot repeat the direct-probe and `data.py` behavior shown in customer testing.
- Ask only unresolved result-changing definitions, but keep unsupported plausible choices visible and labeled instead of silently changing the requested calculation.
- Explain filters as company departments/people or property location with concrete examples, including `不需要额外筛选` and native custom input.
- Return the initial count before any detail pull, and calculate listing average price only after a real Widget button click.
- Keep derived calculations in memory as running totals and expose page-only refresh, price, and detail tools through MCP Apps visibility metadata.
- Populate enumerable departments, people, regions, business districts, and communities as dropdowns; large lists may be searchable but cannot be replaced by a plain search field.
- Fix single-pass Widget asset injection and add a regression that rejects HTML recursively injected into the JavaScript bundle.

## 2.3.0 - 2026-07-15

- Return the fastest verified summary immediately after metric-definition confirmation, then attach the live MCP Apps Widget without waiting for full records.
- Support direct aggregates and minimum-field derived summaries; only explicit metric clicks may start display-detail pagination.
- Add `queryErpDashboardSummary`, `getErpDashboardFilterOptions`, and click-gated `getErpMetricDetails` tools to the local proxy.
- Rebuild the Widget with the official MCP Apps `App` client and make ordinary HTML an honest static fallback.

## 2.2.7 - 2026-07-15

- Replace the old confirmation gate with the explicit customer flow: `COLLECTING_OPTIONS -> READY_FOR_PREVIEW -> PREVIEW_SHOWN -> QUERY_AUTHORIZED -> QUERY_RUNNING -> QUERY_COMPLETE`.
- Treat customer option replies as option collection only, not query authorization.
- Block all ERP probes, samples, one-page reads, and raw business JSON writes until a real `开始查询` event authorizes the query.
- Add self-tests for option selection and preview display still having zero ERP business tool calls.

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
