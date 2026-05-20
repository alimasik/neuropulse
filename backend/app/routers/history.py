from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional
from ..database import get_db
from ..models import Episode, Prediction, Session as SessionModel
from ..schemas import HistoryResponse, EpisodeOut, PredictionOut, Stats7d

router = APIRouter()


@router.get("/history", response_model=HistoryResponse)
def get_history(
    user_id: int = Query(default=1),
    limit: int = Query(default=50),
    db: Session = Depends(get_db)
):
    # Get episodes for user
    episodes = (
        db.query(Episode)
        .filter(Episode.user_id == user_id)
        .order_by(Episode.started_at.desc())
        .limit(limit)
        .all()
    )

    # Get recent predictions via sessions
    user_sessions = (
        db.query(SessionModel.id)
        .filter(SessionModel.user_id == user_id)
        .subquery()
    )
    recent_predictions = (
        db.query(Prediction)
        .filter(Prediction.session_id.in_(user_sessions))
        .order_by(Prediction.ts.desc())
        .limit(limit)
        .all()
    )

    # Stats for last 7 days
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    episodes_7d = (
        db.query(Episode)
        .filter(Episode.user_id == user_id, Episode.started_at >= seven_days_ago)
        .all()
    )

    episodes_count = len(episodes_7d)
    avg_severity = (
        sum(e.severity for e in episodes_7d) / episodes_count
        if episodes_count > 0
        else 0.0
    )

    # Find top trigger
    trigger_counts: dict = {}
    for ep in episodes_7d:
        if ep.trigger_guess:
            trigger_counts[ep.trigger_guess] = trigger_counts.get(ep.trigger_guess, 0) + 1
    top_trigger = max(trigger_counts, key=trigger_counts.get) if trigger_counts else None

    # Count critical events (label=2) in last 7 days
    critical_events = (
        db.query(Prediction)
        .filter(
            Prediction.session_id.in_(user_sessions),
            Prediction.label == 2,
            Prediction.ts >= seven_days_ago,
        )
        .count()
    )

    stats = Stats7d(
        episodes_count=episodes_count,
        avg_severity=round(avg_severity, 2),
        top_trigger=top_trigger,
        critical_events=critical_events,
    )

    return HistoryResponse(
        episodes=[EpisodeOut.model_validate(e) for e in episodes],
        recent_predictions=[PredictionOut.model_validate(p) for p in recent_predictions],
        stats_7d=stats,
    )
