import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models import Teacher, Group, Auditorium, Subject, LessonTask
from schedule_generator import ScheduleGenerator

def run_edge_case_tests():
    print("Testing edge cases...")
    days = ["Mon", "Tue", "Wed", "Thu", "Fri"]

    print("\nTest 1: Resource Shortage (Expected: Failure)")
    t1 = Teacher("T1", "Ivanov", 20, ["Mon"])
    g1 = Group("G1", "Group 1", 20)
    g2 = Group("G2", "Group 2", 20)
    a1 = Auditorium("A1", 30, "lecture", ["Mon"])
    s1 = Subject("S1", "Math", 2, "lecture", True)
    tasks = [LessonTask("1", t1, g1, s1), LessonTask("2", t1, g2, s1)]
    res = ScheduleGenerator(tasks, ["Mon_1"], [a1]).generate()
    print(f"   Result: {'Passed' if not res else 'Failed'}")

    print("\nTest 2: Minimal Valid Set (Expected: Success)")
    res2 = ScheduleGenerator([LessonTask("1", t1, g1, s1)], ["Mon_1"], [a1]).generate()
    print(f"   Result: {'Passed' if res2 else 'Failed'}")

    print("\nTest 3: Teacher Hour Limit (Expected: None / 0 placed)")
    t_lim = Teacher("T2", "Petrov", 1, ["Mon"])
    tasks3 = [LessonTask("1", t_lim, g1, s1), LessonTask("2", t_lim, g1, s1)]
    res3 = ScheduleGenerator(tasks3, ["Mon_1", "Mon_2"], [Auditorium("A1", 30, "lecture", days)]).generate()
    placed = sum(len(v) for v in res3.values()) if res3 else 0
    print(f"   Result: {'Passed' if placed == 0 else 'Failed'} (Placed: {placed})")

    print("\nEdge case testing completed.")

if __name__ == "__main__":
    run_edge_case_tests()