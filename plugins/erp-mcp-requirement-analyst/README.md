# erp-mcp-requirement-analyst

This plugin contains the ERP MCP requirement analyst skill.

It is designed for customers who may not know ERP MCP field availability or reporting definitions. The skill clarifies ambiguous requirements, avoids unsupported assumptions, guides customers to supported exports when needed, prefers MCP Apps realtime dashboards for interactive ERP querying, and renders ordinary interactive HTML only as a safe fallback.

## Important Guarantees

- No fabricated ERP data.
- No unsupported house/property export recommendation.
- Plain Chinese for customer-facing text.
- Technical details kept in folded source sections.
- Drill-down links only when matching real detail data is available.
- Realtime page querying is allowed only through WorkBuddy MCP Apps Widget or another verified secure bridge.
- Ordinary `file:///dashboard.html` pages must not pretend to connect directly to ERP MCP.
- ERP URL, Authorization headers, and Tokens must never be embedded in generated HTML.
- The bundled local `erp_dashboard_proxy` MCP server provides a real WorkBuddy Widget entry point when the remote ERP MCP server source is not available in this repository.
- Preview pages must show `确认后查询`/`等待查询` first; business ERP reads begin only after a visible customer click.
- HTML validation rejects fragile JavaScript that updates metric cards through unsafe `.querySelector(".value")` chains.
