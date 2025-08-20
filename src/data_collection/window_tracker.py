import time
import threading
import logging
from datetime import datetime
import psutil
import pyautogui
from collections import defaultdict
import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config.settings import WINDOW_TRACK_INTERVAL, APP_CATEGORIES
from src.data_processing.database_manager import DatabaseManager

try:
    import win32gui
    import win32process
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False
    print("Windows-specific modules not available. Using fallback methods.")

class WindowTracker:
    """Monitors active windows and application usage for productivity tracking"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db_manager = DatabaseManager()
        self.is_running = False
        
        # Window tracking variables
        self.current_window = None
        self.window_start_time = None
        self.window_history = []
        self.app_usage_time = defaultdict(float)
        
        # Threading
        self.tracker_thread = None
        
    def start(self):
        """Start window monitoring"""
        if self.is_running:
            self.logger.warning("Window tracker is already running")
            return
            
        self.is_running = True
        self.window_start_time = datetime.now()
        
        # Start tracker thread
        self.tracker_thread = threading.Thread(target=self._track_windows, daemon=True)
        self.tracker_thread.start()
        
        self.logger.info("Window tracker started")
    
    def stop(self):
        """Stop window monitoring"""
        self.is_running = False
        
        # Record the final window session
        if self.current_window and self.window_start_time:
            self._record_window_session()
        
        self.logger.info("Window tracker stopped")
    
    def _track_windows(self):
        """Main window tracking loop"""
        while self.is_running:
            try:
                # Get current active window
                window_info = self._get_active_window_info()
                
                if window_info and window_info != self.current_window:
                    # Record previous window session
                    if self.current_window and self.window_start_time:
                        self._record_window_session()
                    
                    # Start new window session
                    self.current_window = window_info
                    self.window_start_time = datetime.now()
                    
                    self.logger.debug(f"Switched to: {window_info['application_name']} - {window_info['window_title']}")
                
                time.sleep(WINDOW_TRACK_INTERVAL)
                
            except Exception as e:
                self.logger.error(f"Error in window tracking: {e}")
                time.sleep(WINDOW_TRACK_INTERVAL)
    
    def _get_active_window_info(self):
        """Get information about the currently active window"""
        try:
            if WINDOWS_AVAILABLE:
                return self._get_windows_window_info()
            else:
                return self._get_fallback_window_info()
                
        except Exception as e:
            self.logger.error(f"Error getting window info: {e}")
            return None
    
    def _get_windows_window_info(self):
        """Get window info on Windows using win32 APIs"""
        try:
            # Get the handle of the active window
            hwnd = win32gui.GetForegroundWindow()
            
            # Get window title
            window_title = win32gui.GetWindowText(hwnd)
            
            # Get process ID
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            
            # Get process info
            try:
                process = psutil.Process(pid)
                app_name = process.name()
                exe_path = process.exe()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                app_name = "Unknown"
                exe_path = ""
            
            # Categorize the application
            category = self._categorize_application(app_name, window_title)
            
            return {
                'window_title': window_title[:200],  # Limit length
                'application_name': app_name,
                'category': category,
                'process_id': pid,
                'executable_path': exe_path
            }
            
        except Exception as e:
            self.logger.error(f"Error getting Windows window info: {e}")
            return None
    
    def _get_fallback_window_info(self):
        """Fallback method for getting window info"""
        try:
            # Try using pyautogui
            active_window = pyautogui.getActiveWindow()
            if active_window:
                window_title = active_window.title
                app_name = "Unknown"
                
                # Try to get more info from running processes
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        if window_title.lower() in ' '.join(proc.info['cmdline'] or []).lower():
                            app_name = proc.info['name']
                            break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                category = self._categorize_application(app_name, window_title)
                
                return {
                    'window_title': window_title[:200],
                    'application_name': app_name,
                    'category': category,
                    'process_id': None,
                    'executable_path': ""
                }
            
        except Exception as e:
            self.logger.error(f"Error with fallback window info: {e}")
        
        return None
    
    def _categorize_application(self, app_name, window_title):
        """Categorize application based on name and window title"""
        try:
            app_name_lower = app_name.lower()
            window_title_lower = window_title.lower()
            
            for category, keywords in APP_CATEGORIES.items():
                if category == 'other':
                    continue
                    
                for keyword in keywords:
                    if (keyword in app_name_lower or 
                        keyword in window_title_lower):
                        return category
            
            return 'other'
            
        except Exception as e:
            self.logger.error(f"Error categorizing application: {e}")
            return 'other'
    
    def _record_window_session(self):
        """Record the completed window session to database"""
        try:
            if not self.current_window or not self.window_start_time:
                return
            
            end_time = datetime.now()
            duration = (end_time - self.window_start_time).total_seconds()
            
            # Only record sessions longer than 1 second
            if duration >= 1.0:
                window_data = {
                    'timestamp': self.window_start_time,
                    'window_title': self.current_window['window_title'],
                    'application_name': self.current_window['application_name'],
                    'category': self.current_window['category'],
                    'duration_seconds': duration
                }
                
                # Store in database
                self.db_manager.insert_window_data(window_data)
                
                # Update local usage tracking
                app_name = self.current_window['application_name']
                self.app_usage_time[app_name] += duration
                
                # Add to history
                self.window_history.append({
                    **window_data,
                    'end_time': end_time
                })
                
                # Keep only recent history (last 100 entries)
                if len(self.window_history) > 100:
                    self.window_history = self.window_history[-100:]
                
                self.logger.debug(f"Recorded session: {app_name} for {duration:.1f}s")
            
        except Exception as e:
            self.logger.error(f"Error recording window session: {e}")
    
    def get_current_session_stats(self):
        """Get statistics for the current session"""
        try:
            total_time = sum(self.app_usage_time.values())
            
            # Calculate usage by category
            category_usage = defaultdict(float)
            for app_name, usage_time in self.app_usage_time.items():
                # Find the app in recent history to get its category
                category = 'other'
                for entry in reversed(self.window_history):
                    if entry['application_name'] == app_name:
                        category = entry['category']
                        break
                category_usage[category] += usage_time
            
            # Get top applications
            top_apps = sorted(
                self.app_usage_time.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10]
            
            return {
                'total_time_seconds': total_time,
                'total_time_minutes': total_time / 60,
                'app_usage': dict(self.app_usage_time),
                'category_usage': dict(category_usage),
                'top_applications': top_apps,
                'current_window': self.current_window,
                'session_count': len(self.window_history)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting session stats: {e}")
            return {}
    
    def get_productivity_score(self):
        """Calculate a productivity score based on application categories"""
        try:
            category_usage = defaultdict(float)
            total_time = sum(self.app_usage_time.values())
            
            if total_time == 0:
                return 0.0
            
            # Get category breakdown
            for app_name, usage_time in self.app_usage_time.items():
                category = 'other'
                for entry in reversed(self.window_history):
                    if entry['application_name'] == app_name:
                        category = entry['category']
                        break
                category_usage[category] += usage_time
            
            # Calculate productivity score (0-100)
            productive_time = (
                category_usage.get('productivity', 0) + 
                category_usage.get('communication', 0) * 0.7 +  # Communication is partially productive
                category_usage.get('browsing', 0) * 0.3  # Browsing can be research
            )
            
            productivity_score = (productive_time / total_time) * 100
            return min(100, max(0, productivity_score))
            
        except Exception as e:
            self.logger.error(f"Error calculating productivity score: {e}")
            return 0.0
    
    def get_recent_activity(self, minutes: int = 60):
        """Get window activity from the last N minutes"""
        try:
            current_time = datetime.now()
            cutoff_time = current_time.timestamp() - (minutes * 60)
            
            recent_activity = [
                entry for entry in self.window_history
                if entry['timestamp'].timestamp() > cutoff_time
            ]
            
            return recent_activity
            
        except Exception as e:
            self.logger.error(f"Error getting recent activity: {e}")
            return []
    
    def get_app_timeline(self, hours: int = 8):
        """Get a timeline of application usage"""
        try:
            current_time = datetime.now()
            cutoff_time = current_time.timestamp() - (hours * 3600)
            
            timeline = []
            for entry in self.window_history:
                if entry['timestamp'].timestamp() > cutoff_time:
                    timeline.append({
                        'start_time': entry['timestamp'],
                        'end_time': entry.get('end_time', current_time),
                        'application': entry['application_name'],
                        'category': entry['category'],
                        'duration': entry['duration_seconds']
                    })
            
            return sorted(timeline, key=lambda x: x['start_time'])
            
        except Exception as e:
            self.logger.error(f"Error getting app timeline: {e}")
            return []

def main():
    """Main function for testing the window tracker"""
    import logging.config
    from config.settings import LOGGING_CONFIG
    
    # Set up logging
    logging.config.dictConfig(LOGGING_CONFIG)
    logger = logging.getLogger(__name__)
    
    # Create and start window tracker
    window_tracker = WindowTracker()
    
    try:
        logger.info("Starting window tracker...")
        window_tracker.start()
        
        # Run for a while to collect data
        while True:
            time.sleep(30)
            stats = window_tracker.get_current_session_stats()
            productivity_score = window_tracker.get_productivity_score()
            
            logger.info(f"Session stats: {len(stats.get('top_applications', []))} apps tracked")
            logger.info(f"Productivity score: {productivity_score:.1f}%")
            logger.info(f"Top app: {stats.get('top_applications', [('None', 0)])[0]}")
            
    except KeyboardInterrupt:
        logger.info("Stopping window tracker...")
        window_tracker.stop()
    except Exception as e:
        logger.error(f"Error in window tracker: {e}")
        window_tracker.stop()

if __name__ == "__main__":
    main()
