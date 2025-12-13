from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class KeystrokeLog(BaseModel):
    id: int
    timestamp: datetime
    typing_speed: float
    key_count: int
    error_count: int = 0
    burstiness: float = 0.0
    active_window: Optional[str] = None
    is_active: bool

class MouseActivity(BaseModel):
    id: int
    timestamp: datetime
    active_window: Optional[str] = None
    application_name: Optional[str] = None
    move_distance: float
    avg_velocity: float
    click_count: int
    scroll_count: int
    scroll_direction: Optional[str] = None
    idle_ratio: float

class WindowActivity(BaseModel):
    id: int
    timestamp: datetime
    window_title: Optional[str] = None
    application_name: Optional[str] = None
    category: Optional[str] = None
    duration_seconds: float

class AttentionData(BaseModel):
    id: int
    timestamp: datetime
    face_detected: bool
    attention_score: float
    blink_rate: float
    looking_at_screen: bool
    head_pose_x: float
    head_pose_y: float
    head_pose_z: float

class DailySummary(BaseModel):
    date: datetime
    total_keystrokes: int
    avg_typing_speed: float
    active_periods: int
    avg_attention: float
    avg_blink_rate: float
    face_detection_rate: float

class AppUsageStats(BaseModel):
    application_name: str
    category: str
    total_duration: float
    session_count: int
