# Benchmark datasets

Наборы для профилирования и регрессии solver. Размер tier задаётся как **teachers × groups** (число сущностей в `meta.json`).

| Tier   | Teachers | Groups | T×G  | Tasks | Slots |
|--------|----------|--------|------|-------|-------|
| tiny   | 2        | 2      | 4    | 8     | 20    |
| small  | 4        | 4      | 16   | 24    | 20    |
| medium | 8        | 8      | 64   | 64    | 25    |
| large  | 12       | 12     | 144  | 96    | 30    |

Число задач = `subjects × groups × hours_per_week` (см. `meta.json`).

## Генерация

```bash
cd dev_alg
python data/benchmarks/generate.py --tier all --seed 42
python tuning/run_benchmarks.py
```

Демо-данные для API/фронта — в `data/*.json`. Метрики и вывод CLI — в `artifacts/`.
