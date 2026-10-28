"""
Configuration module for Multimodal Attendance & Engagement Agent
Classroom Intelligence System
"""
import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
STUDENTS_DIR = DATA_DIR / "students"
EXPORTS_DIR = DATA_DIR / "exports"
STATIC_DIR = BASE_DIR / "app" / "static"
TEMPLATES_DIR = BASE_DIR / "app" / "templates"
DATABASE_PATH = DATA_DIR / "attendance_engagement.db"

# Ensure runtime directories exist
STUDENTS_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Sustained Presence Attendance Parameters
# For live demonstrations: 5 seconds of presence to mark attendance.
# For standard classroom deployment: typically 30-300 seconds.
ATTENDANCE_CONFIG = {
    "SUSTAINED_PRESENCE_SECONDS": 5.0,  # Minimum sustained presence needed for "PRESENT"
    "PARTIAL_PRESENCE_SECONDS": 2.0,    # Minimum presence for "PARTIAL" status
    "CONFIDENCE_THRESHOLD": 0.55,       # Face recognition similarity threshold
    "MAX_ABSENCE_GAP_SECONDS": 10.0,    # Gap allowed before a new presence span is started
    "FRAME_PROCESS_FPS": 5,             # Process rate to conserve CPU
}

# Multimodal Fusion Weights & Thresholds
ENGAGEMENT_CONFIG = {
    # Weights sum to 1.0
    "WEIGHT_VISUAL_ATTENTION": 0.45,  # Gaze, head pose, eye openness
    "WEIGHT_FACIAL_EXPRESSION": 0.20, # Attentive vs bored/confused/drowsy
    "WEIGHT_AUDIO_ACTIVITY": 0.20,    # Speech/discussion vs prolonged silence
    "WEIGHT_BODY_MOTION": 0.15,       # Dynamic movement vs slumped inactivity/excessive fidgeting

    # Attention Thresholds
    "HIGH_ENGAGEMENT_THRESHOLD": 75.0,
    "MODERATE_ENGAGEMENT_THRESHOLD": 50.0,
    "LOW_ENGAGEMENT_THRESHOLD": 35.0,

    # Head Pose Limits (degrees)
    "YAW_TOLERANCE": 25.0,    # Left/Right head turn
    "PITCH_TOLERANCE": 20.0,  # Up/Down tilt (looking down at phone/desk)

    # Rolling window for time-series analysis (seconds)
    "ROLLING_WINDOW_SECONDS": 60,
    "DROPOUT_DETECTION_WINDOW_SECONDS": 15,
}

# AI Teaching Suggestion Agent Settings
AGENT_CONFIG = {
    "ALERT_COOLDOWN_SECONDS": 20,       # Avoid alert spamming the instructor
    "MIN_CONFIDENCE_FOR_ALERT": 0.70,
    "GEMINI_MODEL": "gemini-1.5-flash", # Fallback to local expert rules if API key not set
    "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", ""),
}

# Web Server Settings
SERVER_CONFIG = {
    "HOST": "127.0.0.1",
    "PORT": 8000,
    "DEBUG": True,
}
