import { UI_STATUS } from "./schedule-model.js";
import {
  getCurrentScenario,
  getCurrentViewModel,
  setScenario,
  subscribeViewModel,
} from "./schedule-state.js";

const generateButton = document.getElementById("generate-btn");
const refreshButton = document.getElementById("refresh-btn");
const resetButton = document.getElementById("reset-btn");
const resultModeSelect = document.getElementById("result-mode-select");
const controlHint = document.getElementById("control-hint");

let timerId = null;

function clearPendingTimer() {
  if (!timerId) {
    return;
  }
  window.clearTimeout(timerId);
  timerId = null;
}

function getTargetScenario() {
  const next = resultModeSelect.value;
  return next === "empty" || next === "error" ? next : "ready";
}

function renderActionState(viewModel) {
  const isRunning =
    viewModel.status === UI_STATUS.RUNNING || viewModel.status === UI_STATUS.PENDING;

  generateButton.disabled = isRunning;
  resultModeSelect.disabled = isRunning;
  refreshButton.disabled = false;

  if (isRunning) {
    controlHint.textContent = "Генерация выполняется... можно дождаться результата или нажать Обновить.";
    return;
  }

  if (viewModel.status === UI_STATUS.FAILED) {
    controlHint.textContent = "Генерация завершилась ошибкой. Выбери другой режим и запусти снова.";
    return;
  }

  if (!viewModel.rows.length) {
    controlHint.textContent = "Таблица пока пустая. Нажми Сгенерировать, чтобы получить новый результат.";
    return;
  }

  controlHint.textContent = "Результат готов. Можно обновить статус или запустить генерацию повторно.";
}

function runGenerateFlow() {
  clearPendingTimer();
  setScenario("loading");

  const targetScenario = getTargetScenario();
  timerId = window.setTimeout(() => {
    setScenario(targetScenario);
    timerId = null;
  }, 1200);
}

function refreshState() {
  const currentScenario = getCurrentScenario();
  setScenario(currentScenario);
}

function resetState() {
  clearPendingTimer();
  resultModeSelect.value = "ready";
  setScenario("idle");
}

generateButton.addEventListener("click", runGenerateFlow);
refreshButton.addEventListener("click", refreshState);
resetButton.addEventListener("click", resetState);

const initialScenario = getCurrentScenario();
if (initialScenario === "ready" || initialScenario === "empty" || initialScenario === "error") {
  resultModeSelect.value = initialScenario;
}

renderActionState(getCurrentViewModel());
subscribeViewModel(renderActionState);