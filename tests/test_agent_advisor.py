"""
Unit Tests for Scenario 3: AI-Driven Teaching Suggestions Agent.
Verifies pedagogical decision rules, cooldown timers, and intervention recommendations.
"""
import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.agent_advisor import TeachingAgentAdvisor
from app.database import db

class TestTeachingAgentAdvisor(unittest.TestCase):
    def setUp(self):
        db.init_db()
        self.session_id = db.create_session("Test Session Unit Test")
        self.advisor = TeachingAgentAdvisor()
        # Set cooldown to 0 for instant test evaluation
        self.advisor.cooldown_seconds = 0.0

    def test_attention_drop_triggers_pacing_suggestion(self):
        """Low visual attention triggers Pacing Intervention advice."""
        metrics = {"overall_score": 38.0, "trend": "FALLING", "visual_attention": 32.0}
        visual_data = {"visual_attention_score": 32.0, "head_pose_label": "Looking Down (Phone/Desk)", "inactivity_seconds": 10.0}
        audio_data = {"silence_duration_seconds": 12.0, "acoustic_state": "Quiet"}

        suggestion = self.advisor.evaluate_classroom_state(
            session_id=self.session_id,
            metrics=metrics,
            visual_data=visual_data,
            audio_data=audio_data
        )

        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion["type"], "PACING")
        self.assertEqual(suggestion["priority"], "HIGH")
        self.assertIn("Attention Drop", suggestion["title"])

    def test_prolonged_silence_triggers_interaction_suggestion(self):
        """Prolonged acoustic silence triggers discussion recommendation."""
        metrics = {"overall_score": 50.0, "trend": "STABLE", "visual_attention": 70.0}
        visual_data = {"visual_attention_score": 70.0, "head_pose_label": "Direct Visual Focus", "inactivity_seconds": 5.0}
        audio_data = {"silence_duration_seconds": 22.0, "acoustic_state": "Prolonged Silence / Inactive"}

        suggestion = self.advisor.evaluate_classroom_state(
            session_id=self.session_id,
            metrics=metrics,
            visual_data=visual_data,
            audio_data=audio_data
        )

        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion["type"], "INTERACTION")
        self.assertIn("Discussion", suggestion["title"])

if __name__ == '__main__':
    unittest.main()
