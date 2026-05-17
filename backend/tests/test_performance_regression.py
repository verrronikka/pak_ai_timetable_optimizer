import json
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient

from backend.db_models import GenerationJob, SessionLocal
from backend.main import app

client = TestClient(app)
REPORT_PATH = (
    Path(__file__).resolve().parents[2]
    / "reports"
    / "generated"
    / "performance_regression_latest.json"
)


def make_regression_payload():
    days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    return {
        "teachers": [
            {
                "id": f"t{idx}",
                "name": f"Teacher {idx}",
                "max_hours": 40,
                "available_days": days,
            }
            for idx in range(1, 5)
        ],
        "groups": [
            {
                "id": f"g{idx}",
                "name": f"Group {idx}",
                "student_count": 20 + idx,
            }
            for idx in range(1, 7)
        ],
        "auditoriums": [
            {
                "id": f"a{idx}",
                "capacity": 80,
                "type": "lecture",
                "available_days": days,
            }
            for idx in range(1, 7)
        ],
        "subjects": [
            {
                "id": f"s{idx}",
                "name": f"Subject {idx}",
                "hours_per_week": 1,
                "required_auditorium_type": "lecture",
                "is_lecture": True,
            }
            for idx in range(1, 3)
        ],
        "max_search_steps": 20000,
    }


def clear_jobs():
    db = SessionLocal()
    try:
        db.query(GenerationJob).delete()
        db.commit()
    finally:
        db.close()


def wait_for_job(job_id: int, timeout_seconds: float = 15.0):
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


class PerformanceRegressionTests(unittest.TestCase):
    def setUp(self):
        clear_jobs()

    def test_generation_time_regression_threshold(self):
        threshold_seconds = 5.0
        payload = make_regression_payload()

        start = time.perf_counter()
        create_response = client.post("/api/generate", json=payload)
        self.assertEqual(create_response.status_code, 200)
        job_id = create_response.json()["job_id"]

        schedule_response = wait_for_job(job_id)
        elapsed = time.perf_counter() - start

        self.assertIsNotNone(schedule_response)
        self.assertEqual(schedule_response.status_code, 200)
        self.assertEqual(schedule_response.json().get("status"), "completed")

        metrics_response = client.get(f"/api/metrics/{job_id}")
        self.assertEqual(metrics_response.status_code, 200)
        metrics_payload = metrics_response.json()

        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(
            json.dumps(
                {
                    "job_id": job_id,
                    "threshold_seconds": threshold_seconds,
                    "elapsed_seconds": round(elapsed, 6),
                    "status": schedule_response.json().get("status"),
                    "metrics": metrics_payload.get("metrics"),
                    "generated_at_utc": time.strftime(
                        "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
                    ),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        self.assertLess(
            elapsed,
            threshold_seconds,
            (
                "Generation time regression detected: "
                f"{elapsed:.3f}s >= {threshold_seconds:.3f}s"
            ),
        )


if __name__ == "__main__":
    unittest.main()
