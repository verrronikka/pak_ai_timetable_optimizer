import unittest
from typing import cast

from models import Auditorium, Group, LessonTask, Subject, Teacher
from schedule_generator import ScheduleGenerator


class ScheduleSolverTests(unittest.TestCase):
    def test_solver_successful_generation(self):
        teacher = Teacher("t1", "Teacher", 4, ["Mon"])
        group = Group("g1", "Group", 20)
        subject = Subject("s1", "Math", 1, "lecture", True)
        task = LessonTask("task1", teacher, group, subject)
        aud = Auditorium("L1", 40, "lecture", ["Mon"])

        solver = ScheduleGenerator(
            tasks=[task],
            time_slots=["Mon_1"],
            auditoriums=[aud],
            max_search_steps=100,
        )

        result = solver.generate()
        self.assertIsNotNone(result)
        self.assertEqual(solver.solve_status, "успех")
        schedule = cast(dict, result)
        self.assertIn("Mon_1", schedule)

    def test_solver_returns_no_solution(self):
        teacher = Teacher("t1", "Teacher", 4, ["Mon"])
        group = Group("g1", "Group", 20)
        subject = Subject("s1", "Lab", 1, "practice", False)
        task = LessonTask("task1", teacher, group, subject)
        # Неподходящий тип аудитории => решения нет.
        aud = Auditorium("L1", 40, "lecture", ["Mon"])

        solver = ScheduleGenerator(
            tasks=[task],
            time_slots=["Mon_1"],
            auditoriums=[aud],
            max_search_steps=100,
        )

        result = solver.generate()
        self.assertIsNone(result)
        self.assertEqual(solver.solve_status, "нет_решения")

    def test_solver_stops_on_search_limit(self):
        teacher = Teacher("t1", "Teacher", 6, ["Mon", "Tue"])
        group = Group("g1", "Group", 20)
        subject = Subject("s1", "Math", 2, "lecture", True)
        task1 = LessonTask("task1", teacher, group, subject)
        task2 = LessonTask("task2", teacher, group, subject)
        aud = Auditorium("L1", 40, "lecture", ["Mon", "Tue"])

        solver = ScheduleGenerator(
            tasks=[task1, task2],
            time_slots=["Mon_1", "Tue_1"],
            auditoriums=[aud],
            max_search_steps=0,
        )

        result = solver.generate()
        self.assertIsNone(result)
        self.assertEqual(solver.solve_status, "лимит_поиска_достигнут")
        self.assertTrue(solver.search_aborted)


if __name__ == "__main__":
    unittest.main()
