const DEFAULT_BASE_URL = "http://127.0.0.1:8000";

function joinUrl(baseUrl, path) {
  const normalizedBase = baseUrl.endsWith("/")
    ? baseUrl.slice(0, -1)
    : baseUrl;
  return `${normalizedBase}${path}`;
}

async function parseJsonSafe(response) {
  const text = await response.text();
  if (!text) {
    return null;
  }

  try {
    return JSON.parse(text);
  } catch {
    return { raw: text };
  }
}

function buildApiError({ method, path, status, payload }) {
  const detail = payload?.detail;
  let detailMessage = "";
  if (typeof detail === "string") {
    detailMessage = detail;
  } else if (Array.isArray(detail)) {
    detailMessage = detail
      .map((item) => {
        const location = Array.isArray(item?.loc) ? item.loc.join(".") : "field";
        const itemMessage = item?.msg ?? "validation error";
        return `${location}: ${itemMessage}`;
      })
      .join("; ");
  }

  const message = detailMessage
    ? `HTTP ${status}: ${detailMessage}`
    : `HTTP ${status}: API ${method} ${path} failed`;

  const error = new Error(message);
  error.name = "ApiClientError";
  error.method = method;
  error.path = path;
  error.status = status;
  error.payload = payload;
  return error;
}

export class ApiClient {
  constructor({ baseUrl = DEFAULT_BASE_URL } = {}) {
    this.baseUrl = baseUrl;
  }

  async request(path, { method = "GET", body, headers } = {}) {
    const url = joinUrl(this.baseUrl, path);

    let response;
    try {
      response = await fetch(url, {
        method,
        headers: {
          Accept: "application/json",
          ...(body ? { "Content-Type": "application/json" } : {}),
          ...(headers ?? {}),
        },
        body: body ? JSON.stringify(body) : undefined,
      });
    } catch (error) {
      const networkError = new Error(
        "HTTP 0: Сетевая ошибка: backend недоступен или не отвечает"
      );
      networkError.name = "ApiClientError";
      networkError.method = method;
      networkError.path = path;
      networkError.status = 0;
      networkError.payload = null;
      networkError.cause = error;
      throw networkError;
    }

    const payload = await parseJsonSafe(response);
    if (!response.ok) {
      throw buildApiError({
        method,
        path,
        status: response.status,
        payload,
      });
    }

    return payload;
  }

  async health() {
    return this.request("/health");
  }

  async generate(scheduleRequest) {
    return this.request("/api/generate", {
      method: "POST",
      body: scheduleRequest,
    });
  }

  async getSchedule(jobId) {
    return this.request(`/api/schedule/${jobId}`);
  }

  async listJobs() {
    const payload = await this.request("/api/jobs");
    return Array.isArray(payload) ? payload : [];
  }

  async getLatestJob() {
    const jobs = await this.listJobs();
    return jobs.length ? jobs[0] : null;
  }

  async deleteJob(jobId) {
    return this.request(`/api/schedule/${jobId}`, { method: "DELETE" });
  }
}

export function createApiClient(config) {
  return new ApiClient(config);
}
