from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from src.backend.dependencies import get_db_manager
from src.backend.models import KeystrokeLog, WindowActivity, AppUsageStats, MouseActivity
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
    if not start_date:
        # Default to last 180 days if not specified
        from datetime import timedelta
        start_date = datetime.now() - timedelta(days=180)
        
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
    if not start_date:
        # Default to last 180 days if not specified
        from datetime import timedelta
        start_date = datetime.now() - timedelta(days=180)

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
    if not start_date:
        # Default to last 180 days if not specified
        from datetime import timedelta
        start_date = datetime.now() - timedelta(days=180)

    df = db.get_app_usage_summary(start_date, end_date)
    if df.empty:
        return []
    return df.to_dict('records')
