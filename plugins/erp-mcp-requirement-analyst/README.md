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
- The common new-listing path asks its first question without reading references or probing ERP. Its Skill tool allowlist exposes only the native question control and the bundled Widget entry tool.
- Customer choices say `按公司部门和人员看（全公司、部门、门店、员工）` and `按房源所在位置看（区域、商圈、小区）`; unexplained hierarchy jargon is not shown.
- If an unsupported field remains a plausible customer intent, it stays visible and is labeled unavailable. The Skill never silently swaps it for a supported field.
- Ready-made aggregate metrics normally use one call. Derived metrics may use the minimum required fields and calls, without retaining or rendering display details.
- Widget filters refresh summaries only. A blue metric click fetches the first bounded detail page; `加载更多` fetches the next page.
- Monthly historical totals are not marked drillable when the ERP only exposes an aggregate and no exact same-definition detail query.
- Listing average price is calculated only after the customer clicks its page button; the proxy keeps running totals and does not return or persist one row per property.
- HTML validation rejects fragile JavaScript that updates metric cards through unsafe `.querySelector(".value")` chains.
