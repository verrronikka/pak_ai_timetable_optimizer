from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict
from pydantic_settings import BaseSettings
from sqlalchemy import JSON, Column, DateTime, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


class Settings(BaseSettings):
    database_url: str = "sqlite:///./timetable.db"
    default_max_search_steps: int = 200000


settings = Settings()
DEFAULT_MAX_SEARCH_STEPS = settings.default_max_search_steps

Base = declarative_base()
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    result = Column(JSON, nullable=True)
    error_message = Column(String, nullable=True)
    max_search_steps = Column(Integer, default=DEFAULT_MAX_SEARCH_STEPS)


class TeacherInput(BaseModel):
    id: str
    name: str
    max_hours: int
    available_days: List[str]


class GroupInput(BaseModel):
    id: str
    name: str
    student_count: int


class AuditoriumInput(BaseModel):
    id: str
    capacity: int
    type: str
    available_days: List[str]


class SubjectInput(BaseModel):
    id: str
    name: str
    hours_per_week: int
    required_auditorium_type: str
    is_lecture: bool


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    job_id: Optional[int] = None

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "error": "нет_решения",
                    "message": (
                        "Не удалось составить расписание при текущих "
                        "ограничениях."
                    ),
                    "details": {
                        "solve_status": "нет_решения",
                        "search_steps": 7,
                        "max_search_steps": 200000,
                    },
                    "job_id": 42,
                }
            ]
        }
    )


class ScheduleRequest(BaseModel):
    teachers: List[TeacherInput]
    groups: List[GroupInput]
    auditoriums: List[AuditoriumInput]
    subjects: List[SubjectInput]
    max_search_steps: Optional[int] = DEFAULT_MAX_SEARCH_STEPS

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "teachers": [
                        {
                            "id": "t1",
                            "name": "Teacher 1",
                            "max_hours": 4,
                            "available_days": ["Mon", "Tue"],
                        }
                    ],
                    "groups": [
                        {
                            "id": "g1",
                            "name": "Group 1",
                            "student_count": 20,
                        }
                    ],
                    "auditoriums": [
                        {
                            "id": "a1",
                            "capacity": 40,
                            "type": "lecture",
                            "available_days": ["Mon", "Tue"],
                        }
                    ],
                    "subjects": [
                        {
                            "id": "s1",
                            "name": "Math",
                            "hours_per_week": 1,
                            "required_auditorium_type": "lecture",
                            "is_lecture": True,
                        }
                    ],
                    "max_search_steps": 100,
                }
            ]
        }
    )


class ScheduleResponse(BaseModel):
    job_id: int
    status: str
    schedule: Optional[Dict[str, Any]] = None
    error: Optional[ErrorResponse] = None
    error_message: Optional[str] = None
    message: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "job_id": 42,
                    "status": "pending",
                    "message": (
                        "Генерация запущена. Используйте GET "
                        "/api/schedule/{job_id}"
                    ),
                    "schedule": None,
                    "error": None,
                    "error_message": None,
                }
            ]
        }
    )
