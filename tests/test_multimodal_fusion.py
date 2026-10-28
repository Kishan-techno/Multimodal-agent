"""
Unit Tests for Scenario 2: Multimodal Engagement & Session Dynamics.
Verifies multimodal fusion formulas, head pose tolerances, and dynamic classifications.
"""
import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.multimodal_fusion import MultimodalFusionEngine
from app.core.visual_engagement import VisualEngagementAnalyzer
from app.core.audio_engagement import AudioEngagementAnalyzer

class TestMultimodalFusion(unittest.TestCase):
    def setUp(self):
        self.fusion = MultimodalFusionEngine()
        self.visual = VisualEngagementAnalyzer()
        self.audio = AudioEngagementAnalyzer()

    def test_high_engagement_fusion(self):
        """All high signals produce Optimal Engagement status."""
        result = self.fusion.compute_fusion_score(
            visual_attention=90.0,
            facial_expression=95.0,
            audio_activity=85.0,
            body_motion=80.0
        )
        self.assertGreaterEqual(result["overall_score"], 75.0)
        self.assertEqual(result["state_label"], "Optimal Engagement")

    def test_attention_drop_fusion(self):
        """Looking away and silence triggers Attention Drop status."""
        result = self.fusion.compute_fusion_score(
            visual_attention=25.0,
            facial_expression=20.0,
            audio_activity=30.0,
            body_motion=30.0
        )
        self.assertLess(result["overall_score"], 35.0)
        self.assertEqual(result["state_label"], "Attention Drop")

    def test_head_pose_deviation_penalties(self):
        """Looking down or sideways reduces visual attention score."""
        center_score, center_label = self.visual.analyze_head_pose(yaw=0.0, pitch=0.0)
        down_score, down_label = self.visual.analyze_head_pose(yaw=0.0, pitch=-30.0)
        
        self.assertGreater(center_score, down_score)
        self.assertIn("Looking Down", down_label)

    def test_audio_vad_speech_vs_silence(self):
        """Active speech scores higher than prolonged silence."""
        active = self.audio.process_audio_energy(volume_level=55.0, is_speech=True)
        # Simulate 20 seconds of silence
        for _ in range(20):
            silence = self.audio.process_audio_energy(volume_level=5.0, is_speech=False, dt=1.0)
        
        self.assertGreater(active["audio_engagement_score"], silence["audio_engagement_score"])

if __name__ == '__main__':
    unittest.main()
