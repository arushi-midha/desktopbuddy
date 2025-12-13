import time
import threading
import logging
from datetime import datetime
import math
from pynput import mouse
from collections import deque
import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config.settings import KEYSTROKE_LOG_INTERVAL, IDLE_THRESHOLD
from src.data_processing.database_manager import DatabaseManager
import pyautogui  # For active window
import psutil

class MouseTracker:
    """Monitors mouse activity including movement, clicks, and scrolling"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db_manager = DatabaseManager()
        self.is_running = False
        
        # Mouse tracking variables
        self.mouse_listener = None
        self.analyzer_thread = None
        
        self.last_pos = None
        self.move_distance = 0.0
        self.click_count = 0
        self.scroll_count = 0
        self.scroll_accumulation = 0  # To track direction
        
        self.idle_time_accumulated = 0.0
        self.last_event_time = datetime.now()
        
        # Buffer to calculate velocity
        self.move_events = deque(maxlen=100)  # (timestamp, distance)
        
    def start(self):
        """Start mouse monitoring"""
        if self.is_running:
            return
            
        self.is_running = True
        self.last_event_time = datetime.now()
        
        # Start mouse listener
        self.mouse_listener = mouse.Listener(
            on_move=self._on_move,
            on_click=self._on_click,
            on_scroll=self._on_scroll
        )
        self.mouse_listener.start()
        
        # Start analyzer thread
        self.analyzer_thread = threading.Thread(target=self._analyze_mouse_activity, daemon=True)
        self.analyzer_thread.start()
        
        self.logger.info("Mouse tracker started")
        
    def stop(self):
        """Stop mouse monitoring"""
        self.is_running = False
        if self.mouse_listener:
            self.mouse_listener.stop()
        self.logger.info("Mouse tracker stopped")
        
    def _on_move(self, x, y):
        try:
            current_time = datetime.now()
            if self.last_pos:
                dist = math.sqrt((x - self.last_pos[0])**2 + (y - self.last_pos[1])**2)
                self.move_distance += dist
                self.move_events.append((current_time, dist))
            
            self.last_pos = (x, y)
            self._update_idle_timer(current_time)
            
        except Exception as e:
            pass # Suppress rapid errors

    def _on_click(self, x, y, button, pressed):
        if pressed:
            self.click_count += 1
            self._update_idle_timer(datetime.now())

    def _on_scroll(self, x, y, dx, dy):
        self.scroll_count += 1
        self.scroll_accumulation += dy
        self._update_idle_timer(datetime.now())

    def _update_idle_timer(self, current_time):
        """Update idle status"""
        dt = (current_time - self.last_event_time).total_seconds()
        # If dt was large, it means we were idle
        self.last_event_time = current_time

    def _get_active_window_info(self):
        """Helper to get active window and app name"""
        try:
            # Fallback/Simplified logic similar to other trackers
            window = pyautogui.getActiveWindow()
            title = window.title if window else "Unknown"
            # Getting app name is platform dependent/expensive, we can try best effort or reuse logic
            # For efficiency in this thread, we might skip deep process inspection or cache it
            return title, "Unknown"  # App name might need psutil logic if critical
        except:
            return "Unknown", "Unknown"

    def _analyze_mouse_activity(self):
        """Analyze mouse metrics and store to DB"""
        while self.is_running:
            try:
                time.sleep(KEYSTROKE_LOG_INTERVAL) # Use same interval as keystroke logger (1s usually)
                
                current_time = datetime.now()
                
                # Calculate velocity (pixels/sec)
                total_dist_in_buffer = sum(d for t, d in self.move_events)
                if len(self.move_events) > 1:
                    duration = (self.move_events[-1][0] - self.move_events[0][0]).total_seconds()
                    avg_velocity = total_dist_in_buffer / duration if duration > 0 else 0
                else:
                    avg_velocity = 0
                
                # Determine scroll direction
                scroll_dir = "NONE"
                if self.scroll_accumulation > 0: scroll_dir = "UP"
                elif self.scroll_accumulation < 0: scroll_dir = "DOWN"
                elif self.scroll_count > 0: scroll_dir = "MIXED"
                
                # Calculate idle ratio for this interval
                # A simplistic approach: if no events in this interval ? 
                # Better: The Listener updates last_event_time.
                time_since_last = (current_time - self.last_event_time).total_seconds()
                is_idle_now = time_since_last > 1.0 # If no event in last second
                idle_ratio = 1.0 if is_idle_now else 0.0 # This is coarse. 
                
                # Get Window Info
                active_window, app_name = self._get_active_window_info()

                mouse_data = {
                    'timestamp': current_time,
                    'active_window': active_window,
                    'application_name': app_name, # Can improve this later
                    'move_distance': self.move_distance,
                    'avg_velocity': avg_velocity,
                    'click_count': self.click_count,
                    'scroll_count': self.scroll_count,
                    'scroll_direction': scroll_dir,
                    'idle_ratio': idle_ratio
                }
                
                self.db_manager.insert_mouse_data(mouse_data)
                
                # Reset counters
                self.move_distance = 0
                self.click_count = 0
                self.scroll_count = 0
                self.scroll_accumulation = 0
                self.move_events.clear()
                
            except Exception as e:
                self.logger.error(f"Error in mouse analysis: {e}")
