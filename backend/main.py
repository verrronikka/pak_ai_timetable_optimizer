import sys
from datetime import datetime
from pathlib import Path
from typing import Any, List, cast

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

dev_alg_path = str(Path(__file__).parent.parent / "dev_alg")
if dev_alg_path not in sys.path:
    sys.path.insert(0, dev_alg_path)

from models import (  # noqa: E402, pyright: ignore[reportMissingImports]
    Auditorium,
    Group,
    LessonTask,
    Subject,
    Teacher,
)
from schedule_generator import ScheduleGenerator  # noqa: E402

try:
    from db_models import (
        Base,
        ErrorResponse,
        GenerationJob,
        ScheduleRequest,
        ScheduleResponse,
        SessionLocal,
        engine,
    )
except ImportError:
    from .db_models import (
        Base,
        ErrorResponse,
        GenerationJob,
        ScheduleRequest,
        ScheduleResponse,
        SessionLocal,
        engine,
    )


app = FastAPI(
    title="AI Timetable Optimizer API",
    description="API для автоматической генерации расписания",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


def build_error_response(
    error: str,
    message: str,
    details: dict | None = None,
    job_id: int | None = None,
) -> ErrorResponse:
    return ErrorResponse(
        error=error,
        message=message,
        details=details,
        job_id=job_id,
    )


def raise_validation_error(message: str, details: dict) -> None:
    raise HTTPException(
        status_code=400,
        detail=build_error_response(
            error="validation_error",
            message=message,
            details=details,
        ).model_dump(),
    )


def validate_generate_request(request: ScheduleRequest) -> None:
    if request.max_search_steps is None or request.max_search_steps <= 0:
        raise_validation_error(
            "Параметр max_search_steps должен быть положительным числом.",
            {
                "field": "max_search_steps",
                "value": request.max_search_steps,
            },
        )

    if not request.teachers:
        raise_validation_error(
            "Список преподавателей не может быть пустым.",
            {"field": "teachers"},
        )
    if not request.groups:
        raise_validation_error(
            "Список групп не может быть пустым.",
            {"field": "groups"},
        )
    if not request.auditoriums:
        raise_validation_error(
            "Список аудиторий не может быть пустым.",
            {"field": "auditoriums"},
        )
    if not request.subjects:
        raise_validation_error(
            "Список предметов не может быть пустым.",
            {"field": "subjects"},
        )

    duplicate_checks = [
        ("teachers", request.teachers),
        ("groups", request.groups),
        ("auditoriums", request.auditoriums),
        ("subjects", request.subjects),
    ]
    for field_name, items in duplicate_checks:
        ids = [item.id for item in items]
        duplicate_ids = sorted(
            {item_id for item_id in ids if ids.count(item_id) > 1}
        )
        if duplicate_ids:
            raise_validation_error(
                f"В списке {field_name} найдены дублирующиеся id.",
                {"field": field_name, "duplicate_ids": duplicate_ids},
            )

    for teacher in request.teachers:
        if teacher.max_hours <= 0:
            raise_validation_error(
                (
                    f"У преподавателя {teacher.id} max_hours "
                    "должен быть больше нуля."
                ),
                {
                    "field": "teachers",
                    "teacher_id": teacher.id,
                    "max_hours": teacher.max_hours,
                },
            )
        if not teacher.available_days:
            raise_validation_error(
                (
                    f"У преподавателя {teacher.id} должен быть "
                    "хотя бы один доступный день."
                ),
                {"field": "teachers", "teacher_id": teacher.id},
            )

    for group in request.groups:
        if group.student_count <= 0:
            raise_validation_error(
                (
                    f"У группы {group.id} количество студентов "
                    "должно быть больше нуля."
                ),
                {
                    "field": "groups",
                    "group_id": group.id,
                    "student_count": group.student_count,
                },
            )

    auditorium_types = {auditorium.type for auditorium in request.auditoriums}
    max_capacity = max(
        auditorium.capacity for auditorium in request.auditoriums
    )
    max_group_size = max(group.student_count for group in request.groups)

    for auditorium in request.auditoriums:
        if auditorium.capacity <= 0:
            raise_validation_error(
                (
                    f"У аудитории {auditorium.id} вместимость "
                    "должна быть больше нуля."
                ),
                {
                    "field": "auditoriums",
                    "auditorium_id": auditorium.id,
                    "capacity": auditorium.capacity,
                },
            )
        if not auditorium.available_days:
            raise_validation_error(
                (
                    f"У аудитории {auditorium.id} должен быть "
                    "хотя бы один доступный день."
                ),
                {"field": "auditoriums", "auditorium_id": auditorium.id},
            )

    for subject in request.subjects:
        if subject.hours_per_week <= 0:
            raise_validation_error(
                (
                    f"У предмета {subject.id} hours_per_week "
                    "должен быть больше нуля."
                ),
                {
                    "field": "subjects",
                    "subject_id": subject.id,
                    "hours_per_week": subject.hours_per_week,
                },
            )

        if subject.required_auditorium_type not in auditorium_types:
            raise_validation_error(
                (
                    "Нет доступных аудиторий типа "
                    f"'{subject.required_auditorium_type}' для предмета "
                    f"'{subject.name}'."
                ),
                {
                    "field": "subjects",
                    "subject_id": subject.id,
                    "required_auditorium_type": (
                        subject.required_auditorium_type
                    ),
                },
            )

    if max_capacity < max_group_size:
        raise_validation_error(
            (
                "Ни одна аудитория не подходит по вместимости "
                "хотя бы для одной группы."
            ),
            {
                "field": "groups",
                "max_auditorium_capacity": max_capacity,
                "max_group_size": max_group_size,
            },
        )


def create_lesson_tasks(
    teachers: List[Teacher], groups: List[Group], subjects: List[Subject]
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
        job = cast(
            Any,
            db.query(GenerationJob).filter(GenerationJob.id == job_id).first(),
        )
        if job is None:
            raise RuntimeError(f"Generation job {job_id} not found")

        job.status = "running"
        db.commit()

        teachers = [
            Teacher(t.id, t.name, t.max_hours, t.available_days)
            for t in request.teachers
        ]
        groups = [Group(g.id, g.name, g.student_count) for g in request.groups]
        auditoriums = [
            Auditorium(a.id, a.capacity, a.type, a.available_days)
            for a in request.auditoriums
        ]
        subjects = [
            Subject(
                s.id,
                s.name,
                s.hours_per_week,
                s.required_auditorium_type,
                s.is_lecture,
            )
            for s in request.subjects
        ]

        tasks = create_lesson_tasks(teachers, groups, subjects)
        time_slots = generate_time_slots()

        generator = ScheduleGenerator(
            tasks=tasks,
            time_slots=time_slots,
            auditoriums=auditoriums,
            max_search_steps=request.max_search_steps,
        )

        result = generator.generate()

        job = (
            db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        )
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
                "search_steps": generator.search_steps,
            }
        else:
            job.status = "failed"
            error_response = build_error_response(
                error=generator.solve_status or "no_solution",
                message=(
                    "Не удалось составить расписание при текущих ограничениях."
                ),
                details={
                    "solve_status": generator.solve_status,
                    "search_steps": generator.search_steps,
                    "max_search_steps": request.max_search_steps,
                },
                job_id=job_id,
            )
            job.error_message = error_response.message
            job.result = {
                "error": error_response.model_dump(),
                "solve_status": generator.solve_status,
                "search_steps": generator.search_steps,
            }

        db.commit()

    except Exception as e:
        job = cast(
            Any,
            db.query(GenerationJob).filter(GenerationJob.id == job_id).first(),
        )
        if job is None:
            db.close()
            return

        job.status = "failed"
        error_response = build_error_response(
            error="server_error",
            message="Внутренняя ошибка сервера при генерации расписания.",
            details={"exception": str(e)},
            job_id=job_id,
        )
        job.error_message = error_response.message
        job.result = {"error": error_response.model_dump()}
        job.completed_at = datetime.utcnow()
        db.commit()

    finally:
        db.close()


# API ENDPOINTS
@app.get("/")
async def root():
    return {
        "message": "AI Timetable Optimizer API",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/api/generate", response_model=ScheduleResponse)
async def generate_schedule(
    request: ScheduleRequest, background_tasks: BackgroundTasks
):
    validate_generate_request(request)

    db = SessionLocal()

    try:
        job = GenerationJob(
            status="pending", max_search_steps=request.max_search_steps
        )
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
        message="Генерация запущена. Используйте GET /api/schedule/{job_id}",
    )


@app.get("/api/schedule/{job_id}", response_model=ScheduleResponse)
async def get_schedule(job_id: int):
    db = SessionLocal()

    try:
        job = cast(
            Any,
            db.query(GenerationJob).filter(GenerationJob.id == job_id).first(),
        )

        if not job:
            raise HTTPException(status_code=404, detail="Задача не найдена")

        error_data = None
        if job.status == "failed" and isinstance(job.result, dict):
            error_data = job.result.get("error")

        return ScheduleResponse(
            job_id=job.id,
            status=job.status,
            schedule=job.result if job.status == "completed" else None,
            error=ErrorResponse(**error_data)
            if isinstance(error_data, dict)
            else None,
            error_message=job.error_message,
        )
    finally:
        db.close()


@app.get("/api/jobs")
async def list_jobs():
    db = SessionLocal()

    try:
        jobs = cast(
            list[Any],
            db.query(GenerationJob)
            .order_by(GenerationJob.created_at.desc())
            .all(),
        )

        return [
            {
                "id": job.id,
                "status": job.status,
                "created_at": job.created_at.isoformat(),
                "completed_at": job.completed_at.isoformat()
                if job.completed_at
                else None,
                "max_search_steps": job.max_search_steps,
            }
            for job in jobs
        ]
    finally:
        db.close()


@app.delete("/api/schedule/{job_id}")
async def delete_job(job_id: int):
    db = SessionLocal()

    try:
        job = (
            db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        )

        if not job:
            raise HTTPException(status_code=404, detail="Задача не найдена")

        db.delete(job)
        db.commit()

        return {"message": f"Задача {job_id} удалена"}
    finally:
        db.close()
