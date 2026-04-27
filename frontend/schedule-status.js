import { UI_STATUS } from "./schedule-model.js";
import { getCurrentViewModel, subscribeViewModel } from "./schedule-state.js";

const statusPill = document.getElementById("table-status-pill");
const heroStatusValue = document.getElementById("hero-status-value");
const heroUpdatedValue = document.getElementById("hero-updated-value");
const cardState = document.getElementById("status-card-state");
const cardStateHelp = document.getElementById("status-card-state-help");

const STATUS_CLASS = {
  [UI_STATUS.IDLE]: "status-pill--idle",
  [UI_STATUS.PENDING]: "status-pill--pending",
  [UI_STATUS.RUNNING]: "status-pill--running",
  [UI_STATUS.COMPLETED]: "status-pill--completed",
  [UI_STATUS.FAILED]: "status-pill--failed",
};

const STATUS_HELP = {
  [UI_STATUS.IDLE]: "Ожидаем запуск генерации пользователем.",
  [UI_STATUS.PENDING]: "Задача создана и ждёт начала обработки.",
  [UI_STATUS.RUNNING]: "Генератор сейчас рассчитывает расписание.",
  [UI_STATUS.COMPLETED]: "Расписание успешно построено и готово к просмотру.",
  [UI_STATUS.FAILED]: "Генерация завершилась ошибкой. Нужна диагностика.",
};

function getStatusHelp(viewModel) {
  if (viewModel.solveStatus === "нет_решения") {
    return "При текущих ограничениях решение не найдено.";
  }
  if (viewModel.solveStatus === "лимит_поиска_достигнут") {
    return "Поиск остановлен из-за лимита шагов. Можно увеличить max_search_steps.";
  }

  return STATUS_HELP[viewModel.status] ?? STATUS_HELP[UI_STATUS.IDLE];
}

function formatUpdatedAt(dateIsoString) {
  if (!dateIsoString) {
    return "Пока нет данных";
  }

  const date = new Date(dateIsoString);
  if (Number.isNaN(date.getTime())) {
    return "Пока нет данных";
  }

  return new Intl.DateTimeFormat("ru-RU", {
    dateStyle: "short",
    timeStyle: "medium",
  }).format(date);
}

function applyPillStyle(status) {
  const nextClass = STATUS_CLASS[status] ?? STATUS_CLASS[UI_STATUS.IDLE];
  statusPill.classList.remove(
    "status-pill--idle",
    "status-pill--pending",
    "status-pill--running",
    "status-pill--completed",
    "status-pill--failed"
  );
  statusPill.classList.add(nextClass);
}

function renderStatus(viewModel) {
  if (statusPill) {
    statusPill.textContent = viewModel.statusLabel;
  }
  if (heroStatusValue) {
    heroStatusValue.textContent = viewModel.statusLabel;
  }
  if (heroUpdatedValue) {
    heroUpdatedValue.textContent = formatUpdatedAt(viewModel.updatedAt);
  }

  if (cardState) {
    cardState.textContent = viewModel.statusLabel;
  }
  if (cardStateHelp) {
    cardStateHelp.textContent = getStatusHelp(viewModel);
  }

  if (statusPill) {
    applyPillStyle(viewModel.status);
  }
}

renderStatus(getCurrentViewModel());
subscribeViewModel(renderStatus);