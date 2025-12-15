import time
import threading
import logging
from datetime import datetime
from pynput import keyboard
import psutil
import pyautogui
from collections import deque
import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config.settings import KEYSTROKE_LOG_INTERVAL, IDLE_THRESHOLD
from src.data_processing.database_manager import DatabaseManager

class KeystrokeLogger:
    """Monitors and logs keystroke activity for productivity tracking"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db_manager = DatabaseManager()
        self.is_running = False
        
        # Keystroke tracking variables
        self.key_buffer = deque(maxlen=100)  # Store recent keystrokes
        self.last_keystroke_time = datetime.now()
        self.typing_speeds = deque(maxlen=20)  # Store recent typing speeds
        self.current_key_count = 0
        self.current_error_count = 0 # Track backspaces/deletes
        self.session_start_time = datetime.now()
        
        # Threading
        self.listener_thread = None
        self.analyzer_thread = None
        self.keyboard_listener = None
        
    def start(self):
        """Start keystroke monitoring"""
        if self.is_running:
            self.logger.warning("Keystroke logger is already running")
            return
            
        self.is_running = True
        self.session_start_time = datetime.now()
        
        # Start keyboard listener
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self.keyboard_listener.start()
        
        # Start analyzer thread
        self.analyzer_thread = threading.Thread(target=self._analyze_typing_activity, daemon=True)
        self.analyzer_thread.start()
        
        self.logger.info("Keystroke logger started")
    
    def stop(self):
        """Stop keystroke monitoring"""
        self.is_running = False
        
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            
        self.logger.info("Keystroke logger stopped")
    
    def _on_key_press(self, key):
        """Handle key press events"""
        try:
            current_time = datetime.now()
            
            # Add keystroke to buffer
            self.key_buffer.append({
                'timestamp': current_time,
                'key': str(key),
                'type': 'press'
            })
            
            self.current_key_count += 1
            
            # Check for error keys (Backspace/Delete)
            key_str = str(key)
            if 'Key.backspace' in key_str or 'Key.delete' in key_str:
                self.current_error_count += 1
                
            self.last_keystroke_time = current_time
            
        except Exception as e:
            self.logger.error(f"Error handling key press: {e}")
    
    def _on_key_release(self, key):
        """Handle key release events"""
        try:
            current_time = datetime.now()
            
            # Add keystroke to buffer
            self.key_buffer.append({
                'timestamp': current_time,
                'key': str(key),
                'type': 'release'
            })
            
        except Exception as e:
            self.logger.error(f"Error handling key release: {e}")
    
    def _analyze_typing_activity(self):
        """Analyze typing patterns and calculate metrics"""
        while self.is_running:
            try:
                current_time = datetime.now()
                
                # Calculate metrics
                typing_speed = self._calculate_typing_speed()
                burstiness = self._calculate_burstiness()
                error_count = self.current_error_count
                
                # Check if user is active
                is_active = self._is_user_active()
                
                # Get active window information
                active_window = self._get_active_window()
                
                # Prepare data for database
                keystroke_data = {
                    'timestamp': current_time,
                    'typing_speed': typing_speed,
                    'key_count': self.current_key_count,
                    'error_count': error_count,
                    'burstiness': burstiness,
                    'active_window': active_window,
                    'is_active': is_active
                }
                
                # Store in database
                self.db_manager.insert_keystroke_data(keystroke_data)
                
                # Reset counters
                self.current_key_count = 0
                self.current_error_count = 0 # Reset error count
                
                # Log metrics periodically
                if len(self.typing_speeds) > 0:
                    avg_speed = sum(self.typing_speeds) / len(self.typing_speeds)
                    self.logger.debug(f"Speed: {typing_speed:.1f} WPM, Errors: {error_count}, Burst: {burstiness:.2f}")
                
                time.sleep(KEYSTROKE_LOG_INTERVAL)
                
            except Exception as e:
                self.logger.error(f"Error in typing analysis: {e}")
                time.sleep(KEYSTROKE_LOG_INTERVAL)
    
    def _calculate_typing_speed(self):
        """Calculate typing speed in words per minute"""
        try:
            if len(self.key_buffer) < 2:
                return 0.0
            
            # Get keystrokes from the last minute
            current_time = datetime.now()
            one_minute_ago = current_time.timestamp() - 60
            
            recent_keys = [
                k for k in self.key_buffer 
                if k['timestamp'].timestamp() > one_minute_ago and k['type'] == 'press'
            ]
            
            if len(recent_keys) == 0:
                return 0.0
            
            # Calculate words per minute (assuming 5 characters per word)
            chars_per_minute = len(recent_keys)
            words_per_minute = chars_per_minute / 5.0
            
            # Store for average calculation
            self.typing_speeds.append(words_per_minute)
            
            return words_per_minute
            
        except Exception as e:
            self.logger.error(f"Error calculating typing speed: {e}")
            return 0.0

    def _calculate_burstiness(self):
        """Calculate typing burstiness (standard deviation of inter-key intervals)"""
        try:
            if len(self.key_buffer) < 3:
                return 0.0
                
            current_time = datetime.now()
            twenty_sec_ago = current_time.timestamp() - 20 # shorter window for burstiness
            
            # Get recent press timestamps
            timestamps = [
                k['timestamp'].timestamp() 
                for k in self.key_buffer 
                if k['timestamp'].timestamp() > twenty_sec_ago and k['type'] == 'press'
            ]
            
            if len(timestamps) < 2:
                return 0.0
                
            # Calculate intervals
            intervals = [t2 - t1 for t1, t2 in zip(timestamps[:-1], timestamps[1:])]
            
            if not intervals:
                return 0.0
            
            # Standard deviation
            mean_interval = sum(intervals) / len(intervals)
            variance = sum((x - mean_interval) ** 2 for x in intervals) / len(intervals)
            return variance ** 0.5
            
        except Exception as e:
            self.logger.error(f"Error calculating burstiness: {e}")
            return 0.0
    
    def _is_user_active(self):
        """Determine if user is currently active based on recent keystrokes"""
        try:
            current_time = datetime.now()
            time_since_last_key = (current_time - self.last_keystroke_time).total_seconds()
            
            return time_since_last_key < IDLE_THRESHOLD
            
        except Exception as e:
            self.logger.error(f"Error checking user activity: {e}")
            return False
    
    def _get_active_window(self):
        """Get the title of the currently active window"""
        try:
            # This is a simplified version - in practice, you might need platform-specific code
            return pyautogui.getActiveWindow().title if pyautogui.getActiveWindow() else "Unknown"
        except Exception as e:
            # Fallback method using psutil
            try:
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        # This is a simplified approach
                        return proc.info['name']
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                return "Unknown"
            except Exception as e2:
                self.logger.error(f"Error getting active window: {e}, {e2}")
                return "Unknown"
    
    def get_session_stats(self):
        """Get statistics for the current session"""
        try:
            current_time = datetime.now()
            session_duration = (current_time - self.session_start_time).total_seconds()
            
            total_keystrokes = sum([1 for k in self.key_buffer if k['type'] == 'press'])
            avg_typing_speed = sum(self.typing_speeds) / len(self.typing_speeds) if self.typing_speeds else 0
            
            return {
                'session_duration_minutes': session_duration / 60,
                'total_keystrokes': total_keystrokes,
                'average_typing_speed': avg_typing_speed,
                'is_active': self._is_user_active(),
                'current_typing_speed': self._calculate_typing_speed()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting session stats: {e}")
            return {}
    
    def get_recent_activity(self, minutes: int = 60):
        """Get keystroke activity from the last N minutes"""
        try:
            current_time = datetime.now()
            cutoff_time = current_time.timestamp() - (minutes * 60)
            
            recent_activity = [
                k for k in self.key_buffer 
                if k['timestamp'].timestamp() > cutoff_time
            ]
            
            # Group by minute for visualization
            activity_by_minute = {}
            for activity in recent_activity:
                minute_key = activity['timestamp'].strftime('%H:%M')
                if minute_key not in activity_by_minute:
                    activity_by_minute[minute_key] = 0
                activity_by_minute[minute_key] += 1
            
            return activity_by_minute
            
        except Exception as e:
            self.logger.error(f"Error getting recent activity: {e}")
            return {}

def main():
    """Main function for testing the keystroke logger"""
    import logging.config
    from config.settings import LOGGING_CONFIG
    
    # Set up logging
    logging.config.dictConfig(LOGGING_CONFIG)
    logger = logging.getLogger(__name__)
    
    # Create and start keystroke logger
    keystroke_logger = KeystrokeLogger()
    
    try:
        logger.info("Starting keystroke logger...")
        keystroke_logger.start()
        
        # Run for a while to collect data
        while True:
            time.sleep(10)
            stats = keystroke_logger.get_session_stats()
            logger.info(f"Session stats: {stats}")
            
    except KeyboardInterrupt:
        logger.info("Stopping keystroke logger...")
        keystroke_logger.stop()
    except Exception as e:
        logger.error(f"Error in keystroke logger: {e}")
        keystroke_logger.stop()

if __name__ == "__main__":
    main()
