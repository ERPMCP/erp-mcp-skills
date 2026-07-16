import { App } from "@modelcontextprotocol/ext-apps/app-with-deps";

const app = new App({ name: "ERP 实时看板", version: "2.4.5" });
const state = {
  view: "organization",
  summary: null,
  confirmation: null,
  confirmationTimer: null,
  confirmationRemaining: 0,
  detailPage: 0,
  detailRows: [],
  connected: false,
  includeReferencePrice: false,
  priceMethod: "area_weighted",
  locationRows: [],
  locationOptionsFor: "",
  loadingLocationOptions: false,
};

const $ = (id) => document.getElementById(id);
const elements = {
  badge: $("connectionBadge"), summary: $("summaryText"), orgView: $("orgView"), locationView: $("locationView"),
  orgFilters: $("organizationFilters"), locationFilters: $("locationFilters"), month: $("month"),
  businessType: $("businessType"), deptName: $("deptName"), userName: $("userName"),
  locationBusinessType: $("locationBusinessType"), districtName: $("districtName"), zoneName: $("zoneName"),
  sectionLike: $("sectionLike"), refresh: $("refreshSummary"), hint: $("filterHint"), metricLabel: $("metricLabel"),
  metricStatus: $("metricStatus"), metricValue: $("metricValue"), metricRule: $("metricRule"), metricHelp: $("metricHelp"),
  secondaryMetric: $("secondaryMetric"), secondaryLabel: $("secondaryLabel"), secondaryValue: $("secondaryValue"),
  secondaryRule: $("secondaryRule"), calculatePrice: $("calculatePrice"),
  confirmPanel: $("confirmPanel"), confirmBusinessType: $("confirmBusinessType"), confirmPriceMethod: $("confirmPriceMethod"),
  confirmFilterMode: $("confirmFilterMode"), confirmStart: $("confirmStart"), confirmRecommended: $("confirmRecommended"),
  confirmCountdown: $("confirmCountdown"),
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

function uniqueValues(values) {
  return [...new Set(values.filter(Boolean))].sort((left, right) => left.localeCompare(right, "zh-CN"));
}

function updateSectionOptions() {
  const district = elements.districtName.value;
  const zone = elements.zoneName.value;
  const rows = state.locationRows.filter((row) => (!district || row.district === district) && (!zone || row.zone === zone));
  replaceOptions(elements.sectionLike, uniqueValues(rows.map((row) => row.section)), "全部小区");
  elements.sectionLike.disabled = false;
}

function updateZoneOptions() {
  const district = elements.districtName.value;
  const rows = state.locationRows.filter((row) => !district || row.district === district);
  replaceOptions(elements.zoneName, uniqueValues(rows.map((row) => row.zone)), "全部商圈");
  elements.zoneName.disabled = false;
  updateSectionOptions();
}

function applyLocationOptions(options = {}) {
  state.locationRows = Array.isArray(options.locations) ? options.locations : [];
  replaceOptions(elements.districtName, uniqueValues(state.locationRows.map((row) => row.district)), "全部区域");
  elements.districtName.disabled = false;
  updateZoneOptions();
}

async function loadLocationOptions(force = false) {
  const businessType = elements.locationBusinessType.value;
  if (state.loadingLocationOptions || (!force && state.locationOptionsFor === businessType && state.locationRows.length)) return;
  state.loadingLocationOptions = true;
  elements.districtName.disabled = true;
  elements.zoneName.disabled = true;
  elements.sectionLike.disabled = true;
  elements.districtName.replaceChildren(new Option("正在加载区域…", ""));
  elements.zoneName.replaceChildren(new Option("正在加载商圈…", ""));
  elements.sectionLike.replaceChildren(new Option("正在加载小区…", ""));
  try {
    const result = await app.callServerTool({
      name: "getErpDashboardFilterOptions",
      arguments: { filterKind: "location", businessType, userAction: "load_filter_options" },
    });
    const data = result.structuredContent || {};
    if (data.phase === "QUERY_FAILED" || data.filterOptions?.complete !== true) {
      throw new Error(data.limitation || "没有取得完整的房源位置选项。");
    }
    state.locationOptionsFor = businessType;
    applyLocationOptions(data.filterOptions);
  } catch (error) {
    elements.districtName.replaceChildren(new Option("位置选项加载失败", ""));
    elements.zoneName.replaceChildren(new Option("位置选项加载失败", ""));
    elements.sectionLike.replaceChildren(new Option("位置选项加载失败", ""));
    showError(error?.message || String(error));
  } finally {
    state.loadingLocationOptions = false;
  }
}

function setSelectValue(select, value) {
  if (value && [...select.options].some((option) => option.value === value)) select.value = value;
}

function clearConfirmationTimer() {
  if (state.confirmationTimer) window.clearInterval(state.confirmationTimer);
  state.confirmationTimer = null;
}

function formatRemaining(seconds) {
  const minutes = Math.floor(seconds / 60);
  const rest = seconds % 60;
  return `${minutes}分${String(rest).padStart(2, "0")}秒后自动采用推荐项继续`;
}

function recommendedConfirmation() {
  return state.confirmation?.confirmation?.recommended || {
    businessType: "sell",
    priceMethod: "area_weighted",
    filterMode: "both",
  };
}

function applyRecommendedConfirmation() {
  const recommended = recommendedConfirmation();
  elements.confirmBusinessType.value = recommended.businessType || "sell";
  elements.confirmPriceMethod.value = recommended.priceMethod || "area_weighted";
  elements.confirmFilterMode.value = recommended.filterMode || "both";
}

function confirmationArguments() {
  const filters = state.confirmation?.filters || {};
  const businessType = elements.confirmBusinessType.value || filters.businessType || "sell";
  const priceMethod = elements.confirmPriceMethod.value || filters.priceMethod || "area_weighted";
  const filterMode = elements.confirmFilterMode.value || filters.filterMode || "both";
  return {
    ...filters,
    businessType,
    priceMethod,
    filterMode,
    scenario: filters.includeReferencePrice ? "house_new_listing_price" : filters.scenario || "house_new_listing_count",
    includeReferencePrice: filters.includeReferencePrice === true,
  };
}

async function runConfirmedSummary(auto = false) {
  clearConfirmationTimer();
  elements.confirmStart.disabled = true;
  elements.confirmRecommended.disabled = true;
  elements.confirmCountdown.textContent = auto ? "已自动采用推荐项，正在查询汇总数字…" : "正在查询汇总数字…";
  state.includeReferencePrice = (state.confirmation?.filters?.includeReferencePrice === true);
  state.priceMethod = elements.confirmPriceMethod.value || "area_weighted";
  try {
    const result = await app.callServerTool({ name: "queryErpDashboardSummary", arguments: confirmationArguments() });
    elements.confirmPanel.classList.add("hidden");
    renderSummary(result.structuredContent || {});
  } catch (error) {
    elements.confirmStart.disabled = false;
    elements.confirmRecommended.disabled = false;
    showError(error?.message || String(error));
  }
}

function startConfirmationTimer(seconds) {
  clearConfirmationTimer();
  state.confirmationRemaining = Math.max(10, Number(seconds) || 300);
  elements.confirmCountdown.textContent = formatRemaining(state.confirmationRemaining);
  state.confirmationTimer = window.setInterval(() => {
    state.confirmationRemaining -= 1;
    if (state.confirmationRemaining <= 0) {
      applyRecommendedConfirmation();
      runConfirmedSummary(true);
      return;
    }
    elements.confirmCountdown.textContent = formatRemaining(state.confirmationRemaining);
  }, 1000);
}

function renderConfirmation(data) {
  state.confirmation = data;
  clearError();
  closeDetails();
  elements.confirmPanel.classList.remove("hidden");
  elements.confirmStart.disabled = false;
  elements.confirmRecommended.disabled = false;
  elements.summary.textContent = data.message || "请先确认统计口径；确认前不会读取 ERP 数据。";
  setConnection("pending", "等待确认");
  elements.metricLabel.textContent = data.metrics?.primary?.label || "新上房源数量";
  elements.metricValue.textContent = "确认后查询";
  elements.metricValue.classList.remove("clickable");
  elements.metricValue.dataset.drillable = "false";
  elements.metricStatus.textContent = "未查询";
  elements.metricRule.textContent = data.plainRule || "确认前不会读取 ERP 数据。";
  elements.metricHelp.dataset.reason = "确认后先查汇总数字；点击蓝色数字时才读取明细。";
  elements.technical.textContent = JSON.stringify(data.technical || { erpCallsBeforeConfirmation: 0 }, null, 2);
  applyIncomingFilters(data.filters);
  setSelectValue(elements.confirmBusinessType, data.filters?.businessType);
  setSelectValue(elements.confirmPriceMethod, data.filters?.priceMethod || "area_weighted");
  setSelectValue(elements.confirmFilterMode, data.filters?.filterMode || "both");
  startConfirmationTimer(data.autoContinueSeconds || 300);
}

function applyIncomingFilters(filters = {}) {
  setSelectValue(elements.month, filters.month);
  setSelectValue(elements.businessType, filters.businessType);
  setSelectValue(elements.locationBusinessType, filters.businessType);
  if (filters.deptName) elements.deptName.value = filters.deptName;
  if (filters.userName) elements.userName.value = filters.userName;
  if (filters.districtName) elements.districtName.value = filters.districtName;
  if (filters.zoneName) elements.zoneName.value = filters.zoneName;
  if (filters.sectionLike) elements.sectionLike.value = filters.sectionLike;
  state.includeReferencePrice = filters.includeReferencePrice === true || filters.scenario === "house_new_listing_price";
  state.priceMethod = filters.priceMethod || "area_weighted";
}

function renderSecondary(metric = {}) {
  if (!metric.requested) {
    elements.secondaryMetric.classList.add("hidden");
    return;
  }
  state.includeReferencePrice = true;
  state.priceMethod = metric.priceMethod || state.priceMethod;
  elements.secondaryMetric.classList.remove("hidden");
  elements.secondaryLabel.textContent = metric.label || "当前新上房源挂牌均价";
  elements.secondaryValue.textContent = metric.display || "点击后计算";
  elements.secondaryRule.textContent = metric.plainRule || metric.message || "只有点击计算后才读取价格和面积字段。";
  elements.calculatePrice.disabled = false;
  elements.calculatePrice.textContent = metric.status === "ready" ? "重新计算" : "计算挂牌均价";
  if (metric.status === "failed") {
    elements.secondaryValue.textContent = "计算失败";
    showError(metric.message || "挂牌均价计算失败，没有显示假数字。");
  }
  if (metric.technical) {
    elements.technical.textContent = JSON.stringify({
      ...(state.summary?.technical || {}),
      挂牌均价: metric.technical,
    }, null, 2);
  }
}

function renderSummary(data) {
  if (!data || !data.metrics) return;
  clearConfirmationTimer();
  elements.confirmPanel.classList.add("hidden");
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
  renderSecondary(data.secondaryMetric || {});
  setConnection("ready", "实时连接正常");
  setBusy(false);
  if (data.phase === "QUERY_FAILED" || data.limitation) showError(data.limitation || data.message);
}

function summaryArguments() {
  const common = {
    scenario: state.includeReferencePrice ? "house_new_listing_price" : "house_new_listing_count",
    includeReferencePrice: state.includeReferencePrice,
    priceMethod: state.priceMethod,
  };
  if (state.view === "location") {
    return {
      ...common,
      metricId: "currentNewListingCount",
      businessType: elements.locationBusinessType.value,
      districtName: elements.districtName.value.trim(),
      zoneName: elements.zoneName.value.trim(),
      sectionLike: elements.sectionLike.value.trim(),
    };
  }
  return {
    ...common,
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
    ? "这里按公司里的部门、门店或员工查看所选月份的汇总数字，不读取逐套房源。"
    : "这里按房源所在的区域、商圈或小区查看当前新上总数；这不是历史月份新增。";
  elements.metricValue.textContent = "点击刷新数字";
  elements.metricValue.classList.remove("clickable");
  elements.metricValue.dataset.drillable = "false";
  elements.metricStatus.textContent = "条件已改变";
  if (state.includeReferencePrice) {
    renderSecondary({
      requested: true,
      status: "waiting_for_user",
      display: "点击后计算",
      priceMethod: state.priceMethod,
      message: "先刷新当前条件的数量，再按需计算挂牌均价。",
    });
  }
  closeDetails();
  if (!organization) loadLocationOptions();
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

async function calculatePrice() {
  clearError();
  elements.calculatePrice.disabled = true;
  elements.calculatePrice.textContent = "正在计算";
  elements.secondaryValue.textContent = "正在读取必要字段";
  try {
    const result = await app.callServerTool({
      name: "queryErpDashboardSecondaryMetric",
      arguments: { ...summaryArguments(), userAction: "calculate_price" },
    });
    renderSecondary(result.structuredContent?.secondaryMetric || {});
  } catch (error) {
    renderSecondary({ requested: true, status: "failed", message: error?.message || String(error) });
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
  elements.detailMessage.textContent = page === 1 ? "正在读取第一页明细…" : "正在加载下一页…";
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
elements.calculatePrice.addEventListener("click", calculatePrice);
elements.confirmStart.addEventListener("click", () => runConfirmedSummary(false));
elements.confirmRecommended.addEventListener("click", () => {
  applyRecommendedConfirmation();
  runConfirmedSummary(false);
});
elements.locationBusinessType.addEventListener("change", () => loadLocationOptions(true));
elements.districtName.addEventListener("change", updateZoneOptions);
elements.zoneName.addEventListener("change", updateSectionOptions);
elements.metricValue.addEventListener("click", metricClicked);
elements.metricHelp.addEventListener("click", metricClicked);
elements.closeDetails.addEventListener("click", closeDetails);
elements.loadMore.addEventListener("click", () => loadDetails(state.detailPage + 1, "load_more"));

app.ontoolinput = (params) => applyIncomingFilters(params.arguments || {});
app.ontoolresult = (params) => {
  const data = params.structuredContent || {};
  if (data.phase === "CONFIRMATION_PENDING") renderConfirmation(data);
  else if (data.metrics) renderSummary(data);
  else if (data.secondaryMetric) renderSecondary(data.secondaryMetric);
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
