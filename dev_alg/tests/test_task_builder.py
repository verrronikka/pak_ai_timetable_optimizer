import unittest

from models import Group, Subject, Teacher
from paths import DATA
from task_builder import build_lesson_tasks, load_dataset


class TaskBuilderTests(unittest.TestCase):
    def test_build_lesson_tasks_counts_hours(self):
        teachers = [Teacher("t1", "T1", 10, ["Mon"])]
        groups = [Group("g1", "G1", 20), Group("g2", "G2", 22)]
        subjects = [
            Subject("s1", "Math", 2, "lecture", True),
            Subject("s2", "Lab", 1, "lab", False),
        ]
        tasks = build_lesson_tasks(teachers, groups, subjects)
        self.assertEqual(len(tasks), 6)

    def test_load_demo_dataset(self):
        tasks, auditoriums, time_slots = load_dataset(DATA)
        self.assertEqual(len(tasks), 24)
        self.assertGreater(len(auditoriums), 0)
        self.assertEqual(len(time_slots), 20)


if __name__ == "__main__":
    unittest.main()
