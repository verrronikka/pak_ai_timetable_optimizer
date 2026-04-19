from models import Auditorium, Group, LessonTask, Subject, Teacher
from schedule_generator import ScheduleGenerator


def generate_synthetic_tasks():
    teachers = [
        Teacher(
            f"t{i}", f"Teacher_{i}", 20, ["Mon", "Tue", "Wed", "Thu", "Fri"]
        )
        for i in range(1, 6)
    ]
    groups = [Group(f"g{i}", f"Group_{i}", 25) for i in range(1, 4)]
    auditoriums = [
        Auditorium("A1", 30, "lecture", ["Mon", "Tue", "Wed", "Thu", "Fri"]),
        Auditorium("A2", 20, "practice", ["Mon", "Tue", "Wed", "Thu", "Fri"]),
        Auditorium("A3", 25, "practice", ["Mon", "Tue", "Wed", "Thu", "Fri"]),
    ]
    subjects = [
        Subject("s1", "Math", 4, "lecture", True),
        Subject("s2", "Physics", 2, "practice", False),
        Subject("s3", "History", 2, "practice", False),
    ]

    tasks = []
    task_id = 1
    for subj in subjects:
        for grp in groups:
            teacher = teachers[task_id % len(teachers)]
            for _ in range(subj.hours_per_week):
                tasks.append(
                    LessonTask(
                        id=f"task_{task_id}",
                        teacher=teacher,
                        group=grp,
                        subject=subj,
                    )
                )
                task_id += 1
    return tasks, auditoriums


def main():
    tasks, auditoriums = generate_synthetic_tasks()
    days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    time_slots = [f"{day}_{p}" for day in days for p in range(1, 5)]

    generator = ScheduleGenerator(tasks, time_slots, auditoriums)
    result = generator.generate()

    if result:
        print("\nTimetable is ready!\n")
        for ts in sorted(result.keys()):
            print(f"{ts.replace('_', ' ')}:")
            for aud_id, task in result[ts].items():
                print(
                    f"Auditorium: {aud_id} | "
                    f"{task.group.name} | "
                    f"{task.subject.name} | "
                    f"Teacher: {task.teacher.name}"
                )
    else:
        print(
            "Impossible to generate timetable! "
            "Try to extend number of auditoriums or time periods.\n"
        )


if __name__ == "__main__":
    main()
