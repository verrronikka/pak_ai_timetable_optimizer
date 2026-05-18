"""
Устаревший random-генератор. Используйте конструктивный генератор бенчмарков:

    python dev_alg/data/benchmarks/generate.py --tier small --seed 42
"""

import sys


def main() -> None:
    print(__doc__.strip())
    print("\nДля демо-набора используйте файлы dev_alg/data/*.json (не перезаписывать).")
    sys.exit(0)


if __name__ == "__main__":
    main()
