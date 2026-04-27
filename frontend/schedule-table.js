import { UI_STATUS } from "./schedule-model.js";
import { getCurrentViewModel, subscribeViewModel } from "./schedule-state.js";

const tableBody = document.getElementById("schedule-table-body");
const table = document.querySelector(".schedule-table");
const emptyStatePanel = document.querySelector(".empty-state");

function createSkeletonCell(extraClass = "") {
  const td = document.createElement("td");
  const skeleton = document.createElement("span");
  skeleton.className = `skeleton skeleton--text ${extraClass}`.trim();
  td.appendChild(skeleton);
  return td;
}

function createCell(value, className) {
  const td = document.createElement("td");
  if (className) {
    td.className = className;
  }
  td.textContent = value;
  return td;
}

function getEmptyMessage(viewModel) {
  if (viewModel.status === UI_STATUS.FAILED) {
    return "Расписание не построено. Причина указана в баннере ошибки.";
  }
  if (viewModel.status === UI_STATUS.COMPLETED) {
    return "Генерация завершена, но итоговых строк расписания нет.";
  }
  if (viewModel.status === UI_STATUS.PENDING || viewModel.status === UI_STATUS.RUNNING) {
    return "Генерация выполняется. Таблица заполнится автоматически.";
  }

  return "Пока нет строк расписания для отображения.";
}

function renderEmptyMessage(viewModel) {
  const row = document.createElement("tr");
  row.className = "schedule-row schedule-row--empty";

  const cell = document.createElement("td");
  cell.colSpan = 6;
  cell.textContent = getEmptyMessage(viewModel);

  row.appendChild(cell);
  tableBody.appendChild(row);
}

function renderLoadingRows() {
  tableBody.innerHTML = "";
  for (let index = 0; index < 4; index += 1) {
    const row = document.createElement("tr");
    row.className = "schedule-row";

    row.appendChild(createSkeletonCell());
    row.appendChild(createSkeletonCell());
    row.appendChild(createSkeletonCell());
    row.appendChild(createSkeletonCell());
    row.appendChild(createSkeletonCell("skeleton--wide"));
    row.appendChild(createSkeletonCell("skeleton--wide"));

    tableBody.appendChild(row);
  }
}

function renderRows(rows, viewModel) {
  tableBody.innerHTML = "";

  if (!rows.length) {
    renderEmptyMessage(viewModel);
    return;
  }

  rows.forEach((item) => {
    const row = document.createElement("tr");
    row.className = "schedule-row";

    row.appendChild(createCell(item.day, "schedule-cell schedule-cell--day"));
    row.appendChild(createCell(String(item.pair), "schedule-cell schedule-cell--pair"));
    row.appendChild(
      createCell(item.auditorium, "schedule-cell schedule-cell--auditorium")
    );
    row.appendChild(createCell(item.group, "schedule-cell schedule-cell--group"));
    row.appendChild(
      createCell(item.subject, "schedule-cell schedule-cell--subject")
    );
    row.appendChild(
      createCell(item.teacher, "schedule-cell schedule-cell--teacher")
    );

    tableBody.appendChild(row);
  });
}

function toggleEmptyPanel(isVisible) {
  if (!emptyStatePanel) {
    return;
  }
  emptyStatePanel.classList.toggle("is-hidden", !isVisible);
}

function renderTableByState(viewModel) {
  const isLoading =
    viewModel.status === UI_STATUS.PENDING ||
    viewModel.status === UI_STATUS.RUNNING;

  table.setAttribute("aria-busy", isLoading ? "true" : "false");

  if (isLoading) {
    renderLoadingRows();
    toggleEmptyPanel(false);
    return;
  }

  renderRows(viewModel.rows, viewModel);
  toggleEmptyPanel(viewModel.rows.length === 0);
}

renderTableByState(getCurrentViewModel());
subscribeViewModel(renderTableByState);