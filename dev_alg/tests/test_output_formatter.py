import unittest

from models import Group, LessonTask, Subject, Teacher
from output_formatter import build_markdown_failure, build_markdown_schedule


class OutputFormatterTests(unittest.TestCase):
    def test_build_markdown_schedule_contains_table_and_data(self):
        teacher = Teacher("t1", "Преподаватель", 4, ["Mon"])
        group = Group("g1", "ПИ-201", 25)
        subject = Subject("s1", "Математика", 1, "lecture", True)
        task = LessonTask("task1", teacher, group, subject)

        schedule = {
            "Mon_1": {
                "L1": task,
            }
        }

        md = build_markdown_schedule(schedule)

        self.assertIn("# Расписание занятий", md)
        self.assertIn("| День | Пара | Аудитория |", md)
        self.assertIn("| Mon | 1 | L1 | ПИ-201 | Математика |", md)

    def test_build_markdown_failure_contains_reason(self):
        md = build_markdown_failure(
            reason="Не удалось составить расписание при текущих ограничениях",
            search_steps=123,
            solve_status="нет_решения",
            max_search_steps=500,
        )

        self.assertIn("# Расписание не сформировано", md)
        self.assertIn(
            "Причина: Не удалось составить расписание "
            "при текущих ограничениях",
            md,
        )
        self.assertIn("Шагов поиска: 123", md)


if __name__ == "__main__":
    unittest.main()
