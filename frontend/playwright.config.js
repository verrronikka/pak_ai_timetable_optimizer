import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  testMatch: "**/ui-smoke.spec.js",
  timeout: 45_000,
  retries: 0,
  use: {
    baseURL: "http://127.0.0.1:4173",
    headless: true,
  },
  webServer: {
    command: "python -m http.server 4173 --bind 127.0.0.1",
    port: 4173,
    reuseExistingServer: true,
    timeout: 30_000,
  },
});
