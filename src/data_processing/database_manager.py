import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
from typing import List, Dict, Any, Optional
import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config.settings import DATABASE_PATH, DATA_RETENTION_DAYS

class DatabaseManager:
    """Manages SQLite database operations for DeskBuddy"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DATABASE_PATH
        self.logger = logging.getLogger(__name__)
        self.init_database()
        self._migrate_schema()
        self._migrate_attention_schema()
    
    def _migrate_schema(self):
        """Check and migrate database schema for new columns"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Migrate keystroke_activity
                cursor.execute("PRAGMA table_info(keystroke_activity)")
                columns = [info[1] for info in cursor.fetchall()]
                
                if 'error_count' not in columns:
                    self.logger.info("Migrating keystroke_activity: adding error_count")
                    cursor.execute("ALTER TABLE keystroke_activity ADD COLUMN error_count INTEGER DEFAULT 0")
                
                if 'burstiness' not in columns:
                    self.logger.info("Migrating keystroke_activity: adding burstiness")
                    cursor.execute("ALTER TABLE keystroke_activity ADD COLUMN burstiness REAL DEFAULT 0.0")
                    
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error migrating schema: {e}")
            
    def init_database(self):
        """Initialize database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create keystroke logs table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS keystroke_activity (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME,
                        typing_speed REAL,
                        key_count INTEGER,
                        error_count INTEGER DEFAULT 0,
                        burstiness REAL DEFAULT 0.0,
                        active_window TEXT,
                        is_active BOOLEAN
                    )
                ''')
                
                # Window/Application usage table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS window_activity (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME NOT NULL,
                        window_title TEXT,
                        application_name TEXT,
                        category TEXT,
                        duration_seconds REAL DEFAULT 0
                    )
                ''')
                
                # Create mouse activity table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS mouse_activity (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME,
                        active_window TEXT,
                        application_name TEXT,
                        move_distance REAL,
                        avg_velocity REAL,
                        click_count INTEGER,
                        scroll_count INTEGER,
                        scroll_direction TEXT,
                        idle_ratio REAL
                    )
                ''')
                
                # Webcam attention data table (Updated Schema)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS attention_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME NOT NULL,
                        gaze_on_screen_ratio REAL,
                        gaze_dispersion REAL,
                        gaze_shift_rate REAL,
                        blink_rate REAL,
                        eye_closure_ratio REAL,
                        head_pose_variance REAL,
                        head_turn_rate REAL,
                        face_screen_distance REAL,
                        posture_stability REAL,
                        secondary_device_detected_ratio REAL,
                        hand_device_interaction_time REAL,
                        face_identity_switch_rate REAL,
                        face_detected BOOLEAN
                    )
                ''')
                
                # Productivity sessions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS productivity_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        start_time DATETIME NOT NULL,
                        end_time DATETIME,
                        session_type TEXT,
                        productivity_score REAL,
                        focus_level REAL,
                        break_count INTEGER DEFAULT 0,
                        total_keystrokes INTEGER DEFAULT 0
                    )
                ''')
                
                # Daily summaries table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS daily_summaries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date DATE NOT NULL UNIQUE,
                        total_active_time REAL,
                        total_keystrokes INTEGER,
                        productivity_score REAL,
                        focus_score REAL,
                        break_count INTEGER,
                        top_application TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                self.logger.info("Database initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Error initializing database: {e}")
            raise
    
    def insert_keystroke_data(self, data: Dict[str, Any]):
        """Insert keystroke activity data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO keystroke_activity 
                    (timestamp, typing_speed, key_count, error_count, burstiness, active_window, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data.get('timestamp', datetime.now()),
                    data.get('typing_speed', 0.0),
                    data.get('key_count', 0),
                    data.get('error_count', 0),
                    data.get('burstiness', 0.0),
                    data.get('active_window', ''),
                    data.get('is_active', True)
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error inserting keystroke data: {e}")
    
    def insert_window_data(self, data: Dict[str, Any]):
        """Insert window activity data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO window_activity 
                    (timestamp, window_title, application_name, category, duration_seconds)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    data.get('timestamp', datetime.now()),
                    data.get('window_title', ''),
                    data.get('application_name', ''),
                    data.get('category', 'other'),
                    data.get('duration_seconds', 0.0)
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error inserting window data: {e}")
    
    def insert_attention_data(self, data: Dict[str, Any]):
        """Insert attention tracking data (New Schema)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO attention_data 
                    (timestamp, gaze_on_screen_ratio, gaze_dispersion, gaze_shift_rate, blink_rate, 
                     eye_closure_ratio, head_pose_variance, head_turn_rate, face_screen_distance, 
                     posture_stability, secondary_device_detected_ratio, hand_device_interaction_time, 
                     face_identity_switch_rate, face_detected)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data.get('timestamp', datetime.now()),
                    data.get('gaze_on_screen_ratio', 0.0),
                    data.get('gaze_dispersion', 0.0),
                    data.get('gaze_shift_rate', 0.0),
                    data.get('blink_rate', 0.0),
                    data.get('eye_closure_ratio', 0.0),
                    data.get('head_pose_variance', 0.0),
                    data.get('head_turn_rate', 0.0),
                    data.get('face_screen_distance', 0.0),
                    data.get('posture_stability', 0.0),
                    data.get('secondary_device_detected_ratio', 0.0),
                    data.get('hand_device_interaction_time', 0.0),
                    data.get('face_identity_switch_rate', 0.0),
                    data.get('face_detected', False)
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error inserting attention data: {e}")
    
    def get_keystroke_data(self, start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
        """Retrieve keystroke activity data"""
        try:
            if not start_date:
                start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            if not end_date:
                end_date = datetime.now()
                
            query = '''
                SELECT * FROM keystroke_activity
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp
            '''
            
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query(query, conn, params=[start_date, end_date])
                
                # Convert timestamp string back to datetime objects
                if not df.empty and 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    
            return df
            
        except Exception as e:
            self.logger.error(f"Error retrieving keystroke data: {e}")
            return pd.DataFrame()
    
    def _migrate_attention_schema(self):
        """Migrate attention_data table to new schema if needed"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(attention_data)")
                columns = [info[1] for info in cursor.fetchall()]
                
                # Check if old schema exists (looking for 'attention_score')
                if 'attention_score' in columns:
                    self.logger.info("Migrating attention_data: backing up old table and creating new schema")
                    
                    # Rename old table
                    cursor.execute("ALTER TABLE attention_data RENAME TO attention_data_backup_v1")
                    
                    # Create new table
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS attention_data (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            timestamp DATETIME NOT NULL,
                            gaze_on_screen_ratio REAL,
                            gaze_dispersion REAL,
                            gaze_shift_rate REAL,
                            blink_rate REAL,
                            eye_closure_ratio REAL,
                            head_pose_variance REAL,
                            head_turn_rate REAL,
                            face_screen_distance REAL,
                            posture_stability REAL,
                            secondary_device_detected_ratio REAL,
                            hand_device_interaction_time REAL,
                            face_identity_switch_rate REAL,
                            face_detected BOOLEAN
                        )
                    ''')
                    conn.commit()
                    
        except Exception as e:
            self.logger.error(f"Error migrating attention schema: {e}")

    def insert_mouse_data(self, data: Dict[str, Any]):
        """Insert mouse activity data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO mouse_activity 
                    (timestamp, active_window, application_name, move_distance, 
                     avg_velocity, click_count, scroll_count, scroll_direction, idle_ratio)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data.get('timestamp', datetime.now()),
                    data.get('active_window', 'Unknown'),
                    data.get('application_name', 'Unknown'),
                    data.get('move_distance', 0.0),
                    data.get('avg_velocity', 0.0),
                    data.get('click_count', 0),
                    data.get('scroll_count', 0),
                    data.get('scroll_direction', 'NONE'),
                    data.get('idle_ratio', 0.0)
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error inserting mouse data: {e}")

    def get_mouse_data(self, start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
        """Retrieve mouse activity data"""
        try:
            if not start_date:
                start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            if not end_date:
                end_date = datetime.now()
                
            query = '''
                SELECT * FROM mouse_activity 
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp
            '''
            
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query(query, conn, params=[start_date, end_date])
                
                if not df.empty and 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    
            return df
            
        except Exception as e:
            self.logger.error(f"Error retrieving mouse data: {e}")
            return pd.DataFrame()
    
    def get_window_data(self, start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
        """Retrieve window activity data"""
        try:
            if not start_date:
                start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            if not end_date:
                end_date = datetime.now()
                
            query = '''
                SELECT * FROM window_activity 
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp
            '''
            
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query(query, conn, params=[start_date, end_date])
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                return df
                
        except Exception as e:
            self.logger.error(f"Error retrieving window data: {e}")
            return pd.DataFrame()
    
    def get_attention_data(self, start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
        """Retrieve attention data"""
        try:
            if not start_date:
                start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            if not end_date:
                end_date = datetime.now()
                
            query = '''
                SELECT timestamp, gaze_on_screen_ratio, gaze_dispersion, gaze_shift_rate, blink_rate, 
                       eye_closure_ratio, head_pose_variance, head_turn_rate, face_screen_distance, 
                       posture_stability, secondary_device_detected_ratio, hand_device_interaction_time, 
                       face_identity_switch_rate, face_detected
                FROM attention_data 
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp
            '''
            
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query(query, conn, params=[start_date, end_date])
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                return df
                
        except Exception as e:
            self.logger.error(f"Error retrieving attention data: {e}")
            return pd.DataFrame()
    
    def get_app_usage_summary(self, start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
        """Get application usage summary"""
        try:
            if not start_date:
                start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            if not end_date:
                end_date = datetime.now()
                
            query = '''
                SELECT 
                    application_name,
                    category,
                    SUM(duration_seconds) as total_duration,
                    COUNT(*) as session_count
                FROM window_activity 
                WHERE timestamp BETWEEN ? AND ?
                GROUP BY application_name, category
                ORDER BY total_duration DESC
            '''
            
            with sqlite3.connect(self.db_path) as conn:
                return pd.read_sql_query(query, conn, params=[start_date, end_date])
                
        except Exception as e:
            self.logger.error(f"Error retrieving app usage summary: {e}")
            return pd.DataFrame()
    
    def cleanup_old_data(self):
        """Remove data older than retention period"""
        try:
            cutoff_date = datetime.now() - timedelta(days=DATA_RETENTION_DAYS)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                tables = ['keystroke_activity', 'window_activity', 'attention_data']
                for table in tables:
                    cursor.execute(f'DELETE FROM {table} WHERE timestamp < ?', (cutoff_date,))
                
                conn.commit()
                self.logger.info(f"Cleaned up data older than {DATA_RETENTION_DAYS} days")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up old data: {e}")
    
    def get_productivity_stats(self, date: datetime = None) -> Dict[str, Any]:
        """Get productivity statistics for a given date"""
        try:
            if not date:
                date = datetime.now().date()
            else:
                date = date.date() if isinstance(date, datetime) else date
            
            start_time = datetime.combine(date, datetime.min.time())
            end_time = datetime.combine(date, datetime.max.time())
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get keystroke stats
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_entries,
                        SUM(key_count) as total_keystrokes,
                        AVG(typing_speed) as avg_typing_speed,
                        SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_periods
                    FROM keystroke_activity 
                    WHERE timestamp BETWEEN ? AND ?
                ''', (start_time, end_time))
                
                keystroke_stats = cursor.fetchone()
                
                # Get attention stats
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_readings,
                        AVG(gaze_on_screen_ratio) as avg_attention,
                        AVG(blink_rate) as avg_blink_rate,
                        SUM(CASE WHEN face_detected = 1 THEN 1 ELSE 0 END) as face_detected_count
                    FROM attention_data 
                    WHERE timestamp BETWEEN ? AND ?
                ''', (start_time, end_time))
                
                attention_stats = cursor.fetchone()
                
                return {
                    'date': date,
                    'total_keystrokes': keystroke_stats[1] or 0,
                    'avg_typing_speed': keystroke_stats[2] or 0,
                    'active_periods': keystroke_stats[3] or 0,
                    'avg_attention': attention_stats[1] or 0,
                    'avg_blink_rate': attention_stats[2] or 0,
                    'face_detection_rate': (attention_stats[3] / attention_stats[0]) if attention_stats[0] > 0 else 0
                }
                
        except Exception as e:
            self.logger.error(f"Error getting productivity stats: {e}")
            return {}

if __name__ == "__main__":
    # Test the database manager
    db = DatabaseManager()
    print("Database manager initialized successfully!")
    
    # Test data insertion
    test_keystroke_data = {
        'timestamp': datetime.now(),
        'typing_speed': 45.5,
        'key_count': 10,
        'active_window': 'Test Window',
        'is_active': True
    }
    
    db.insert_keystroke_data(test_keystroke_data)
    print("Test data inserted successfully!")
    
    # Test data retrieval
    df = db.get_keystroke_data()
    print(f"Retrieved {len(df)} keystroke records")
    print(df.head() if not df.empty else "No data found")
