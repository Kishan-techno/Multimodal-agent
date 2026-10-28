"""
Multimodal Attendance & Engagement Agent - Launcher Script
Starts the FastAPI application and automatically opens Google Chrome.
"""
import sys
import os
import time
import webbrowser
import threading
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

import config
from app.database import db, seed_data

def open_browser():
    """Wait for server to bind and launch Chrome browser."""
    time.sleep(1.2)
    url = f"http://{config.SERVER_CONFIG['HOST']}:{config.SERVER_CONFIG['PORT']}"
    print(f"\n[Launcher] Opening Google Chrome to {url}...")
    try:
        # Try specifically opening Google Chrome if available
        chrome = webbrowser.get('chrome')
        chrome.open(url)
    except Exception:
        # Fallback to system default browser
        webbrowser.open(url)

def main():
    print("=" * 70)
    print("   MULTIMODAL ATTENDANCE & ENGAGEMENT AGENT")
    print("   AI-Powered Privacy-Preserving Classroom Intelligence System")
    print("=" * 70)
    print("[1] Initializing SQLite Database & Seeding Sample Roster...")
    db.init_db()
    seed_data.seed_database()

    print(f"[2] Launching Web Interface on http://{config.SERVER_CONFIG['HOST']}:{config.SERVER_CONFIG['PORT']}...")
    threading.Thread(target=open_browser, daemon=True).start()

    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=config.SERVER_CONFIG["HOST"],
        port=config.SERVER_CONFIG["PORT"],
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    main()
