"""
Pre-populates sample students and demographic data for classroom demonstration.
"""
from app.database import db

INITIAL_STUDENTS = [
    {
        "student_id": "STU-1001",
        "name": "Alex Chen",
        "email": "alex.chen@university.edu",
        "department": "Artificial Intelligence",
        "roll_no": "AI-2024-041",
    },
    {
        "student_id": "STU-1002",
        "name": "Priya Sharma",
        "email": "priya.sharma@university.edu",
        "department": "Data Science",
        "roll_no": "DS-2024-019",
    },
    {
        "student_id": "STU-1003",
        "name": "Rohan Mehta",
        "email": "rohan.mehta@university.edu",
        "department": "Computer Science",
        "roll_no": "CS-2024-088",
    },
    {
        "student_id": "STU-1004",
        "name": "Sarah Khan",
        "email": "sarah.khan@university.edu",
        "department": "Machine Learning",
        "roll_no": "ML-2024-012",
    },
    {
        "student_id": "STU-1005",
        "name": "David Miller",
        "email": "david.miller@university.edu",
        "department": "Computer Science",
        "roll_no": "CS-2024-105",
    },
    {
        "student_id": "STU-1006",
        "name": "Ananya Patel",
        "email": "ananya.patel@university.edu",
        "department": "Information Systems",
        "roll_no": "IS-2024-033",
    }
]

def seed_database():
    """Seeds the initial roster and an initial active session if empty."""
    db.init_db()
    
    # Check if students already exist
    existing = db.get_all_students()
    if not existing:
        for s in INITIAL_STUDENTS:
            db.add_student(
                student_id=s["student_id"],
                name=s["name"],
                email=s["email"],
                department=s["department"],
                roll_no=s["roll_no"],
            )
        print(f"Seeded {len(INITIAL_STUDENTS)} students successfully.")
    
    # Check active session
    active = db.get_active_session()
    if not active:
        session_id = db.create_session(
            session_name="Lecture 14: Multimodal AI & Neural Architectures",
            instructor_name="Prof. Harrison Vance",
            subject="Deep Learning & Multimodal Systems"
        )
        print(f"Created active classroom session: ID {session_id}")
