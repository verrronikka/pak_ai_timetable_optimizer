import { expect, test } from "@playwright/test";

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

  await expect(page.locator("#control-hint")).toContainText("Job #701");
  await expect(page.locator("#schedule-table-body tr")).toHaveCount(2);
  await expect(page.locator("#schedule-table-body")).toContainText("Математика");
  await expect(page.locator("#schedule-table-body")).toContainText("Физика");

  await expect(page.locator("#render-time-value")).toContainText("Время рендера:");
});

