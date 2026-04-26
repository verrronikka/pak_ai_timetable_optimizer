import { ERROR_KIND } from "./schedule-model.js";
import { getCurrentViewModel, subscribeViewModel } from "./schedule-state.js";

const banner = document.getElementById("global-error-banner");
const bannerTitle = document.getElementById("global-error-title");
const bannerMessage = document.getElementById("global-error-message");

const TITLE_BY_KIND = {
  [ERROR_KIND.VALIDATION]: "Ошибка входных данных",
  [ERROR_KIND.NO_SOLUTION]: "Решение не найдено",
  [ERROR_KIND.SERVER]: "Ошибка сервиса",
  [ERROR_KIND.UNKNOWN]: "Ошибка генерации",
};

function renderErrorBanner(viewModel) {
  if (!viewModel.error) {
    banner.classList.add("is-hidden");
    return;
  }

  const errorTitle = TITLE_BY_KIND[viewModel.error.kind] ?? "Ошибка генерации";
  bannerTitle.textContent = errorTitle;
  bannerMessage.textContent = viewModel.error.message;
  banner.classList.remove("is-hidden");
}

renderErrorBanner(getCurrentViewModel());
subscribeViewModel(renderErrorBanner);