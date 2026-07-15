# 性能优化规则

目标：在不降低回复质量、不减少必要问题的前提下，让客户更快看到可确认的内容。

## 不能做的提速方式

- 不能省略会改变结果的关键问题。
- 不能把不确定的统计方式当成默认规则。
- 不能用截图、示例值或猜测值先填页面。
- 不能为了节省时间跳过数据来源、计算方式和限制说明。
- 不能把缺失数据写成 0。

## 正确的提速方式

0. **先出可确认的预览或实时看板壳子**

   对绝大多数 ERP 报表，不要一开始就拉全公司、全员、全分页或全明细数据。

   这是硬性规则，不是建议。只要请求可能涉及全公司、多层级、房源明细、合同明细、分页、钻取明细或精装修看板，第一步必须先让客户看到一个轻量预览或实时看板壳子。

   预览页或 Widget 壳子必须明确写：

   `点击确认后，我才会开始读取 ERP 数据。`

   正确顺序是：

   1. 快速确认客户要查什么；
   2. 生成轻量预览页或 MCP Apps Widget 壳子；
   3. 页面只显示筛选条件、指标位置、明细区位置、导出入口和 `等待查询`；
   4. 客户点击 `开始查询`、`确认并读取 ERP` 或在聊天里明确确认；
   5. 再按客户选择的范围调用 ERP MCP；
   6. 再写入真实数据并生成完整结果。

   预览或 Widget 壳子里不能写假数字，也不能预先写入大段 MCP 原始返回。

   生成预览或 Widget 壳子后必须停止，不能在后台继续查 ERP、分页拉取、写 raw JSON、写全量明细文件或生成最终看板。

1. **先轻量确认，再深度查询**

   首轮只做：

   - ERP 连接是否可用；
   - 用户大概要查什么；
   - 需要哪些会改变数字的选择；
   - 是否需要导出最终结果表格。

   首轮不要先跑完整报表查询、全量分页、全员组织扫描或正式 HTML 生成。

   客户可见流程里，不要展示这些内部过程：

   - 加载技能；
   - 阅读参考文件；
   - 学习规则；
   - 探索可用工具；
   - 探测真实数据结构；
   - 英文进度说明。

   如果需要给客户进度，只说一句中文：

   `我先确认 ERP 是否已连接，然后给你一个可确认的查询页面。`

   如果已经生成了问题确认页、WorkBuddy 原生选择卡、MCP Apps Widget 壳子或排版预览，必须立即停止，等待客户选择或点击页面按钮。不能一边等客户确认，一边继续查询或写正式页面。

   最长等待 5 分钟。超过 5 分钟仍未确认时，可以按推荐方案继续到“预览/Widget 壳子”，但不要直接拉全量 ERP 数据。只有在用户确认预览或点击查询按钮后，才开始读取大量数据。最终页面必须说明这是因为客户没有及时确认而采用的推荐方案，并提供重新选择入口。

   5 分钟默认方案只代表“先按推荐条件准备查询入口”，不代表客户同意拉取全量数据。没有点击或明确回复前，仍然不能开始重型 MCP 查询。

2. **保留所有必要问题**

   必须询问的问题包括但不限于：

   - 统计时间按什么算；
   - 业务类型是否包含买卖、租赁、新房；
   - 查看范围按全公司、片区、门店、小组还是个人；
   - 人均、开单率等指标的分子和分母怎么定义；
   - 均价类指标用哪种算法；
   - 是否需要表格导出入口。

   如果某个选择只有一种可行方案，不生成无意义选择题，改成说明卡。

3. **先给排版预览**

   当完整查询和页面生成预计较慢时，先用 `scripts/render_layout_preview.py` 生成排版预览。

   预览页只展示：

   - 顶部筛选会放哪些；
   - 核心指标卡会放哪些；
   - 明细区、指标说明、数据来源说明会怎么排；
   - 是否有导出按钮；
   - 哪些内容需要等正式查询后填入。

   预览页必须显示 `等待查询`，不能填任何假数字。

   生成预览页后必须尝试自动打开。如果打不开，要明确告诉客户点击链接打开。随后停止等待客户确认，不再继续写正式页面。

   如果可以生成 MCP Apps Widget，优先生成 Widget 壳子，而不是普通预览 HTML。Widget 壳子应该很快打开，并把真正耗时的数据查询放到客户点击按钮之后。

   Widget 壳子的按钮文案优先使用 `确认后读取 ERP` 或 `开始查询`，不要写成已经完成查询的语气。首屏指标卡显示 `等待查询`，不要展示任何未经查询验证的数字。

4. **查询后先给核心预览**

   如果数据量大，先返回核心数字和主要限制，再继续写完整 HTML。不要让客户长时间不知道进展。

   客户可见进度必须用中文，例如：

   - `已确认统计方式，正在读取 ERP 数据。`
   - `已拿到核心数字，正在生成可点击页面。`
   - `数据量较大，先生成核心结果，再补明细表格。`

   不要显示英文内部过程。

5. **减少无效工作**

   - 已经有 MCP 工具清单时，不要重复完整读取大型字段文档。
   - 不需要人员维度时，不查询人员级明细。
   - 不需要明细钻取时，不抓取超出指标所需的明细字段。
   - 分页时先用较大页数读取；只有确实还有下一页并且明细必须完整时才继续。
   - 中间 JSON 写入文件即可，不要贴到聊天窗口。
   - 写入文件前先去重，避免重复写入再修正。

6. **导出入口**

   首轮或排版预览中必须提供：

   - `需要导出本次结果`
   - `汇总和明细都导出`
   - `暂时不需要`

   导出只能基于本次已经查询并校验过的数据。不要承诺导出系统没有提供的数据。

## 常见慢点和处理方式

| 慢点 | 优化方式 |
|---|---|
| 第一个问题出来前等待很久 | 不要先做完整数据探测；先问必要问题 |
| 客户确认后等待很久 | 先给排版预览、MCP Apps Widget 壳子或核心数字预览 |
| 生成页面前刷大量原始 JSON | 原始数据写文件，聊天里只说进度和结论 |
| 反复读取大文档 | 先查小型 TSV 或 live schema，需要时再读详细文档 |
| 全量分页太慢 | 先判断是否真的需要全量明细；需要时再分页 |
| 组织层级很大 | 先按客户选择的层级查询，不默认拉全公司全员 |

## 质量底线

快，只能来自更好的流程；不能来自减少必要确认、减少真实查询、减少口径说明或降低数据校验。

## 停止点

以下动作发生后，Agent 必须停止并等待客户：

- 已展示 WorkBuddy 原生选择卡；
- 已生成并打开需求确认 HTML；
- 已生成并打开 MCP Apps Widget 壳子；
- 已生成并打开排版预览 HTML；
- 已告知客户需要点击确认页链接。

只有客户把选择结果发回对话，才能继续查询真实数据和生成正式看板。

如果是 MCP Apps Widget 壳子，只有客户点击页面里的 `开始查询` / `确认并读取 ERP` 后，才允许调用真实 ERP 数据工具。

例外：如果 5 分钟内没有收到客户选择，并且宿主环境支持继续执行，可以采用推荐选项继续。继续后的最终结果必须显示：

> 因为 5 分钟内没有收到确认，本次先按推荐方案生成。你仍然可以重新修改选择并生成新页面。


## Hard pre-confirmation gate

This rule exists because WorkBuddy may otherwise spend 10+ minutes pulling ERP data before showing the first question.

Before the first customer confirmation page/card, MCP Apps Widget shell, or layout preview is visible, the agent may only do these fast actions:

- check whether the `erp` MCP connector/tools exist;
- classify the user's request;
- read local skill references, templates, and schemas;
- decide which questions are required;
- render and open the requirement wizard, native WorkBuddy question card, MCP Apps Widget shell, or layout preview.

Before the customer answers, the agent must not call `queryRptData`, `queryContractFinanceData`, `listHouseByCondition`, `getHouseByHouseNo`, section market tools, or any ERP tool that returns business data, counts, sample rows, pages, or full datasets.

For the common house request `上月新上房源数量 + 挂牌均价`, do not probe live house/listing data before asking required choices. Ask first, then query after the customer confirms or after the 5-minute recommended fallback is explicitly applied.

If the agent has already shown a question card, requirement wizard, MCP Apps Widget shell, or layout preview, it must stop. Continuing to fetch ERP data in the background is a failure of this skill.

## Screenshot-style step audit

For a flow like:

1. loading the skill;
2. reading `house_new_listing_price_case.md`;
3. explaining internal tools such as `queryRptData` and `listHouseByCondition`;
4. saying "let me do exploratory calls";
5. calling `queryRptData` twice and `listHouseByCondition` twice before the preview;

only item 1 is internally necessary, and it should not be narrated in English to the customer. Item 2 may be needed internally only when no cached scenario is available, but it should not delay the first customer-facing preview. Items 3, 4, and 5 are not allowed before customer confirmation.

For known scenarios, use the local scenario template immediately. Do not do exploratory MCP calls to "learn data shape" before showing the preview/question page.

## Deferred data mode

Use deferred data mode for reports that include:

- all-company or multi-level organization scope;
- house listing lists or contract/detail rows;
- more than one ERP data source;
- drilldown details;
- a final polished HTML dashboard;
- any query expected to take more than 30 seconds.

Deferred data mode means:

1. generate the UI shell first;
2. show `等待查询` placeholders;
3. do not write raw MCP data files yet;
4. do not paginate yet;
5. do not query all employees or all departments yet;
6. wait for the customer to confirm exact scope or click the Widget query button;
7. query only the selected scope first, not the broadest possible scope.

Do not default to pulling full-company data just because the customer did not specify a smaller scope. Ask or show the scope selector first.
