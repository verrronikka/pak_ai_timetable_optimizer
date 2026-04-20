import json
import random
import os

def main():
    # random.seed(42)
    
    # Paths
    script_dir = os.path.dirname(__file__)
    os.makedirs(script_dir, exist_ok=True)

    days = ["Mon", "Tue", "Wed", "Thu", "Fri"]

    teachers = [
        {
            "id": f"T{i}",
            "name": f"Teacher {i}",
            "max_hours": random.choice([16, 18, 20]),
            "available_days": random.sample(days, random.randint(3, 5))
        }
        for i in range(1, 8)
    ]

    groups = [
        {"id": f"G{i}", "name": f"Group {i}", "student_count": random.randint(18, 30)}
        for i in range(1, 5)
    ]

    auditoriums = [
        {"id": "A1", "capacity": 40, "type": "lecture", "available_days": days},
        {"id": "A2", "capacity": 25, "type": "practice", "available_days": days},
        {"id": "A3", "capacity": 20, "type": "lab", "available_days": days},
        {"id": "A4", "capacity": 30, "type": "lecture", "available_days": ["Mon", "Tue", "Wed"]},
        {"id": "A5", "capacity": 25, "type": "practice", "available_days": ["Wed", "Thu", "Fri"]}
    ]

    subjects = [
        {"id": "S1", "name": "Mathematics", "hours_per_week": 4, "required_auditorium_type": "lecture", "is_lecture": True},
        {"id": "S2", "name": "Physics", "hours_per_week": 2, "required_auditorium_type": "practice", "is_lecture": False},
        {"id": "S3", "name": "Computer Science", "hours_per_week": 2, "required_auditorium_type": "lab", "is_lecture": False},
        {"id": "S4", "name": "History", "hours_per_week": 2, "required_auditorium_type": "practice", "is_lecture": False}
    ]

    datasets = {
        "teachers.json": teachers,
        "groups.json": groups,
        "auditoriums.json": auditoriums,
        "subjects.json": subjects
    }

    for filename, data in datasets.items():
        filepath = os.path.join(script_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Generated: {filepath}")

if __name__ == "__main__":
    main()