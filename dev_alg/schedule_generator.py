from typing import Dict, List, Optional

from conflict_checker import ScheduleConflictChecker
from models import Auditorium, LessonTask


class ScheduleGenerator:
    def __init__(
        self,
        tasks: List[LessonTask],
        time_slots: List[str],
        auditoriums: List[Auditorium],
        max_search_steps: int = 200000,
    ):
        self.tasks = tasks
        self.time_slots = time_slots
        self.auditoriums = auditoriums
        self.max_search_steps = max_search_steps
        self.schedule: Dict[str, Dict[str, LessonTask]] = {}
        self.teacher_hours: Dict[str, int] = {}
        self.checker = ScheduleConflictChecker()
        self.search_steps = 0
        self.search_aborted = False

    def generate(self) -> Optional[Dict[str, Dict[str, LessonTask]]]:
        """
        Cортируем задачи от "самых сложных" к "простым"
        Сложность = меньше свободных дней у преподавателя +
        строгие требования к аудитории
        """
        sorted_tasks = sorted(
            self.tasks,
            key=lambda t: (
                len(t.teacher.available_days),
                0 if t.subject.required_auditorium_type == "lecture" else 1,
            ),
        )

        self.search_steps = 0
        self.search_aborted = False

        print("Генерируется расписание...")
        if self._backtrack(sorted_tasks):
            return self.schedule
        if self.search_aborted:
            print(
                "Ошибка! Достигнут лимит поиска. "
                "Уменьшите количество задач или увеличьте max_search_steps."
            )
            return None

        print(
            "Ошибка! Не удалось составить расписание при текущих ограничениях"
        )
        return None

    def _backtrack(self, tasks: List[LessonTask]) -> bool:
        """Рекурсивный поиск с возвратом."""
        if self.search_steps >= self.max_search_steps:
            self.search_aborted = True
            return False

        self.search_steps += 1

        if not tasks:
            return True

        # MRV-эвристика: выбираем задачу с минимальным числом вариантов.
        task = min(tasks, key=self._count_candidates)
        candidates = self._get_candidates(task)
        if not candidates:
            return False

        task_idx = tasks.index(task)
        remaining_tasks = tasks[:task_idx] + tasks[task_idx + 1 :]

        for time_slot, aud in candidates:
            self._place(task, time_slot, aud.id)

            if self._backtrack(remaining_tasks):
                return True
            self._unplace(task, time_slot, aud.id)

        return False

    def _count_candidates(self, task: LessonTask) -> int:
        return len(self._get_candidates(task))

    def _get_candidates(
        self, task: LessonTask
    ) -> List[tuple[str, Auditorium]]:
        candidates: List[tuple[str, Auditorium]] = []
        for time_slot in self.time_slots:
            for aud in self.auditoriums:
                if self._is_valid(task, time_slot, aud):
                    candidates.append((time_slot, aud))

        # Сначала пробуем менее занятые слоты, чтобы снизить коллизии.
        candidates.sort(key=lambda item: len(self.schedule.get(item[0], {})))
        return candidates

    def _is_valid(self, task: LessonTask, time_slot: str, aud: Auditorium):
        day = time_slot.split("_")[0]

        # 1. Доступность дней
        if (
            day not in task.teacher.available_days
            or day not in aud.available_days
        ):
            return False
        # 2. Вместимость
        if task.group.student_count > aud.capacity:
            return False
        # 3. Тип аудитории
        if aud.type != task.subject.required_auditorium_type:
            return False
        # 4. Лимит часов преподавателя
        if (
            self.teacher_hours.get(task.teacher.id, 0)
            >= task.teacher.max_hours
        ):
            return False
        # 5. Проверка коллизий (ядро валидатора)
        if self.checker.has_conflict(self.schedule, task, time_slot, aud.id):
            return False

        return True

    def _place(self, task: LessonTask, time_slot: str, aud_id: str):
        if time_slot not in self.schedule:
            self.schedule[time_slot] = {}
        self.schedule[time_slot][aud_id] = task
        self.teacher_hours[task.teacher.id] = (
            self.teacher_hours.get(task.teacher.id, 0) + 1
        )

    def _unplace(self, task: LessonTask, time_slot: str, aud_id: str):
        if time_slot in self.schedule and aud_id in self.schedule[time_slot]:
            del self.schedule[time_slot][aud_id]
            if not self.schedule[time_slot]:
                del self.schedule[time_slot]
            self.teacher_hours[task.teacher.id] -= 1
