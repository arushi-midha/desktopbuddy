import time
import threading
import logging
import logging.config
import signal
import sys
import os
from datetime import datetime
# add at top with your other imports
import atexit



# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from config.settings import LOGGING_CONFIG
from src.data_collection.keystroke_logger import KeystrokeLogger
from src.data_collection.window_tracker import WindowTracker
from src.data_collection.webcam_monitor import WebcamMonitor
from src.data_processing.database_manager import DatabaseManager

class DataCollector:
    """Unified data collection orchestrator for DeskBuddy"""
    
    def __init__(self, enable_webcam=True, enable_keystroke=True, enable_window=True):
        # Set up logging
        logging.config.dictConfig(LOGGING_CONFIG)
        self.logger = logging.getLogger(__name__)
        
        # Initialize database manager
        self.db_manager = DatabaseManager()
        
        # Component flags
        self.enable_webcam = enable_webcam
        self.enable_keystroke = enable_keystroke
        self.enable_window = enable_window
        
        # Initialize collectors
        self.collectors = {}
        self.is_running = False
        
        # Statistics tracking
        self.session_start_time = None
        self.stats_thread = None
        
        # Set up signal handlers for graceful shutdown
        # signal.signal(signal.SIGINT, self._signal_handler)
        # signal.signal(signal.SIGTERM, self._signal_handler)
        # --- replace your current signal.signal(...) lines with this ---
        in_main_thread = threading.current_thread() is threading.main_thread()
        running_in_streamlit = ("streamlit" in sys.modules) or (os.environ.get("STREAMLIT_RUNTIME") == "true")

        if in_main_thread and not running_in_streamlit:
            try:
                signal.signal(signal.SIGINT, self._signal_handler)
                if hasattr(signal, "SIGTERM"):  # SIGTERM guard for Windows
                    signal.signal(signal.SIGTERM, self._signal_handler)
            except Exception as e:
                self.logger.debug(f"Could not set signal handlers: {e}")
        else:
            self.logger.info("Non-main thread or Streamlit detected — skipping signal handlers.")

        # Always ensure cleanup on process exit
        atexit.register(self.stop)

    
    def start(self):
        """Start all enabled data collectors"""
        if self.is_running:
            self.logger.warning("Data collector is already running")
            return
        
        self.logger.info("Starting DeskBuddy data collection...")
        self.session_start_time = datetime.now()
        
        try:
            # Initialize and start collectors
            if self.enable_keystroke:
                self.logger.info("Initializing keystroke logger...")
                self.collectors['keystroke'] = KeystrokeLogger()
                self.collectors['keystroke'].start()
                self.logger.info("Keystroke logger started")
            
            if self.enable_window:
                self.logger.info("Initializing window tracker...")
                self.collectors['window'] = WindowTracker()
                self.collectors['window'].start()
                self.logger.info("Window tracker started")
            
            if self.enable_webcam:
                self.logger.info("Initializing webcam monitor...")
                try:
                    self.collectors['webcam'] = WebcamMonitor()
                    self.collectors['webcam'].start()
                    self.logger.info("Webcam monitor started")
                except Exception as e:
                    self.logger.warning(f"Could not start webcam monitor: {e}")
                    self.enable_webcam = False
            
            self.is_running = True
            
            # Start statistics reporting thread
            self.stats_thread = threading.Thread(target=self._periodic_stats, daemon=True)
            self.stats_thread.start()
            
            self.logger.info("All data collectors started successfully!")
            
        except Exception as e:
            self.logger.error(f"Error starting data collectors: {e}")
            self.stop()
            raise
    
    def stop(self):
        """Stop all data collectors"""
        if not self.is_running:
            return
        
        self.logger.info("Stopping data collection...")
        self.is_running = False
        
        # Stop all collectors
        for name, collector in self.collectors.items():
            try:
                self.logger.info(f"Stopping {name} collector...")
                collector.stop()
            except Exception as e:
                self.logger.error(f"Error stopping {name} collector: {e}")
        
        # Clean up database
        try:
            self.db_manager.cleanup_old_data()
        except Exception as e:
            self.logger.error(f"Error during database cleanup: {e}")
        
        self.logger.info("Data collection stopped")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
    
    def _periodic_stats(self):
        """Periodically log collection statistics"""
        while self.is_running:
            try:
                time.sleep(60)  # Report stats every minute
                if self.is_running:
                    stats = self.get_collection_stats()
                    self._log_stats(stats)
                    
            except Exception as e:
                self.logger.error(f"Error in periodic stats: {e}")
    
    def get_collection_stats(self):
        """Get comprehensive statistics from all collectors"""
        stats = {
            'session_duration_minutes': 0,
            'keystroke_stats': {},
            'window_stats': {},
            'webcam_stats': {},
            'overall_productivity': 0.0
        }
        
        try:
            # Calculate session duration
            if self.session_start_time:
                duration = (datetime.now() - self.session_start_time).total_seconds() / 60
                stats['session_duration_minutes'] = duration
            
            # Get keystroke statistics
            if 'keystroke' in self.collectors:
                try:
                    keystroke_stats = self.collectors['keystroke'].get_session_stats()
                    stats['keystroke_stats'] = keystroke_stats
                except Exception as e:
                    self.logger.error(f"Error getting keystroke stats: {e}")
            
            # Get window statistics
            if 'window' in self.collectors:
                try:
                    window_stats = self.collectors['window'].get_current_session_stats()
                    productivity_score = self.collectors['window'].get_productivity_score()
                    stats['window_stats'] = window_stats
                    stats['window_stats']['productivity_score'] = productivity_score
                except Exception as e:
                    self.logger.error(f"Error getting window stats: {e}")
            
            # Get webcam statistics
            if 'webcam' in self.collectors:
                try:
                    webcam_state = self.collectors['webcam'].get_current_attention_state()
                    webcam_summary = self.collectors['webcam'].get_session_summary()
                    stats['webcam_stats'] = {**webcam_state, **webcam_summary}
                except Exception as e:
                    self.logger.error(f"Error getting webcam stats: {e}")
            
            # Calculate overall productivity score
            stats['overall_productivity'] = self._calculate_overall_productivity(stats)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting collection stats: {e}")
            return stats
    
    def _calculate_overall_productivity(self, stats):
        """Calculate overall productivity score combining all metrics"""
        try:
            scores = []
            weights = []
            
            # Window productivity score (weight: 40%)
            if 'productivity_score' in stats.get('window_stats', {}):
                scores.append(stats['window_stats']['productivity_score'])
                weights.append(0.4)
            
            # Attention score (weight: 35%)
            if 'average_attention' in stats.get('webcam_stats', {}):
                attention_score = stats['webcam_stats']['average_attention'] * 100
                scores.append(attention_score)
                weights.append(0.35)
            
            # Typing activity score (weight: 25%)
            if 'is_active' in stats.get('keystroke_stats', {}):
                activity_score = 100 if stats['keystroke_stats']['is_active'] else 20
                scores.append(activity_score)
                weights.append(0.25)
            
            if scores and weights:
                # Weighted average
                total_weight = sum(weights)
                weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
                return weighted_sum / total_weight
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculating productivity: {e}")
            return 0.0
    
    def _log_stats(self, stats):
        """Log collection statistics"""
        try:
            duration = stats.get('session_duration_minutes', 0)
            productivity = stats.get('overall_productivity', 0)
            
            log_msg = f"Session: {duration:.1f}min, Overall Productivity: {productivity:.1f}%"
            
            # Add keystroke info
            keystroke_stats = stats.get('keystroke_stats', {})
            if keystroke_stats:
                typing_speed = keystroke_stats.get('current_typing_speed', 0)
                is_active = keystroke_stats.get('is_active', False)
                log_msg += f", Typing: {typing_speed:.1f}WPM {'(Active)' if is_active else '(Idle)'}"
            
            # Add window info
            window_stats = stats.get('window_stats', {})
            if window_stats and 'top_applications' in window_stats:
                top_apps = window_stats['top_applications']
                if top_apps:
                    top_app = top_apps[0][0]
                    log_msg += f", Top App: {top_app}"
            
            # Add attention info
            webcam_stats = stats.get('webcam_stats', {})
            if webcam_stats:
                attention = webcam_stats.get('current_attention', 0)
                face_detected = webcam_stats.get('face_detected', False)
                log_msg += f", Attention: {attention:.2f} {'(Face)' if face_detected else '(No Face)'}"
            
            self.logger.info(log_msg)
            
        except Exception as e:
            self.logger.error(f"Error logging stats: {e}")
    
    def get_live_dashboard_data(self):
        """Get real-time data for dashboard display"""
        try:
            stats = self.get_collection_stats()
            
            # Format data for dashboard consumption
            dashboard_data = {
                'timestamp': datetime.now().isoformat(),
                'session_duration': stats.get('session_duration_minutes', 0),
                'productivity_score': stats.get('overall_productivity', 0),
                'current_activity': {
                    'typing_speed': stats.get('keystroke_stats', {}).get('current_typing_speed', 0),
                    'is_typing_active': stats.get('keystroke_stats', {}).get('is_active', False),
                    'current_window': stats.get('window_stats', {}).get('current_window', {}),
                    'attention_level': stats.get('webcam_stats', {}).get('current_attention', 0),
                    'face_detected': stats.get('webcam_stats', {}).get('face_detected', False)
                },
                'session_summary': {
                    'total_keystrokes': stats.get('keystroke_stats', {}).get('total_keystrokes', 0),
                    'avg_typing_speed': stats.get('keystroke_stats', {}).get('average_typing_speed', 0),
                    'app_usage': stats.get('window_stats', {}).get('app_usage', {}),
                    'focus_percentage': stats.get('webcam_stats', {}).get('focus_percentage', 0),
                    'avg_attention': stats.get('webcam_stats', {}).get('average_attention', 0)
                }
            }
            
            return dashboard_data
            
        except Exception as e:
            self.logger.error(f"Error getting live dashboard data: {e}")
            return {}
    
    def run_continuously(self):
        """Run the data collector continuously"""
        try:
            self.start()
            
            self.logger.info("DeskBuddy is now collecting data. Press Ctrl+C to stop.")
            
            # Keep the main thread alive
            while self.is_running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        except Exception as e:
            self.logger.error(f"Error in continuous run: {e}")
        finally:
            self.stop()

def main():
    """Main function for running the data collector"""
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='DeskBuddy Data Collector')
    parser.add_argument('--no-webcam', action='store_true', help='Disable webcam monitoring')
    parser.add_argument('--no-keystroke', action='store_true', help='Disable keystroke logging')
    parser.add_argument('--no-window', action='store_true', help='Disable window tracking')
    parser.add_argument('--stats-only', action='store_true', help='Only show statistics, no continuous collection')
    
    args = parser.parse_args()
    
    # Create data collector with specified options
    collector = DataCollector(
        enable_webcam=not args.no_webcam,
        enable_keystroke=not args.no_keystroke,
        enable_window=not args.no_window
    )
    
    if args.stats_only:
        # Just show current statistics
        print("DeskBuddy Data Collection Statistics")
        print("=" * 40)
        try:
            collector.start()
            time.sleep(5)  # Collect data for a few seconds
            stats = collector.get_collection_stats()
            collector.stop()
            
            print(f"Session Duration: {stats.get('session_duration_minutes', 0):.1f} minutes")
            print(f"Overall Productivity: {stats.get('overall_productivity', 0):.1f}%")
            print("\nKeystroke Stats:", stats.get('keystroke_stats', {}))
            print("\nWindow Stats:", stats.get('window_stats', {}))
            print("\nWebcam Stats:", stats.get('webcam_stats', {}))
            
        except Exception as e:
            print(f"Error getting stats: {e}")
    else:
        # Run continuously
        collector.run_continuously()

if __name__ == "__main__":
    main()
