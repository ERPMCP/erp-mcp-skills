# Changelog

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
