import { expect, test } from "@playwright/test";
import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

let backendProcess = null;
const repoRoot = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "..",
  "..",
);

async function waitForBackendHealth(timeoutMs = 30000) {
  const deadline = Date.now() + timeoutMs;

  while (Date.now() < deadline) {
    try {
      const response = await fetch("http://127.0.0.1:8000/health");
      if (response.ok) {
        return;
      }
    } catch {
      // Ignore startup races while the backend bootstraps.
    }

    await new Promise((resolve) => setTimeout(resolve, 500));
  }

  throw new Error("Backend did not become ready in time");
}

test.beforeAll(async () => {
  backendProcess = spawn("python", [
    "-m",
    "uvicorn",
    "backend.main:app",
    "--host",
    "127.0.0.1",
    "--port",
    "8000",
  ], {
    cwd: repoRoot,
  });

  backendProcess.stderr?.on("data", (chunk) => {
    process.stderr.write(chunk);
  });

  await waitForBackendHealth();
});

test.afterAll(async () => {
  if (backendProcess && !backendProcess.killed) {
    backendProcess.kill();
  }
});

test("UI smoke: load -> generate -> render result", async ({ page }) => {
  await page.route("http://127.0.0.1:8000/api/generate", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        job_id: 701,
        status: "pending",
        message: "Генерация запущена",
      }),
    });
  });

  await page.route("http://127.0.0.1:8000/api/jobs", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([
        {
          id: 701,
          status: "completed",
          created_at: "2026-05-17T12:00:00Z",
          completed_at: "2026-05-17T12:00:02Z",
          max_search_steps: 200000,
        },
      ]),
    });
  });

  await page.route("http://127.0.0.1:8000/api/schedule/701", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        job_id: 701,
        status: "completed",
        schedule: {
          solve_status: "успех",
          search_steps: 9,
          schedule: {
            Mon_1: [
              {
                auditorium: "A-101",
                group: "G1",
                group_name: "ИВТ-21",
                subject: "Математика",
                teacher: "Иванова И.И.",
              },
            ],
            Tue_2: [
              {
                auditorium: "B-202",
                group: "G2",
                group_name: "ИВТ-22",
                subject: "Физика",
                teacher: "Петров П.П.",
              },
            ],
          },
        },
        error: null,
        error_message: null,
      }),
    });
  });

  await page.goto("/index.html");

  await expect(page.locator("#generate-btn")).toBeVisible();
  await expect(page.locator("#schedule-table-body")).toBeVisible();

  await page.click("#generate-btn");

  await expect(page.locator("#control-hint")).toContainText("Job #");
  await page.waitForFunction(
    () => document.querySelectorAll("#schedule-table-body tr").length > 0,
  );
  await expect(page.locator("#render-time-value")).toContainText("Время рендера:");
});

test("UI smoke: no_solution shows a friendly error", async ({ page }) => {
  await page.route("http://127.0.0.1:8000/api/generate", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        job_id: 801,
        status: "pending",
        message: "Генерация запущена",
      }),
    });
  });

  await page.route("http://127.0.0.1:8000/api/jobs", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([
        {
          id: 801,
          status: "failed",
          created_at: "2026-05-17T12:00:00Z",
          completed_at: "2026-05-17T12:00:02Z",
          max_search_steps: 200000,
        },
      ]),
    });
  });

  await page.route("http://127.0.0.1:8000/api/schedule/801", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        job_id: 801,
        status: "failed",
        schedule: {
          solve_status: "нет_решения",
          schedule: {},
        },
        error_message: "Не удалось составить расписание при текущих ограничениях.",
        error_status: 500,
      }),
    });
  });

  await page.goto("/index.html");
  await page.click("#generate-btn");

  await expect(page.locator("#global-error-banner")).toBeVisible();
  await expect(page.locator("#global-error-title")).toContainText("Решение не найдено");
  await expect(page.locator("#global-error-message")).toContainText("Не удалось составить расписание");
});

test("UI smoke: limit_reached shows a clear error", async ({ page }) => {
  await page.route("http://127.0.0.1:8000/api/generate", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        job_id: 802,
        status: "pending",
        message: "Генерация запущена",
      }),
    });
  });

  await page.route("http://127.0.0.1:8000/api/jobs", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([
        {
          id: 802,
          status: "failed",
          created_at: "2026-05-17T12:00:00Z",
          completed_at: "2026-05-17T12:00:02Z",
          max_search_steps: 200000,
        },
      ]),
    });
  });

  await page.route("http://127.0.0.1:8000/api/schedule/802", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        job_id: 802,
        status: "failed",
        schedule: {
          solve_status: "лимит_поиска_достигнут",
          schedule: {},
        },
        error_message: "Достигнут лимит поиска при генерации.",
        error_status: 500,
      }),
    });
  });

  await page.goto("/index.html");
  await page.click("#generate-btn");

  await expect(page.locator("#global-error-banner")).toBeVisible();
  await expect(page.locator("#global-error-title")).toContainText("Достигнут лимит поиска");
  await expect(page.locator("#global-error-message")).toContainText("Достигнут лимит поиска");

  await expect(page.locator("#render-time-value")).toContainText("Время рендера:");
});

