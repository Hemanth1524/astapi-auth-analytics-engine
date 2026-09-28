from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.routers.auth import get_current_user
from app import models, schemas

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])

@router.get("/summary", response_model=schemas.AnalyticsSummary)
def get_analytics_summary(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    total = db.query(func.count(models.RequestMetric.id)).scalar() or 0
    avg_latency = db.query(func.avg(models.RequestMetric.process_time_ms)).scalar() or 0.0
    errors = db.query(func.count(models.RequestMetric.id)).filter(models.RequestMetric.status_code >= 400).scalar() or 0

    return {
        "total_requests": total,
        "avg_latency_ms": round(float(avg_latency), 2),
        "error_count": errors
    }
