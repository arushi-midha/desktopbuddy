from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from datetime import datetime
from src.backend.dependencies import get_db_manager
from src.backend.models import AttentionData
from src.data_processing.database_manager import DatabaseManager

router = APIRouter(
    prefix="/api/attention",
    tags=["attention"]
)

@router.get("/logs", response_model=List[AttentionData])
async def get_attention_logs(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: DatabaseManager = Depends(get_db_manager)
):
    """Get attention data logs for a specific time range"""
    df = db.get_attention_data(start_date, end_date)
    if df.empty:
        return []
    return df.to_dict('records')
