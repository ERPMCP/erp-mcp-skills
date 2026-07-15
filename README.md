# erp-mcp-skills

ERP MCP Skills for WorkBuddy and Codex.

This repository publishes the `erp-mcp-requirement-analyst` plugin. It helps ERP customers clarify reporting requirements, use real ERP MCP data when available, recommend only supported export tables when MCP data is incomplete, and generate interactive HTML reports with plain-language explanations.

## Plugin

- Name: `erp-mcp-requirement-analyst`
- Version: `2.2.7`
- Supports: WorkBuddy / CodeBuddy style plugin marketplace and Codex plugin marketplace
- Main skill path: `plugins/erp-mcp-requirement-analyst/skills/erp-mcp-requirement-analyst/SKILL.md`

## Core Rules

- Do not fabricate ERP data.
- Screenshots are only references and must not be treated as verified source data.
- Final formal answers should be rendered as interactive HTML whenever possible.
- Numeric results must explain where they came from and whether drill-down details are available.
- Do not recommend exporting a house/property listing table. Supported exports are contract, payment, received-payment, performance, and personnel exports only.
- Customer-facing pages should use plain Chinese. Technical MCP tool names and field names belong in folded technical details.
- Before the first customer confirmation page/card or layout preview is answered, the skill must not pull ERP business data, samples, pages, counts, or full datasets.
- For known scenarios, the first page is selected by a tiny local router before the full capability guide or live ERP tools are consulted.
- The plugin now includes a local `erp_dashboard_proxy` MCP server for WorkBuddy MCP Apps Widget shells. The first Widget render is a live query entrance, not a prefilled full-data report.
- Before the customer clicks `开始查询`, business tool calls and raw business JSON writes must pass the deterministic query gate; otherwise they fail with `客户尚未点击开始查询，禁止读取ERP业务数据。`

## WorkBuddy Installation

Add this repository as a plugin marketplace in WorkBuddy, then install:

```text
/plugin marketplace add ERPMCP/erp-mcp-skills
/plugin install erp-mcp-requirement-analyst@fangline-erp-skills
/reload-plugins
```

If WorkBuddy requires a full Git URL, use:

```text
https://github.com/ERPMCP/erp-mcp-skills.git
```

## Codex Installation

Add this repository as a Codex plugin marketplace, then install `erp-mcp-requirement-analyst`.

The Codex marketplace file is:

```text
.agents/plugins/marketplace.json
```

The Codex plugin manifest is:

```text
plugins/erp-mcp-requirement-analyst/.codex-plugin/plugin.json
```

## Updating

When releasing a new version:

1. Update the skill files.
2. Increase the version in both plugin manifests and marketplace files.
3. Update `CHANGELOG.md`.
4. Validate the skill and plugin.
5. Push to GitHub.

Customers can then update from WorkBuddy or Codex plugin management without receiving a new ZIP manually.

## ERP MCP Connection

This plugin includes a non-secret ERP MCP configuration template. Customers still need to provide their own ERP MCP token in WorkBuddy/Codex connector settings. Never commit a real token to GitHub.
