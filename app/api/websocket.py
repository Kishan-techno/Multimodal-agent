"""
WebSocket Real-Time Multimodal Streaming & Orchestration Pipeline.
Synchronizes visual tracking, audio processing, sustained presence verification,
multimodal fusion, and AI agent recommendations at 10-30 FPS.
"""
import json
import time
from typing import Dict, Any, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.face_recognition import AttendanceFaceEngine
from app.core.visual_engagement import VisualEngagementAnalyzer
from app.core.audio_engagement import AudioEngagementAnalyzer
from app.core.multimodal_fusion import MultimodalFusionEngine
from app.core.agent_advisor import TeachingAgentAdvisor
from app.database import db

router = APIRouter()

# Global state instances
face_engine = AttendanceFaceEngine()
visual_analyzer = VisualEngagementAnalyzer()
audio_analyzer = AudioEngagementAnalyzer()
fusion_engine = MultimodalFusionEngine()
agent_advisor = TeachingAgentAdvisor()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        face_engine.refresh_enrolled_students()

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

@router.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    session = db.get_active_session()
    session_id = session["id"] if session else 1

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)

            msg_type = payload.get("type", "telemetry")

            if msg_type == "telemetry":
                # Extract client multimodal signals
                detected_faces = payload.get("faces", [])
                audio_level = float(payload.get("audio_level", 20.0))
                is_speech = bool(payload.get("is_speech", False))
                head_pose = payload.get("head_pose", {"yaw": 0.0, "pitch": 0.0, "roll": 0.0})
                expression = payload.get("expression", "focused")
                motion = float(payload.get("motion", 15.0))
                selected_student = payload.get("assigned_student_id", None)

                if selected_student and detected_faces:
                    for f in detected_faces:
                        f["student_id"] = selected_student

                # 1. Process Face & Sustained Presence Attendance
                face_results = face_engine.process_frame_detections(session_id, detected_faces)

                # 2. Process Visual Attention Signals
                visual_metrics = visual_analyzer.process_frame(head_pose, expression, motion)

                # 3. Process Acoustic Signal
                audio_metrics = audio_analyzer.process_audio_energy(audio_level, is_speech)

                # 4. Multimodal Fusion
                fusion_result = fusion_engine.compute_fusion_score(
                    visual_attention=visual_metrics["visual_attention_score"],
                    facial_expression=visual_metrics["facial_expression_score"],
                    audio_activity=audio_metrics["audio_engagement_score"],
                    body_motion=visual_metrics["motion_score"]
                )

                # 5. Evaluate AI Teaching Suggestion Agent
                suggestion = agent_advisor.evaluate_classroom_state(
                    session_id=session_id,
                    metrics=fusion_result,
                    visual_data=visual_metrics,
                    audio_data=audio_metrics
                )

                # 6. Log metrics in DB periodically (every ~3-5 seconds or when significant)
                now = time.time()
                if int(now) % 3 == 0:
                    db.log_engagement_metric(
                        session_id=session_id,
                        overall=fusion_result["overall_score"],
                        visual=visual_metrics["visual_attention_score"],
                        facial=visual_metrics["facial_expression_score"],
                        audio=audio_metrics["audio_engagement_score"],
                        motion=visual_metrics["motion_score"],
                        state=fusion_result["state_label"],
                        active_faces=len(detected_faces)
                    )

                # 7. Current Attendance Roster Summary
                attendance_roster = db.get_session_attendance(session_id)
                total_present = sum(1 for a in attendance_roster if a["status"] == "PRESENT")
                total_partial = sum(1 for a in attendance_roster if a["status"] == "PARTIAL")

                # Send unified real-time telemetry back
                response_packet = {
                    "type": "telemetry_response",
                    "timestamp": time.time(),
                    "fusion": fusion_result,
                    "visual": visual_metrics,
                    "audio": audio_metrics,
                    "faces": face_results,
                    "attendance": {
                        "total_enrolled": len(attendance_roster),
                        "total_present": total_present,
                        "total_partial": total_partial,
                        "roster": attendance_roster
                    },
                    "suggestion": suggestion
                }

                await websocket.send_json(response_packet)

            elif msg_type == "reset_tracker":
                face_engine.presence_tracker.reset()
                await websocket.send_json({"type": "tracker_reset_ack"})

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        manager.disconnect(websocket)
