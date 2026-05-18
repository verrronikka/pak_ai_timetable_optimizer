import json
import os
import unittest
from typing import Any, Dict

from paths import ARTIFACTS, BENCHMARKS, DATA
from tuning.benchmark_runner import run_solver_profile


class ProfilingTests(unittest.TestCase):
    def _print_metrics(self, label: str, metrics: Dict[str, Any]):
        print(f"\n{'=' * 60}")
        print(f"PROFILING: {label}")
        print(f"{'=' * 60}")
        for key, value in metrics.items():
            print(f"  {key:<20} : {value}")
        print(f"{'=' * 60}\n")

    def _export_metrics(self, prefix: str, metrics: Dict[str, Any]):
        if os.getenv("EXPORT_METRICS") == "1":
            ARTIFACTS.mkdir(parents=True, exist_ok=True)
            out_path = ARTIFACTS / f"{prefix}_metrics.json"
            with open(out_path, "w", encoding="utf-8") as handle:
                json.dump(metrics, handle, ensure_ascii=False, indent=2)
            print(f"Метрики сохранены: {out_path.name}")

    def test_profile_demo_dataset(self):
        metrics = run_solver_profile(DATA, max_search_steps=200_000)
        self._print_metrics("Demo (24 tasks)", metrics)
        self.assertIn(
            metrics["solve_status"],
            ["успех", "нет_решения", "лимит_поиска_достигнут"],
        )
        self._export_metrics("profile_demo", metrics)

    def test_profile_benchmark_tiers_if_present(self):
        if not BENCHMARKS.is_dir():
            self.skipTest("Benchmark datasets not generated yet")

        for tier_dir in sorted(BENCHMARKS.iterdir()):
            if not tier_dir.is_dir() or not (tier_dir / "teachers.json").exists():
                continue

            metrics = run_solver_profile(
                tier_dir,
                max_search_steps=500_000,
            )
            self._print_metrics(f"Benchmark {tier_dir.name}", metrics)
            self._export_metrics(f"profile_{tier_dir.name}", metrics)
            self.assertIn(
                metrics["solve_status"],
                ["успех", "нет_решения", "лимит_поиска_достигнут"],
            )


if __name__ == "__main__":
    unittest.main()
