import unittest

from models import Auditorium, Group, LessonTask, Subject, Teacher
from validator import ScheduleValidator


class ScheduleValidatorTests(unittest.TestCase):
    def setUp(self):
        self.validator = ScheduleValidator()
        self.teacher = Teacher("t1", "Teacher", 2, ["Mon", "Tue"])
        self.group = Group("g1", "Group", 25)
        self.subject_practice = Subject("s1", "Practice", 2, "practice", False)
        self.subject_lecture = Subject("s2", "Lecture", 2, "lecture", True)
        self.task_practice = LessonTask(
            "task1", self.teacher, self.group, self.subject_practice
        )

        self.practice_aud = Auditorium(
            "A1", 30, "practice", ["Mon", "Tue", "Wed"]
        )
        self.lecture_aud = Auditorium(
            "L1", 50, "lecture", ["Mon", "Tue", "Wed"]
        )

    def test_valid_placement(self):
        result = self.validator.validate_placement(
            schedule={},
            task=self.task_practice,
            time_slot="Mon_1",
            auditorium=self.practice_aud,
            teacher_hours={},
        )
        self.assertTrue(result.is_valid)
        self.assertEqual(result.reason, "OK")

    def test_teacher_day_unavailable(self):
        result = self.validator.validate_placement(
            schedule={},
            task=self.task_practice,
            time_slot="Fri_1",
            auditorium=self.practice_aud,
            teacher_hours={},
        )
        self.assertFalse(result.is_valid)
        self.assertEqual(result.reason, "TEACHER_DAY_UNAVAILABLE")

    def test_auditorium_day_unavailable(self):
        limited_aud = Auditorium("A2", 30, "practice", ["Mon"])
        result = self.validator.validate_placement(
            schedule={},
            task=self.task_practice,
            time_slot="Tue_1",
            auditorium=limited_aud,
            teacher_hours={},
        )
        self.assertFalse(result.is_valid)
        self.assertEqual(result.reason, "AUDITORIUM_DAY_UNAVAILABLE")

    def test_auditorium_capacity_exceeded(self):
        small_aud = Auditorium("A3", 10, "practice", ["Mon", "Tue"])
        result = self.validator.validate_placement(
            schedule={},
            task=self.task_practice,
            time_slot="Mon_1",
            auditorium=small_aud,
            teacher_hours={},
        )
        self.assertFalse(result.is_valid)
        self.assertEqual(result.reason, "AUDITORIUM_CAPACITY_EXCEEDED")

    def test_auditorium_type_mismatch(self):
        result = self.validator.validate_placement(
            schedule={},
            task=self.task_practice,
            time_slot="Mon_1",
            auditorium=self.lecture_aud,
            teacher_hours={},
        )
        self.assertFalse(result.is_valid)
        self.assertEqual(result.reason, "AUDITORIUM_TYPE_MISMATCH")

    def test_teacher_hours_limit_reached(self):
        result = self.validator.validate_placement(
            schedule={},
            task=self.task_practice,
            time_slot="Mon_1",
            auditorium=self.practice_aud,
            teacher_hours={"t1": 2},
        )
        self.assertFalse(result.is_valid)
        self.assertEqual(result.reason, "TEACHER_HOURS_LIMIT_REACHED")

    def test_schedule_conflict_by_group(self):
        existing_task = LessonTask(
            "task2",
            Teacher("t2", "Other", 4, ["Mon", "Tue"]),
            self.group,
            self.subject_lecture,
        )
        schedule = {"Mon_1": {"L1": existing_task}}

        result = self.validator.validate_placement(
            schedule=schedule,
            task=self.task_practice,
            time_slot="Mon_1",
            auditorium=self.practice_aud,
            teacher_hours={},
        )
        self.assertFalse(result.is_valid)
        self.assertEqual(result.reason, "SCHEDULE_CONFLICT")


if __name__ == "__main__":
    unittest.main()
