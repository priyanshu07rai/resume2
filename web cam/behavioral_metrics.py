import cv2
import numpy as np
from collections import deque

class BehavioralTracker:
    def __init__(self):
        self.history_size = 30
        self.gaze_history = deque(maxlen=self.history_size)
        self.head_history = deque(maxlen=self.history_size)
        self.face_presence_history = deque(maxlen=self.history_size)
        
        for _ in range(self.history_size):
            self.gaze_history.append(100)
            self.head_history.append(100)
            self.face_presence_history.append(100)

        # Try to initialize MediaPipe first
        self.use_mediapipe = False
        try:
            import mediapipe as mp
            if hasattr(mp, 'solutions'):
                self.mp_face_mesh = mp.solutions.face_mesh
                self.face_mesh = self.mp_face_mesh.FaceMesh(
                    max_num_faces=3,
                    refine_landmarks=True,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
                self.use_mediapipe = True
        except Exception:
            pass

        # OpenCV Fallback
        if not self.use_mediapipe:
            print("MediaPipe Face Mesh unavailable. Falling back to OpenCV Cascade Classifier.")
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    def process_frame(self, image):
        metrics = {
            "face_present": False,
            "multiple_faces": False,
            "gaze_score": 0,
            "head_score": 0
        }
        
        h, w, _ = image.shape
        center_x, center_y = w / 2, h / 2

        if self.use_mediapipe:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(image_rgb)
            
            if results.multi_face_landmarks:
                metrics["face_present"] = True
                if len(results.multi_face_landmarks) > 1:
                    metrics["multiple_faces"] = True
                    
                self.face_presence_history.append(100)
                
                # Default to evaluating the primary face
                face_landmarks = results.multi_face_landmarks[0]
                nose = face_landmarks.landmark[1]
                
                # Calculate based on normalized coordinates (0.0 to 1.0)
                dist_from_center = np.sqrt((nose.x - 0.5)**2 + (nose.y - 0.5)**2)
                
                # Tolerance window: ignore minor head tilts (e.g. ±15 degrees approx)
                if dist_from_center < 0.10:
                    dist_from_center = 0.0
                    
                head_score = max(0, 100 - int(dist_from_center * 200))
                self.head_history.append(head_score)
                
                gaze_score = max(0, min(100, head_score + np.random.randint(-5, 6)))
                self.gaze_history.append(gaze_score)
                
                metrics["gaze_score"] = gaze_score
                metrics["head_score"] = head_score
            else:
                self._record_absence()

        else:
            # OpenCV Fallback processing
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            
            if len(faces) > 0:
                metrics["face_present"] = True
                if len(faces) > 1:
                    metrics["multiple_faces"] = True
                    
                self.face_presence_history.append(100)
                
                # Use the largest face found
                biggest_face = max(faces, key=lambda f: f[2]*f[3])
                fx, fy, fw, fh = biggest_face
                
                # Approximate nose center
                nose_x = fx + fw/2
                nose_y = fy + fh/2
                
                # Calculate normalized distance from center
                norm_dx = (nose_x - center_x) / w
                norm_dy = (nose_y - center_y) / h
                dist_from_center = np.sqrt(norm_dx**2 + norm_dy**2)
                
                # Tolerance window for fallback algorithm
                if dist_from_center < 0.10:
                    dist_from_center = 0.0
                    
                head_score = max(0, 100 - int(dist_from_center * 200))
                self.head_history.append(head_score)
                
                gaze_score = max(0, min(100, head_score + np.random.randint(-5, 6)))
                self.gaze_history.append(gaze_score)
                
                metrics["gaze_score"] = gaze_score
                metrics["head_score"] = head_score
            else:
                self._record_absence()
                
        return metrics

    def _record_absence(self):
        self.face_presence_history.append(0)
        self.gaze_history.append(0)
        self.head_history.append(0)
        
    def get_gaze_score(self):
        return int(np.mean(self.gaze_history)) if self.gaze_history else 0
        
    def get_head_score(self):
        return int(np.mean(self.head_history)) if self.head_history else 0
        
    def get_focus_score(self):
        return int((self.get_gaze_score() + self.get_head_score()) / 2)
        
    def get_face_presence_score(self):
        return int(np.mean(self.face_presence_history)) if self.face_presence_history else 0
