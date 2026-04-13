from typing import Dict

from models import LessonTask


class ScheduleConflictChecker:
    """
        Возвращает True, если размещение задачи вызовет конфликт.
    """
    @staticmethod
    def has_conflict(schedule: Dict[str, Dict[str, LessonTask]],
                     task: LessonTask,
                     time_slot: str,
                     auditorium_id: str):
        if time_slot in schedule and auditorium_id in schedule[time_slot]:
            return True

        if time_slot in schedule:
            for assigned_task in schedule[time_slot].values():
                if assigned_task.teacher.id == task.teacher.id:
                    return True  # Преподаватель ведёт две пары одновременно
                if assigned_task.group.id == task.group.id:
                    return True  # Группа учится в двух местах одновременно

        return False
