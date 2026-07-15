# MCP Apps 实时看板规则

## 唯一实时入口

页面内重新查询必须使用插件自带的 `erp_dashboard_proxy` MCP Server 和 `ui://erp/dashboard` 资源。普通 `file:///` HTML 不能冒充实时页面。

Widget 客户端必须：

- 使用 `@modelcontextprotocol/ext-apps` 的 `App` 类；
- 在 `app.connect()` 前注册 `ontoolinput` 和 `ontoolresult`；
- 使用 `app.callServerTool({name, arguments})` 调用代理工具；
- 从首次工具结果的 `structuredContent` 直接渲染初始数字；
- 不读取或保存 ERP Token。

## 工具职责

`showErpDashboard`

- 仅在客户确认统计定义后调用；
- 执行一次主指标汇总；
- 返回汇总数字并附加 Widget；
- 不读取逐条明细。

`queryErpDashboardSummary`

- 由页面的刷新数字按钮调用；
- 每次只查询一个汇总；
- 不返回逐套房源或逐份合同。

`getErpDashboardFilterOptions`

- 返回最近汇总已带回的部门/人员选项；
- 不为了做下拉框额外扫描明细。

`getErpMetricDetails`

- 只允许 `metric_click` 或 `load_more` 事件；
- 默认每页 20 条，最大 50 条；
- 返回脱敏、受控字段；
- 不自动分页。

## 数字样式

- 有完全相同统计方式的明细：蓝色可点击数字；
- 没有同口径明细：普通深色数字；
- 点击不可钻取数字时显示指标说明，不调用明细工具；
- 缺失或失败：显示 `暂无可验证数据` 或 `查询失败`，不得显示假 0。

## 筛选语义

- 月度新增房源：月份、业务类型、部门、人员；
- 当前新上房源：业务类型、区域、商圈、小区；
- 不允许把两套筛选混在一个数字中；
- 当前工具无法支持的筛选必须隐藏、禁用或解释限制。

## 安全和降级

- Widget HTML 内不得出现 ERP URL、Token、Authorization 或 Bearer；
- 代理进程从插件配置读取凭证并调用远程 ERP MCP；
- Widget 资源不可用时显示构建/连接错误，不生成死按钮；
- 普通 HTML 降级页只能筛选已加载数据，并必须明确不能实时连接 ERP。
