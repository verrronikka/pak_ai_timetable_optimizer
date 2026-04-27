import { buildScheduleViewModel } from "./schedule-model.js";
import { getDemoPayloadByScenario, getDemoScenario } from "./demo-data.js";

const listeners = new Set();

let currentScenario = getDemoScenario();
let currentViewModel = buildViewModelByScenario(currentScenario);

function buildViewModelByScenario(scenario) {
  const { demoJob, demoScheduleResponse } = getDemoPayloadByScenario(scenario);
  return buildScheduleViewModel(demoJob, demoScheduleResponse);
}

function syncUrlScenario(scenario) {
  const url = new URL(window.location.href);
  if (scenario === "ready") {
    url.searchParams.delete("demo");
  } else {
    url.searchParams.set("demo", scenario);
  }
  window.history.replaceState({}, "", url);
}

function notify() {
  listeners.forEach((listener) => listener(currentViewModel));
}

function clearDemoQueryParam() {
  const url = new URL(window.location.href);
  if (!url.searchParams.has("demo")) {
    return;
  }
  url.searchParams.delete("demo");
  window.history.replaceState({}, "", url);
}

export function getCurrentViewModel() {
  return currentViewModel;
}

export function getCurrentScenario() {
  return currentScenario;
}

export function subscribeViewModel(listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function setScenario(nextScenario) {
  currentScenario = nextScenario;
  currentViewModel = buildViewModelByScenario(nextScenario);
  syncUrlScenario(nextScenario);
  notify();
}

export function setApiSnapshot({ job = null, scheduleResponse = null } = {}) {
  currentScenario = "api";
  currentViewModel = buildScheduleViewModel(job, scheduleResponse);
  clearDemoQueryParam();
  notify();
}