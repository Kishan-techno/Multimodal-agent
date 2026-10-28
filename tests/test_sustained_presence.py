"""
Unit Tests for Scenario 1: Sustained Presence Attendance Tracking.
Verifies that attendance is only granted upon continuous sustained presence,
preventing false positives from fleeting appearances.
"""
import unittest
import time
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.face_recognition import SustainedPresenceTracker

class TestSustainedPresence(unittest.TestCase):
    def setUp(self):
        # 5.0 seconds threshold, 8.0s gap tolerance
        self.tracker = SustainedPresenceTracker(sustained_threshold=5.0, gap_tolerance=8.0)

    def test_single_frame_does_not_mark_present(self):
        """Transient single frame should NOT grant attendance."""
        summary = self.tracker.update_presence("STU-1001", confidence=0.92, current_time=100.0)
        self.assertEqual(summary["status"], "ABSENT")
        self.assertEqual(summary["sustained_duration"], 0.0)

    def test_partial_presence(self):
        """Accumulated presence between 2.0s and 5.0s should be PARTIAL."""
        self.tracker.update_presence("STU-1001", confidence=0.92, current_time=100.0)
        self.tracker.update_presence("STU-1001", confidence=0.92, current_time=101.0)
        summary = self.tracker.update_presence("STU-1001", confidence=0.92, current_time=102.5)
        self.assertEqual(summary["status"], "PARTIAL")

    def test_sustained_presence_reaches_present(self):
        """Continuous presence >= 5.0s marks student as PRESENT."""
        start = 100.0
        for i in range(7):
            summary = self.tracker.update_presence("STU-1001", confidence=0.95, current_time=start + i)
        
        self.assertEqual(summary["status"], "PRESENT")
        self.assertGreaterEqual(summary["sustained_duration"], 5.0)
        self.assertEqual(summary["progress_percent"], 100.0)

if __name__ == '__main__':
    unittest.main()
