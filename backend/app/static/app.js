// LeaveBot 請假頁（docs/05-sds.md UI-01）。
// 所有業務規則在後端；前端只收集輸入、鎖按鈕、以 textContent 顯示結果。

const LEAVE_TYPE_LABELS = { annual: "特休", personal: "事假", sick: "病假" };
const PERIOD_LABELS = { full: "整天", am: "上午", pm: "下午" };
const STATUS_LABELS = { pending: "待審核" };
const GENERIC_ERROR = "系統暫時無法存檔，請稍後再試";

const els = {
  health: document.getElementById("health-status"),
  form: document.getElementById("leave-form"),
  employee: document.getElementById("employee"),
  leaveType: document.getElementById("leave-type"),
  startDate: document.getElementById("start-date"),
  endDate: document.getElementById("end-date"),
  period: document.getElementById("period"),
  reason: document.getElementById("reason"),
  submit: document.getElementById("submit-btn"),
  formMessage: document.getElementById("form-message"),
  listMessage: document.getElementById("list-message"),
  list: document.getElementById("leave-list"),
};

function showFormMessage(text, kind) {
  els.formMessage.textContent = text;
  els.formMessage.className = kind;
}

async function checkHealth() {
  try {
    const response = await fetch("/api/health");
    const body = await response.json();
    if (!response.ok || body.status !== "ok") throw new Error("unexpected");
    els.health.textContent = "已連線";
    els.health.className = "ok";
  } catch (err) {
    els.health.textContent = "無法連線";
    els.health.className = "error";
  }
}

async function loadEmployees() {
  try {
    const response = await fetch("/api/employees");
    if (!response.ok) throw new Error("employees failed");
    const employees = await response.json();
    for (const emp of employees) {
      const option = document.createElement("option");
      option.value = emp.id;
      option.textContent = `${emp.name}（${emp.id}）`;
      els.employee.appendChild(option);
    }
  } catch (err) {
    showFormMessage("無法載入員工名單，請重新整理", "error");
  }
}

function renderLeaves(leaves) {
  els.list.replaceChildren();
  if (leaves.length === 0) {
    els.listMessage.textContent = "目前沒有假單";
    return;
  }
  els.listMessage.textContent = "";
  for (const leave of leaves) {
    const item = document.createElement("li");

    const title = document.createElement("div");
    title.className = "leave-title";
    const type = LEAVE_TYPE_LABELS[leave.leave_type] || leave.leave_type;
    const period = PERIOD_LABELS[leave.period] || leave.period;
    title.textContent = `${type}｜${leave.start_date} ～ ${leave.end_date}｜${period}｜${leave.days} 天`;

    const status = document.createElement("span");
    status.className = "status";
    status.textContent = STATUS_LABELS[leave.status] || leave.status;
    title.appendChild(status);
    item.appendChild(title);

    if (leave.reason) {
      const reason = document.createElement("div");
      reason.className = "leave-reason";
      reason.textContent = `理由：${leave.reason}`;
      item.appendChild(reason);
    }
    els.list.appendChild(item);
  }
}

async function loadLeaves() {
  const employeeId = els.employee.value;
  if (!employeeId) {
    els.list.replaceChildren();
    els.listMessage.textContent = "請先選擇員工";
    return;
  }
  try {
    const response = await fetch(`/api/leave-requests?employee_id=${encodeURIComponent(employeeId)}`);
    const body = await response.json();
    if (!response.ok) {
      els.list.replaceChildren();
      els.listMessage.textContent = body.error ? body.error.message : GENERIC_ERROR;
      return;
    }
    renderLeaves(body);
  } catch (err) {
    els.list.replaceChildren();
    els.listMessage.textContent = "無法載入假單，請稍後再試";
  }
}

function clearLeaveFields() {
  // 成功後清空表單，但保留所選員工（D-04、UI-01）。
  els.leaveType.value = "";
  els.startDate.value = "";
  els.endDate.value = "";
  els.period.value = "";
  els.reason.value = "";
}

async function submitLeave(event) {
  event.preventDefault();
  els.submit.disabled = true; // FR-10：請求進行中停用
  showFormMessage("送出中…", "");
  const payload = {
    employee_id: els.employee.value,
    leave_type: els.leaveType.value,
    start_date: els.startDate.value,
    end_date: els.endDate.value,
    period: els.period.value,
    reason: els.reason.value,
  };
  try {
    const response = await fetch("/api/leave-requests", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const body = await response.json().catch(() => null);
    if (response.status === 201) {
      showFormMessage("已送出，狀態：待審核", "ok");
      clearLeaveFields();
      await loadLeaves();
    } else if (response.status === 422 && body && body.error) {
      showFormMessage(body.error.message, "error"); // 保留表單內容（D-04）
    } else {
      showFormMessage(GENERIC_ERROR, "error");
    }
  } catch (err) {
    showFormMessage(GENERIC_ERROR, "error");
  } finally {
    els.submit.disabled = false;
  }
}

els.form.addEventListener("submit", submitLeave);
els.employee.addEventListener("change", () => {
  showFormMessage("", "");
  loadLeaves();
});

checkHealth();
loadEmployees();
