import { ERROR_KIND, UI_STATUS } from "./schedule-model.js";
import { createApiClient } from "./api-client.js";
import {
  getCurrentScenario,
  getCurrentViewModel,
  setApiSnapshot,
  setScenario,
  subscribeViewModel,
} from "./schedule-state.js";

const generateButton = document.getElementById("generate-btn");
const refreshButton = document.getElementById("refresh-btn");
const resetButton = document.getElementById("reset-btn");
const resultModeSelect = document.getElementById("result-mode-select");
const controlHint = document.getElementById("control-hint");

const apiClient = createApiClient();
const POLL_INTERVAL_MS = 1500;
const POLL_TIMEOUT_MS = 90000;

const DEFAULT_GENERATE_REQUEST = {
  teachers: [
    {
      id: "T1",
      name: "Иванова И.И.",
      max_hours: 8,
      available_days: ["Mon", "Tue", "Wed", "Thu", "Fri"],
    },
  ],
  groups: [
    {
      id: "G1",
      name: "ИВТ-21",
      student_count: 28,
    },
  ],
  auditoriums: [
    {
      id: "A-101",
      capacity: 40,
      type: "lecture",
      available_days: ["Mon", "Tue", "Wed", "Thu", "Fri"],
    },
  ],
  subjects: [
    {
      id: "S1",
      name: "Математика",
      hours_per_week: 1,
      required_auditorium_type: "lecture",
      is_lecture: true,
    },
  ],
  max_search_steps: 50000,
};

const DATA_FILES = {
  teachers: "../dev_alg/data/teachers.json",
  groups: "../dev_alg/data/groups.json",
  auditoriums: "../dev_alg/data/auditoriums.json",
  subjects: "../dev_alg/data/subjects.json",
};

let cachedGenerateRequest = null;

function sleep(ms) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

async function findJobById(jobId) {
  try {
    const jobs = await apiClient.listJobs();
    return jobs.find((job) => job.id === jobId) ?? null;
  } catch {
    return null;
  }
}

function buildFallbackJob(jobId, status, startedAt) {
  const isFinal = status === "completed" || status === "failed";
  return {
    id: jobId,
    status,
    created_at: startedAt,
    completed_at: isFinal ? new Date().toISOString() : null,
  };
}

function buildFailedSnapshot(message, errorStatus = null) {
  return {
    job: {
      id: null,
      status: "failed",
      created_at: new Date().toISOString(),
      completed_at: new Date().toISOString(),
    },
    scheduleResponse: {
      job_id: 0,
      status: "failed",
      schedule: null,
      error_message: message,
      error_status: Number.isFinite(errorStatus) ? errorStatus : null,
    },
  };
}

async function waitForJobResult(jobId, startedAt) {
  const startedAtMs = Date.now();

  while (Date.now() - startedAtMs < POLL_TIMEOUT_MS) {
    const [scheduleResponse, jobFromList] = await Promise.all([
      apiClient.getSchedule(jobId),
      findJobById(jobId),
    ]);

    const mergedJob =
      jobFromList ?? buildFallbackJob(jobId, scheduleResponse.status, startedAt);

    setApiSnapshot({
      job: mergedJob,
      scheduleResponse,
    });

    if (scheduleResponse.status === "completed" || scheduleResponse.status === "failed") {
      return scheduleResponse;
    }

    await sleep(POLL_INTERVAL_MS);
  }

  throw new Error("Превышено время ожидания результата генерации");
}

async function loadGenerateRequestFromDataFiles() {
  if (cachedGenerateRequest) {
    return cachedGenerateRequest;
  }

  try {
    const [teachersRes, groupsRes, auditoriumsRes, subjectsRes] = await Promise.all([
      fetch(DATA_FILES.teachers),
      fetch(DATA_FILES.groups),
      fetch(DATA_FILES.auditoriums),
      fetch(DATA_FILES.subjects),
    ]);

    const responses = [teachersRes, groupsRes, auditoriumsRes, subjectsRes];
    const allOk = responses.every((response) => response.ok);
    if (!allOk) {
      throw new Error("Не удалось загрузить один или несколько JSON-файлов из dev_alg/data");
    }

    const [teachers, groups, auditoriums, subjects] = await Promise.all(
      responses.map((response) => response.json()),
    );

    cachedGenerateRequest = {
      teachers,
      groups,
      auditoriums,
      subjects,
      max_search_steps: DEFAULT_GENERATE_REQUEST.max_search_steps,
    };

    return cachedGenerateRequest;
  } catch (_error) {
    return DEFAULT_GENERATE_REQUEST;
  }
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
    if (viewModel.error?.kind === ERROR_KIND.VALIDATION) {
      controlHint.textContent =
        "Проверь входные данные: у части полей некорректный формат или пропущены значения.";
      return;
    }

    if (viewModel.error?.kind === ERROR_KIND.NO_SOLUTION) {
      controlHint.textContent =
        "Решение не найдено. Ослабь ограничения или измени входные данные и запусти снова.";
      return;
    }

    if (viewModel.error?.kind === ERROR_KIND.SERVER) {
      controlHint.textContent =
        "Ошибка backend/сети. Проверь, что сервер запущен, и повтори запрос.";
      return;
    }

    controlHint.textContent = "Генерация завершилась ошибкой. Выбери другой режим и запусти снова.";
    return;
  }

  if (!viewModel.rows.length) {
    controlHint.textContent = "Таблица пока пустая. Нажми Сгенерировать, чтобы получить новый результат.";
    return;
  }

  controlHint.textContent = "Результат готов. Можно обновить статус или запустить генерацию повторно.";
}

async function runGenerateFlow() {
  setScenario("loading");

  try {
    const generateRequest = await loadGenerateRequestFromDataFiles();
    const generateResponse = await apiClient.generate(generateRequest);
    const startedAt = new Date().toISOString();

    setApiSnapshot({
      job: {
        id: generateResponse.job_id,
        status: generateResponse.status,
        created_at: startedAt,
        completed_at: null,
      },
      scheduleResponse: generateResponse,
    });

    controlHint.textContent =
      `Запрос отправлен. Job #${generateResponse.job_id}. ` +
      "Ожидаем завершения и подгружаем результат...";

    const finalResponse = await waitForJobResult(generateResponse.job_id, startedAt);

    if (finalResponse.status === "completed") {
      controlHint.textContent =
        `Job #${generateResponse.job_id} завершён. Готовое расписание загружено.`;
      return;
    }

    controlHint.textContent =
      `Job #${generateResponse.job_id} завершён с ошибкой. Проверь сообщение в баннере.`;
  } catch (error) {
    const message =
      error?.message ??
      "Не удалось отправить запрос на генерацию. Проверь доступность backend.";

    setApiSnapshot(buildFailedSnapshot(message, error?.status));

    controlHint.textContent =
      "Ошибка отправки generate-запроса. Убедись, что backend запущен на 127.0.0.1:8000.";
  }
}

async function refreshState() {
  try {
    const latestJob = await apiClient.getLatestJob();

    if (!latestJob) {
      setApiSnapshot({
        job: null,
        scheduleResponse: null,
      });
      controlHint.textContent =
        "Задач генерации пока нет. Нажми Сгенерировать, чтобы создать первую.";
      return;
    }

    const scheduleResponse = await apiClient.getSchedule(latestJob.id);
    setApiSnapshot({
      job: latestJob,
      scheduleResponse,
    });

    controlHint.textContent =
      `Данные обновлены для Job #${latestJob.id}. ` +
      "Статус и таблица синхронизированы с backend.";
  } catch (error) {
    const message =
      error?.message ??
      "Не удалось получить latest result. Проверь доступность backend.";

    setApiSnapshot(buildFailedSnapshot(message, error?.status));

    controlHint.textContent =
      "Ошибка получения latest result. Убедись, что backend запущен на 127.0.0.1:8000.";
  }
}

function resetState() {
  resultModeSelect.value = "ready";
  setScenario("idle");
}

generateButton.addEventListener("click", runGenerateFlow);
refreshButton.addEventListener("click", refreshState);
resetButton.addEventListener("click", resetState);
resultModeSelect.addEventListener("change", () => {
  setScenario(resultModeSelect.value);
});

const initialScenario = getCurrentScenario();
if (initialScenario === "ready" || initialScenario === "empty" || initialScenario === "error") {
  resultModeSelect.value = initialScenario;
}

renderActionState(getCurrentViewModel());
subscribeViewModel(renderActionState);