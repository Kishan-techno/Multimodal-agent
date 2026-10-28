"""
AI-Driven Teaching Suggestion Agent.
Implements Scenario 3: Agent-based pedagogical reasoning engine.
Provides context-aware, non-intrusive decision-support recommendations to educators.
Supports 100% offline rule-based reasoning with optional Google Gemini LLM synthesis.
"""
import time
from typing import Dict, Any, List, Optional
import config
from app.database import db

class TeachingAgentAdvisor:
    """
    Intelligent agent that monitors multimodal classroom dynamics and generates
    actionable pedagogical advice for instructors.
    """
    def __init__(self):
        self.last_suggestion_time = 0.0
        self.cooldown_seconds = config.AGENT_CONFIG["ALERT_COOLDOWN_SECONDS"]
        self.recent_alerts = []

    def evaluate_classroom_state(
        self,
        session_id: int,
        metrics: Dict[str, Any],
        visual_data: Dict[str, Any],
        audio_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluates current session snapshot and triggers suggestion if condition met.
        """
        now = time.time()
        if (now - self.last_suggestion_time) < self.cooldown_seconds:
            return None

        overall = metrics.get("overall_score", 70.0)
        trend = metrics.get("trend", "STABLE")
        visual_score = metrics.get("visual_attention", 70.0)
        pose_label = visual_data.get("head_pose_label", "Direct Visual Focus")
        inactivity_sec = visual_data.get("inactivity_seconds", 0.0)
        motion_label = visual_data.get("motion_label", "")
        silence_sec = audio_data.get("silence_duration_seconds", 0.0)
        acoustic_state = audio_data.get("acoustic_state", "")

        suggestion = None

        # Rule 1: Attention Drop / Distraction (Looking down at devices)
        if visual_score < 40.0 or "Looking Down" in pose_label:
            suggestion = {
                "type": "PACING",
                "priority": "HIGH",
                "title": "Attention Drop Detected (Off-screen Focus)",
                "description": f"Visual attention is currently at {visual_score}%. Students appear to be looking down at mobile devices or desks. Consider launching a 30-second live quiz or presenting a contrasting visual slide.",
                "action": "Launch Quick Checkpoint Quiz"
            }

        # Rule 2: Prolonged Classroom Silence during lecture/discussion
        elif silence_sec > 18.0 and overall < 55.0:
            suggestion = {
                "type": "INTERACTION",
                "priority": "MEDIUM",
                "title": "Interactive Discussion Opportunity",
                "description": f"Prolonged acoustic inactivity ({silence_sec:.0f}s). Break passive listening by asking an open-ended question: 'Who can point out a flaw in this premise?' or prompt a 60-second peer pair-share.",
                "action": "Pose Open-Ended Question"
            }

        # Rule 3: Restlessness / Sluggish Inactivity
        elif "Restlessness" in motion_label or inactivity_sec > 50.0:
            suggestion = {
                "type": "BREAK",
                "priority": "MEDIUM",
                "title": "Learner Fatigue / Fidgeting Alert",
                "description": f"Physical indicators indicate restlessness or slump. Recommended: 60-second micro-break or transition from theoretical explanation to a hands-on terminal exercise.",
                "action": "Take 60s Energizer Break"
            }

        # Rule 4: Downward Trend
        elif trend == "FALLING" and overall < 50.0:
            suggestion = {
                "type": "PACING",
                "priority": "MEDIUM",
                "title": "Engagement Momentum Falling",
                "description": "Session engagement has declined over the last minute. Adjust speaking tempo, modulate vocal pitch, or solicit a student reaction to restore momentum.",
                "action": "Modulate Tone & Ask Feedback"
            }

        # Rule 5: Optimal Flow State
        elif overall >= 85.0 and len(self.recent_alerts) == 0:
            suggestion = {
                "type": "REINFORCEMENT",
                "priority": "LOW",
                "title": "High Engagement Peak",
                "description": f"Classroom engagement peaked at {overall}%. Current presentation style and visual demonstration resonate strongly with learners.",
                "action": "Bookmark Slide for Future Delivery"
            }

        if suggestion:
            self.last_suggestion_time = now
            self.recent_alerts.append(suggestion)
            if len(self.recent_alerts) > 10:
                self.recent_alerts.pop(0)

            # Persist to DB
            s_id = db.add_teaching_suggestion(
                session_id=session_id,
                stype=suggestion["type"],
                title=suggestion["title"],
                description=suggestion["description"],
                priority=suggestion["priority"]
            )
            suggestion["id"] = s_id
            return suggestion

        return None
