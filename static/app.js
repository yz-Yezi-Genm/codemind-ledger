/* D3：接口请求、操作提示和分类图表。接口遵循 docs/CONTRACT.md。
 * D2 接入约定：
 * #record-form：字段 name 为 type/date/amount/category/note。
 * #filter-form：字段 name 为 start_date/end_date/record_type/category/
 *               min_amount/max_amount/limit（均可选）。
 * #home-view / #add-view / #stats-view：页面容器，以 .is-active 切换。
 * #open-add-btn / #open-stats-btn / .back-home-btn：页面导航。
 * #record-list：按日期分组的最近记录列表。
 * #summary-income / #summary-expense / #summary-balance / #summary-count：统计值。
 * 同一个值若在多个页面展示，副本使用 data-summary="income|expense|balance|count"。
 * #category-chart：全部支出类别分布容器（本版不随查询筛选变化）。
 * #category-list：从类别接口动态生成的分类按钮，选中状态为 .is-selected。
 * 可选增强：#record-type-tabs 收支按钮、#amount-keypad 数字键盘，
 * #amount-display/#amount-expression 金额与算式、#month-picker 月份输入框，
 * #chart-view-toggle 图表切换按钮。
 * #filter-drawer / #filter-toggle-btn：使用 details/summary 原生筛选抽屉。
 * 筛选展开只由浏览器控制，脚本监听 toggle 同步 aria-expanded 和 .is-active。
 * #message-toast（或骨架中的 #build-status）：提示区域；#refresh-button：刷新。
 * 页面缺少某个区域时跳过该功能；分类图前补充统计范围说明。
 */
(() => {
  "use strict";

  const ids = {
    recordForm: "record-form", filterForm: "filter-form", records: "records-body",
    income: "summary-income", expense: "summary-expense", balance: "summary-balance",
    count: "summary-count", chart: "category-chart", message: "message-toast",
    refresh: "refresh-button", picker: "category-list",
    typeTabs: "record-type-tabs", keypad: "amount-keypad", amount: "amount-display",
    expression: "amount-expression", month: "month-picker", groups: "record-list",
    chartToggle: "chart-view-toggle", caption: "records-caption", period: "period-label",
  };
  const ui = {};
  const money = new Intl.NumberFormat("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  let categories = null;
  let activeFilters = {};
  let viewVersion = 0;
  let submitting = false;
  let messageTimer;
  let amountExpression = "";
  const categoryIcons = { 餐饮: "🍚", 交通: "🚕", 购物: "🛍️", 学习: "📚", 娱乐: "🎮",
    医疗: "💊", 其他支出: "📦", 工资: "💼", 奖学金: "🎓", 兼职: "🧰", 其他收入: "🪙" };

  function formatMoney(value) {
    return Number.isFinite(Number(value)) ? `¥${money.format(Number(value))}` : "—";
  }

  function notify(message, kind = "info") {
    if (!ui.message) return;
    clearTimeout(messageTimer);
    ui.message.textContent = message;
    ui.message.dataset.kind = kind;
    ui.message.hidden = false;
    ui.message.classList.add("is-active");
    ui.message.classList.toggle("has-error", kind === "error");
    ui.message.setAttribute("role", kind === "error" ? "alert" : "status");
    if (kind === "success") messageTimer = setTimeout(() => {
      ui.message.hidden = true;
      ui.message.classList.remove("is-active");
    }, 2500);
  }

  // 本地校验只改善交互；服务端仍须校验所有字段。
  async function requestJSON(path, options = {}) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 10000);
    try {
      const response = await fetch(path, {
        ...options, signal: controller.signal,
        headers: { Accept: "application/json", ...options.headers },
      });
      let payload;
      try {
        payload = await response.json();
      } catch (error) {
        if (error.name === "AbortError") throw error;
        throw new Error(`服务器未返回有效 JSON（HTTP ${response.status}）`);
      }
      if (!response.ok || payload?.success !== true) {
        const detail = typeof payload?.error === "string" ? payload.error : `请求失败（HTTP ${response.status}）`;
        throw new Error(response.status === 501 ? `后端接口尚未实现：${detail}` : detail);
      }
      if (!("data" in payload)) throw new Error("接口响应缺少 data 字段");
      return payload.data;
    } catch (error) {
      if (error.name === "AbortError") throw new Error("请求超时，请稍后重试");
      if (error instanceof TypeError) throw new Error("无法连接服务器，请检查服务是否启动");
      throw error;
    } finally {
      clearTimeout(timer);
    }
  }

  function field(form, name) {
    return form?.elements.namedItem(name);
  }

  function populateCategories(form, isFilter = false) {
    const select = field(form, "category");
    if (!select) {
      if (!isFilter) renderCategoryPicker();
      return;
    }
    const previous = select.value;
    if (select.tagName === "SELECT") select.replaceChildren(new Option(isFilter ? "全部类别" : "请选择类别", ""));
    select.disabled = !categories;
    if (!categories) {
      if (!isFilter) renderCategoryPicker();
      return;
    }
    const type = field(form, isFilter ? "record_type" : "type")?.value || "";
    const choices = type ? categories[type] || [] : [...categories.income, ...categories.expense];
    if (select.tagName === "SELECT") [...new Set(choices)].forEach((name) => select.add(new Option(name, name)));
    select.value = choices.includes(previous) ? previous : "";
    if (!isFilter) renderCategoryPicker();
  }

  function renderCategoryPicker() {
    const type = field(ui.recordForm, "type")?.value || "expense";
    ui.typeTabs?.querySelectorAll("[data-record-type]").forEach((button) => {
      button.setAttribute("aria-pressed", String(button.dataset.recordType === type));
      button.classList.toggle("is-selected", button.dataset.recordType === type);
    });
    if (!ui.picker) return;
    const current = field(ui.recordForm, "category")?.value;
    ui.picker.replaceChildren();
    if (!categories) { ui.picker.textContent = "正在等待类别数据，可点击刷新重试"; return; }
    (categories[type] || []).forEach((category) => {
      const button = document.createElement("button");
      button.type = "button";
      button.dataset.category = category;
      button.className = "category-item";
      button.setAttribute("aria-pressed", String(category === current));
      button.classList.toggle("is-selected", category === current);
      const icon = document.createElement("span");
      icon.className = "category-icon";
      icon.setAttribute("aria-hidden", "true");
      icon.textContent = categoryIcons[category] || "🪙";
      const name = document.createElement("span");
      name.textContent = category;
      button.append(icon, name);
      if (["UL", "OL"].includes(ui.picker.tagName)) {
        const item = document.createElement("li");
        item.append(button);
        ui.picker.append(item);
      } else ui.picker.append(button);
    });
  }

  async function loadCategories() {
    const data = await requestJSON("/api/categories");
    if (!data || ![data.income, data.expense].every((list) =>
      Array.isArray(list) && list.every((name) => typeof name === "string" && name.trim()))) {
      throw new Error("类别数据格式不正确");
    }
    categories = data;
    populateCategories(ui.recordForm);
    populateCategories(ui.filterForm, true);
  }

  function recordsMessage(message) {
    if (ui.groups) ui.groups.textContent = message;
    if (ui.caption) ui.caption.textContent = "";
    if (!ui.records) return;
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 5;
    cell.textContent = message;
    row.append(cell);
    ui.records.replaceChildren(row);
  }

  function renderRecords(records) {
    if (!Array.isArray(records)) throw new Error("记录数据格式不正确");
    if (records.length === 0) return recordsMessage("暂无符合条件的记录");
    if (ui.groups) renderGroups(records);
    if (ui.caption) ui.caption.textContent = `本次显示 ${records.length} 笔记录`;
    if (!ui.records) return;
    const fragment = document.createDocumentFragment();
    records.forEach((record) => {
      const row = document.createElement("tr");
      row.dataset.type = record.type;
      [record.date, record.type === "income" ? "收入" : "支出", formatMoney(record.amount),
        record.category, record.note || "—"].forEach((value) => {
        const cell = document.createElement("td");
        // 备注等用户内容仅作为文本显示，不能拼入 HTML。
        cell.textContent = value;
        row.append(cell);
      });
      fragment.append(row);
    });
    ui.records.replaceChildren(fragment);
  }

  function renderGroups(records) {
    const grouped = new Map();
    records.forEach((record) => {
      if (!grouped.has(record.date)) grouped.set(record.date, []);
      grouped.get(record.date).push(record);
    });
    const fragment = document.createDocumentFragment();
    grouped.forEach((rows, date) => {
      const group = document.createElement(["UL", "OL"].includes(ui.groups.tagName) ? "li" : "section");
      group.className = "record-day record-group";
      const heading = document.createElement("h3");
      heading.className = "date-chip";
      const expense = rows.filter((row) => row.type === "expense").reduce((sum, row) => sum + Math.round(row.amount * 100), 0) / 100;
      const income = rows.filter((row) => row.type === "income").reduce((sum, row) => sum + Math.round(row.amount * 100), 0) / 100;
      heading.textContent = `${date} · 支出 ${formatMoney(expense)}${income ? ` · 收入 ${formatMoney(income)}` : ""}`;
      group.append(heading);
      rows.forEach((record) => {
        const row = document.createElement("div");
        row.className = "record-item";
        row.dataset.type = record.type;
        const icon = document.createElement("span");
        icon.className = "record-icon record-emoji";
        icon.textContent = categoryIcons[record.category] || "🪙";
        icon.setAttribute("aria-hidden", "true");
        const detail = document.createElement("div");
        detail.className = "record-copy";
        const name = document.createElement("strong");
        name.textContent = record.category;
        const note = document.createElement("p");
        note.textContent = record.note || "暂无备注";
        detail.append(name, note);
        const amount = document.createElement("strong");
        amount.className = "record-amount";
        amount.textContent = `${record.type === "income" ? "+" : "−"}${formatMoney(record.amount)}`;
        row.append(icon, detail, amount);
        group.append(row);
      });
      fragment.append(group);
    });
    ui.groups.replaceChildren(fragment);
  }

  function summaryTargets(key) {
    return [...new Set([ui[key], ...document.querySelectorAll(`[data-summary="${key}"]`)].filter(Boolean))];
  }

  function hasSummary() {
    return ["income", "expense", "balance", "count"].some((key) => summaryTargets(key).length > 0);
  }

  function showChartScope() {
    if (!ui.chart) return;
    let note = document.getElementById("chart-scope-note");
    if (!note) {
      // D2 的气泡区域使用绝对定位；复用标题内的说明，避免插入段落被气泡遮挡。
      const heading = ui.chart.previousElementSibling;
      note = heading?.classList.contains("chart-heading") ? heading.querySelector("small") : null;
      if (!note) {
        note = document.createElement("p");
        ui.chart.before(note);
      }
      note.id = "chart-scope-note";
      note.classList.add("muted", "chart-scope-note");
    }
    note.textContent = "图表：全部日期支出；汇总、列表：按筛选";
    note.title = "分类图不随月份或其他筛选条件变化；列表和收支汇总按当前查询条件计算。";
    const descriptions = new Set((ui.chart.getAttribute("aria-describedby") || "").split(/\s+/).filter(Boolean));
    descriptions.add(note.id);
    ui.chart.setAttribute("aria-describedby", [...descriptions].join(" "));
  }

  function renderSummary(summary) {
    if (!summary || !["income", "expense", "balance", "count"].every((key) =>
      typeof summary[key] === "number" && Number.isFinite(summary[key]))) {
      throw new Error("统计数据格式不正确");
    }
    ["income", "expense", "balance"].forEach((key) => {
      summaryTargets(key).forEach((target) => { target.textContent = formatMoney(summary[key]); });
    });
    summaryTargets("count").forEach((target) => { target.textContent = String(summary.count); });
  }

  function renderChart(rows) {
    if (!Array.isArray(rows) || rows.some((row) => !row || typeof row.category !== "string" ||
      typeof row.amount !== "number" || !Number.isFinite(row.amount) || row.amount < 0)) {
      throw new Error("图表数据格式不正确");
    }
    const items = rows.filter((row) => row.amount > 0).slice().sort((a, b) => b.amount - a.amount);
    const total = items.reduce((sum, row) => sum + row.amount, 0);
    ui.chart.replaceChildren();
    if (!items.length) {
      ui.chart.textContent = "暂无支出数据";
      return;
    }
    const list = document.createElement("ul");
    list.className = "category-chart-list";
    const largest = items[0].amount;
    items.forEach((row) => {
      const item = document.createElement("li");
      const button = document.createElement("button");
      button.type = "button";
      button.dataset.chartCategory = row.category;
      button.className = "chart-category category-bubble stat-bubble";
      button.style.setProperty("--bubble-weight", String(Math.sqrt(row.amount / largest)));
      button.setAttribute("aria-label", `${row.category}：${formatMoney(row.amount)}，占比 ${(row.amount / total * 100).toFixed(1)}%，点击筛选此类别`);
      const label = document.createElement("span");
      label.className = "chart-name";
      label.textContent = row.category;
      const amount = document.createElement("strong");
      amount.className = "chart-amount";
      amount.textContent = formatMoney(row.amount);
      const percent = document.createElement("span");
      percent.className = "chart-percent";
      percent.textContent = `${(row.amount / total * 100).toFixed(1)}%`;
      const bar = document.createElement("progress");
      bar.max = total;
      bar.value = row.amount;
      bar.setAttribute("aria-label", button.getAttribute("aria-label"));
      button.append(label, amount, percent, bar);
      item.append(button);
      list.append(item);
    });
    ui.chart.append(list);
  }

  function readFilters() {
    const result = {};
    const data = new FormData(ui.filterForm);
    ["start_date", "end_date", "record_type", "category", "min_amount", "max_amount", "limit"].forEach((key) => {
      const value = String(data.get(key) ?? "").trim();
      if (value !== "") result[key] = value;
    });
    if (result.start_date && result.end_date && result.start_date > result.end_date) {
      throw new Error("开始日期不能晚于结束日期");
    }
    ["min_amount", "max_amount"].forEach((key) => {
      if (key in result && (!Number.isFinite(Number(result[key])) || Number(result[key]) < 0)) {
        throw new Error("筛选金额必须是大于或等于 0 的数字");
      }
    });
    if ("min_amount" in result && "max_amount" in result && Number(result.min_amount) > Number(result.max_amount)) {
      throw new Error("最低金额不能大于最高金额");
    }
    if (result.limit && (!/^[1-9]\d*$/.test(result.limit) || !Number.isSafeInteger(Number(result.limit)))) {
      throw new Error("显示笔数必须为正整数");
    }
    return result;
  }

  async function refreshData(successMessage = "数据已更新") {
    const version = ++viewVersion;
    notify("正在加载…");
    const query = new URLSearchParams(activeFilters);
    const recordQuery = query.toString();
    query.delete("limit"); // 统计不能被“最近几笔”截断。
    const summaryQuery = query.toString();
    const jobs = [];
    if (ui.records || ui.groups) jobs.push({ label: "记录", path: `/api/records${recordQuery ? `?${recordQuery}` : ""}`,
      render: renderRecords, fail: () => recordsMessage("记录加载失败，请重试") });
    if (hasSummary()) {
      jobs.push({ label: "统计", path: `/api/statistics${summaryQuery ? `?${summaryQuery}` : ""}`,
        render: renderSummary, fail: () => ["income", "expense", "balance", "count"].forEach((key) => {
          summaryTargets(key).forEach((target) => { target.textContent = "—"; });
        }) });
    }
    // CONTRACT.md 尚未统一图表筛选行为，本版明确展示全部支出。
    if (ui.chart) jobs.push({ label: "图表", path: "/api/charts", render: renderChart,
      fail: () => { ui.chart.textContent = "图表加载失败，请重试"; } });
    [ui.records, ui.groups, ui.chart].filter(Boolean).forEach((node) => {
      node.setAttribute("aria-busy", "true");
      node.classList.add("is-loading");
    });
    const results = await Promise.allSettled(jobs.map((job) => requestJSON(job.path)));
    // 快速连续查询时，只允许最后一次查询更新页面。
    if (version !== viewVersion) return;
    [ui.records, ui.groups, ui.chart].filter(Boolean).forEach((node) => {
      node.removeAttribute("aria-busy");
      node.classList.remove("is-loading");
    });
    const errors = [];
    results.forEach((result, index) => {
      const job = jobs[index];
      try {
        if (result.status === "rejected") throw result.reason;
        job.render(result.value);
      } catch (error) {
        job.fail();
        errors.push(`${job.label}：${error.message}`);
      }
    });
    notify(errors.length ? `${successMessage === "保存成功" ? "保存成功，但刷新失败。" : ""}${errors.join("；")}` : successMessage,
      errors.length ? "error" : "success");
  }

  function setDefaultDate() {
    const dateInput = field(ui.recordForm, "date");
    if (dateInput && !dateInput.value) {
      const today = new Date();
      dateInput.value = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;
    }
  }

  // 数字键盘只做加减，用整数“分”计算，禁止 eval 和任意表达式执行。
  function expressionCents(expression) {
    if (!expression) return 0;
    const parts = expression.replace(/[+-]$/, "").split(/([+-])/);
    let total = 0;
    let sign = 1;
    parts.forEach((part) => {
      if (part === "+") sign = 1;
      else if (part === "-") sign = -1;
      else {
        if (!/^\d+(?:\.\d{0,2})?$/.test(part)) throw new Error("每笔金额最多输入两位小数");
        const [whole, fraction = ""] = part.split(".");
        const cents = Number(whole) * 100 + Number(fraction.padEnd(2, "0"));
        total += sign * cents;
        if (!Number.isSafeInteger(total) || !Number.isSafeInteger(cents)) throw new Error("金额过大，请重新输入");
      }
    });
    return total;
  }

  function renderAmount() {
    const cents = expressionCents(amountExpression);
    const input = field(ui.recordForm, "amount");
    if (input) input.value = amountExpression ? (cents / 100).toFixed(2) : "";
    if (ui.amount) ui.amount.textContent = money.format(cents / 100);
    if (ui.expression) ui.expression.textContent = amountExpression || "请输入金额";
  }

  function pressAmountKey(key) {
    if (submitting) return;
    if (key === "submit") {
      amountExpression = amountExpression.replace(/[+-]$/, "");
      renderAmount();
      ui.recordForm?.requestSubmit();
      return;
    }
    if (key === "date") {
      const date = field(ui.recordForm, "date");
      if (!date) return;
      try { if (date.showPicker) date.showPicker(); else date.focus(); } catch { date.focus(); }
      return;
    }
    let next = amountExpression;
    if (key === "clear") next = "";
    else if (key === "backspace") next = next.slice(0, -1);
    else if (key === "+" || key === "-") {
      if (!next) return;
      next = next.replace(/[+-]$/, "") + key;
    } else if (/^[0-9.]$/.test(key)) {
      const last = next.split(/[+-]/).pop();
      if (key === "." && last.includes(".")) return;
      if (last.includes(".") && last.split(".")[1].length >= 2) return;
      next += key === "." && !last ? "0." : key;
    } else return;
    try {
      expressionCents(next);
      amountExpression = next;
      renderAmount();
    } catch (error) { notify(error.message, "error"); }
  }

  function applyMonth(value, refresh = true) {
    if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(value)) {
      notify("请选择有效月份", "error"); return;
    }
    const [year, month] = value.split("-").map(Number);
    const endDay = new Date(year, month, 0).getDate();
    activeFilters = { ...activeFilters, start_date: `${value}-01`, end_date: `${value}-${endDay}` };
    ["start_date", "end_date"].forEach((name) => {
      const input = field(ui.filterForm, name);
      if (input) input.value = activeFilters[name];
    });
    if (ui.period) ui.period.textContent = `${year} 年 ${month} 月`;
    if (refresh) void refreshData();
  }

  function updatePeriodFromFilters() {
    if (ui.month) ui.month.value = "";
    if (ui.period) ui.period.textContent = activeFilters.start_date || activeFilters.end_date ? "自定义日期范围" : "全部日期";
  }

  async function addRecord(event) {
    event.preventDefault();
    if (submitting || !ui.recordForm.reportValidity()) return;
    const data = new FormData(ui.recordForm);
    const record = {
      type: String(data.get("type") || ""), date: String(data.get("date") || ""),
      amount: Number(data.get("amount")), category: String(data.get("category") || ""),
      note: String(data.get("note") || ""),
    };
    if (!Number.isFinite(record.amount) || record.amount <= 0) return notify("金额必须是大于 0 的数字", "error");
    if (!["income", "expense"].includes(record.type) || !record.date || !record.category) {
      return notify("请填写收支类型、日期和类别", "error");
    }
    if (!categories) return notify("类别尚未加载成功，请点击刷新后重试", "error");
    if (!categories[record.type].includes(record.category)) return notify("类别与收支类型不匹配", "error");
    submitting = true;
    ui.recordForm.classList.add("is-loading");
    const buttons = [...ui.recordForm.querySelectorAll('button[type="submit"], button:not([type]), input[type="submit"]')];
    const previousDisabled = buttons.map((button) => button.disabled);
    buttons.forEach((button) => { button.disabled = true; });
    notify("正在保存…");
    try {
      await requestJSON("/api/records", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(record) });
      ui.recordForm.reset();
      amountExpression = "";
      renderAmount();
      setDefaultDate();
      populateCategories(ui.recordForm);
      switchView("home-view");
      await refreshData("保存成功");
    } catch (error) {
      notify(`保存失败：${error.message}。如不确定是否写入，请刷新记录后再决定是否重试。`, "error");
    } finally {
      submitting = false;
      ui.recordForm.classList.remove("is-loading");
      buttons.forEach((button, index) => { button.disabled = previousDisabled[index]; });
    }
  }

  async function refreshAll() {
    // 类别请求失败也不阻止其他区域加载；刷新按钮也用于重试类别接口。
    const categoryResult = (ui.recordForm || ui.filterForm)
      ? loadCategories().then(() => null, (error) => error) : Promise.resolve(null);
    const loading = refreshData();
    const version = viewVersion;
    const [, error] = await Promise.all([loading, categoryResult]);
    if (error && version === viewVersion) notify(`${ui.message?.textContent || ""}；类别：${error.message}`, "error");
  }

  function switchView(id) {
    const target = document.getElementById(id);
    if (!target) return;
    ["home-view", "add-view", "stats-view"].forEach((viewId) => {
      const view = document.getElementById(viewId);
      if (!view) return;
      view.classList.toggle("is-active", viewId === id);
      view.hidden = viewId !== id;
    });
    const heading = target.querySelector("h1, h2");
    if (heading) { heading.tabIndex = -1; heading.focus({ preventScroll: true }); }
    window.scrollTo({ top: 0, behavior: "auto" });
  }

  function init() {
    Object.entries(ids).forEach(([key, id]) => { ui[key] = document.getElementById(id); });
    ui.message ||= document.getElementById("build-status");
    if (ui.chart && !ui.chart.dataset.view) ui.chart.dataset.view = "bubble";
    showChartScope();
    if (!ui.recordForm && !ui.filterForm && !ui.records && !ui.groups && !ui.chart &&
      !hasSummary()) {
      notify("前端交互脚本已加载，等待页面接入表单、记录和统计区域");
      return;
    }
    setDefaultDate();
    populateCategories(ui.recordForm);
    populateCategories(ui.filterForm, true);
    if (ui.month) {
      if (!ui.month.value) {
        const today = new Date();
        ui.month.value = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}`;
      }
      applyMonth(ui.month.value, false);
      ui.month.addEventListener("change", () => applyMonth(ui.month.value));
    }
    ui.recordForm?.addEventListener("submit", addRecord);
    ui.recordForm?.addEventListener("change", (event) => {
      if (event.target.name === "type") populateCategories(ui.recordForm);
      if (event.target.name === "category") renderCategoryPicker();
    });
    ui.recordForm?.addEventListener("reset", () => setTimeout(() => {
      amountExpression = ""; renderAmount(); setDefaultDate(); populateCategories(ui.recordForm);
    }, 0));
    ui.picker?.addEventListener("click", (event) => {
      const button = event.target.closest("[data-category]");
      const select = field(ui.recordForm, "category");
      if (!button || !select) return;
      select.value = button.dataset.category;
      renderCategoryPicker();
      // 重建按钮后把焦点还给当前类别，保持键盘操作连续。
      [...ui.picker.querySelectorAll("[data-category]")].find((item) => item.dataset.category === select.value)?.focus();
    });
    ui.typeTabs?.addEventListener("click", (event) => {
      const button = event.target.closest("[data-record-type]");
      const input = field(ui.recordForm, "type");
      if (!button || !input) return;
      input.value = button.dataset.recordType;
      populateCategories(ui.recordForm);
    });
    ui.keypad?.addEventListener("click", (event) => {
      const button = event.target.closest("[data-key]");
      if (button) pressAmountKey(button.dataset.key);
    });
    field(ui.recordForm, "amount")?.addEventListener("input", (event) => {
      amountExpression = event.target.value;
      if (ui.amount) ui.amount.textContent = money.format(Number(amountExpression) || 0);
      if (ui.expression) ui.expression.textContent = amountExpression || "请输入金额";
    });
    document.getElementById("open-add-btn")?.addEventListener("click", (event) => {
      event.preventDefault(); switchView("add-view"); setDefaultDate();
    });
    document.getElementById("open-stats-btn")?.addEventListener("click", (event) => {
      event.preventDefault(); switchView("stats-view");
    });
    document.querySelectorAll(".back-home-btn").forEach((button) => {
      button.addEventListener("click", (event) => { event.preventDefault(); switchView("home-view"); });
    });
    switchView("home-view");
    const filterToggle = document.getElementById("filter-toggle-btn");
    // closest 兼容 D2 尚未补上 filter-drawer ID 的原生 details 页面。
    const filterDrawer = document.getElementById("filter-drawer") || filterToggle?.closest("details");
    if (filterDrawer && filterToggle) {
      const syncFilterState = () => {
        const expanded = filterDrawer.open;
        filterToggle.setAttribute("aria-expanded", String(expanded));
        filterToggle.classList.toggle("is-active", expanded);
      };
      filterDrawer.addEventListener("toggle", syncFilterState);
      syncFilterState();
    }
    ui.chartToggle?.addEventListener("click", () => {
      if (!ui.chart) return;
      const bubble = ui.chart.dataset.view !== "bubble";
      ui.chart.dataset.view = bubble ? "bubble" : "list";
      ui.chartToggle.textContent = bubble ? "查看排行" : "查看气泡";
      ui.chartToggle.setAttribute("aria-pressed", String(bubble));
      ui.chartToggle.classList.toggle("is-selected", bubble);
    });
    ui.chart?.addEventListener("click", (event) => {
      const button = event.target.closest("[data-chart-category]");
      if (!button || !ui.filterForm) return;
      if (!categories) return notify("类别尚未加载成功，请点击刷新后重试", "error");
      const type = field(ui.filterForm, "record_type");
      if (type) type.value = "expense";
      populateCategories(ui.filterForm, true);
      const category = field(ui.filterForm, "category");
      if (category) category.value = button.dataset.chartCategory;
      activeFilters = { ...activeFilters, record_type: "expense", category: button.dataset.chartCategory };
      switchView("home-view");
      void refreshData(`已筛选：${button.dataset.chartCategory}`);
    });
    field(ui.filterForm, "record_type")?.addEventListener("change", () => populateCategories(ui.filterForm, true));
    ui.filterForm?.addEventListener("submit", (event) => {
      event.preventDefault();
      if (!ui.filterForm.reportValidity()) return;
      try { activeFilters = readFilters(); } catch (error) { notify(error.message, "error"); return; }
      updatePeriodFromFilters();
      void refreshData();
    });
    ui.filterForm?.addEventListener("reset", () => setTimeout(() => {
      populateCategories(ui.filterForm, true);
      activeFilters = {};
      updatePeriodFromFilters();
      void refreshData();
    }, 0));
    ui.refresh?.addEventListener("click", (event) => { event.preventDefault(); void refreshAll(); });
    void refreshAll();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init, { once: true });
  else init();
})();
