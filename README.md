# AI Timetable Optimizer

## Участники команды

- Вероника Алпатова - DevOps и Team Lead
- Екатерина Юдина - Backend
- Машковцева Анастасия - Fullstack
- Шелестов Даниил - ML и Algorithms

## Pre-commit хуки для команды

Важно: файлы конфигурации хуков хранятся в репозитории и приходят после
git pull, но установка хука выполняется вручную!

### Инструкция по установке

1. Установить зависимости:
   - python -m pip install pre-commit ruff
2. Установить git-хук в этом репозитории:
   - python -m pre_commit install
3. Опционально запустить полную проверку после pull:
   - python -m pre_commit run --all-files

После этой настройки проверки и автоформатирование запускаются автоматически
перед каждым коммитом.

## Модель данных

В проекте уже выделены основные сущности предметной области:

- `Teacher` - преподаватель. Хранит `id`, `name`, `max_hours` и список
   доступных дней `available_days`.
- `Group` - учебная группа. Хранит `id`, `name` и количество студентов
   `student_count`.
- `Auditorium` - аудитория. Хранит `id`, `capacity`, тип аудитории `type`
   и список доступных дней `available_days`.
- `Subject` - дисциплина. Хранит `id`, `name`, нагрузку в неделю
   `hours_per_week`, требуемый тип аудитории `required_auditorium_type`
   и признак лекции `is_lecture`.
- `LessonTask` - учебная задача на расписание. Связывает преподавателя,
   группу и дисциплину.

## Контракт входа/выхода

### Входные данные

Программа ожидает четыре JSON файла в папке `dev_alg/data/`:

- `teachers.json` — массив объектов преподавателей с полями:
  `id`, `name`, `max_hours`, `available_days`
- `groups.json` — массив объектов групп с полями:
  `id`, `name`, `student_count`
- `auditoriums.json` — массив объектов аудиторий с полями:
  `id`, `capacity`, `type`, `available_days`
- `subjects.json` — массив объектов дисциплин с полями:
  `id`, `name`, `hours_per_week`, `required_auditorium_type`, `is_lecture`

### Выходные данные

Программа генерирует расписание:

1. Выводит его в консоль в формате:

```text
<день_недели> <номер_пары>:
  Auditorium: <аудитория> | <группа> | <дисциплина> | Teacher: <преподаватель>
  ...
```

1. Сохраняет его в файл `reports/generated/schedule_output.json`.

1. Формирует читаемый отчет
   `reports/generated/schedule_report.md` в виде таблицы.

Каждая запись содержит: временной слот, аудиторию, группу,
дисциплину и преподавателя.

### Запуск

```bash
cd dev_alg
python test.py
```

Примеры параметров:

```bash
python test.py --output-format markdown
python test.py --output-format both --max-search-steps 300000
```

Процесс работы программы:

1. Загружает примеры данных
2. Генерирует расписание без конфликтов
3. Выводит результат в консоль
4. Сохраняет результат в JSON файл

## Валидатор расписания

Валидатор проверяет:

1. Доступность преподавателя по дню недели
2. Доступность аудитории по дню недели
3. Вместимость аудитории относительно размера группы
4. Соответствие типа аудитории требованиям дисциплины
5. Ограничение нагрузки преподавателя (`max_hours`)
6. Коллизии в одном временном слоте (аудитория, преподаватель, группа)

Интерфейс валидатора:

- Возвращает `ValidationResult(is_valid: bool, reason: str)`
- При успехе: `reason == "OK"`
- При ошибке: код причины (`TEACHER_DAY_UNAVAILABLE`,
  `AUDITORIUM_DAY_UNAVAILABLE`, `AUDITORIUM_CAPACITY_EXCEEDED`,
  `AUDITORIUM_TYPE_MISMATCH`, `TEACHER_HOURS_LIMIT_REACHED`,
  `SCHEDULE_CONFLICT`)

Тесты правил находятся в `dev_alg/tests/test_validator.py`.

## Solver

Solver реализован в `dev_alg/schedule_generator.py`.

Что делает solver:

1. Сортирует задачи от более ограниченных к менее ограниченным
2. Использует backtracking для построения полного расписания
3. Применяет MRV-эвристику (выбор задачи с минимальным числом кандидатов)
4. Ограничивает глубину/объем поиска параметром `max_search_steps`

Параметры запуска:

- `--max-search-steps` (по умолчанию: `200000`) задает лимит шагов поиска.

Контракт результата:

- При успехе `generate()` возвращает словарь расписания и
  `solve_status == "успех"`
- При достижении лимита возвращает `None` и
   `solve_status == "лимит_поиска_достигнут"`
- При отсутствии решения возвращает `None` и
   `solve_status == "нет_решения"`

Тесты решателя находятся в `dev_alg/tests/test_solver.py`.

## Читаемый вывод

Модуль `dev_alg/output_formatter.py` формирует markdown-отчет с
удобной таблицей по дням, парам, аудиториям, группам, дисциплинам и
преподавателям.

Поддерживаемые форматы сохранения через `--output-format`:

- `json`: только JSON файл `schedule_output.json`
- `markdown`: только markdown-отчет `schedule_report.md`
- `both`: JSON и markdown

При неуспешной генерации также создается markdown-отчет с причиной,
статусом и статистикой поиска.

## Frontend

В репозитории есть MVP интерфейс просмотра расписания и статуса генерации.
Экран расположен в папке `frontend/` и работает без сборщика (plain HTML/CSS/JS).

Что уже умеет фронтенд:

1. Запускает генерацию через `POST /api/generate`.
2. Дожидается результата job и показывает актуальный статус.
3. Загружает и отображает расписание в таблице.
4. Показывает ошибки валидации, отсутствия решения и серверные ошибки.

### Данные для generate

По умолчанию фронтенд пытается собрать payload из файлов:

- `dev_alg/data/teachers.json`
- `dev_alg/data/groups.json`
- `dev_alg/data/auditoriums.json`
- `dev_alg/data/subjects.json`

Если эти файлы недоступны, используется резервный встроенный payload.

### Локальный запуск backend + frontend

1. Запустить API:

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

1. В отдельном терминале поднять простой static-server из корня репозитория:

```bash
python -m http.server 5500
```

1. Открыть страницу:

```text
http://127.0.0.1:5500/frontend/index.html
```

### Быстрый smoke-check

1. Нажать кнопку `Сгенерировать`.
2. Дождаться финального статуса (`Готово` или ошибка).
3. Убедиться, что таблица заполнилась (для тестовых data обычно 24 строки).
4. Нажать `Обновить` и проверить, что данные синхронизируются с последним job.
5. Проверить, что при ошибках показывается красный баннер с понятной причиной.

### Основные frontend модули

- `frontend/api-client.js` — HTTP клиент для backend API.
- `frontend/schedule-actions.js` — действия UI (generate, refresh, reset, polling).
- `frontend/schedule-state.js` — общее состояние экрана.
- `frontend/schedule-model.js` — преобразование API ответа в view-model.
- `frontend/schedule-table.js` — рендер таблицы расписания.
- `frontend/schedule-status.js` — рендер статуса и времени обновления.
- `frontend/schedule-error-banner.js` — глобальный баннер ошибок.
