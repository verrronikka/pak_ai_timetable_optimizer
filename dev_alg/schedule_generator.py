from typing import List, Dict, Optional

from models import LessonTask, Auditorium
from conflict_checker import ScheduleConflictChecker


class ScheduleGenerator:
    def __init__(self, tasks: List[LessonTask], time_slots: List[str],
                 auditoriums: List[Auditorium]):
        self.tasks = tasks
        self.time_slots = time_slots
        self.auditoriums = auditoriums
        self.schedule: Dict[str, Dict[str, LessonTask]] = {}
        self.teacher_hours: Dict[str, int] = {}
        self.checker = ScheduleConflictChecker()

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
                0 if t.subject.required_auditorium_type == "lecture" else 1
            )
        )

        print("Generating schedule...")
        if self._backtrack(sorted_tasks, 0):
            return self.schedule
        else:
            print("Error! Can`t make schedule due to limitations")
            return None

    def _backtrack(self, tasks: List[LessonTask], idx: int) -> bool:
        """Рекурсивный поиск с возвратом."""
        if idx == len(tasks):
            return True

        task = tasks[idx]

        for time_slot in self.time_slots:
            for aud in self.auditoriums:
                if self._is_valid(task, time_slot, aud):
                    self._place(task, time_slot, aud.id)

                    if self._backtrack(tasks, idx + 1):
                        return True
                    self._unplace(task, time_slot, aud.id)

        return False

    def _is_valid(self, task: LessonTask, time_slot: str, aud: Auditorium):
        day = time_slot.split("_")[0]

        # 1. Доступность дней
        if (
            day not in task.teacher.available_days or
            day not in aud.available_days
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
