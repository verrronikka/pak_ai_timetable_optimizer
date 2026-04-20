import argparse
import json
import os

from models import Auditorium, Group, LessonTask, Subject, Teacher
from output_formatter import (
    save_failure_to_markdown,
    save_schedule_to_markdown,
)
from schedule_generator import ScheduleGenerator


def load_data_from_json(data_dir: str = "data"):
    """Загружает данные из JSON файлов."""
    if data_dir == "data":
        data_dir = os.path.join(os.path.dirname(__file__), "data")

    teachers_data = []
    groups_data = []
    auditoriums_data = []
    subjects_data = []

    try:
        with open(
            os.path.join(data_dir, "teachers.json"), "r", encoding="utf-8"
        ) as f:
            teachers_data = json.load(f)
        with open(
            os.path.join(data_dir, "groups.json"), "r", encoding="utf-8"
        ) as f:
            groups_data = json.load(f)
        with open(
            os.path.join(data_dir, "auditoriums.json"), "r", encoding="utf-8"
        ) as f:
            auditoriums_data = json.load(f)
        with open(
            os.path.join(data_dir, "subjects.json"), "r", encoding="utf-8"
        ) as f:
            subjects_data = json.load(f)
    except FileNotFoundError as e:
        print(f"Error loading data: {e}")
        return None, None

    # Преобразуем JSON в объекты моделей
    teachers = [
        Teacher(t["id"], t["name"], t["max_hours"], t["available_days"])
        for t in teachers_data
    ]
    groups = [
        Group(g["id"], g["name"], g["student_count"]) for g in groups_data
    ]
    auditoriums = [
        Auditorium(
            a["id"],
            a["capacity"],
            a["type"],
            a["available_days"],
        )
        for a in auditoriums_data
    ]
    subjects = [
        Subject(
            s["id"],
            s["name"],
            s["hours_per_week"],
            s["required_auditorium_type"],
            s["is_lecture"],
        )
        for s in subjects_data
    ]

    # Генерируем задачи на расписание
    tasks = []
    task_id = 1
    for subj in subjects:
        for grp in groups:
            teacher = teachers[task_id % len(teachers)]
            for _ in range(subj.hours_per_week):
                tasks.append(
                    LessonTask(
                        id=f"task_{task_id}",
                        teacher=teacher,
                        group=grp,
                        subject=subj,
                    )
                )
                task_id += 1

    return tasks, auditoriums


def save_schedule_to_json(schedule, output_file: str = "schedule_output.json"):
    """Сохраняет расписание в JSON файл."""
    if output_file == "schedule_output.json":
        project_root = os.path.dirname(os.path.dirname(__file__))
        output_dir = os.path.join(project_root, "reports", "generated")
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, output_file)

    schedule_data = {}
    for ts, lessons in schedule.items():
        schedule_data[ts] = [
            {
                "auditorium": aud_id,
                "group": lesson.group.id,
                "group_name": lesson.group.name,
                "subject": lesson.subject.name,
                "teacher": lesson.teacher.name,
            }
            for aud_id, lesson in lessons.items()
        ]

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(schedule_data, f, ensure_ascii=False, indent=2)
    print(f"Schedule saved to: {output_file}")


def get_default_output_path() -> str:
    project_root = os.path.dirname(os.path.dirname(__file__))
    output_dir = os.path.join(project_root, "reports", "generated")
    os.makedirs(output_dir, exist_ok=True)
    return os.path.join(output_dir, "schedule_output.json")


def get_default_markdown_path() -> str:
    project_root = os.path.dirname(os.path.dirname(__file__))
    output_dir = os.path.join(project_root, "reports", "generated")
    os.makedirs(output_dir, exist_ok=True)
    return os.path.join(output_dir, "schedule_report.md")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Генерация учебного расписания"
    )
    parser.add_argument(
        "--max-search-steps",
        type=int,
        default=200000,
        help="Максимальное количество шагов backtracking",
    )
    parser.add_argument(
        "--output-format",
        choices=["json", "markdown", "both"],
        default="both",
        help="Формат выходного файла расписания",
    )
    return parser.parse_args()


def main(max_search_steps: int = 200000, output_format: str = "both"):
    tasks, auditoriums = load_data_from_json()
    if tasks is None or auditoriums is None:
        return

    output_file = get_default_output_path()
    markdown_file = get_default_markdown_path()

    days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    time_slots = [f"{day}_{p}" for day in days for p in range(1, 5)]

    generator = ScheduleGenerator(
        tasks,
        time_slots,
        auditoriums,
        max_search_steps=max_search_steps,
    )
    result = generator.generate()

    if result:
        print("\nTimetable is ready!\n")
        for ts in sorted(result.keys()):
            print(f"{ts.replace('_', ' ')}:")
            for aud_id, task in result[ts].items():
                print(
                    f"Auditorium: {aud_id} | "
                    f"{task.group.name} | "
                    f"{task.subject.name} | "
                    f"Teacher: {task.teacher.name}"
                )

        if output_format in ("json", "both"):
            save_schedule_to_json(result, output_file=output_file)
        if output_format in ("markdown", "both"):
            save_schedule_to_markdown(result, output_file=markdown_file)
    else:
        failure_data = {
            "status": "failed",
            "reason": (
                "Не удалось составить расписание при текущих ограничениях"
            ),
            "search_steps": generator.search_steps,
            "solve_status": generator.solve_status,
            "max_search_steps": max_search_steps,
        }
        if output_format in ("json", "both"):
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(failure_data, f, ensure_ascii=False, indent=2)
            print(f"Failure details saved to: {output_file}")
        if output_format in ("markdown", "both"):
            save_failure_to_markdown(
                output_file=markdown_file,
                reason=failure_data["reason"],
                search_steps=failure_data["search_steps"],
                solve_status=failure_data["solve_status"],
                max_search_steps=failure_data["max_search_steps"],
            )
        print(
            "Impossible to generate timetable! "
            "Try to extend number of auditoriums or time periods.\n"
        )


if __name__ == "__main__":
    args = parse_args()
    main(
        max_search_steps=args.max_search_steps,
        output_format=args.output_format,
    )
