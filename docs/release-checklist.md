# Release checklist

Перед релизом и merge в `main` проверь:

## Код и тесты
- [ ] `backend/tests/test_api.py` и `backend/tests/test_config.py` проходят локально.
- [ ] Frontend открывается без ошибок в консоли браузера.
- [ ] Smoke-сценарии `?demo=ready`, `?demo=validation`, `?demo=limit`, `?demo=error` работают как ожидается.

## Контракты
- [ ] `backend/solver_contraints.json` синхронизирован с README и frontend-подсказкой.
- [ ] `DEFAULT_MAX_SEARCH_STEPS` подтверждён и не захардкожен в новых местах.
- [ ] Ошибки `validation_error`, `no_solution`, `limit_reached`, `server_error`, `404` проверены.

## Репозиторий
- [ ] `timetable.db` не попадает в коммит.
- [ ] Локальные `.env` и временные артефакты игнорируются.
- [ ] `README.md` и отчёты не противоречат текущему состоянию кода.

## CI
- [ ] GitHub Actions smoke-check проходит на актуальной ветке.
- [ ] Backend API tests проходят в CI.
- [ ] Frontend static smoke-check проходит в CI.
