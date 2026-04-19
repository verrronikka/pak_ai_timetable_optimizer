from typing import List


class Teacher:
    def __init__(
        self, id: str, name: str, max_hours: int, available_days: List[str]
    ):
        self.id = id
        self.name = name
        self.max_hours = max_hours
        self.available_days = available_days


class Group:
    def __init__(self, id: str, name: str, student_count: int):
        self.id = id
        self.name = name
        self.student_count = student_count


class Auditorium:
    def __init__(
        self, id: str, capacity: int, type: str, available_days: List[str]
    ):
        self.id = id
        self.capacity = capacity
        self.type = type
        self.available_days = available_days


class Subject:
    def __init__(
        self,
        id: str,
        name: str,
        hours_per_week: int,
        required_auditorium_type: str,
        is_lecture: bool,
    ):
        self.id = id
        self.name = name
        self.hours_per_week = hours_per_week
        self.required_auditorium_type = required_auditorium_type
        self.is_lecture = is_lecture


class LessonTask:
    def __init__(
        self, id: str, teacher: Teacher, group: Group, subject: Subject
    ):
        self.id = id
        self.teacher = teacher
        self.group = group
        self.subject = subject
