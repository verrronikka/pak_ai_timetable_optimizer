import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  testMatch: "**/ui-smoke.spec.js",
  timeout: 45_000,
  retries: 0,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: "http://127.0.0.1:4173",
    headless: true,
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
    video: "retain-on-failure",
  },
  outputDir: "./test-results",
  webServer: {
    command: "python -m http.server 4173 --bind 127.0.0.1",
    port: 4173,
    reuseExistingServer: true,
    timeout: 30_000,
  },
});
