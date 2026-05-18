from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
BENCHMARKS = DATA / "benchmarks"
ARTIFACTS = ROOT / "artifacts"

SCHEDULE_JSON = "schedule_output.json"
SCHEDULE_MARKDOWN = "schedule_report.md"
BENCHMARK_RESULTS_JSON = "benchmark_results.json"
TUNING_GRID_JSON = "tuning_grid.json"


def bootstrap() -> None:
    """Добавляет dev_alg в sys.path при запуске скриптов из подпапок."""
    root = str(ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)


def ensure_artifacts_dir() -> Path:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    return ARTIFACTS


def artifact(name: str) -> Path:
    return ensure_artifacts_dir() / name


def relative_to_root(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.name


def resolve_dataset(name: str) -> Path:
    """Имя набора: demo | tiny | small | medium | large."""
    if name == "demo":
        return DATA
    return BENCHMARKS / name
