from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from pydantic_settings import BaseSettings
from sqlalchemy import JSON, Column, DateTime, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


class Settings(BaseSettings):
    database_url: str = "sqlite:///./timetable.db"
    default_max_search_steps: int = 200000


settings = Settings()

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
    max_search_steps = Column(Integer, default=200000)


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


class ScheduleRequest(BaseModel):
    teachers: List[TeacherInput]
    groups: List[GroupInput]
    auditoriums: List[AuditoriumInput]
    subjects: List[SubjectInput]
    max_search_steps: Optional[int] = settings.default_max_search_steps


class ScheduleResponse(BaseModel):
    job_id: int
    status: str
    schedule: Optional[Dict[str, Any]] = None
    error: Optional[ErrorResponse] = None
    error_message: Optional[str] = None
    message: Optional[str] = None
