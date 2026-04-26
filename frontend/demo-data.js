const READY_JOB = {
  id: 17,
  status: "completed",
  created_at: "2026-04-26T10:02:00Z",
  completed_at: "2026-04-26T10:02:04Z",
};

const IDLE_PAYLOAD = {
  demoJob: null,
  demoScheduleResponse: null,
};

const READY_RESPONSE = {
  job_id: 17,
  status: "completed",
  schedule: {
    schedule: {
      Mon_1: [
        {
          auditorium: "A-101",
          group: "G1",
          group_name: "ИВТ-21",
          subject: "Математика",
          teacher: "Иванова И.И.",
        },
        {
          auditorium: "B-207",
          group: "G2",
          group_name: "ПМИ-22",
          subject: "Физика",
          teacher: "Петров П.П.",
        },
      ],
      Tue_2: [
        {
          auditorium: "C-302",
          group: "G1",
          group_name: "ИВТ-21",
          subject: "Алгоритмы",
          teacher: "Сидоров С.С.",
        },
      ],
      Thu_3: [
        {
          auditorium: "Lab-4",
          group: "G3",
          group_name: "ПИ-23",
          subject: "Базы данных",
          teacher: "Кузнецова А.А.",
        },
      ],
    },
  },
  error_message: null,
};

const LOADING_JOB = {
  id: 18,
  status: "running",
  created_at: "2026-04-26T11:10:00Z",
  completed_at: null,
};

const LOADING_RESPONSE = {
  job_id: 18,
  status: "running",
  schedule: {
    schedule: {},
  },
  error_message: null,
};

const EMPTY_JOB = {
  id: 19,
  status: "completed",
  created_at: "2026-04-26T12:00:00Z",
  completed_at: "2026-04-26T12:00:05Z",
};

const EMPTY_RESPONSE = {
  job_id: 19,
  status: "completed",
  schedule: {
    schedule: {},
  },
  error_message: null,
};

const ERROR_JOB = {
  id: 20,
  status: "failed",
  created_at: "2026-04-26T12:30:00Z",
  completed_at: "2026-04-26T12:30:03Z",
};

const ERROR_RESPONSE = {
  job_id: 20,
  status: "failed",
  schedule: {
    schedule: {},
  },
  error_message: "Сервис генерации временно недоступен. Повторите попытку позже.",
};

export function getDemoScenario() {
  const params = new URLSearchParams(window.location.search);
  const scenario = params.get("demo");
  if (
    scenario === "idle" ||
    scenario === "loading" ||
    scenario === "empty" ||
    scenario === "error"
  ) {
    return scenario;
  }
  return "ready";
}

export function getDemoPayloadByScenario(scenario) {
  if (scenario === "idle") {
    return IDLE_PAYLOAD;
  }
  if (scenario === "loading") {
    return {
      demoJob: LOADING_JOB,
      demoScheduleResponse: LOADING_RESPONSE,
    };
  }
  if (scenario === "empty") {
    return {
      demoJob: EMPTY_JOB,
      demoScheduleResponse: EMPTY_RESPONSE,
    };
  }
  if (scenario === "error") {
    return {
      demoJob: ERROR_JOB,
      demoScheduleResponse: ERROR_RESPONSE,
    };
  }

  return {
    demoJob: READY_JOB,
    demoScheduleResponse: READY_RESPONSE,
  };
}

export function getDemoPayload() {
  return getDemoPayloadByScenario(getDemoScenario());
}