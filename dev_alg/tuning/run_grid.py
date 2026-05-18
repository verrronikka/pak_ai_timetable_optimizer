"""Параметрический перебор max_search_steps и эвристик на выбранном tier."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from paths import TUNING_GRID_JSON, artifact  # noqa: E402
from solver_heuristics import SolverHeuristics  # noqa: E402
from tuning.benchmark_runner import run_grid_on_tier  # noqa: E402

HEURISTIC_VARIANTS = [
    ("default", SolverHeuristics()),
    ("least_loaded", SolverHeuristics(candidate_order="least_loaded")),
    ("capacity_fit", SolverHeuristics(candidate_order="capacity_fit")),
    ("mrv_only", SolverHeuristics(task_order="mrv", degree_weight=False)),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Grid search for solver tuning.")
    parser.add_argument(
        "--tier",
        default="medium",
        choices=["tiny", "small", "medium", "large", "demo"],
    )
    parser.add_argument(
        "--limits",
        default="10000,50000,200000,500000",
        help="max_search_steps через запятую",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Имя файла в artifacts/ (по умолчанию tuning_grid.json)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    limits = [int(value.strip()) for value in args.limits.split(",") if value.strip()]
    rows = run_grid_on_tier(args.tier, limits, HEURISTIC_VARIANTS)

    for metrics in rows:
        print(
            f"{metrics['variant']:14} limit={metrics['max_search_steps']:7} "
            f"steps={metrics['search_steps']:6} time={metrics['time_sec']}s "
            f"status={metrics['solve_status']}"
        )

    output_path = artifact(args.output or TUNING_GRID_JSON)
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(rows, handle, ensure_ascii=False, indent=2)
    print(f"Grid results: {output_path.name}")


if __name__ == "__main__":
    main()
