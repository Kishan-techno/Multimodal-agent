"""
Visual Engagement Analysis Engine.
Implements behavioral indicators:
- Head Pose Estimation (Yaw, Pitch, Roll)
- Gaze & Eye State / Drowsiness Detection
- Facial Expression / Valence (Focused, Confused, Bored, Distracted)
- Body Motion / Restlessness / Inactivity Duration
"""
import math
import time
from typing import Dict, Any, Tuple, Optional
import config

class VisualEngagementAnalyzer:
    """
    Extracts and evaluates visual engagement signals from face geometry and movement.
    """
    def __init__(self):
        self.last_motion_time = time.time()
        self.inactivity_seconds = 0.0
        self.motion_history = []
        self.blink_count = 0
        self.last_ear = 0.30

    def analyze_head_pose(self, yaw: float, pitch: float, roll: float = 0.0) -> Tuple[float, str]:
        """
        Evaluates visual attention from head orientation.
        Yaw: negative = left, positive = right
        Pitch: negative = down, positive = up
        Returns (attention_score: 0.0 to 100.0, pose_label: str)
        """
        yaw_tol = config.ENGAGEMENT_CONFIG["YAW_TOLERANCE"]
        pitch_tol = config.ENGAGEMENT_CONFIG["PITCH_TOLERANCE"]

        abs_yaw = abs(yaw)
        abs_pitch = abs(pitch)

        # Base orientation penalty
        yaw_penalty = max(0.0, (abs_yaw - 10.0) / yaw_tol) if abs_yaw > 10.0 else 0.0
        pitch_penalty = max(0.0, (abs_pitch - 8.0) / pitch_tol) if abs_pitch > 8.0 else 0.0

        penalty = min(1.0, (yaw_penalty * 0.6) + (pitch_penalty * 0.5))
        attention_score = max(10.0, (1.0 - penalty) * 100.0)

        # Determine semantic orientation label
        if pitch < -18.0:
            label = "Looking Down (Phone/Desk)"
        elif pitch > 22.0:
            label = "Looking Up (Ceiling)"
        elif yaw < -22.0:
            label = "Looking Left"
        elif yaw > 22.0:
            label = "Looking Right"
        elif abs_yaw <= 12.0 and abs_pitch <= 10.0:
            label = "Direct Visual Focus"
        else:
            label = "Slight Deviation"

        return round(attention_score, 1), label

    def analyze_facial_expression(self, expression_type: str = "focused") -> Tuple[float, str]:
        """
        Maps facial sentiment/expression to attention valence.
        """
        mapping = {
            "focused": (95.0, "Focused & Attentive"),
            "engaged": (98.0, "Actively Engaged"),
            "smiling": (90.0, "Positive & Receptive"),
            "neutral": (75.0, "Attentive Neutral"),
            "confused": (45.0, "Perplexed / Confused"),
            "bored": (25.0, "Bored / Inattentive"),
            "drowsy": (15.0, "Drowsy / Eyes Heavy"),
            "distracted": (20.0, "Distracted Elsewhere")
        }
        score, label = mapping.get(expression_type.lower(), (70.0, "Neutral"))
        return score, label

    def analyze_motion(self, motion_magnitude: float, dt: float = 1.0) -> Tuple[float, str, float]:
        """
        Analyzes body movement dynamics.
        motion_magnitude: 0.0 (still) to 100.0 (intense movement).
        Returns: (motion_score: 0-100, motion_state: str, inactivity_seconds: float)
        """
        now = time.time()
        self.motion_history.append(motion_magnitude)
        if len(self.motion_history) > 30:
            self.motion_history.pop(0)

        # Inactivity tracking
        if motion_magnitude < 6.0:
            self.inactivity_seconds += dt
        else:
            self.inactivity_seconds = max(0.0, self.inactivity_seconds - (dt * 1.5))

        # Classify motion dynamics
        if motion_magnitude > 75.0:
            state = "High Restlessness / Fidgeting"
            motion_score = 40.0  # Excessive agitation degrades sustained attention
        elif motion_magnitude > 40.0:
            state = "Active Movement"
            motion_score = 80.0
        elif motion_magnitude >= 10.0:
            state = "Normal Attentive Micro-movement"
            motion_score = 95.0
        else:
            if self.inactivity_seconds > 45.0:
                state = "Prolonged Slump / Lethargy"
                motion_score = 25.0
            else:
                state = "Quiet Contemplation"
                motion_score = 85.0

        return motion_score, state, round(self.inactivity_seconds, 1)

    def process_frame(self, head_pose: Dict[str, float], expression: str, motion_val: float) -> Dict[str, Any]:
        """
        Processes full visual packet for a student / classroom frame.
        """
        yaw = head_pose.get("yaw", 0.0)
        pitch = head_pose.get("pitch", 0.0)
        roll = head_pose.get("roll", 0.0)

        att_score, pose_label = self.analyze_head_pose(yaw, pitch, roll)
        expr_score, expr_label = self.analyze_facial_expression(expression)
        motion_score, motion_label, inactivity_sec = self.analyze_motion(motion_val)

        return {
            "visual_attention_score": att_score,
            "head_pose_label": pose_label,
            "yaw": yaw,
            "pitch": pitch,
            "roll": roll,
            "facial_expression_score": expr_score,
            "facial_expression_label": expr_label,
            "motion_score": motion_score,
            "motion_label": motion_label,
            "inactivity_seconds": inactivity_sec
        }
