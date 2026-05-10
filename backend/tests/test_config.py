import importlib
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


class ConfigTests(unittest.TestCase):
    def test_default_max_search_steps_is_shared(self):
        from backend import db_models

        job_column_default = (
            db_models.GenerationJob.__table__.columns["max_search_steps"]
        ).default.arg
        request_default = db_models.ScheduleRequest.model_fields[
            "max_search_steps"
        ].default

        self.assertEqual(
            db_models.DEFAULT_MAX_SEARCH_STEPS,
            db_models.settings.default_max_search_steps,
        )
        self.assertEqual(
            request_default,
            db_models.DEFAULT_MAX_SEARCH_STEPS,
        )
        self.assertEqual(
            job_column_default,
            db_models.DEFAULT_MAX_SEARCH_STEPS,
        )

    def test_default_max_search_steps_can_be_overridden_by_env(self):
        env_var = "DEFAULT_MAX_SEARCH_STEPS"
        original_value = os.environ.get(env_var)
        os.environ[env_var] = "123456"

        try:
            from backend import db_models

            reloaded = importlib.reload(db_models)

            reloaded_request_default = reloaded.ScheduleRequest.model_fields[
                "max_search_steps"
            ].default
            reloaded_job_default = (
                reloaded.GenerationJob.__table__.columns["max_search_steps"]
            ).default.arg

            self.assertEqual(
                reloaded.settings.default_max_search_steps,
                123456,
            )
            self.assertEqual(reloaded.DEFAULT_MAX_SEARCH_STEPS, 123456)
            self.assertEqual(reloaded_request_default, 123456)
            self.assertEqual(reloaded_job_default, 123456)
        finally:
            if original_value is None:
                os.environ.pop(env_var, None)
            else:
                os.environ[env_var] = original_value
            importlib.reload(db_models)


if __name__ == "__main__":
    unittest.main()
