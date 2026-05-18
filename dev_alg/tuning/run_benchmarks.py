"""Прогон solver по demo + benchmark tier и сохранение метрик."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from paths import BENCHMARK_RESULTS_JSON, artifact  # noqa: E402
from tuning.benchmark_runner import run_all_benchmarks  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Profile solver on all datasets.")
    parser.add_argument("--max-search-steps", type=int, default=500_000)
    parser.add_argument(
        "--output",
        default=None,
        help="Имя файла в artifacts/ (по умолчанию benchmark_results.json)",
    )
    parser.add_argument(
        "--skip-demo",
        action="store_true",
        help="Только наборы benchmarks/*",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = artifact(args.output or BENCHMARK_RESULTS_JSON)
    results = run_all_benchmarks(
        max_search_steps=args.max_search_steps,
        include_demo=not args.skip_demo,
    )
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, ensure_ascii=False, indent=2)

    print(f"Wrote {len(results)} profiles to {output_path.name}")
    for row in results:
        print(
            f"  {row['dataset']:8} tasks={row['task_count']:4} "
            f"steps={row['search_steps']:6} time={row['time_sec']}s "
            f"status={row['solve_status']}"
        )


if __name__ == "__main__":
    main()
