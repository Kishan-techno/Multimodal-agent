"""
Multimodal Fusion Engine for Classroom Dynamics.
Combines visual attention, facial valence, acoustic signals, and motion patterns
into a unified engagement score and detects session dynamics trends.
"""
from typing import Dict, Any, List
import config

class MultimodalFusionEngine:
    """
    Computes weighted multimodal fusion and tracks temporal dynamics.
    """
    def __init__(self):
        self.weights = {
            "visual": config.ENGAGEMENT_CONFIG["WEIGHT_VISUAL_ATTENTION"],
            "facial": config.ENGAGEMENT_CONFIG["WEIGHT_FACIAL_EXPRESSION"],
            "audio": config.ENGAGEMENT_CONFIG["WEIGHT_AUDIO_ACTIVITY"],
            "motion": config.ENGAGEMENT_CONFIG["WEIGHT_BODY_MOTION"]
        }
        self.history: List[Dict[str, Any]] = []

    def compute_fusion_score(
        self,
        visual_attention: float,
        facial_expression: float,
        audio_activity: float,
        body_motion: float
    ) -> Dict[str, Any]:
        """
        Fuses multimodal feature scores into composite engagement index (0 - 100).
        """
        score = (
            (visual_attention * self.weights["visual"]) +
            (facial_expression * self.weights["facial"]) +
            (audio_activity * self.weights["audio"]) +
            (body_motion * self.weights["motion"])
        )
        score = max(0.0, min(100.0, score))

        # Semantic classification
        if score >= config.ENGAGEMENT_CONFIG["HIGH_ENGAGEMENT_THRESHOLD"]:
            state_label = "Optimal Engagement"
            badge_color = "emerald"
        elif score >= config.ENGAGEMENT_CONFIG["MODERATE_ENGAGEMENT_THRESHOLD"]:
            state_label = "Active Interaction"
            badge_color = "blue"
        elif score >= config.ENGAGEMENT_CONFIG["LOW_ENGAGEMENT_THRESHOLD"]:
            state_label = "Passive Listening"
            badge_color = "amber"
        else:
            state_label = "Attention Drop"
            badge_color = "rose"

        # Record history window
        entry = {
            "overall_score": round(score, 1),
            "visual_attention": round(visual_attention, 1),
            "facial_expression": round(facial_expression, 1),
            "audio_activity": round(audio_activity, 1),
            "body_motion": round(body_motion, 1),
            "state_label": state_label,
            "badge_color": badge_color
        }
        self.history.append(entry)
        if len(self.history) > config.ENGAGEMENT_CONFIG["ROLLING_WINDOW_SECONDS"]:
            self.history.pop(0)

        # Compute trend
        trend = self.calculate_trend()

        return {
            **entry,
            "trend": trend,
            "rolling_avg_60s": self.get_rolling_average()
        }

    def calculate_trend(self) -> str:
        """Determines if engagement is rising, steady, or falling over recent frames."""
        if len(self.history) < 6:
            return "STABLE"
        recent = [h["overall_score"] for h in self.history[-5:]]
        earlier = [h["overall_score"] for h in self.history[-10:-5]] if len(self.history) >= 10 else [self.history[0]["overall_score"]]
        
        diff = (sum(recent) / len(recent)) - (sum(earlier) / len(earlier))
        if diff > 3.0:
            return "RISING"
        elif diff < -3.0:
            return "FALLING"
        return "STABLE"

    def get_rolling_average(self) -> float:
        if not self.history:
            return 0.0
        return round(sum(h["overall_score"] for h in self.history) / len(self.history), 1)

    def is_attention_drop_detected(self) -> bool:
        """True if recent window is consistently below low engagement threshold."""
        window_size = min(len(self.history), 10)
        if window_size < 5:
            return False
        recent = self.history[-window_size:]
        drop_count = sum(1 for h in recent if h["overall_score"] < config.ENGAGEMENT_CONFIG["LOW_ENGAGEMENT_THRESHOLD"])
        return (drop_count / window_size) >= 0.7
