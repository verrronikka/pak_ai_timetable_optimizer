import argparse
import json

from output_formatter import (
    save_failure_to_markdown,
    save_schedule_to_markdown,
)
from paths import (
    SCHEDULE_JSON,
    SCHEDULE_MARKDOWN,
    artifact,
    ensure_artifacts_dir,
)
from schedule_generator import ScheduleGenerator
from task_builder import build_time_slots, load_dataset


def schedule_to_json(schedule) -> dict:
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
    return schedule_data


def save_schedule_to_json(schedule, output_file):
    with open(output_file, "w", encoding="utf-8") as handle:
        json.dump(schedule_to_json(schedule), handle, ensure_ascii=False, indent=2)
    print(f"Schedule saved to: {output_file.name}")


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
    ensure_artifacts_dir()
    json_path = artifact(SCHEDULE_JSON)
    markdown_path = artifact(SCHEDULE_MARKDOWN)

    try:
        tasks, auditoriums, _ = load_dataset()
    except FileNotFoundError as error:
        print(f"Error loading data: {error}")
        return

    generator = ScheduleGenerator(
        tasks,
        build_time_slots(),
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
            save_schedule_to_json(result, json_path)
        if output_format in ("markdown", "both"):
            save_schedule_to_markdown(result, output_file=str(markdown_path))
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
            with open(json_path, "w", encoding="utf-8") as handle:
                json.dump(failure_data, handle, ensure_ascii=False, indent=2)
            print(f"Failure details saved to: {json_path.name}")
        if output_format in ("markdown", "both"):
            save_failure_to_markdown(
                output_file=str(markdown_path),
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
