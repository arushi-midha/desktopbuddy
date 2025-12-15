import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"

# Database settings
DATABASE_PATH = DATA_DIR / "deskbuddy.db"

# Data collection settings
KEYSTROKE_LOG_INTERVAL = 1.0  # seconds
WINDOW_TRACK_INTERVAL = 5.0   # seconds
WEBCAM_CAPTURE_INTERVAL = 2.0 # seconds

# Webcam settings
WEBCAM_WIDTH = 640
WEBCAM_HEIGHT = 480
FACE_DETECTION_CONFIDENCE = 0.5
BLINK_THRESHOLD = 0.25

# Privacy settings
STORE_FACIAL_IMAGES = False  # Only store metadata, not actual images
ANONYMIZE_DATA = True
DATA_RETENTION_DAYS = 30

# Dashboard settings
DASHBOARD_UPDATE_INTERVAL = 10  # seconds
DEFAULT_TIME_RANGE = "today"    # today, week, month

# Productivity thresholds
IDLE_THRESHOLD = 60  # seconds of no activity to consider idle
BREAK_REMINDER_INTERVAL = 3600  # seconds (1 hour)
FOCUS_SESSION_MIN_DURATION = 25 * 60  # 25 minutes

# Application categories for tracking
APP_CATEGORIES = {
    'productivity': [
        'notepad', 'code', 'visual studio', 'pycharm', 'intellij',
        'sublime', 'atom', 'vim', 'emacs', 'word', 'excel', 'powerpoint',
        'google docs', 'notion', 'obsidian', 'typora', 'antigravity'
    ],
    'communication': [
        'slack', 'teams', 'discord', 'zoom', 'skype', 'whatsapp',
        'telegram', 'outlook', 'gmail', 'mail'
    ],
    'browsing': [
        'chrome', 'firefox', 'safari', 'edge', 'browser', 'brave', 'comet'
    ],
    'entertainment': [
        'youtube', 'netflix', 'spotify', 'vlc', 'media player',
        'steam', 'game', 'twitch'
    ],
    'other': []  # Fallback category
}

# Logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.FileHandler',
            'filename': LOGS_DIR / 'app.log',
            'mode': 'a',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default', 'file'],
            'level': 'INFO',
            'propagate': False
        }
    }
}

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
