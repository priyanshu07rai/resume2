from behavioral_metrics import BehavioralTracker
from cheating_detector import CheatingDetector
import time
import base64
import cv2
import numpy as np

class InterviewEngine:
    def __init__(self, candidate_hash):
        self.candidate_hash = candidate_hash
        self.start_time = time.time()
        self.behavioral_tracker = BehavioralTracker()
        self.cheating_detector = CheatingDetector()
        self.evaluated_answers = []
        self.no_face_start = None
        self.previous_confidence = 100.0
        
    def log_evaluated_answer(self, eval_data):
        self.evaluated_answers.append(eval_data)
        
    def _decode_image(self, b64_string):
        try:
            if ',' in b64_string:
                b64_string = b64_string.split(',')[1]
            img_data = base64.b64decode(b64_string)
            nparr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return img
        except Exception as e:
            print(f"Image decode error: {e}")
            return None

    def process_frame(self, image_b64):
        img = self._decode_image(image_b64)
        if img is None:
            return self.get_current_metrics()
            
        # Process behavior
        behavior_metrics = self.behavioral_tracker.process_frame(img)
        
        # Check for NO_FACE cheating event with 3-second tolerance
        if behavior_metrics.get("face_present"):
            self.no_face_start = None
            if behavior_metrics.get("multiple_faces"):
                self.cheating_detector.log_event("MULTIPLE_FACES", "high")
        else:
            if self.no_face_start is None:
                self.no_face_start = time.time()
            
            duration = time.time() - self.no_face_start
            if duration > 8.0:   # 8 solid seconds of absence before logging
                self.cheating_detector.log_event("NO_FACE", "high")
                self.no_face_start = time.time()  # reset window
            
        return self.get_current_metrics()

    def log_cheating_event(self, event_type):
        severity = "medium"
        if event_type == "TAB_SWITCH":
            severity = "high"
        elif event_type == "WINDOW_UNFOCUS":
            severity = "medium"
        elif event_type == "MULTIPLE_FACES":
            severity = "high"
        self.cheating_detector.log_event(event_type, severity)

    def get_current_metrics(self):
        gaze = self.behavioral_tracker.get_gaze_score()
        head = self.behavioral_tracker.get_head_score()
        focus = self.behavioral_tracker.get_focus_score()
        face_presence = self.behavioral_tracker.get_face_presence_score()
        
        # 1. Grace Period
        session_time = time.time() - self.start_time
        if session_time < 20.0:
            return {
                "gaze_stability": gaze,
                "head_stability": head,
                "focus_score": focus,
                "confidence_score": 75, # Start stable
                "anomaly_points": 0,
                "cheating_flags_count": 0
            }
            
        # 2. Base Behavior Stability (Low Weight in Final)
        behavior_stability = (gaze * 0.40) + (head * 0.40) + (focus * 0.20)
        
        # 3. Apply Anomalies to Target Score
        anomaly_penalty = self.cheating_detector.get_penalty_score()
        target = behavior_stability - anomaly_penalty
        
        # 4. Inertia Model (Slow Drift)
        alpha = 0.08
        self.previous_confidence = self.previous_confidence * (1 - alpha) + target * alpha
        
        # 5. Hard Clamp
        self.previous_confidence = max(30, min(100, self.previous_confidence))

        return {
            "gaze_stability": gaze,
            "head_stability": head,
            "focus_score": focus,
            "confidence_score": int(self.previous_confidence),
            "anomaly_points": anomaly_penalty,
            "cheating_flags_count": len(self.cheating_detector.events),
            "cheating_events": [
                {
                    "type": e['event_type'],
                    "time": time.strftime('%H:%M:%S', time.localtime(e['timestamp']))
                } for e in self.cheating_detector.events
            ]
        }

    def finalize_session(self):
        duration = int(time.time() - self.start_time)
        metrics = self.get_current_metrics()
        
        flags = [e['event_type'] for e in self.cheating_detector.events]
        risk_level = "Session Completed"
        anomaly_points = self.cheating_detector.get_penalty_score()
        
        # New strict termination logic (only severe fraud)
        if anomaly_points >= 20: 
            risk_level = "Integrity Concern Detected"
        elif anomaly_points >= 10:
            risk_level = "Session Flagged for Review"
            
        # Behavior Confidence (from live tracking)
        behavioral_confidence = metrics["confidence_score"]
        
        # Answer Reliability
        avg_answer_quality = 0
        if self.evaluated_answers:
            avg_answer_quality = sum([a["evaluation"]["answer_quality"] for a in self.evaluated_answers]) / len(self.evaluated_answers)
            
        # Final Interview Integrity Formula (Shifted to Fraud Base)
        # 60% Behavior/Fraud Integrity + 40% Speech/Answer Quality
        fraud_index = max(0, 100 - (anomaly_points * 5)) # Each anomaly point hits final score hard
        
        integrity_index = int(
            (fraud_index * 0.60) +
            (avg_answer_quality * 0.40)
        )
        
        # Clamp Final Score to baseline 25 minimum unless completely compromised
        integrity_index = max(25, min(100, integrity_index))
        if anomaly_points > 30:
            integrity_index = 0
        
        summary_text = "Stable behavior with strong answer reliability."
        if risk_level == "Integrity Concern Detected":
            summary_text = "Session terminated early due to high unusual activity."
        elif risk_level == "Session Flagged for Review":
            summary_text = "Minor anomalies observed during session."
            
        final_data = {
            "candidate_hash": self.candidate_hash,
            "session_duration": f"{duration}s",
            "integrity_index": integrity_index,
            "behavioral_confidence": behavioral_confidence,
            "answer_quality": avg_answer_quality,
            "anomaly_points": anomaly_points,
            "cheating_flags": flags,
            "gaze_stability": metrics["gaze_stability"],
            "head_stability": metrics["head_stability"],
            "focus_score": metrics["focus_score"],
            "risk_level": risk_level,
            "interview_summary": summary_text,
            "answers_logged": len(self.evaluated_answers)
        }
        return final_data
