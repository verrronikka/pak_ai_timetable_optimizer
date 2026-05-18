"""Запуск solver на датасетах и сбор метрик (только dev_alg)."""

from __future__ import annotations

import json
import time
import tracemalloc
from pathlib import Path
from typing import Any, Dict, List, Optional

from paths import BENCHMARKS, DATA, relative_to_root, resolve_dataset
from schedule_generator import ScheduleGenerator
from solver_heuristics import SolverHeuristics
from task_builder import load_dataset


def _read_meta(dataset_dir: Path) -> dict:
    meta_path = dataset_dir / "meta.json"
    if meta_path.exists():
        with open(meta_path, encoding="utf-8") as handle:
            return json.load(handle)
    return {}


def list_datasets(include_demo: bool = True) -> List[Path]:
    datasets: List[Path] = []
    if include_demo and (DATA / "teachers.json").exists():
        datasets.append(DATA)
    if BENCHMARKS.is_dir():
        for tier_dir in sorted(BENCHMARKS.iterdir()):
            if tier_dir.is_dir() and (tier_dir / "teachers.json").exists():
                datasets.append(tier_dir)
    return datasets


def run_solver_profile(
    dataset: Path | str,
    max_search_steps: int,
    heuristics: Optional[SolverHeuristics] = None,
) -> Dict[str, Any]:
    dataset_dir = Path(dataset)
    meta = _read_meta(dataset_dir)
    pairs_per_day = meta.get("pairs_per_day", 4)
    tasks, auditoriums, time_slots = load_dataset(dataset_dir, pairs_per_day)

    tracemalloc.start()
    started = time.perf_counter()
    solver = ScheduleGenerator(
        tasks=tasks,
        time_slots=time_slots,
        auditoriums=auditoriums,
        max_search_steps=max_search_steps,
        heuristics=heuristics,
    )
    result = solver.generate()
    elapsed = time.perf_counter() - started
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    dataset_key = (
        "demo"
        if dataset_dir.resolve() == DATA.resolve()
        else dataset_dir.name
    )
    return {
        "dataset": dataset_key,
        "dataset_ref": relative_to_root(dataset_dir),
        "task_count": len(tasks),
        "time_slot_count": len(time_slots),
        "teachers_x_groups": meta.get("teachers_x_groups"),
        "success": result is not None,
        "solve_status": solver.solve_status,
        "time_sec": round(elapsed, 4),
        "memory_mb": round(peak / (1024 * 1024), 3),
        "search_steps": solver.search_steps,
        "max_search_steps": max_search_steps,
        "heuristics": (heuristics or SolverHeuristics()).normalized().__dict__,
    }


def run_all_benchmarks(
    max_search_steps: int = 500_000,
    heuristics: Optional[SolverHeuristics] = None,
    include_demo: bool = True,
) -> List[Dict[str, Any]]:
    return [
        run_solver_profile(path, max_search_steps, heuristics)
        for path in list_datasets(include_demo=include_demo)
    ]


def run_grid_on_tier(
    tier: str,
    limits: List[int],
    variants: List[tuple[str, SolverHeuristics]],
) -> List[Dict[str, Any]]:
    dataset_dir = resolve_dataset(tier)
    if not (dataset_dir / "teachers.json").exists():
        raise FileNotFoundError(f"Dataset not found: {tier}")

    rows: List[Dict[str, Any]] = []
    for label, heuristics in variants:
        for limit in limits:
            metrics = run_solver_profile(dataset_dir, limit, heuristics)
            metrics["variant"] = label
            rows.append(metrics)
    return rows
