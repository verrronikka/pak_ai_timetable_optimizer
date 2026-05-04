import unittest
import time
import tracemalloc
import json
import os
from pathlib import Path
from typing import List, Tuple, Dict, Any
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from models import Teacher, Group, Auditorium, Subject, LessonTask
from schedule_generator import ScheduleGenerator


def clean_json_data(data_list: List[dict]) -> List[dict]:
    cleaned = []
    for item in data_list:
        clean_item = {}
        for k, v in item.items():
            clean_key = k.strip()
            clean_val = v.strip() if isinstance(v, str) else v
            clean_item[clean_key] = clean_val
        cleaned.append(clean_item)
    return cleaned


def load_synthetic_dataset(dataset_dir: Path = None) -> Tuple[List[LessonTask], List[Auditorium], List[str]]:

    script_dir = Path(__file__).resolve().parent
    dataset_dir = script_dir.parent / "data"
    target_dir = None
    if (dataset_dir / "teachers.json").exists():
        target_dir = dataset_dir
    if target_dir is None:
        raise FileNotFoundError(
            "Датасет не найден!\n"
            "1. Убедитесь, что вы запустили: python generate_synthetic_data.py\n"
            f"2. Файлы должны лежать в: {dataset_dir}\n"
        )
    def load_json(name: str) -> list:
        with open(target_dir / name, "r", encoding="utf-8") as f:
            return clean_json_data(json.load(f))

    raw_teachers = load_json("teachers.json")
    raw_groups = load_json("groups.json")
    raw_auditoriums = load_json("auditoriums.json")
    raw_subjects = load_json("subjects.json")

    teachers = [
        Teacher(id=t["id"], name=t["name"], max_hours=t["max_hours"], available_days=t["available_days"])
        for t in raw_teachers
    ]
    groups = [
        Group(id=g["id"], name=g["name"], student_count=g["student_count"])
        for g in raw_groups
    ]
    auditoriums = [
        Auditorium(id=a["id"], capacity=a["capacity"], type=a["type"], available_days=a["available_days"])
        for a in raw_auditoriums
    ]
    subjects = [
        Subject(id=s["id"], name=s["name"], hours_per_week=s["hours_per_week"],
                required_auditorium_type=s["required_auditorium_type"], is_lecture=s["is_lecture"])
        for s in raw_subjects
    ]

    # Генерация задач (циклическое назначение)
    tasks = []
    for i, subj in enumerate(subjects):
        t = teachers[i % len(teachers)]
        g = groups[i % len(groups)]
        tasks.append(LessonTask(id=f"task_{i}", teacher=t, group=g, subject=subj))
    days = sorted({d for a in raw_auditoriums for d in a["available_days"]})
    time_slots = [f"{d}_{p}" for d in days for p in range(1, 5)]

    return tasks, auditoriums, time_slots


class ProfilingTests(unittest.TestCase):
    def _run_with_profiling(self, tasks, auditoriums, time_slots, max_steps: int = 200_000) -> Dict[str, Any]:
        tracemalloc.start()
        start_time = time.time()

        solver = ScheduleGenerator(
            tasks=tasks,
            time_slots=time_slots,
            auditoriums=auditoriums,
            max_search_steps=max_steps
        )
        result = solver.generate()

        elapsed = time.time() - start_time
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        return {
            "success": result is not None,
            "solve_status": solver.solve_status,
            "time_sec": round(elapsed, 3),
            "memory_mb": round(peak / (1024 * 1024), 2),
            "search_steps": solver.search_steps,
            "max_search_steps": max_steps,
            "steps_ratio": round(solver.search_steps / max_steps, 3) if max_steps > 0 else 0.0
        }

    def _print_metrics(self, label: str, metrics: Dict[str, Any]):
        print(f"\n{'=' * 60}")
        print(f"PROFILING: {label}")
        print(f"{'=' * 60}")
        for k, v in metrics.items():
            print(f"  {k:<20} : {v}")
        print(f"{'=' * 60}\n")

    def test_profile_synthetic_dataset_default(self):
        tasks, auditoriums, time_slots = load_synthetic_dataset()
        metrics = self._run_with_profiling(tasks, auditoriums, time_slots, max_steps=200_000)
        self._print_metrics("Synthetic Dataset (200K steps)", metrics)

        self.assertIsInstance(metrics["time_sec"], (int, float))
        self.assertIn(metrics["solve_status"], ["успех", "нет_решения", "лимит_поиска_достигнут"])
        self._export_metrics("profile_default", metrics)

    def test_profile_step_limit_impact(self):
        tasks, auditoriums, time_slots = load_synthetic_dataset()

        for limit in [10_000, 50_000, 200_000]:
            metrics = self._run_with_profiling(tasks, auditoriums, time_slots, max_steps=limit)
            self._print_metrics(f"Limited to {limit} steps", metrics)
            self._export_metrics(f"profile_limit_{limit}", metrics)

            self.assertGreaterEqual(metrics["steps_ratio"], 0.0)
            self.assertLessEqual(metrics["steps_ratio"], 1.0)

    def _export_metrics(self, prefix: str, metrics: Dict[str, Any]):
        if os.getenv("EXPORT_METRICS") == "1":
            out_path = Path(__file__).resolve().parent / f"{prefix}_metrics.json"
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(metrics, f, ensure_ascii=False, indent=2)
            print(f"Метрики сохранены: {out_path}")


if __name__ == "__main__":
    unittest.main()