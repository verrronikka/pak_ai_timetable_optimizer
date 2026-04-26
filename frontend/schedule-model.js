const DAY_ORDER = {
  Mon: 1,
  Tue: 2,
  Wed: 3,
  Thu: 4,
  Fri: 5,
};

export const UI_STATUS = {
  IDLE: "idle",
  PENDING: "pending",
  RUNNING: "running",
  COMPLETED: "completed",
  FAILED: "failed",
};

export const ERROR_KIND = {
  VALIDATION: "validation",
  NO_SOLUTION: "no_solution",
  SERVER: "server",
  UNKNOWN: "unknown",
};

export const EMPTY_VIEW_MODEL = {
  jobId: null,
  status: UI_STATUS.IDLE,
  statusLabel: "Нет активной генерации",
  updatedAt: null,
  rows: [],
  error: null,
};

function parseSlot(slot) {
  if (typeof slot !== "string" || !slot.includes("_")) {
    return { day: "Unknown", pair: 99 };
  }

  const [day, pairRaw] = slot.split("_");
  const pair = Number.parseInt(pairRaw, 10);
  return {
    day,
    pair: Number.isFinite(pair) ? pair : 99,
  };
}

function toUiStatus(status) {
  switch (status) {
    case "pending":
      return UI_STATUS.PENDING;
    case "running":
      return UI_STATUS.RUNNING;
    case "completed":
      return UI_STATUS.COMPLETED;
    case "failed":
      return UI_STATUS.FAILED;
    default:
      return UI_STATUS.IDLE;
  }
}

function toStatusLabel(uiStatus) {
  switch (uiStatus) {
    case UI_STATUS.PENDING:
      return "В очереди";
    case UI_STATUS.RUNNING:
      return "Генерация идёт";
    case UI_STATUS.COMPLETED:
      return "Готово";
    case UI_STATUS.FAILED:
      return "Ошибка генерации";
    default:
      return "Нет активной генерации";
  }
}

function classifyError(message) {
  if (!message) {
    return null;
  }

  const text = message.toLowerCase();
  if (text.includes("validation") || text.includes("невалид")) {
    return ERROR_KIND.VALIDATION;
  }
  if (text.includes("нет_решения") || text.includes("не удалось составить")) {
    return ERROR_KIND.NO_SOLUTION;
  }
  if (text.includes("500") || text.includes("timeout") || text.includes("network")) {
    return ERROR_KIND.SERVER;
  }

  return ERROR_KIND.UNKNOWN;
}

export function flattenSchedule(schedulePayload) {
  if (!schedulePayload || typeof schedulePayload !== "object") {
    return [];
  }

  const rows = [];
  Object.entries(schedulePayload).forEach(([slot, lessons]) => {
    const { day, pair } = parseSlot(slot);
    if (!Array.isArray(lessons)) {
      return;
    }

    lessons.forEach((lesson) => {
      rows.push({
        slot,
        day,
        pair,
        auditorium: lesson.auditorium ?? "—",
        group: lesson.group_name ?? lesson.group ?? "—",
        subject: lesson.subject ?? "—",
        teacher: lesson.teacher ?? "—",
      });
    });
  });

  rows.sort((left, right) => {
    const dayDiff = (DAY_ORDER[left.day] ?? 99) - (DAY_ORDER[right.day] ?? 99);
    if (dayDiff !== 0) {
      return dayDiff;
    }
    if (left.pair !== right.pair) {
      return left.pair - right.pair;
    }
    return String(left.auditorium).localeCompare(String(right.auditorium));
  });

  return rows;
}

export function buildScheduleViewModel(job, scheduleResponse) {
  if (!job && !scheduleResponse) {
    return { ...EMPTY_VIEW_MODEL };
  }

  const backendStatus = scheduleResponse?.status ?? job?.status;
  const uiStatus = toUiStatus(backendStatus);
  const schedulePayload = scheduleResponse?.schedule?.schedule;
  const errorMessage = scheduleResponse?.error_message ?? null;

  return {
    jobId: scheduleResponse?.job_id ?? job?.id ?? null,
    status: uiStatus,
    statusLabel: toStatusLabel(uiStatus),
    updatedAt: job?.completed_at ?? job?.created_at ?? null,
    rows: flattenSchedule(schedulePayload),
    error: errorMessage
      ? {
          kind: classifyError(errorMessage),
          message: errorMessage,
        }
      : null,
  };
}

window.scheduleUiModel = {
  DAY_ORDER,
  UI_STATUS,
  ERROR_KIND,
  EMPTY_VIEW_MODEL,
  flattenSchedule,
  buildScheduleViewModel,
};