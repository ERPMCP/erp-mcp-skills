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
- The first confirmed response returns the fastest valid summary number and opens the Widget; it does not wait for full detail rows.
- Ready-made aggregate metrics normally use one call. Derived metrics may use the minimum required fields and calls, without retaining or rendering display details.
- Widget filters refresh summaries only. A blue metric click fetches the first bounded detail page; `加载更多` fetches the next page.
- Monthly historical totals are not marked drillable when the ERP only exposes an aggregate and no exact same-definition detail query.
- HTML validation rejects fragile JavaScript that updates metric cards through unsafe `.querySelector(".value")` chains.
