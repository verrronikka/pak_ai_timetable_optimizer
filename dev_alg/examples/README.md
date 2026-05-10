Примеры для демонстрации сценариев `no_solution` и `limit_reached`.

Файлы:
- `no_solution_input.json` — входные данные, в которых предмет требует `lab`, но аудитории только `lecture` → ожидается `нет_решения`.
- `limit_reached_input.json` — входные данные для демонстрации достижения лимита поиска; runner запускает `ScheduleGenerator` с `max_search_steps=0` чтобы принудительно получить `лимит_поиска_достигнут`.
- `run_examples.py` — небольшой скрипт, который загружает оба примера и печатает статусы.

Как запустить:

```bash
# из корня репозитория
python dev_alg/examples/run_examples.py
```

Ожидаемый вывод показывает статус решателя и флаги `search_steps`/`search_aborted`.
