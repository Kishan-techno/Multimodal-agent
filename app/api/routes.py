"""
FastAPI HTTP Routes for Multimodal Attendance & Engagement Agent.
Provides views and REST endpoints for sessions, students, analytics, and CSV exports.
"""
import io
import csv
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Request, Form, UploadFile, File, Response
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from app.database import db
from app.database import seed_data
import config

router = APIRouter()
templates = Jinja2Templates(directory=str(config.TEMPLATES_DIR))

@router.get("/", response_class=HTMLResponse)
async def dashboard_view(request: Request):
    """Main Instructor Live Monitoring Dashboard."""
    session = db.get_active_session()
    if not session:
        seed_data.seed_database()
        session = db.get_active_session()

    students = db.get_all_students()
    attendance = db.get_session_attendance(session["id"]) if session else []
    suggestions = db.get_session_suggestions(session["id"]) if session else []
    
    total_present = sum(1 for a in attendance if a["status"] == "PRESENT")
    total_partial = sum(1 for a in attendance if a["status"] == "PARTIAL")

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "session": session,
            "students": students,
            "attendance": attendance,
            "suggestions": [s for s in suggestions if not s["is_dismissed"]][:5],
            "total_present": total_present,
            "total_partial": total_partial,
            "total_enrolled": len(students),
            "config": config.ATTENDANCE_CONFIG
        }
    )

@router.get("/students", response_class=HTMLResponse)
async def students_view(request: Request):
    """Student Enrollment & Roster Management."""
    students = db.get_all_students()
    return templates.TemplateResponse(
        request=request,
        name="students.html",
        context={
            "students": students
        }
    )

@router.post("/api/students")
async def add_student_endpoint(
    student_id: str = Form(...),
    name: str = Form(...),
    email: str = Form(...),
    department: str = Form("Computer Science"),
    roll_no: str = Form(...)
):
    """Enrolls a new student in the system."""
    db.add_student(
        student_id=student_id.strip(),
        name=name.strip(),
        email=email.strip(),
        department=department.strip(),
        roll_no=roll_no.strip()
    )
    return RedirectResponse(url="/students", status_code=303)

@router.get("/analytics", response_class=HTMLResponse)
async def analytics_view(request: Request):
    """Detailed Session Analytics & Engagement Deep Dive."""
    session = db.get_active_session()
    if not session:
        session = {"id": 1, "session_name": "Classroom Session"}
    
    metrics = db.get_session_metrics(session["id"], limit=180)
    attendance = db.get_session_attendance(session["id"])
    
    return templates.TemplateResponse(
        request=request,
        name="analytics.html",
        context={
            "session": session,
            "metrics": metrics,
            "attendance": attendance
        }
    )

@router.get("/reports", response_class=HTMLResponse)
async def reports_view(request: Request):
    """Formal Attendance & Session Audit Report."""
    session = db.get_active_session()
    attendance = db.get_session_attendance(session["id"]) if session else []
    metrics = db.get_session_metrics(session["id"], limit=60) if session else []
    suggestions = db.get_session_suggestions(session["id"]) if session else []

    avg_engagement = round(sum(m["overall_score"] for m in metrics) / max(1, len(metrics)), 1) if metrics else 76.5
    total_present = sum(1 for a in attendance if a["status"] == "PRESENT")

    return templates.TemplateResponse(
        request=request,
        name="report.html",
        context={
            "session": session,
            "attendance": attendance,
            "suggestions": suggestions,
            "avg_engagement": avg_engagement,
            "total_present": total_present,
            "total_enrolled": len(attendance),
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    )

@router.get("/api/attendance/export.csv")
async def export_attendance_csv():
    """Generates timestamped CSV attendance log with sustained presence duration."""
    session = db.get_active_session()
    if not session:
        return Response("No active session", status_code=404)

    attendance = db.get_session_attendance(session["id"])
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Student ID", "Roll Number", "Full Name", "Department",
        "Attendance Status", "Sustained Duration (s)", "Verification Confidence",
        "First Seen", "Last Seen", "Session Name"
    ])

    for row in attendance:
        writer.writerow([
            row["student_id"],
            row["roll_no"],
            row["name"],
            row["department"],
            row["status"],
            row["sustained_duration_seconds"],
            f"{row['verification_confidence'] * 100:.1f}%",
            row["first_seen"],
            row["last_seen"],
            session["session_name"]
        ])

    output.seek(0)
    filename = f"Attendance_{session['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.post("/api/session/new")
async def start_new_session(
    session_name: str = Form(...),
    instructor: str = Form("Dr. Harrison Vance"),
    subject: str = Form("Machine Learning & AI")
):
    """Starts a fresh classroom intelligence session."""
    session_id = db.create_session(session_name, instructor, subject)
    return RedirectResponse(url="/", status_code=303)

@router.post("/api/suggestions/{suggestion_id}/dismiss")
async def dismiss_suggestion_endpoint(suggestion_id: int):
    """Dismisses an alert card in the teacher's feed."""
    db.dismiss_suggestion(suggestion_id)
    return {"status": "ok", "dismissed_id": suggestion_id}
