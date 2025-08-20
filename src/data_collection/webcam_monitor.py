import cv2
import time
import threading
import logging
import numpy as np
from datetime import datetime
import mediapipe as mp
from collections import deque
import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config.settings import (
    WEBCAM_CAPTURE_INTERVAL, WEBCAM_WIDTH, WEBCAM_HEIGHT,
    FACE_DETECTION_CONFIDENCE, BLINK_THRESHOLD, STORE_FACIAL_IMAGES
)
from src.data_processing.database_manager import DatabaseManager

class WebcamMonitor:
    """Monitors webcam for attention tracking and facial analysis"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db_manager = DatabaseManager()
        self.is_running = False
        
        # Webcam and MediaPipe setup
        self.cap = None
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Face analysis models
        self.face_mesh = None
        self.face_detection = None
        
        # Tracking variables
        self.attention_scores = deque(maxlen=50)
        self.blink_history = deque(maxlen=100)
        self.face_positions = deque(maxlen=30)
        self.last_blink_time = datetime.now()
        self.consecutive_no_face = 0
        
        # Threading
        self.monitor_thread = None
        
        # Eye aspect ratio thresholds for blink detection
        self.EAR_THRESHOLD = 0.25
        self.CONSECUTIVE_FRAMES_THRESHOLD = 3
        
    def start(self):
        """Start webcam monitoring"""
        if self.is_running:
            self.logger.warning("Webcam monitor is already running")
            return
        
        try:
            # Initialize webcam
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                raise Exception("Could not open webcam")
            
            # Set webcam properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, WEBCAM_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, WEBCAM_HEIGHT)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            # Initialize MediaPipe models
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=FACE_DETECTION_CONFIDENCE,
                min_tracking_confidence=0.5
            )
            
            self.face_detection = self.mp_face_detection.FaceDetection(
                model_selection=0,
                min_detection_confidence=FACE_DETECTION_CONFIDENCE
            )
            
            self.is_running = True
            
            # Start monitoring thread
            self.monitor_thread = threading.Thread(target=self._monitor_webcam, daemon=True)
            self.monitor_thread.start()
            
            self.logger.info("Webcam monitor started")
            
        except Exception as e:
            self.logger.error(f"Error starting webcam monitor: {e}")
            self.cleanup()
            raise
    
    def stop(self):
        """Stop webcam monitoring"""
        self.is_running = False
        self.cleanup()
        self.logger.info("Webcam monitor stopped")
    
    def cleanup(self):
        """Clean up resources"""
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
    
    def _monitor_webcam(self):
        """Main webcam monitoring loop"""
        while self.is_running:
            try:
                # Capture frame
                ret, frame = self.cap.read()
                if not ret:
                    self.logger.warning("Failed to capture frame")
                    time.sleep(WEBCAM_CAPTURE_INTERVAL)
                    continue
                
                # Flip frame horizontally for mirror effect
                frame = cv2.flip(frame, 1)
                
                # Convert BGR to RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Analyze frame
                analysis_result = self._analyze_frame(rgb_frame)
                
                # Store analysis results
                if analysis_result:
                    self._record_attention_data(analysis_result)
                
                time.sleep(WEBCAM_CAPTURE_INTERVAL)
                
            except Exception as e:
                self.logger.error(f"Error in webcam monitoring: {e}")
                time.sleep(WEBCAM_CAPTURE_INTERVAL)
    
    def _analyze_frame(self, rgb_frame):
        """Analyze frame for attention metrics"""
        try:
            current_time = datetime.now()
            
            # Face detection
            face_results = self.face_detection.process(rgb_frame)
            face_detected = face_results.detections is not None and len(face_results.detections) > 0
            
            if not face_detected:
                self.consecutive_no_face += 1
                return {
                    'timestamp': current_time,
                    'face_detected': False,
                    'attention_score': 0.0,
                    'blink_rate': 0.0,
                    'looking_at_screen': False,
                    'head_pose_x': 0.0,
                    'head_pose_y': 0.0,
                    'head_pose_z': 0.0
                }
            
            self.consecutive_no_face = 0
            
            # Face mesh analysis for detailed metrics
            mesh_results = self.face_mesh.process(rgb_frame)
            
            if mesh_results.multi_face_landmarks:
                landmarks = mesh_results.multi_face_landmarks[0]
                
                # Calculate attention metrics
                attention_score = self._calculate_attention_score(landmarks, rgb_frame.shape)
                blink_rate = self._detect_blinks(landmarks)
                looking_at_screen = self._is_looking_at_screen(landmarks)
                head_pose = self._estimate_head_pose(landmarks, rgb_frame.shape)
                
                return {
                    'timestamp': current_time,
                    'face_detected': True,
                    'attention_score': attention_score,
                    'blink_rate': blink_rate,
                    'looking_at_screen': looking_at_screen,
                    'head_pose_x': head_pose[0],
                    'head_pose_y': head_pose[1],
                    'head_pose_z': head_pose[2]
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error analyzing frame: {e}")
            return None
    
    def _calculate_attention_score(self, landmarks, frame_shape):
        """Calculate attention score based on face orientation and eye gaze"""
        try:
            # Get eye landmarks
            left_eye_landmarks = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
            right_eye_landmarks = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
            
            # Calculate eye aspect ratios
            left_ear = self._calculate_ear(landmarks, left_eye_landmarks, frame_shape)
            right_ear = self._calculate_ear(landmarks, right_eye_landmarks, frame_shape)
            avg_ear = (left_ear + right_ear) / 2.0
            
            # Base attention score on eye openness
            attention_score = min(1.0, max(0.0, avg_ear / 0.3))  # Normalize to 0-1
            
            # Adjust based on head pose
            head_pose = self._estimate_head_pose(landmarks, frame_shape)
            
            # Penalize extreme head movements
            pose_penalty = 1.0
            if abs(head_pose[0]) > 30:  # Extreme yaw
                pose_penalty *= 0.7
            if abs(head_pose[1]) > 20:  # Extreme pitch
                pose_penalty *= 0.8
            
            attention_score *= pose_penalty
            
            # Store for trend analysis
            self.attention_scores.append(attention_score)
            
            return attention_score
            
        except Exception as e:
            self.logger.error(f"Error calculating attention score: {e}")
            return 0.0
    
    def _calculate_ear(self, landmarks, eye_landmarks, frame_shape):
        """Calculate Eye Aspect Ratio for blink detection"""
        try:
            h, w = frame_shape[:2]
            
            # Get eye landmark coordinates
            eye_points = []
            for idx in eye_landmarks[:6]:  # Use first 6 landmarks for basic EAR
                landmark = landmarks.landmark[idx]
                x = int(landmark.x * w)
                y = int(landmark.y * h)
                eye_points.append([x, y])
            
            # Calculate EAR using the standard formula
            if len(eye_points) >= 6:
                # Vertical distances
                A = np.linalg.norm(np.array(eye_points[1]) - np.array(eye_points[5]))
                B = np.linalg.norm(np.array(eye_points[2]) - np.array(eye_points[4]))
                
                # Horizontal distance
                C = np.linalg.norm(np.array(eye_points[0]) - np.array(eye_points[3]))
                
                # EAR calculation
                ear = (A + B) / (2.0 * C) if C > 0 else 0.0
                return ear
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculating EAR: {e}")
            return 0.0
    
    def _detect_blinks(self, landmarks):
        """Detect blinks and calculate blink rate"""
        try:
            # Calculate average EAR for both eyes
            left_ear = self._calculate_ear(landmarks, [33, 7, 163, 144, 145, 153], (480, 640))
            right_ear = self._calculate_ear(landmarks, [362, 382, 381, 380, 374, 373], (480, 640))
            avg_ear = (left_ear + right_ear) / 2.0
            
            # Detect blink
            current_time = datetime.now()
            is_blink = avg_ear < self.EAR_THRESHOLD
            
            if is_blink:
                # Record blink
                time_since_last_blink = (current_time - self.last_blink_time).total_seconds()
                if time_since_last_blink > 0.1:  # Minimum time between blinks
                    self.blink_history.append(current_time)
                    self.last_blink_time = current_time
            
            # Calculate blinks per minute
            one_minute_ago = current_time.timestamp() - 60
            recent_blinks = [
                blink_time for blink_time in self.blink_history
                if blink_time.timestamp() > one_minute_ago
            ]
            
            blink_rate = len(recent_blinks)  # Blinks per minute
            return blink_rate
            
        except Exception as e:
            self.logger.error(f"Error detecting blinks: {e}")
            return 0.0
    
    def _is_looking_at_screen(self, landmarks):
        """Determine if user is looking at the screen"""
        try:
            # Estimate gaze direction based on head pose and eye position
            head_pose = self._estimate_head_pose(landmarks, (480, 640))
            
            # Consider looking at screen if head is roughly facing forward
            yaw, pitch, roll = head_pose
            
            # Thresholds for "looking at screen"
            looking_at_screen = (
                abs(yaw) < 25 and    # Not turned too far left/right
                abs(pitch) < 15 and  # Not looking too far up/down
                abs(roll) < 20       # Not tilted too much
            )
            
            return looking_at_screen
            
        except Exception as e:
            self.logger.error(f"Error determining screen gaze: {e}")
            return False
    
    def _estimate_head_pose(self, landmarks, frame_shape):
        """Estimate head pose (yaw, pitch, roll) in degrees"""
        try:
            h, w = frame_shape[:2]
            
            # 3D model points for head pose estimation
            model_points = np.array([
                (0.0, 0.0, 0.0),             # Nose tip
                (0.0, -330.0, -65.0),        # Chin
                (-225.0, 170.0, -135.0),     # Left eye left corner
                (225.0, 170.0, -135.0),      # Right eye right corner
                (-150.0, -150.0, -125.0),    # Left mouth corner
                (150.0, -150.0, -125.0)      # Right mouth corner
            ])
            
            # Corresponding 2D points from face landmarks
            nose_tip = landmarks.landmark[1]
            chin = landmarks.landmark[175]
            left_eye_corner = landmarks.landmark[33]
            right_eye_corner = landmarks.landmark[263]
            left_mouth = landmarks.landmark[61]
            right_mouth = landmarks.landmark[291]
            
            image_points = np.array([
                (nose_tip.x * w, nose_tip.y * h),
                (chin.x * w, chin.y * h),
                (left_eye_corner.x * w, left_eye_corner.y * h),
                (right_eye_corner.x * w, right_eye_corner.y * h),
                (left_mouth.x * w, left_mouth.y * h),
                (right_mouth.x * w, right_mouth.y * h)
            ], dtype="double")
            
            # Camera matrix (approximation)
            focal_length = w
            center = (w/2, h/2)
            camera_matrix = np.array([
                [focal_length, 0, center[0]],
                [0, focal_length, center[1]],
                [0, 0, 1]
            ], dtype="double")
            
            # Distortion coefficients (assuming no distortion)
            dist_coeffs = np.zeros((4, 1))
            
            # Solve PnP
            success, rotation_vector, translation_vector = cv2.solvePnP(
                model_points, image_points, camera_matrix, dist_coeffs
            )
            
            if success:
                # Convert rotation vector to rotation matrix
                rotation_matrix, _ = cv2.Rodrigues(rotation_vector)
                
                # Extract Euler angles
                yaw = np.arctan2(rotation_matrix[1, 0], rotation_matrix[0, 0])
                pitch = np.arctan2(-rotation_matrix[2, 0], np.sqrt(rotation_matrix[2, 1]**2 + rotation_matrix[2, 2]**2))
                roll = np.arctan2(rotation_matrix[2, 1], rotation_matrix[2, 2])
                
                # Convert to degrees
                yaw_deg = np.degrees(yaw)
                pitch_deg = np.degrees(pitch)
                roll_deg = np.degrees(roll)
                
                return (yaw_deg, pitch_deg, roll_deg)
            
            return (0.0, 0.0, 0.0)
            
        except Exception as e:
            self.logger.error(f"Error estimating head pose: {e}")
            return (0.0, 0.0, 0.0)
    
    def _record_attention_data(self, analysis_result):
        """Record attention analysis results to database"""
        try:
            self.db_manager.insert_attention_data(analysis_result)
            
        except Exception as e:
            self.logger.error(f"Error recording attention data: {e}")
    
    def get_current_attention_state(self):
        """Get current attention state summary"""
        try:
            if len(self.attention_scores) == 0:
                return {
                    'current_attention': 0.0,
                    'average_attention': 0.0,
                    'blink_rate': 0.0,
                    'face_detected': False,
                    'looking_at_screen': False
                }
            
            current_attention = self.attention_scores[-1] if self.attention_scores else 0.0
            average_attention = sum(self.attention_scores) / len(self.attention_scores)
            
            # Calculate recent blink rate
            current_time = datetime.now()
            one_minute_ago = current_time.timestamp() - 60
            recent_blinks = [
                blink_time for blink_time in self.blink_history
                if blink_time.timestamp() > one_minute_ago
            ]
            
            return {
                'current_attention': current_attention,
                'average_attention': average_attention,
                'blink_rate': len(recent_blinks),
                'face_detected': self.consecutive_no_face < 5,
                'looking_at_screen': current_attention > 0.3,
                'attention_trend': list(self.attention_scores)[-10:]  # Last 10 readings
            }
            
        except Exception as e:
            self.logger.error(f"Error getting attention state: {e}")
            return {}
    
    def get_session_summary(self):
        """Get session summary statistics"""
        try:
            if not self.attention_scores:
                return {}
            
            total_readings = len(self.attention_scores)
            avg_attention = sum(self.attention_scores) / total_readings
            max_attention = max(self.attention_scores)
            min_attention = min(self.attention_scores)
            
            # Calculate focus periods (attention > threshold)
            focus_threshold = 0.5
            focus_periods = [score for score in self.attention_scores if score > focus_threshold]
            focus_percentage = (len(focus_periods) / total_readings) * 100
            
            return {
                'total_readings': total_readings,
                'average_attention': avg_attention,
                'max_attention': max_attention,
                'min_attention': min_attention,
                'focus_percentage': focus_percentage,
                'total_blinks': len(self.blink_history),
                'avg_blink_rate': len(self.blink_history) / (total_readings * WEBCAM_CAPTURE_INTERVAL / 60) if total_readings > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error getting session summary: {e}")
            return {}

def main():
    """Main function for testing the webcam monitor"""
    import logging.config
    from config.settings import LOGGING_CONFIG
    
    # Set up logging
    logging.config.dictConfig(LOGGING_CONFIG)
    logger = logging.getLogger(__name__)
    
    # Create and start webcam monitor
    webcam_monitor = WebcamMonitor()
    
    try:
        logger.info("Starting webcam monitor...")
        webcam_monitor.start()
        
        # Run for a while to collect data
        while True:
            time.sleep(10)
            state = webcam_monitor.get_current_attention_state()
            summary = webcam_monitor.get_session_summary()
            
            logger.info(f"Attention: {state.get('current_attention', 0):.2f}, "
                       f"Blinks/min: {state.get('blink_rate', 0)}, "
                       f"Face detected: {state.get('face_detected', False)}")
            
            if summary:
                logger.info(f"Session focus: {summary.get('focus_percentage', 0):.1f}%")
            
    except KeyboardInterrupt:
        logger.info("Stopping webcam monitor...")
        webcam_monitor.stop()
    except Exception as e:
        logger.error(f"Error in webcam monitor: {e}")
        webcam_monitor.stop()

if __name__ == "__main__":
    main()
