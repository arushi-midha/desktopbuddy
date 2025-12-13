from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional
from datetime import datetime
from src.backend.dependencies import get_data_processor, get_db_manager
from src.backend.models import DailySummary
from src.data_processing.data_processor import DataProcessor
from src.data_processing.database_manager import DatabaseManager

router = APIRouter(
    prefix="/api/analytics",
    tags=["analytics"]
)

@router.get("/daily/{date}")
async def get_daily_analysis(
    date: datetime,
    processor: DataProcessor = Depends(get_data_processor)
):
    """Get detailed daily analysis and insights"""
    summary = processor.get_daily_summary(date)
    if not summary:
        raise HTTPException(status_code=404, detail="No data available for this date")
    return summary

@router.get("/weekly")
async def get_weekly_trends(
    end_date: Optional[datetime] = None,
    processor: DataProcessor = Depends(get_data_processor)
):
    """Get weekly trend analysis"""
    if not end_date:
        end_date = datetime.now()
    
    trends = processor.get_weekly_trends(end_date)
    if not trends:
        raise HTTPException(status_code=404, detail="No weekly data available")
    return trends

@router.get("/productivity/stats")
async def get_productivity_stats(
    date: Optional[datetime] = None,
    db: DatabaseManager = Depends(get_db_manager)
):
    """Get productivity statistics for a specific date"""
    stats = db.get_productivity_stats(date)
    if not stats:
        raise HTTPException(status_code=404, detail="No stats available")
    return stats
