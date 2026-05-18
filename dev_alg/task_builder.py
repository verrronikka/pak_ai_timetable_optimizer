from __future__ import annotations

import json
from pathlib import Path
from typing import List, Tuple, Union

from models import Auditorium, Group, LessonTask, Subject, Teacher
from paths import DATA

DEFAULT_DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]
DEFAULT_PAIRS_PER_DAY = 4

PathLike = Union[str, Path]


def build_lesson_tasks(
    teachers: List[Teacher],
    groups: List[Group],
    subjects: List[Subject],
) -> List[LessonTask]:
    """Одна задача на каждый час: предмет × группа × hours_per_week."""
    if not teachers or not groups or not subjects:
        return []

    tasks: List[LessonTask] = []
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
    return tasks


def build_time_slots(
    days: List[str] | None = None,
    pairs_per_day: int = DEFAULT_PAIRS_PER_DAY,
) -> List[str]:
    days = days or list(DEFAULT_DAYS)
    return [f"{day}_{pair}" for day in days for pair in range(1, pairs_per_day + 1)]


def time_slots_from_auditoriums(
    auditoriums: List[Auditorium],
    pairs_per_day: int = DEFAULT_PAIRS_PER_DAY,
) -> List[str]:
    days = sorted({day for aud in auditoriums for day in aud.available_days})
    return build_time_slots(days, pairs_per_day)


def load_entities_from_dir(
    data_dir: PathLike,
) -> Tuple[List[Teacher], List[Group], List[Auditorium], List[Subject]]:
    base = Path(data_dir)

    def read_json(name: str) -> list:
        with open(base / name, encoding="utf-8") as handle:
            return json.load(handle)

    teachers = [
        Teacher(
            t["id"],
            t["name"],
            t["max_hours"],
            t["available_days"],
        )
        for t in read_json("teachers.json")
    ]
    groups = [
        Group(g["id"], g["name"], g["student_count"]) for g in read_json("groups.json")
    ]
    auditoriums = [
        Auditorium(
            a["id"],
            a["capacity"],
            a["type"],
            a["available_days"],
        )
        for a in read_json("auditoriums.json")
    ]
    subjects = [
        Subject(
            s["id"],
            s["name"],
            s["hours_per_week"],
            s["required_auditorium_type"],
            s["is_lecture"],
        )
        for s in read_json("subjects.json")
    ]
    return teachers, groups, auditoriums, subjects


def load_dataset(
    data_dir: PathLike | None = None,
    pairs_per_day: int = DEFAULT_PAIRS_PER_DAY,
) -> Tuple[List[LessonTask], List[Auditorium], List[str]]:
    base = Path(data_dir) if data_dir is not None else DATA
    teachers, groups, auditoriums, subjects = load_entities_from_dir(base)
    tasks = build_lesson_tasks(teachers, groups, subjects)
    time_slots = time_slots_from_auditoriums(auditoriums, pairs_per_day)
    return tasks, auditoriums, time_slots
