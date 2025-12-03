from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from datetime import datetime
from src.backend.dependencies import get_db_manager
from src.backend.models import KeystrokeLog, WindowActivity, AppUsageStats
from src.data_processing.database_manager import DatabaseManager

router = APIRouter(
    prefix="/api/activity",
    tags=["activity"]
)

@router.get("/keystrokes", response_model=List[KeystrokeLog])
async def get_keystrokes(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: DatabaseManager = Depends(get_db_manager)
):
    """Get keystroke logs for a specific time range"""
    df = db.get_keystroke_data(start_date, end_date)
    if df.empty:
        return []
    return df.to_dict('records')

@router.get("/windows", response_model=List[WindowActivity])
async def get_windows(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: DatabaseManager = Depends(get_db_manager)
):
    """Get window activity logs for a specific time range"""
    df = db.get_window_data(start_date, end_date)
    if df.empty:
        return []
    return df.to_dict('records')

@router.get("/app-usage", response_model=List[AppUsageStats])
async def get_app_usage(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: DatabaseManager = Depends(get_db_manager)
):
    """Get aggregated application usage statistics"""
    df = db.get_app_usage_summary(start_date, end_date)
    if df.empty:
        return []
    return df.to_dict('records')
