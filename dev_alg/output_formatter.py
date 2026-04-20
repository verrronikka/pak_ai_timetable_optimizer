from datetime import datetime
from typing import Dict, List, Tuple

from models import LessonTask

DAY_ORDER = {"Mon": 1, "Tue": 2, "Wed": 3, "Thu": 4, "Fri": 5}


def _parse_slot(slot: str) -> Tuple[int, int]:
    day, pair = slot.split("_")
    return DAY_ORDER.get(day, 99), int(pair)


def build_markdown_schedule(schedule: Dict[str, Dict[str, LessonTask]]) -> str:
    """Собирает удобный markdown-отчет с таблицей расписания."""
    rows: List[Tuple[str, int, str, str, str, str]] = []

    for slot in sorted(schedule.keys(), key=_parse_slot):
        day, pair = slot.split("_")
        lessons = schedule[slot]
        for aud_id in sorted(lessons.keys()):
            lesson = lessons[aud_id]
            rows.append(
                (
                    day,
                    int(pair),
                    aud_id,
                    lesson.group.name,
                    lesson.subject.name,
                    lesson.teacher.name,
                )
            )

    lines = [
        "# Расписание занятий",
        "",
        f"Сформировано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "| День | Пара | Аудитория | Группа | Дисциплина | Преподаватель |",
        "| --- | --- | --- | --- | --- | --- |",
    ]

    if not rows:
        lines.append("| - | - | - | - | Нет занятий | - |")
    else:
        current_slot = None
        for day, pair, aud, group, subject, teacher in rows:
            slot_key = (day, pair)
            if slot_key == current_slot:
                day_col = ""
                pair_col = ""
            else:
                day_col = day
                pair_col = str(pair)
                current_slot = slot_key
            lines.append(
                f"| {day_col} | {pair_col} | {aud} | "
                f"{group} | {subject} | {teacher} |"
            )

    return "\n".join(lines) + "\n"


def build_markdown_failure(
    reason: str,
    search_steps: int,
    solve_status: str,
    max_search_steps: int,
) -> str:
    """Собирает markdown-отчет при неуспешной генерации."""
    lines = [
        "# Расписание не сформировано",
        "",
        f"Сформировано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f"- Статус: {solve_status}",
        f"- Причина: {reason}",
        f"- Шагов поиска: {search_steps}",
        f"- Лимит шагов: {max_search_steps}",
    ]
    return "\n".join(lines) + "\n"


def save_markdown_report(content: str, output_file: str) -> None:
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Markdown report saved to: {output_file}")


def save_schedule_to_markdown(
    schedule: Dict[str, Dict[str, LessonTask]], output_file: str
) -> None:
    report = build_markdown_schedule(schedule)
    save_markdown_report(report, output_file)


def save_failure_to_markdown(
    output_file: str,
    reason: str,
    search_steps: int,
    solve_status: str,
    max_search_steps: int,
) -> None:
    report = build_markdown_failure(
        reason=reason,
        search_steps=search_steps,
        solve_status=solve_status,
        max_search_steps=max_search_steps,
    )
    save_markdown_report(report, output_file)
