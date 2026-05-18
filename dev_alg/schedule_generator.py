from typing import Dict, List, Optional, Tuple

from models import Auditorium, LessonTask
from solver_heuristics import DEFAULT_HEURISTICS, SolverHeuristics
from validator import ScheduleValidator


class ScheduleGenerator:
    def __init__(
        self,
        tasks: List[LessonTask],
        time_slots: List[str],
        auditoriums: List[Auditorium],
        max_search_steps: int = 200000,
        heuristics: Optional[SolverHeuristics] = None,
    ):
        self.tasks = tasks
        self.time_slots = time_slots
        self.auditoriums = auditoriums
        self.max_search_steps = max_search_steps
        self.heuristics = (heuristics or DEFAULT_HEURISTICS).normalized()
        self.schedule: Dict[str, Dict[str, LessonTask]] = {}
        self.teacher_hours: Dict[str, int] = {}
        self.validator = ScheduleValidator()
        self.search_steps = 0
        self.search_aborted = False
        self.solve_status = "не_начато"
        self._slot_load: Dict[str, int] = {}

    def generate(self) -> Optional[Dict[str, Dict[str, LessonTask]]]:
        if self.heuristics.task_order in ("static", "static_mrv"):
            ordered_tasks = sorted(self.tasks, key=self._static_task_key)
        else:
            ordered_tasks = list(self.tasks)

        self.search_steps = 0
        self.search_aborted = False
        self.solve_status = "начато"
        self.schedule = {}
        self.teacher_hours = {}
        self._slot_load = {}

        print("Генерируется расписание...")
        if self._backtrack(ordered_tasks):
            self.solve_status = "успех"
            return self.schedule
        if self.search_aborted:
            self.solve_status = "лимит_поиска_достигнут"
            print(
                "Ошибка! Достигнут лимит поиска. "
                "Уменьшите количество задач или увеличьте max_search_steps."
            )
            return None

        self.solve_status = "нет_решения"
        print(
            "Ошибка! Не удалось составить расписание при текущих ограничениях"
        )
        return None

    def _static_task_key(self, task: LessonTask) -> Tuple:
        lecture_penalty = 0 if task.subject.required_auditorium_type == "lecture" else 1
        degree = 0
        if self.heuristics.degree_weight:
            degree = -self._task_degree(task)
        return (
            len(task.teacher.available_days),
            lecture_penalty,
            degree,
            task.teacher.id,
            task.group.id,
            task.subject.id,
        )

    def _task_degree(self, task: LessonTask) -> int:
        """Число задач, конкурирующих за того же преподавателя или группу."""
        score = 0
        for other in self.tasks:
            if other.id == task.id:
                continue
            if other.teacher.id == task.teacher.id:
                score += 1
            if other.group.id == task.group.id:
                score += 1
        return score

    def _backtrack(self, tasks: List[LessonTask]) -> bool:
        if self.search_steps >= self.max_search_steps:
            self.search_aborted = True
            return False

        self.search_steps += 1

        if not tasks:
            return True

        task_idx, candidates = self._select_task(tasks)
        if not candidates:
            return False

        remaining = tasks[:task_idx] + tasks[task_idx + 1 :]
        task = tasks[task_idx]

        for time_slot, aud in candidates:
            self._place(task, time_slot, aud.id)
            if self._backtrack(remaining):
                return True
            self._unplace(task, time_slot, aud.id)

        return False

    def _select_task(
        self, tasks: List[LessonTask]
    ) -> Tuple[int, List[Tuple[str, Auditorium]]]:
        if self.heuristics.task_order == "static":
            candidates = self._get_candidates(tasks[0])
            return 0, candidates

        best_idx = 0
        best_candidates: List[Tuple[str, Auditorium]] = []
        best_count = None

        for idx, task in enumerate(tasks):
            candidates = self._get_candidates(task)
            count = len(candidates)
            if count == 0:
                return idx, []
            if best_count is None or count < best_count:
                best_count = count
                best_idx = idx
                best_candidates = candidates
                if count == 1:
                    break

        return best_idx, best_candidates

    def _get_candidates(
        self, task: LessonTask
    ) -> List[Tuple[str, Auditorium]]:
        candidates: List[Tuple[str, Auditorium]] = []
        for time_slot in self.time_slots:
            for aud in self.auditoriums:
                if self._is_valid(task, time_slot, aud):
                    candidates.append((time_slot, aud))

        candidates.sort(key=lambda item: self._candidate_sort_key(task, item))
        return candidates

    def _candidate_sort_key(
        self, task: LessonTask, item: Tuple[str, Auditorium]
    ) -> Tuple:
        time_slot, aud = item
        load = self._slot_load.get(time_slot, 0)
        slack = aud.capacity - task.group.student_count
        teacher_load = self.teacher_hours.get(task.teacher.id, 0)

        if self.heuristics.candidate_order == "least_loaded":
            return (load, slack, aud.id)
        if self.heuristics.candidate_order == "capacity_fit":
            return (slack, load, aud.id)
        return (load, slack, teacher_load, aud.id)

    def _is_valid(self, task: LessonTask, time_slot: str, aud: Auditorium) -> bool:
        validation = self.validator.validate_placement(
            schedule=self.schedule,
            task=task,
            time_slot=time_slot,
            auditorium=aud,
            teacher_hours=self.teacher_hours,
        )
        return validation.is_valid

    def _place(self, task: LessonTask, time_slot: str, aud_id: str):
        if time_slot not in self.schedule:
            self.schedule[time_slot] = {}
        self.schedule[time_slot][aud_id] = task
        self.teacher_hours[task.teacher.id] = (
            self.teacher_hours.get(task.teacher.id, 0) + 1
        )
        self._slot_load[time_slot] = self._slot_load.get(time_slot, 0) + 1

    def _unplace(self, task: LessonTask, time_slot: str, aud_id: str):
        if time_slot in self.schedule and aud_id in self.schedule[time_slot]:
            del self.schedule[time_slot][aud_id]
            if not self.schedule[time_slot]:
                del self.schedule[time_slot]
            self.teacher_hours[task.teacher.id] -= 1
            self._slot_load[time_slot] -= 1
            if self._slot_load[time_slot] <= 0:
                del self._slot_load[time_slot]
