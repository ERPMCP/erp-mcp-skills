# MCP Apps 实时看板规则

## 目标

客户希望在结果页面里改月份、层级、业务类型后直接重新查询 ERP。这个体验可以实现，但不能靠普通 `file:///dashboard.html` 直接访问 ERP MCP。

正确方式是优先使用 WorkBuddy 原生 MCP Apps Widget，或使用明确存在的安全桥接服务。页面只负责发起查询请求，ERP Token 和真实 MCP 调用必须留在 WorkBuddy Host、MCP Server 或受控桥接服务里。

## 默认策略：优先生成 MCP Apps Widget

ERP 报表绝大多数都需要后续交互，例如：

- 切换月份或日期范围；
- 按全公司、片区、门店、小组、人员切换；
- 切换二手房、租房、新房等业务类型；
- 点击数字查看明细；
- 改筛选条件后重新读取 ERP；
- 导出当前筛选后的汇总或明细。

因此，只要页面存在上述任一能力，就必须先判断是否能生成 MCP Apps Widget。能生成 Widget 时，优先生成 Widget；不能生成时，才退回普通 HTML。

普通 HTML 是降级方案，不是首选方案。不要因为普通 HTML 生成更简单，就跳过 Widget 判断。

## 必须区分三种页面

### 1. 普通本地 HTML

特征：

- 地址通常是 `file:///.../dashboard.html`；
- 页面里没有 WorkBuddy 提供的工具调用桥；
- 只能展示已加载数据、做本地筛选、搜索和明细切换；
- 不能直接调用 ERP MCP。

按钮文案必须是：

`复制筛选条件，回到对话继续查询`

不得写成：

- `按此条件重新查询`
- `实时查询 ERP`
- `连接后台查询`

除非点击后真的能通过安全桥接调用 ERP。

### 2. WorkBuddy 原生 MCP Apps Widget

特征：

- 页面作为 Widget 嵌入 WorkBuddy 对话；
- Host 提供类似 `app.callServerTool()` 的安全调用能力；
- Widget 不保存 ERP Token；
- 点击按钮后由 Host 调用同一个 MCP Server 的工具；
- 查询结果通过结构化数据返回并局部刷新页面。

按钮文案可以是：

`实时查询`

或：

`按当前条件查询`

但必须先检测桥接能力存在。没有检测到桥接时，必须降级为普通本地 HTML 行为。

### 3. 安全本地或远程桥接服务

特征：

- 页面通过 `http://127.0.0.1` 或受控 HTTPS 服务请求桥接层；
- Token 只在桥接层保存，不能进入 HTML；
- 桥接层再调用 ERP MCP；
- 需要安装、启动、鉴权和错误提示。

只有用户或部署文档明确说明该桥接已安装并启动时，才允许生成这种页面。

## 生成看板前必须判断

生成最终页面前，先判断：

1. 当前是否是 MCP Apps Widget 输出；
2. 是否有 Host 提供的工具调用桥；
3. 是否有明确可用的本地/远程桥接服务；
4. 如果都没有，只能生成普通本地 HTML，并在页面里清楚说明它不能实时读取 ERP。

不要凭空假设桥接存在。不要为了满足实时查询愿望而把 Token 写进页面。

## 普通 HTML 的降级行为

如果没有实时桥接：

- 页面顶部要说明：`当前页面只能筛选已加载数据。需要重新读取 ERP 时，请把条件发回对话，由 WorkBuddy 调用 ERP 查询。`
- 改月份、层级、业务类型时，按钮必须复制或显示查询指令；
- 如果浏览器禁止复制，要在页面内显示可手动复制的指令；
- 聊天回复必须提醒：`这是普通 HTML 页面，不是 MCP Apps 实时看板。`

## MCP Apps Widget 的推荐工具

如果能改 ERP MCP 服务端，优先新增：

- `showErpDashboard`: 打开实时看板；
- `queryErpDashboardData`: 根据页面条件查询汇总数据；
- `getErpMetricDetails`: 点击数字后查询明细。

Widget 资源建议：

- URI: `ui://erp/dashboard`
- MIME: `text/html;profile=mcp-app`

工具返回结果必须把 Widget 资源与工具绑定，具体字段以 WorkBuddy 当前 MCP Apps 规范为准。不要在 Skill 里伪造这些工具；只有实时工具真实存在时才调用。

## HTML 模板行为

最终 HTML 模板应支持两种模式：

- `realtime.enabled=true`: 尝试使用 `app.callServerTool()` 调用 `queryErpDashboardData`；
- 无桥接或调用失败：显示清楚的降级提示，并提供复制查询条件。

页面中不得出现：

- ERP Token；
- Authorization；
- Bearer；
- 客户公司密钥；
- 任何可直接复用的认证信息。

## 客户可理解的说明

推荐说法：

`如果这个页面是 WorkBuddy 原生实时看板，点击查询会直接读取 ERP。当前如果只是浏览器打开的普通 HTML，它不能自己连接 ERP，我会把筛选条件发回聊天，由 WorkBuddy 安全地调用 ERP。`

不推荐说法：

`file 页面没有 MCP bridge，需要 app.callServerTool。`

技术说明可以放到折叠区。
