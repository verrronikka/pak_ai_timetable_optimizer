from sqlalchemy import create_engine, Column, Integer, String, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

Base = declarative_base()
engine = create_engine("sqlite:///./timetable.db", connect_args={"check_same_thread": False})
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

class ScheduleRequest(BaseModel):
    teachers: List[TeacherInput]
    groups: List[GroupInput]
    auditoriums: List[AuditoriumInput]
    subjects: List[SubjectInput]
    max_search_steps: Optional[int] = 200000

class ScheduleResponse(BaseModel):
    job_id: int
    status: str
    schedule: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    message: Optional[str] = None