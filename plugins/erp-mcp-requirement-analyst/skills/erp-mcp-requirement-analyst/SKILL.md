---
name: erp-mcp-requirement-analyst
description: Fast ERP question clarification and live MCP Apps dashboard. Use when customers ask for new-listing counts, listing prices, ERP summary numbers, filters, or clickable drilldowns. Ask only result-changing questions first, return a verified summary through the bundled proxy, and never preload full records.
allowed-tools: AskUserQuestion, mcp__erp_dashboard_proxy__showErpDashboard
---

# ERP MCP Fast Answer

## First Response Hard Stop

For requests containing `新上房源`, `新增房源`, `新上数量`, or `挂牌均价`, do not read any reference, asset, example, capability file, schema, or workspace file before responding.

Do not call any ERP or MCP tool before the required definitions are confirmed. Do not inspect live fields, run samples, probe one page, create a plan, write code, or narrate internal work.

Use `AskUserQuestion` so the customer can click an option. Prefix the question with `快速模式 2.4.4` so the customer can verify that the new Skill is loaded.

For native WorkBuddy question cards, the visible option `label` itself must contain the explanation. Do not rely on hidden descriptions or later chat text, because WorkBuddy may show only the label. Do not shorten, paraphrase, or rename these labels.

Forbidden visible option labels: `每套等权平均`, `面积加权平均`, `每套等权`, `面积加权`, `加权均价`, `简单平均`, `算术平均`, `组织层级`, `地理层级`.

### Count Only

If business type is missing, ask exactly one question and stop:

```text
快速模式 2.4.4
要统计哪类房源？
A. 买卖房源（推荐，二手房出售）
B. 租赁房源（出租房源）
C. 新房业务（新房项目相关数据）
D. 全部业务（买卖、租赁、新房都算；如果后面要算均价，可能不能合并）
```

### Count Plus Listing Average Price

If business type or price method is missing, ask both in one response and stop:

```text
快速模式 2.4.4
请确认两项，确认后马上先给你新增数量和实时看板：

1. 房源类型
A. 买卖房源（推荐，二手房出售）
B. 租赁房源（出租房源）
C. 新房业务（新增数量可查；当前挂牌均价查不到）
D. 全部业务（新增数量可查；挂牌均价不能用同一种方式合并）

2. 挂牌均价怎么算
A. 按面积计算均价（推荐，先算每套房单价，再按面积大小综合；大面积房源影响更大，适合看市场均价）
B. 按套数简单平均（每套房都算一票；小房子和大房子影响一样，适合快速粗略核对）
```

The two price-method option labels must be exactly the two labels above. If a native UI seems too narrow, keep the exact labels anyway; do not replace them with `每套等权平均` or `面积加权平均`.

If the customer selects `新房业务` or `全部业务`, do not silently replace it with buy or rent. Explain that the requested new-listing count can continue, but the current listing-average-price interface cannot produce the same requested combined result. Ask whether to continue with count only or change the business type, then stop without querying.

### Requested Filters Are Unclear

If the customer asks for `多层级筛选`, `按层级筛选`, or other filters without naming the dimensions, include this question in the same first popup:

```text
3. 页面里需要哪些筛选入口？
A. 两类都要（推荐）
   页面分成两个入口：既能按公司部门/人员看“是谁、哪个店带来的数量”，也能按房源位置看“房子在哪个区域、商圈、小区”。
B. 只按公司部门和人员看
   适合问“哪个大区、门店、员工的新上房源多”。例：全公司、大区、片区、门店、员工。月度新增数量可以这样筛；当前挂牌均价不能按这类条件筛。
C. 只按房源所在位置看
   适合问“哪个区域、商圈、小区的新上房源多、挂牌均价多少”。例：区域、商圈、小区。当前新上总数和挂牌均价可以这样筛；月度新增数量不能按这类条件筛。
D. 不需要额外筛选
   只看所选月份、业务类型和全公司汇总，速度最快。
```

Keep the native `其他补充` entry so the customer can type a custom filter. Before accepting a custom filter, state whether it is directly available, available with a limitation, or unavailable. Never claim that a custom filter works until the proxy supports it.

Every native popup option must be self-explanatory. Do not show short labels such as `每套等权平均`, `面积加权平均`, `加权均价`, `简单平均`, `组织层级`, or `地理层级` without a same-line plain Chinese explanation. Assume the customer does not know ERP terms. Prefer longer option labels over making the customer guess.

When the ERP result or a dedicated option tool can enumerate filter values, the Widget must use a dropdown. Do not replace an available department, store, person, region, business-district, or community list with a plain search box to save implementation work. This remains mandatory even when there are dozens or hundreds of values, such as 72 branches. For a large list, put search inside the dropdown; search may help narrow the list but may not replace the list. Use dependent dropdowns for parent-child values such as region -> business district -> community. Use free text only when the MCP truly cannot enumerate a complete option set, and explain that limitation beside the field.

Ask this filter question only when the customer requested filters but left their meaning unclear. If the customer named exact filters, preserve them and state their availability. If no filters were requested, do not delay the first number merely to ask about optional filters.

Do not ask about sorting, export, detail columns, or page style before the first number. These do not change the core result and can be offered in the Widget later.

Never show the unexplained labels `组织层级` or `地理层级` to customers. Use concrete wording instead:

- `按公司部门和人员看：例如全公司、大区、片区、门店或某位员工`;
- `按房源所在位置看：例如区域、商圈或小区`.

Only show levels that the current ERP result actually provides. Do not invent a company structure or display empty selectors. Selecting `两类都要` means two clearly separated views; it does not mean the two kinds of filters can be mixed into one falsely unified number.

If the user already supplied every required definition, skip the question and continue to the summary call. Never invent a missing choice.

Skip the question only after checking that the request has one reasonable interpretation for every result-changing definition. Think carefully, but do not expose that reasoning or delay the visible response with file reads and live probes.

If another plausible interpretation would change the number, ask. This remains mandatory when that interpretation uses a field the current MCP cannot query. Show the unsupported choice honestly, for example `合同录入时间（当前接口查不到）`, instead of hiding it or silently choosing a supported substitute.

Never translate an unavailable request into a nearby available field without confirmation. If the customer selects an unavailable definition, say exactly what cannot be obtained, present the closest valid alternative separately, and wait for explicit approval before using it.

Do not ask about decorative or optional features that do not change the first number. Those belong in the Widget after the quick result.

After asking any question, stop the turn. A selected business type or price method is only an option answer; it is not permission to probe or preload data.

## Only Allowed Initial Data Call

After the user answers all required questions, call only `mcp__erp_dashboard_proxy__showErpDashboard`.

Pass:

- `scenario=house_new_listing_count` for count only;
- `scenario=house_new_listing_price` and `includeReferencePrice=true` for count plus price;
- confirmed `businessType`;
- confirmed `priceMethod` when price was requested;
- confirmed `filterMode` when the customer requested filters;
- `month=上月` unless the customer selected another month.

Do not call direct `erp` tools, including `queryRptData`, `listHouseByCondition`, `queryContractFinanceData`, or any schema/probe tool. The bundled proxy calls the required upstream ERP tool internally and attaches the real MCP Apps Widget.

If `showErpDashboard` is unavailable, reply only:

```text
实时看板组件没有加载。请把插件更新到 2.4.4 后执行 /reload-plugins，再新建任务重试。
```

Do not fall back to direct ERP calls or a `file:///` report.

## Quick Summary Rules

Use the fastest valid calculation inside the proxy:

1. exact aggregate when available;
2. server-side calculation when available;
3. minimum-field derived calculation when no ready-made number exists;
4. honest unavailable state when required fields do not exist.

This is one logical summary task, not a hard one-upstream-call rule. A derived metric may need multiple pages, but it must keep only formula fields and running totals. It must not return or persist display records before the number.

For monthly new-listing count, use the exact `新增房源·套` aggregate. Do not count houses one by one.

For listing average price, show the monthly count and Widget first. The Widget displays a separate `计算挂牌均价` action. Only that real page click may scan current new-listing price fields. Aggregate in memory and discard rows; never create `data.py`, `prices.json`, or a full house table.

## Widget Rules

- Filter changes call summary tools inside the Widget and return numbers only.
- Organization filters apply to the monthly official aggregate.
- Region, business-district, and community filters apply only to the clearly labeled current-new-listing view.
- A number is blue only when an exact same-definition detail query exists.
- A blue-number click loads at most 20 detail rows. `加载更多` loads the next page.
- A non-drillable number opens its plain-language definition instead of fabricating details.
- Never expose ERP URLs, tokens, headers, or raw MCP responses in the page.

## Forbidden Output

- English progress narration;
- `Let me read`, `probe`, `schema`, `deep thinking`, or tool-planning text;
- raw JSON, personnel rows, house rows, or Python list literals in chat;
- any generated business-data `.py` or `.json` file;
- full-data pagination before a real Widget action;
- a static HTML page pretending to call MCP;
- any recommendation to export a house/property table;
- fake zeroes or screenshot-derived numbers.

## Customer Completion

After `showErpDashboard` succeeds, keep chat to one sentence:

```text
核心数字已显示在实时看板中；换条件只刷新数字，点击蓝色数字才会读取明细。
```
