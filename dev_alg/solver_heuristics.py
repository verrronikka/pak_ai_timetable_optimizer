from dataclasses import dataclass


@dataclass(frozen=True)
class SolverHeuristics:
    """Конфигурация эвристик backtracking."""
    # static: начальная сортировка; mrv: только MRV на каждом шаге
    task_order: str = "static_mrv"
    # least_loaded | capacity_fit | combined
    candidate_order: str = "combined"
    # none | degree — доп. вес в начальной сортировке
    degree_weight: bool = True

    def normalized(self) -> "SolverHeuristics":
        task_order = self.task_order if self.task_order in ("static", "mrv", "static_mrv") else "static_mrv"
        candidate_order = self.candidate_order if self.candidate_order in (
            "least_loaded",
            "capacity_fit",
            "combined",
        ) else "combined"
        return SolverHeuristics(
            task_order=task_order,
            candidate_order=candidate_order,
            degree_weight=self.degree_weight,
        )


DEFAULT_HEURISTICS = SolverHeuristics()
