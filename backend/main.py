from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from datetime import datetime
import sys
from pathlib import Path

dev_alg_path = str(Path(__file__).parent.parent / "dev_alg")
if dev_alg_path not in sys.path:
    sys.path.insert(0, dev_alg_path)

from models import Teacher, Group, Auditorium, Subject, LessonTask
from schedule_generator import ScheduleGenerator

try:
    from db_models import (
        Base, engine, SessionLocal,
        GenerationJob, ScheduleRequest, ScheduleResponse,
        TeacherInput, GroupInput, AuditoriumInput, SubjectInput
    )
except ImportError:
    from .db_models import (
        Base, engine, SessionLocal,
        GenerationJob, ScheduleRequest, ScheduleResponse,
        TeacherInput, GroupInput, AuditoriumInput, SubjectInput
    )


app = FastAPI(
    title="AI Timetable Optimizer API",
    description="API для автоматической генерации расписания",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

def create_lesson_tasks(
    teachers: List[Teacher],
    groups: List[Group],
    subjects: List[Subject]
) -> List[LessonTask]:
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
    
    return tasks

def generate_time_slots():
    days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    return [f"{day}_{p}" for day in days for p in range(1, 5)]

def run_generation(job_id: int, request: ScheduleRequest):
    db = SessionLocal()
    
    try:
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        job.status = "running"
        db.commit()
        
        teachers = [Teacher(t.id, t.name, t.max_hours, t.available_days) for t in request.teachers]
        groups = [Group(g.id, g.name, g.student_count) for g in request.groups]
        auditoriums = [Auditorium(a.id, a.capacity, a.type, a.available_days) for a in request.auditoriums]
        subjects = [Subject(s.id, s.name, s.hours_per_week, s.required_auditorium_type, s.is_lecture) for s in request.subjects]
        
        tasks = create_lesson_tasks(teachers, groups, subjects)
        time_slots = generate_time_slots()
        
        generator = ScheduleGenerator(
            tasks=tasks,
            time_slots=time_slots,
            auditoriums=auditoriums,
            max_search_steps=request.max_search_steps
        )
        
        result = generator.generate()
        
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        job.completed_at = datetime.utcnow()
        
        if result:
            schedule_data = {}
            for ts, lessons in result.items():
                schedule_data[ts] = [
                    {
                        "auditorium": aud_id,
                        "group": lesson.group.id,
                        "group_name": lesson.group.name,
                        "subject": lesson.subject.name,
                        "teacher": lesson.teacher.name,
                    }
                    for aud_id, lesson in lessons.items()
                ]
            
            job.status = "completed"
            job.result = {
                "schedule": schedule_data,
                "solve_status": generator.solve_status,
                "search_steps": generator.search_steps
            }
        else:
            job.status = "failed"
            job.error_message = f"Не удалось составить расписание. Статус: {generator.solve_status}"
            job.result = {
                "solve_status": generator.solve_status,
                "search_steps": generator.search_steps
            }
        
        db.commit()
        
    except Exception as e:
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        job.status = "failed"
        job.error_message = str(e)
        job.completed_at = datetime.utcnow()
        db.commit()
        
    finally:
        db.close()

# API ENDPOINTS
@app.get("/")
async def root():
    return {"message": "AI Timetable Optimizer API", "status": "running", "docs": "/docs"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/generate", response_model=ScheduleResponse)
async def generate_schedule(request: ScheduleRequest, background_tasks: BackgroundTasks):
    db = SessionLocal()
    
    try:
        job = GenerationJob(status="pending", max_search_steps=request.max_search_steps)
        db.add(job)
        db.commit()
        db.refresh(job)
        job_id = job.id
    finally:
        db.close()
    
    background_tasks.add_task(run_generation, job_id, request)
    
    return ScheduleResponse(
        job_id=job_id,
        status="pending",
        message="Генерация запущена. Используйте GET /api/schedule/{job_id}"
    )

@app.get("/api/schedule/{job_id}", response_model=ScheduleResponse)
async def get_schedule(job_id: int):
    db = SessionLocal()
    
    try:
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="Задача не найдена")
        
        return ScheduleResponse(
            job_id=job.id,
            status=job.status,
            schedule=job.result if job.status == "completed" else None,
            error_message=job.error_message
        )
    finally:
        db.close()

@app.get("/api/jobs")
async def list_jobs():
    db = SessionLocal()
    
    try:
        jobs = db.query(GenerationJob).order_by(GenerationJob.created_at.desc()).all()
        
        return [
            {
                "id": job.id,
                "status": job.status,
                "created_at": job.created_at.isoformat(),
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "max_search_steps": job.max_search_steps
            }
            for job in jobs
        ]
    finally:
        db.close()

@app.delete("/api/schedule/{job_id}")
async def delete_job(job_id: int):
    db = SessionLocal()
    
    try:
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="Задача не найдена")
        
        db.delete(job)
        db.commit()
        
        return {"message": f"Задача {job_id} удалена"}
    finally:
        db.close()