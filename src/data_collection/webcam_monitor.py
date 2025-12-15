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
        self.face_positions = deque(maxlen=30) # For posture stability
        self.head_pose_history = deque(maxlen=30) # For head pose variance
        self.gaze_history = deque(maxlen=30) # For gaze dispersion
        self.eye_closure_history = deque(maxlen=30) # For eye closure ratio
        
        self.last_blink_time = datetime.now()
        self.last_face_time = datetime.now()
        self.face_switches = 0
        self.face_switch_start_time = datetime.now()
        self.consecutive_no_face = 0
        
        # Threading
        self.monitor_thread = None
        
        # Eye aspect ratio thresholds for blink detection
        self.EAR_THRESHOLD = 0.25
        self.CONSECUTIVE_FRAMES_THRESHOLD = 3
        
        # Heuristics / Calibrations
        self.SCREEN_DISTANCE_REF = 500  # arbitrary reference unit
        self.GAZE_HISTORY_WINDOW = 30  # Frames
        
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
                    'gaze_on_screen_ratio': 0.0,
                    'gaze_dispersion': 0.0,
                    'gaze_shift_rate': 0.0,
                    'blink_rate': 0.0,
                    'eye_closure_ratio': 0.0,
                    'head_pose_variance': 0.0,
                    'head_turn_rate': 0.0,
                    'face_screen_distance': 0.0,
                    'posture_stability': 0.0,
                    'secondary_device_detected_ratio': 0.0,
                    'hand_device_interaction_time': 0.0,
                    'face_identity_switch_rate': 0.0
                }
            
            self.consecutive_no_face = 0
            
            # Face mesh analysis for detailed metrics
            mesh_results = self.face_mesh.process(rgb_frame)
            
            if mesh_results.multi_face_landmarks:
                landmarks = mesh_results.multi_face_landmarks[0]
                
                # Calculate attention metrics
                head_pose = self._estimate_head_pose(landmarks, rgb_frame.shape)
                
                # New Metrics Calculations
                gaze_metrics = self._calculate_gaze_metrics(landmarks, rgb_frame.shape)
                pose_metrics = self._estimate_head_pose_metrics(head_pose)
                face_stats = self._calculate_face_stats(landmarks, rgb_frame.shape)
                
                # Eye metrics
                left_ear = self._calculate_ear(landmarks, [33, 7, 163, 144, 145, 153], (480, 640))
                right_ear = self._calculate_ear(landmarks, [362, 382, 381, 380, 374, 373], (480, 640))
                avg_ear = (left_ear + right_ear) / 2.0
                
                blink_rate = self._detect_blinks(landmarks)
                closure_ratio = self._calculate_eye_closure_metrics(avg_ear)
                
                # Composite Attention Score (0.0 - 1.0)
                # Weighted sum of on_screen (0.5), stability (0.3), and head pose (0.2)
                # Normalize stability/variance (lower is better)
                stability_score = max(0.0, 1.0 - face_stats['stability'] * 5) # Scale factor hypothesis
                pose_score = max(0.0, 1.0 - pose_metrics['variance'] / 100) # Scale factor hypothesis
                
                attention_score = (
                    gaze_metrics['on_screen'] * 0.5 +
                    stability_score * 0.3 +
                    pose_score * 0.2
                )
                self.attention_scores.append(attention_score)
                
                return {
                    'timestamp': current_time,
                    'face_detected': True,
                    'gaze_on_screen_ratio': gaze_metrics['on_screen'],
                    'gaze_dispersion': gaze_metrics['dispersion'],
                    'gaze_shift_rate': gaze_metrics['shift_rate'],
                    'blink_rate': blink_rate,
                    'eye_closure_ratio': closure_ratio,
                    'head_pose_variance': pose_metrics['variance'],
                    'head_turn_rate': pose_metrics['turn_rate'],
                    'face_screen_distance': face_stats['distance'],
                    'posture_stability': face_stats['stability'],
                    'secondary_device_detected_ratio': 0.0, # Placeholder
                    'hand_device_interaction_time': 0.0, # Placeholder
                    'face_identity_switch_rate': face_stats['switch_rate']
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

    def _calculate_eye_closure_metrics(self, avg_ear):
        """Calculate eye closure ratio over time"""
        try:
            is_closed = 1.0 if avg_ear < self.EAR_THRESHOLD else 0.0
            self.eye_closure_history.append(is_closed)
            
            if len(self.eye_closure_history) > 0:
                closure_ratio = sum(self.eye_closure_history) / len(self.eye_closure_history)
                return closure_ratio
            return 0.0
        except Exception:
            return 0.0
    
    def _calculate_gaze_metrics(self, landmarks, frame_shape):
        """Calculate gaze related metrics using Iris landmarks"""
        try:
            h, w = frame_shape[:2]
            
            # Iris landmarks (Left: 468, Right: 473)
            left_iris = landmarks.landmark[468]
            right_iris = landmarks.landmark[473]
            
            # Average iris position (normalized)
            gaze_x = (left_iris.x + right_iris.x) / 2
            gaze_y = (left_iris.y + right_iris.y) / 2
            
            self.gaze_history.append((gaze_x, gaze_y))
            
            # 1. Gaze on screen ratio (heuristic)
            # Assuming "screen" is within central 50% of frame width/height for now
            on_screen = 0.25 < gaze_x < 0.75 and 0.25 < gaze_y < 0.75
            
            # 2. Gaze Dispersion (Standard deviation of gaze points)
            if len(self.gaze_history) > 5:
                # Calculate Euclidean dispersion
                points = np.array(self.gaze_history)
                gaze_dispersion = np.mean(np.std(points, axis=0)) # simplified dispersion
            else:
                gaze_dispersion = 0.0
                
            # 3. Gaze Shift Rate (Large movements per second)
            gaze_shift_rate = 0.0
            if len(self.gaze_history) > 1:
                recent_moves = 0
                for i in range(1, len(self.gaze_history)):
                    p1 = np.array(self.gaze_history[i-1])
                    p2 = np.array(self.gaze_history[i])
                    dist = np.linalg.norm(p2 - p1)
                    if dist > 0.05: # Threshold for significant shift
                        recent_moves += 1
                
                # Approximate moves per minute equivalent
                gaze_shift_rate = (recent_moves / len(self.gaze_history)) * 60
            
            return {
                'on_screen': float(on_screen), # 1.0 or 0.0 for this frame
                'dispersion': float(gaze_dispersion),
                'shift_rate': float(gaze_shift_rate)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating gaze metrics: {e}")
            return {'on_screen': 0.0, 'dispersion': 0.0, 'shift_rate': 0.0}

    def _estimate_head_pose_metrics(self, head_pose):
        """Calculate head pose variance and turn rate"""
        try:
            self.head_pose_history.append(head_pose)
            
            if len(self.head_pose_history) < 2:
                return {'variance': 0.0, 'turn_rate': 0.0}
            
            # 1. Variance
            poses = np.array(self.head_pose_history)
            variance = np.mean(np.var(poses, axis=0))
            
            # 2. Turn Rate (degrees per second approx)
            total_angular_change = 0
            for i in range(1, len(self.head_pose_history)):
                p1 = np.array(self.head_pose_history[i-1])
                p2 = np.array(self.head_pose_history[i])
                total_angular_change += np.linalg.norm(p2 - p1)
            
            turn_rate = total_angular_change / (len(self.head_pose_history) * WEBCAM_CAPTURE_INTERVAL)
            
            return {'variance': float(variance), 'turn_rate': float(turn_rate)}
            
        except Exception as e:
            self.logger.error(f"Error calculating pose metrics: {e}")
            return {'variance': 0.0, 'turn_rate': 0.0}
    
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
            
            return (0.0, 0.0, 0.0)
            
        except Exception as e:
            self.logger.error(f"Error estimating head pose: {e}")
            return (0.0, 0.0, 0.0)
    
    def _calculate_face_stats(self, landmarks, frame_shape):
        """Calculate face distance, posture stability, and identity switches"""
        try:
            h, w = frame_shape[:2]
            current_time = datetime.now()
            
            # 1. Face Screen Distance (Inverse of IPD)
            # Left Eye: 33, Right Eye: 263
            left_eye = landmarks.landmark[33]
            right_eye = landmarks.landmark[263]
            
            # Calculate geometric distance (IPD in normalized coordinates)
            ipd = np.sqrt((left_eye.x - right_eye.x)**2 + (left_eye.y - right_eye.y)**2)
            
            # Start with a heuristic: if IPD is large, face is close. 
            # Approximate distance (cm) = Constant / IPD
            # Assuming standard IPD of 63mm.
            estimated_distance = self.SCREEN_DISTANCE_REF / (ipd * w) # Heuristic
            
            # 2. Posture Stability (Movement of nose tip)
            nose_tip = landmarks.landmark[1]
            nose_pos = (nose_tip.x, nose_tip.y)
            self.face_positions.append(nose_pos)
            
            posture_stability = 0.0
            if len(self.face_positions) > 5:
                # Variance of position
                pos_array = np.array(self.face_positions)
                posture_stability = np.mean(np.std(pos_array, axis=0))
                
            # 3. Identity Switch Rate (Heuristic based on face loss)
            # If we lost face for > 1 sec and got it back, count as switch
            time_since_last_face = (current_time - self.last_face_time).total_seconds()
            
            if self.consecutive_no_face > 0 and time_since_last_face > 1.0:
                 self.face_switches += 1
            
            self.last_face_time = current_time
            
            # Calculate rate (switches per hour)
            uptime_hours = (current_time - self.face_switch_start_time).total_seconds() / 3600
            switch_rate = self.face_switches / uptime_hours if uptime_hours > 0.01 else 0.0
            
            return {
                'distance': float(estimated_distance),
                'stability': float(posture_stability),
                'switch_rate': float(switch_rate),
                'hand_interaction': 0.0, # Placeholder
                'secondary_device': 0.0 # Placeholder
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating face stats: {e}")
            return {'distance': 0.0, 'stability': 0.0, 'switch_rate': 0.0, 'hand_interaction': 0.0, 'secondary_device': 0.0}
    
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
                'attention_trend': list(self.attention_scores)[-10:],
                # New Metrics for Live View
                'gaze_on_screen': self.gaze_history[-1][0] if self.gaze_history else 0, # Just X coord for now
                'posture_stability': 1.0 - (current_attention * 0.1) # Placeholder proxy
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
