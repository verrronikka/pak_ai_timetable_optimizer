import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient

from backend.db_models import GenerationJob, SessionLocal
from backend.main import app

client = TestClient(app)


def make_valid_request():
    return {
        "teachers": [
            {
                "id": "t1",
                "name": "Teacher 1",
                "max_hours": 4,
                "available_days": ["Mon", "Tue"],
            },
            {
                "id": "t2",
                "name": "Teacher 2",
                "max_hours": 4,
                "available_days": ["Mon", "Tue"],
            },
        ],
        "groups": [
            {
                "id": "g1",
                "name": "Group 1",
                "student_count": 20,
            },
        ],
        "auditoriums": [
            {
                "id": "a1",
                "capacity": 40,
                "type": "lecture",
                "available_days": ["Mon", "Tue"],
            },
        ],
        "subjects": [
            {
                "id": "s1",
                "name": "Math",
                "hours_per_week": 1,
                "required_auditorium_type": "lecture",
                "is_lecture": True,
            },
        ],
        "max_search_steps": 100,
    }


def clear_jobs():
    db = SessionLocal()
    try:
        db.query(GenerationJob).delete()
        db.commit()
    finally:
        db.close()


def wait_for_job(job_id: int, timeout_seconds: float = 5.0):
    deadline = time.time() + timeout_seconds
    response = None
    while time.time() < deadline:
        response = client.get(f"/api/schedule/{job_id}")
        if response.status_code == 200:
            status = response.json().get("status")
            if status in {"completed", "failed"}:
                return response
        time.sleep(0.05)
    return response


class ApiTests(unittest.TestCase):
    def setUp(self):
        clear_jobs()

    def test_health_check(self):
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")

    def test_generate_success_and_get_schedule(self):
        response = client.post("/api/generate", json=make_valid_request())
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "pending")
        self.assertIn("job_id", payload)

        schedule_response = wait_for_job(payload["job_id"])
        self.assertIsNotNone(schedule_response)
        self.assertEqual(schedule_response.status_code, 200)
        schedule_payload = schedule_response.json()
        self.assertEqual(schedule_payload["status"], "completed")
        self.assertIsNotNone(schedule_payload["schedule"])
        self.assertIsNone(schedule_payload.get("error"))

    def test_generate_rejects_empty_teachers(self):
        request = make_valid_request()
        request["teachers"] = []

        response = client.post("/api/generate", json=request)
        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertEqual(payload["detail"]["error"], "validation_error")
        self.assertEqual(payload["detail"]["details"]["field"], "teachers")

    def test_generate_rejects_invalid_capacity(self):
        request = make_valid_request()
        request["groups"][0]["student_count"] = 120

        response = client.post("/api/generate", json=request)
        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertEqual(payload["detail"]["error"], "validation_error")
        self.assertEqual(payload["detail"]["details"]["field"], "groups")

    def test_generate_rejects_duplicate_teacher_ids(self):
        request = make_valid_request()
        request["teachers"][1]["id"] = request["teachers"][0]["id"]

        response = client.post("/api/generate", json=request)
        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertEqual(payload["detail"]["error"], "validation_error")
        self.assertEqual(payload["detail"]["details"]["field"], "teachers")
        self.assertIn(
            request["teachers"][0]["id"],
            payload["detail"]["details"]["duplicate_ids"],
        )

    def test_generate_rejects_missing_auditorium_type(self):
        request = make_valid_request()
        request["auditoriums"][0]["type"] = "practice"

        response = client.post("/api/generate", json=request)
        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertEqual(payload["detail"]["error"], "validation_error")
        self.assertEqual(payload["detail"]["details"]["field"], "subjects")
        self.assertEqual(
            payload["detail"]["details"]["required_auditorium_type"],
            "lecture",
        )

    def test_generate_rejects_invalid_search_limit(self):
        request = make_valid_request()
        request["max_search_steps"] = 0

        response = client.post("/api/generate", json=request)
        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertEqual(payload["detail"]["error"], "validation_error")
        self.assertEqual(
            payload["detail"]["details"]["field"], "max_search_steps"
        )

    def test_schedule_contract_reports_no_solution(self):
        from backend import main as backend_main

        original_generate = backend_main.ScheduleGenerator.generate

        def fake_generate(self):
            self.solve_status = "нет_решения"
            self.search_steps = 7
            return None

        backend_main.ScheduleGenerator.generate = fake_generate
        try:
            response = client.post("/api/generate", json=make_valid_request())
            self.assertEqual(response.status_code, 200)
            job_id = response.json()["job_id"]

            schedule_response = wait_for_job(job_id)
            self.assertIsNotNone(schedule_response)
            self.assertEqual(schedule_response.status_code, 200)
            payload = schedule_response.json()
            self.assertEqual(payload["status"], "failed")
            self.assertEqual(payload["error"]["error"], "нет_решения")
            self.assertIn(
                "Не удалось составить расписание", payload["error"]["message"]
            )
        finally:
            backend_main.ScheduleGenerator.generate = original_generate

    def test_schedule_contract_reports_server_error(self):
        from backend import main as backend_main

        original_generate = backend_main.ScheduleGenerator.generate

        def fake_generate(self):
            raise RuntimeError("boom")

        backend_main.ScheduleGenerator.generate = fake_generate
        try:
            response = client.post("/api/generate", json=make_valid_request())
            self.assertEqual(response.status_code, 200)
            job_id = response.json()["job_id"]

            schedule_response = wait_for_job(job_id)
            self.assertIsNotNone(schedule_response)
            self.assertEqual(schedule_response.status_code, 200)
            payload = schedule_response.json()
            self.assertEqual(payload["status"], "failed")
            self.assertEqual(payload["error"]["error"], "server_error")
            self.assertEqual(payload["error"]["job_id"], job_id)
        finally:
            backend_main.ScheduleGenerator.generate = original_generate

    def test_schedule_contract_reports_limit_reached(self):
        from backend import main as backend_main

        original_generate = backend_main.ScheduleGenerator.generate

        def fake_generate(self):
            self.solve_status = "лимит_поиска_достигнут"
            self.search_steps = 100
            return None

        backend_main.ScheduleGenerator.generate = fake_generate
        try:
            response = client.post("/api/generate", json=make_valid_request())
            self.assertEqual(response.status_code, 200)
            job_id = response.json()["job_id"]

            schedule_response = wait_for_job(job_id)
            self.assertIsNotNone(schedule_response)
            self.assertEqual(schedule_response.status_code, 200)
            payload = schedule_response.json()
            self.assertEqual(payload["status"], "failed")
            self.assertEqual(
                payload["error"]["error"], "лимит_поиска_достигнут"
            )
            self.assertEqual(payload["error"]["job_id"], job_id)
        finally:
            backend_main.ScheduleGenerator.generate = original_generate

    def test_get_schedule_returns_404_for_missing_job(self):
        response = client.get("/api/schedule/999999")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Задача не найдена")

    def test_delete_schedule_returns_404_for_missing_job(self):
        response = client.delete("/api/schedule/999999")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Задача не найдена")


if __name__ == "__main__":
    unittest.main()
