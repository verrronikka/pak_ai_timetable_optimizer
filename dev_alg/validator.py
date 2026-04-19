from dataclasses import dataclass
from typing import Dict

from conflict_checker import ScheduleConflictChecker
from models import Auditorium, LessonTask


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    reason: str = "OK"


class ScheduleValidator:
    """Проверяет корректность размещения пары в расписании."""

    def __init__(self):
        self.conflict_checker = ScheduleConflictChecker()

    def validate_placement(
        self,
        schedule: Dict[str, Dict[str, LessonTask]],
        task: LessonTask,
        time_slot: str,
        auditorium: Auditorium,
        teacher_hours: Dict[str, int],
    ) -> ValidationResult:
        day = time_slot.split("_")[0]

        if day not in task.teacher.available_days:
            return ValidationResult(False, "TEACHER_DAY_UNAVAILABLE")

        if day not in auditorium.available_days:
            return ValidationResult(False, "AUDITORIUM_DAY_UNAVAILABLE")

        if task.group.student_count > auditorium.capacity:
            return ValidationResult(False, "AUDITORIUM_CAPACITY_EXCEEDED")

        if auditorium.type != task.subject.required_auditorium_type:
            return ValidationResult(False, "AUDITORIUM_TYPE_MISMATCH")

        if teacher_hours.get(task.teacher.id, 0) >= task.teacher.max_hours:
            return ValidationResult(False, "TEACHER_HOURS_LIMIT_REACHED")

        if self.conflict_checker.has_conflict(
            schedule, task, time_slot, auditorium.id
        ):
            return ValidationResult(False, "SCHEDULE_CONFLICT")

        return ValidationResult(True)
