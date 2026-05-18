"""
Генератор бенчмарк-наборов с гарантией разрешимости (constructive placement).

Размер tier задаётся как teachers × groups (число сущностей).
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from paths import BENCHMARKS, relative_to_root  # noqa: E402

from models import Auditorium, Group, LessonTask, Subject, Teacher  # noqa: E402
from schedule_generator import ScheduleGenerator  # noqa: E402
from task_builder import DEFAULT_DAYS, build_lesson_tasks, build_time_slots  # noqa: E402

AUDITORIUM_TYPES = ("lecture", "practice", "lab")
SUBJECT_TEMPLATES = [
    ("Mathematics", "lecture", True),
    ("Algorithms", "practice", False),
    ("Databases", "practice", False),
    ("English", "lecture", True),
]


@dataclass(frozen=True)
class TierSpec:
    name: str
    teachers: int
    groups: int
    subject_count: int
    hours_per_week: int
    pairs_per_day: int
    auditorium_multiplier: int


TIER_SPECS: Dict[str, TierSpec] = {
    "tiny": TierSpec("tiny", 2, 2, 2, 2, 4, 2),
    "small": TierSpec("small", 4, 4, 3, 2, 4, 2),
    "medium": TierSpec("medium", 8, 8, 4, 2, 5, 3),
    "large": TierSpec("large", 12, 12, 4, 2, 6, 4),
}


def _write_json(path: Path, payload: list) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def _build_entities(spec: TierSpec, seed: int) -> Tuple[
    List[Teacher],
    List[Group],
    List[Auditorium],
    List[Subject],
    list,
    list,
    list,
    list,
]:
    rng = random.Random(seed)
    days = list(DEFAULT_DAYS)

    teachers = [
        {
            "id": f"t{i}",
            "name": f"Teacher {i}",
            "max_hours": 40,
            "available_days": days,
        }
        for i in range(1, spec.teachers + 1)
    ]

    groups = [
        {
            "id": f"g{i}",
            "name": f"Group {i}",
            "student_count": rng.randint(20, 28),
        }
        for i in range(1, spec.groups + 1)
    ]

    subjects = []
    for idx, template in enumerate(SUBJECT_TEMPLATES[: spec.subject_count], start=1):
        name, aud_type, is_lecture = template
        subjects.append(
            {
                "id": f"s{idx}",
                "name": name,
                "hours_per_week": spec.hours_per_week,
                "required_auditorium_type": aud_type,
                "is_lecture": is_lecture,
            }
        )

    auditoriums = []
    aud_idx = 1
    for aud_type in AUDITORIUM_TYPES:
        for _ in range(spec.auditorium_multiplier):
            auditoriums.append(
                {
                    "id": f"a{aud_idx}",
                    "capacity": 60,
                    "type": aud_type,
                    "available_days": days,
                }
            )
            aud_idx += 1

    teacher_objs = [
        Teacher(t["id"], t["name"], t["max_hours"], t["available_days"])
        for t in teachers
    ]
    group_objs = [Group(g["id"], g["name"], g["student_count"]) for g in groups]
    aud_objs = [
        Auditorium(a["id"], a["capacity"], a["type"], a["available_days"])
        for a in auditoriums
    ]
    subject_objs = [
        Subject(
            s["id"],
            s["name"],
            s["hours_per_week"],
            s["required_auditorium_type"],
            s["is_lecture"],
        )
        for s in subjects
    ]
    return (
        teacher_objs,
        group_objs,
        aud_objs,
        subject_objs,
        teachers,
        groups,
        auditoriums,
        subjects,
    )


def constructively_place(
    tasks: List[LessonTask],
    auditoriums: List[Auditorium],
    time_slots: List[str],
) -> bool:
    schedule: Dict[str, Dict[str, LessonTask]] = {}
    teacher_hours: Dict[str, int] = {}
    generator = ScheduleGenerator(
        tasks=[],
        time_slots=time_slots,
        auditoriums=auditoriums,
    )

    ordered = sorted(
        tasks,
        key=lambda task: (
            len(task.teacher.available_days),
            task.subject.required_auditorium_type,
            -task.group.student_count,
        ),
    )

    for task in ordered:
        placed = False
        for time_slot in time_slots:
            for aud in auditoriums:
                generator.schedule = schedule
                generator.teacher_hours = teacher_hours
                if generator._is_valid(task, time_slot, aud):
                    generator._place(task, time_slot, aud.id)
                    schedule = generator.schedule
                    teacher_hours = generator.teacher_hours
                    placed = True
                    break
            if placed:
                break
        if not placed:
            return False
    return True


def generate_tier(
    tier: str,
    seed: int,
    output_root: Path,
    max_verify_steps: int,
) -> dict:
    if tier not in TIER_SPECS:
        raise ValueError(f"Unknown tier: {tier}. Choose from: {', '.join(TIER_SPECS)}")

    spec = TIER_SPECS[tier]
    (
        teacher_objs,
        group_objs,
        aud_objs,
        subject_objs,
        teachers_json,
        groups_json,
        auditoriums_json,
        subjects_json,
    ) = _build_entities(spec, seed)

    tasks = build_lesson_tasks(teacher_objs, group_objs, subject_objs)
    time_slots = build_time_slots(DEFAULT_DAYS, spec.pairs_per_day)

    if not constructively_place(tasks, aud_objs, time_slots):
        raise RuntimeError(
            f"Constructive placement failed for tier={tier}. "
            "Increase pairs_per_day or auditorium_multiplier."
        )

    tier_dir = output_root / tier
    tier_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "tier": tier,
        "seed": seed,
        "teachers": spec.teachers,
        "groups": spec.groups,
        "teachers_x_groups": spec.teachers * spec.groups,
        "task_count": len(tasks),
        "time_slot_count": len(time_slots),
        "pairs_per_day": spec.pairs_per_day,
        "dataset_ref": relative_to_root(tier_dir),
    }
    _write_json(tier_dir / "teachers.json", teachers_json)
    _write_json(tier_dir / "groups.json", groups_json)
    _write_json(tier_dir / "auditoriums.json", auditoriums_json)
    _write_json(tier_dir / "subjects.json", subjects_json)
    _write_json(tier_dir / "meta.json", meta)

    verified = False
    search_steps = 0
    solve_status = "skipped"
    if max_verify_steps > 0:
        solver = ScheduleGenerator(
            tasks=tasks,
            time_slots=time_slots,
            auditoriums=aud_objs,
            max_search_steps=max_verify_steps,
        )
        result = solver.generate()
        verified = result is not None
        search_steps = solver.search_steps
        solve_status = solver.solve_status
        if not verified:
            raise RuntimeError(
                f"Solver verification failed for tier={tier}: {solve_status}"
            )

    return {
        **meta,
        "verified": verified,
        "verify_search_steps": search_steps,
        "verify_status": solve_status,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate solvable benchmark datasets (teachers × groups)."
    )
    parser.add_argument(
        "--tier",
        choices=list(TIER_SPECS.keys()) + ["all"],
        default="all",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Корень tier-папок (по умолчанию data/benchmarks)",
    )
    parser.add_argument("--verify-steps", type=int, default=500_000)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_root = args.output_dir or BENCHMARKS
    tiers = list(TIER_SPECS.keys()) if args.tier == "all" else [args.tier]
    results = []
    for tier_name in tiers:
        print(f"Generating tier={tier_name} seed={args.seed} ...")
        info = generate_tier(
            tier=tier_name,
            seed=args.seed,
            output_root=output_root,
            max_verify_steps=args.verify_steps,
        )
        results.append(info)
        print(
            f"  tasks={info['task_count']} slots={info['time_slot_count']} "
            f"verify_steps={info.get('verify_search_steps', 'n/a')}"
        )

    summary_path = output_root / "generation_summary.json"
    with open(summary_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, ensure_ascii=False, indent=2)
    print(f"Summary written to {summary_path.name}")


if __name__ == "__main__":
    main()
