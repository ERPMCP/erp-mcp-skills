import { App } from "@modelcontextprotocol/ext-apps/app-with-deps";

const app = new App({ name: "ERP 实时看板", version: "2.3.0" });
const state = {
  view: "organization",
  summary: null,
  detailPage: 0,
  detailRows: [],
  connected: false,
};

const $ = (id) => document.getElementById(id);
const elements = {
  badge: $("connectionBadge"), summary: $("summaryText"), orgView: $("orgView"), locationView: $("locationView"),
  orgFilters: $("organizationFilters"), locationFilters: $("locationFilters"), month: $("month"),
  businessType: $("businessType"), deptName: $("deptName"), userName: $("userName"),
  locationBusinessType: $("locationBusinessType"), districtName: $("districtName"), zoneName: $("zoneName"),
  sectionLike: $("sectionLike"), refresh: $("refreshSummary"), hint: $("filterHint"), metricLabel: $("metricLabel"),
  metricStatus: $("metricStatus"), metricValue: $("metricValue"), metricRule: $("metricRule"), metricHelp: $("metricHelp"),
  detailSection: $("detailSection"), detailMessage: $("detailMessage"), tableWrap: $("tableWrap"), detailHead: $("detailHead"),
  detailBody: $("detailBody"), loadMore: $("loadMore"), closeDetails: $("closeDetails"), error: $("errorPanel"),
  technical: $("technicalText"),
};

function setConnection(kind, text) {
  elements.badge.className = `badge ${kind}`;
  elements.badge.textContent = text;
}

function setBusy(busy, text = "") {
  elements.refresh.disabled = busy;
  if (text) elements.metricStatus.textContent = text;
}

function showError(message) {
  elements.error.textContent = message || "查询失败，没有显示假数字。";
  elements.error.classList.remove("hidden");
  setConnection("error", "查询失败");
}

function clearError() {
  elements.error.textContent = "";
  elements.error.classList.add("hidden");
}

function replaceOptions(select, values, allLabel) {
  const current = select.value;
  select.replaceChildren(new Option(allLabel, ""));
  for (const value of values || []) select.add(new Option(value, value));
  if ([...select.options].some((option) => option.value === current)) select.value = current;
}

function applyFilterOptions(options = {}) {
  replaceOptions(elements.deptName, options.departments, "全公司");
  replaceOptions(elements.userName, options.people, "全部人员");
}

function applyIncomingFilters(filters = {}) {
  if (filters.month) elements.month.value = filters.month;
  if (filters.businessType && [...elements.businessType.options].some((option) => option.value === filters.businessType)) {
    elements.businessType.value = filters.businessType;
  }
  if (filters.deptName) elements.deptName.value = filters.deptName;
  if (filters.userName) elements.userName.value = filters.userName;
}

function renderSummary(data) {
  if (!data || !data.metrics) return;
  state.summary = data;
  clearError();
  applyFilterOptions(data.filterOptions);
  applyIncomingFilters(data.filters);
  const metric = data.metrics.primary || {};
  const drilldown = metric.drilldown || {};
  elements.metricLabel.textContent = metric.label || "新上房源数量";
  elements.metricValue.textContent = metric.display || "暂无可验证数据";
  elements.metricValue.classList.toggle("clickable", drilldown.available === true);
  elements.metricValue.dataset.drillable = drilldown.available === true ? "true" : "false";
  elements.metricStatus.textContent = data.phase === "SUMMARY_READY" ? "已更新" : "查询失败";
  elements.metricRule.textContent = data.plainRule || "暂无统计说明。";
  elements.summary.textContent = data.message || "汇总数字已返回。";
  elements.metricHelp.dataset.reason = drilldown.reason || data.plainRule || "暂无更多说明。";
  elements.technical.textContent = JSON.stringify(data.technical || {}, null, 2);
  setConnection("ready", "实时连接正常");
  setBusy(false);
  if (data.phase === "QUERY_FAILED" || data.limitation) showError(data.limitation || data.message);
}

function summaryArguments() {
  if (state.view === "location") {
    return {
      metricId: "currentNewListingCount",
      businessType: elements.locationBusinessType.value,
      districtName: elements.districtName.value.trim(),
      zoneName: elements.zoneName.value.trim(),
      sectionLike: elements.sectionLike.value.trim(),
    };
  }
  return {
    metricId: "monthlyNewListingCount",
    month: elements.month.value,
    businessType: elements.businessType.value,
    deptName: elements.deptName.value,
    userName: elements.userName.value,
  };
}

function switchView(view) {
  state.view = view;
  const organization = view === "organization";
  elements.orgView.classList.toggle("active", organization);
  elements.locationView.classList.toggle("active", !organization);
  elements.orgFilters.classList.toggle("hidden", !organization);
  elements.locationFilters.classList.toggle("hidden", organization);
  elements.hint.textContent = organization
    ? "按月份和部门/人员查询官方汇总，不读取逐套房源。"
    : "按区域、商圈或小区查询当前新上总数；这不是历史月份新增。";
  elements.metricValue.textContent = "点击刷新数字";
  elements.metricValue.classList.remove("clickable");
  elements.metricValue.dataset.drillable = "false";
  elements.metricStatus.textContent = "条件已改变";
  closeDetails();
}

async function refreshSummary() {
  clearError();
  setBusy(true, "正在查询汇总");
  try {
    const result = await app.callServerTool({ name: "queryErpDashboardSummary", arguments: summaryArguments() });
    renderSummary(result.structuredContent || {});
  } catch (error) {
    setBusy(false, "查询失败");
    showError(error?.message || String(error));
  }
}

function detailArguments(page, userAction) {
  const filters = state.summary?.filters || summaryArguments();
  return { ...filters, metricId: state.summary?.metrics?.primary?.id || "", userAction, page, pageSize: 20 };
}

function renderDetailTable(rows, append = false) {
  if (!append) state.detailRows = [];
  state.detailRows.push(...rows);
  if (!state.detailRows.length) {
    elements.detailMessage.textContent = "当前条件没有可展示的明细。";
    elements.detailMessage.classList.remove("hidden");
    elements.tableWrap.classList.add("hidden");
    return;
  }
  const columns = [...new Set(state.detailRows.flatMap((row) => Object.keys(row)))];
  elements.detailHead.innerHTML = `<tr>${columns.map((column) => `<th>${escapeHtml(column)}</th>`).join("")}</tr>`;
  elements.detailBody.innerHTML = state.detailRows.map((row) => `<tr>${columns.map((column) => `<td>${escapeHtml(row[column] ?? "")}</td>`).join("")}</tr>`).join("");
  elements.detailMessage.classList.add("hidden");
  elements.tableWrap.classList.remove("hidden");
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[char]);
}

async function loadDetails(page = 1, userAction = "metric_click") {
  elements.detailSection.classList.remove("hidden");
  elements.detailMessage.classList.remove("hidden");
  elements.detailMessage.textContent = page === 1 ? "正在读取第一页面明细…" : "正在加载下一页…";
  elements.loadMore.disabled = true;
  try {
    const result = await app.callServerTool({ name: "getErpMetricDetails", arguments: detailArguments(page, userAction) });
    const data = result.structuredContent || {};
    if (data.phase === "QUERY_FAILED") throw new Error(data.limitation || "明细查询失败");
    state.detailPage = page;
    renderDetailTable(data.rows || [], page > 1);
    elements.loadMore.classList.toggle("hidden", !data.hasMore);
    elements.loadMore.disabled = false;
  } catch (error) {
    elements.detailMessage.textContent = error?.message || String(error);
    elements.loadMore.classList.add("hidden");
  }
}

function metricClicked() {
  const metric = state.summary?.metrics?.primary;
  if (!metric?.drilldown?.available) {
    elements.detailSection.classList.remove("hidden");
    elements.detailMessage.classList.remove("hidden");
    elements.detailMessage.textContent = metric?.drilldown?.reason || "这个数字目前没有同一统计方式的明细。";
    elements.tableWrap.classList.add("hidden");
    elements.loadMore.classList.add("hidden");
    return;
  }
  loadDetails(1, "metric_click");
}

function closeDetails() {
  elements.detailSection.classList.add("hidden");
  elements.tableWrap.classList.add("hidden");
  elements.loadMore.classList.add("hidden");
  state.detailRows = [];
  state.detailPage = 0;
}

elements.orgView.addEventListener("click", () => switchView("organization"));
elements.locationView.addEventListener("click", () => switchView("location"));
elements.refresh.addEventListener("click", refreshSummary);
elements.metricValue.addEventListener("click", metricClicked);
elements.metricHelp.addEventListener("click", metricClicked);
elements.closeDetails.addEventListener("click", closeDetails);
elements.loadMore.addEventListener("click", () => loadDetails(state.detailPage + 1, "load_more"));

app.ontoolinput = (params) => applyIncomingFilters(params.arguments || {});
app.ontoolresult = (params) => {
  if (params.structuredContent) renderSummary(params.structuredContent);
};

async function boot() {
  try {
    await app.connect();
    state.connected = true;
    setConnection("ready", "实时连接正常");
  } catch (error) {
    showError(`实时看板连接失败：${error?.message || String(error)}`);
  }
}

boot();
