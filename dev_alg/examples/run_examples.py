import json
from paths import ROOT, bootstrap

bootstrap()

EXAMPLES_DIR = ROOT / "examples"

from models import Auditorium, Group, LessonTask, Subject, Teacher
from schedule_generator import ScheduleGenerator


def load_input(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_objects(data):
    teachers = [
        Teacher(
            id=t["id"],
            name=t["name"],
            max_hours=t["max_hours"],
            available_days=t["available_days"],
        )
        for t in data["teachers"]
    ]
    groups = [
        Group(id=g["id"], name=g["name"], student_count=g["student_count"])
        for g in data["groups"]
    ]
    auditoriums = [
        Auditorium(
            id=a["id"],
            capacity=a["capacity"],
            type=a["type"],
            available_days=a["available_days"],
        )
        for a in data["auditoriums"]
    ]
    subjects = [
        Subject(
            id=s["id"],
            name=s["name"],
            hours_per_week=s["hours_per_week"],
            required_auditorium_type=s["required_auditorium_type"],
            is_lecture=s.get("is_lecture", False),
        )
        for s in data["subjects"]
    ]

    tasks = []
    for i, subj in enumerate(subjects):
        teacher = teachers[i % len(teachers)]
        group = groups[i % len(groups)]
        tasks.append(
            LessonTask(
                id=f"task_{i}", teacher=teacher, group=group, subject=subj
            )
        )

    days = sorted(
        {d for a in data["auditoriums"] for d in a["available_days"]}
    )
    time_slots = [f"{d}_{p}" for d in days for p in range(1, 5)]

    return tasks, auditoriums, time_slots


if __name__ == "__main__":
    data_ns = load_input(EXAMPLES_DIR / "no_solution_input.json")
    tasks_ns, auds_ns, slots_ns = build_objects(data_ns)
    solver_ns = ScheduleGenerator(
        tasks=tasks_ns,
        time_slots=slots_ns,
        auditoriums=auds_ns,
        max_search_steps=200000,
    )
    res_ns = solver_ns.generate()
    print("\n=== No-solution example ===")
    print("Status:", solver_ns.solve_status)
    print("Search steps:", solver_ns.search_steps)
    print("Result is None?:", res_ns is None)

    data_lr = load_input(EXAMPLES_DIR / "limit_reached_input.json")
    tasks_lr, auds_lr, slots_lr = build_objects(data_lr)
    solver_lr = ScheduleGenerator(
        tasks=tasks_lr,
        time_slots=slots_lr,
        auditoriums=auds_lr,
        max_search_steps=0,
    )
    res_lr = solver_lr.generate()
    print("\n=== Limit-reached example ===")
    print("Status:", solver_lr.solve_status)
    print("Search steps:", solver_lr.search_steps)
    print("Search aborted flag:", getattr(solver_lr, "search_aborted", False))
    print("Result is None?:", res_lr is None)
