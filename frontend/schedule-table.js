import { UI_STATUS } from "./schedule-model.js";
import { getCurrentViewModel, subscribeViewModel } from "./schedule-state.js";

const tableBody = document.getElementById("schedule-table-body");
const table = document.querySelector(".schedule-table");
const emptyStatePanel = document.querySelector(".empty-state");
const teacherFilter = document.getElementById("filter-teacher");
const groupFilter = document.getElementById("filter-group");
const auditoriumFilter = document.getElementById("filter-auditorium");
const filtersResetButton = document.getElementById("filters-reset-btn");
const filtersSummary = document.getElementById("filters-summary");
const renderTimeValue = document.getElementById("render-time-value");

const filtersState = {
  teacher: "",
  group: "",
  auditorium: "",
};
const RENDER_BATCH_SIZE = 120;
let activeRenderToken = 0;

function createSkeletonCell(extraClass = "") {
  const td = document.createElement("td");
  const skeleton = document.createElement("span");
  skeleton.className = `skeleton skeleton--text ${extraClass}`.trim();
  td.appendChild(skeleton);
  return td;
}

function createCell(value, className, title = "") {
  const td = document.createElement("td");
  if (className) {
    td.className = className;
  }
  if (title) {
    td.title = title;
  }
  td.textContent = value;
  return td;
}

function toOptionValues(rows, key) {
  return [...new Set(rows.map((row) => String(row[key] ?? "")).filter(Boolean))].sort(
    (left, right) => left.localeCompare(right, "ru"),
  );
}

function repopulateSelect(selectElement, values, allLabel, selectedValue) {
  if (!selectElement) {
    return;
  }

  const previousValue = selectedValue ?? "";
  selectElement.innerHTML = "";

  const allOption = document.createElement("option");
  allOption.value = "";
  allOption.textContent = allLabel;
  selectElement.appendChild(allOption);

  values.forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    selectElement.appendChild(option);
  });

  const canRestoreSelection = previousValue && values.includes(previousValue);
  selectElement.value = canRestoreSelection ? previousValue : "";
}

function updateFilterOptions(rows) {
  repopulateSelect(
    teacherFilter,
    toOptionValues(rows, "teacher"),
    "Все преподаватели",
    filtersState.teacher,
  );
  repopulateSelect(
    groupFilter,
    toOptionValues(rows, "group"),
    "Все группы",
    filtersState.group,
  );
  repopulateSelect(
    auditoriumFilter,
    toOptionValues(rows, "auditorium"),
    "Все аудитории",
    filtersState.auditorium,
  );

  filtersState.teacher = teacherFilter?.value ?? "";
  filtersState.group = groupFilter?.value ?? "";
  filtersState.auditorium = auditoriumFilter?.value ?? "";
}

function applyFilters(rows) {
  return rows.filter((row) => {
    if (filtersState.teacher && row.teacher !== filtersState.teacher) {
      return false;
    }
    if (filtersState.group && row.group !== filtersState.group) {
      return false;
    }
    if (filtersState.auditorium && row.auditorium !== filtersState.auditorium) {
      return false;
    }
    return true;
  });
}

function updateFiltersSummary(filteredRowsCount, totalRowsCount) {
  if (!filtersSummary) {
    return;
  }

  const activeFilters = [];
  if (filtersState.teacher) {
    activeFilters.push(`преподаватель: ${filtersState.teacher}`);
  }
  if (filtersState.group) {
    activeFilters.push(`группа: ${filtersState.group}`);
  }
  if (filtersState.auditorium) {
    activeFilters.push(`аудитория: ${filtersState.auditorium}`);
  }

  if (!activeFilters.length) {
    filtersSummary.textContent = `Фильтры не применены. Показано строк: ${totalRowsCount}.`;
    return;
  }

  filtersSummary.textContent =
    `Активные фильтры: ${activeFilters.join(", ")}. ` +
    `Показано строк: ${filteredRowsCount} из ${totalRowsCount}.`;
}

function countByCompositeKey(rows, pickKey) {
  const counts = new Map();
  rows.forEach((row) => {
    const key = pickKey(row);
    counts.set(key, (counts.get(key) ?? 0) + 1);
  });
  return counts;
}

function getConflictFlags(row, counters) {
  const teacherConflict =
    (counters.bySlotTeacher.get(`${row.slot}|${row.teacher}`) ?? 0) > 1;
  const groupConflict =
    (counters.bySlotGroup.get(`${row.slot}|${row.group}`) ?? 0) > 1;
  const auditoriumConflict =
    (counters.bySlotAuditorium.get(`${row.slot}|${row.auditorium}`) ?? 0) > 1;

  const reasons = [];
  if (teacherConflict) {
    reasons.push("Преподаватель занят в этом же слоте");
  }
  if (groupConflict) {
    reasons.push("Группа занята в этом же слоте");
  }
  if (auditoriumConflict) {
    reasons.push("Аудитория занята в этом же слоте");
  }

  return {
    teacherConflict,
    groupConflict,
    auditoriumConflict,
    hasConflict: teacherConflict || groupConflict || auditoriumConflict,
    title: reasons.join("; "),
  };
}

function updateRenderMetric(value) {
  if (!renderTimeValue) {
    return;
  }
  renderTimeValue.textContent = value;
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

function buildScheduleRowElement(item, counters) {
  const conflict = getConflictFlags(item, counters);
  const row = document.createElement("tr");
  row.className = `schedule-row ${conflict.hasConflict ? "schedule-row--conflict" : ""}`.trim();
  if (conflict.title) {
    row.title = conflict.title;
  }

  row.appendChild(createCell(item.day, "schedule-cell schedule-cell--day", conflict.title));
  row.appendChild(createCell(String(item.pair), "schedule-cell schedule-cell--pair", conflict.title));
  row.appendChild(
    createCell(
      item.auditorium,
      `schedule-cell schedule-cell--auditorium ${conflict.auditoriumConflict ? "schedule-cell--conflict" : ""}`.trim(),
      conflict.auditoriumConflict ? "Конфликт аудитории" : "",
    )
  );
  row.appendChild(
    createCell(
      item.group,
      `schedule-cell schedule-cell--group ${conflict.groupConflict ? "schedule-cell--conflict" : ""}`.trim(),
      conflict.groupConflict ? "Конфликт группы" : "",
    )
  );
  row.appendChild(
    createCell(item.subject, "schedule-cell schedule-cell--subject", conflict.title)
  );
  row.appendChild(
    createCell(
      item.teacher,
      `schedule-cell schedule-cell--teacher ${conflict.teacherConflict ? "schedule-cell--conflict" : ""}`.trim(),
      conflict.teacherConflict ? "Конфликт преподавателя" : "",
    )
  );

  return row;
}

function renderRowsSync(rows, counters, onComplete) {
  const fragment = document.createDocumentFragment();
  rows.forEach((item) => {
    fragment.appendChild(buildScheduleRowElement(item, counters));
  });
  tableBody.appendChild(fragment);
  onComplete();
}

function renderRowsLazy(rows, counters, renderToken, onComplete) {
  let startIndex = 0;

  const appendNextBatch = () => {
    if (renderToken !== activeRenderToken) {
      return;
    }

    const fragment = document.createDocumentFragment();
    const endIndex = Math.min(startIndex + RENDER_BATCH_SIZE, rows.length);

    for (let index = startIndex; index < endIndex; index += 1) {
      fragment.appendChild(buildScheduleRowElement(rows[index], counters));
    }

    tableBody.appendChild(fragment);
    startIndex = endIndex;

    if (startIndex < rows.length) {
      window.requestAnimationFrame(appendNextBatch);
      return;
    }

    onComplete();
  };

  window.requestAnimationFrame(appendNextBatch);
}

function renderRows(rows, viewModel, renderToken, onComplete) {
  tableBody.innerHTML = "";

  if (!rows.length) {
    renderEmptyMessage(viewModel);
    onComplete();
    return;
  }

  const counters = {
    bySlotTeacher: countByCompositeKey(rows, (row) => `${row.slot}|${row.teacher}`),
    bySlotGroup: countByCompositeKey(rows, (row) => `${row.slot}|${row.group}`),
    bySlotAuditorium: countByCompositeKey(rows, (row) => `${row.slot}|${row.auditorium}`),
  };

  if (rows.length <= RENDER_BATCH_SIZE * 2) {
    renderRowsSync(rows, counters, onComplete);
    return;
  }

  renderRowsLazy(rows, counters, renderToken, onComplete);
}

function toggleEmptyPanel(isVisible) {
  if (!emptyStatePanel) {
    return;
  }
  emptyStatePanel.classList.toggle("is-hidden", !isVisible);
}

function renderTableByState(viewModel) {
  activeRenderToken += 1;
  const currentRenderToken = activeRenderToken;

  const isLoading =
    viewModel.status === UI_STATUS.PENDING ||
    viewModel.status === UI_STATUS.RUNNING;

  table.setAttribute("aria-busy", isLoading ? "true" : "false");

  if (isLoading) {
    renderLoadingRows();
    updateFilterOptions([]);
    updateFiltersSummary(0, 0);
    updateRenderMetric("Время рендера: ожидание данных...");
    toggleEmptyPanel(false);
    return;
  }

  updateFilterOptions(viewModel.rows);
  const filteredRows = applyFilters(viewModel.rows);
  updateFiltersSummary(filteredRows.length, viewModel.rows.length);

  const startedAt = performance.now();
  renderRows(filteredRows, viewModel, currentRenderToken, () => {
    const elapsedMs = performance.now() - startedAt;
    updateRenderMetric(
      `Время рендера: ${elapsedMs.toFixed(2)} мс (${filteredRows.length} строк).`,
    );
  });

  toggleEmptyPanel(filteredRows.length === 0);
}

function handleFiltersChange() {
  filtersState.teacher = teacherFilter?.value ?? "";
  filtersState.group = groupFilter?.value ?? "";
  filtersState.auditorium = auditoriumFilter?.value ?? "";
  renderTableByState(getCurrentViewModel());
}

function resetFilters() {
  filtersState.teacher = "";
  filtersState.group = "";
  filtersState.auditorium = "";

  if (teacherFilter) {
    teacherFilter.value = "";
  }
  if (groupFilter) {
    groupFilter.value = "";
  }
  if (auditoriumFilter) {
    auditoriumFilter.value = "";
  }

  renderTableByState(getCurrentViewModel());
}

teacherFilter?.addEventListener("change", handleFiltersChange);
groupFilter?.addEventListener("change", handleFiltersChange);
auditoriumFilter?.addEventListener("change", handleFiltersChange);
filtersResetButton?.addEventListener("click", resetFilters);

renderTableByState(getCurrentViewModel());
subscribeViewModel(renderTableByState);