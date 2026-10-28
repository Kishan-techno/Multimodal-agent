"""
Audio Signal Processing and Classroom Acoustic Dynamics Engine.
Analyzes audio activity, Voice Activity Detection (VAD), speech energy,
monologue vs discussion dynamics, and classroom silence duration.
"""
import math
import time
from typing import Dict, Any, Tuple
import config

class AudioEngagementAnalyzer:
    """
    Processes acoustic signal metrics and classifies classroom interaction dynamics.
    """
    def __init__(self):
        self.silence_seconds = 0.0
        self.speech_seconds = 0.0
        self.energy_history = []
        self.last_speech_time = time.time()

    def process_audio_energy(self, volume_level: float, is_speech: bool, dt: float = 1.0) -> Dict[str, Any]:
        """
        Processes audio frame/window metrics.
        volume_level: 0.0 to 100.0 (normalized RMS sound pressure level).
        is_speech: Boolean from VAD (Voice Activity Detection).
        dt: Window step duration in seconds.
        """
        now = time.time()
        self.energy_history.append(volume_level)
        if len(self.energy_history) > 60:
            self.energy_history.pop(0)

        # Track speech vs silence intervals
        if is_speech or volume_level > 25.0:
            self.speech_seconds += dt
            self.silence_seconds = max(0.0, self.silence_seconds - (dt * 2.0))
            self.last_speech_time = now
        else:
            self.silence_seconds += dt

        # Audio engagement scoring:
        # A lively lecture or discussion has dynamic speech patterns (volume 30-75).
        # Dead silence (> 10s) or chaotic yelling (> 85) receive lower score.
        if is_speech:
            if 30.0 <= volume_level <= 75.0:
                score = 90.0
                state = "Active Speech / Discussion"
            elif volume_level > 75.0:
                score = 70.0
                state = "High Volume / Classroom Noise"
            else:
                score = 80.0
                state = "Quiet / Clear Speech"
        else:
            if self.silence_seconds > 15.0:
                score = 30.0
                state = "Prolonged Silence / Inactive"
            elif self.silence_seconds > 5.0:
                score = 60.0
                state = "Silent Thinking / Note Taking"
            else:
                score = 75.0
                state = "Brief Pause"

        return {
            "audio_engagement_score": round(score, 1),
            "acoustic_state": state,
            "volume_level": round(volume_level, 1),
            "is_speech_active": is_speech,
            "silence_duration_seconds": round(self.silence_seconds, 1),
            "speech_ratio": round(self.speech_seconds / max(1.0, (self.speech_seconds + self.silence_seconds)), 2)
        }
