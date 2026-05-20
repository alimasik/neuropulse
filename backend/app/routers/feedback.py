from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel
from ..database import get_db
from ..models import Episode, Prediction, Session as SessionModel

router = APIRouter()


class FeedbackRequest(BaseModel):
    prediction_id: int
    helpful: bool
    user_state: str = "ok"


@router.post("/feedback")
def submit_feedback(req: FeedbackRequest, db: Session = Depends(get_db)):
    pred = db.query(Prediction).filter(Prediction.id == req.prediction_id).first()
    if pred and req.user_state == "ok":
        # Резолвим user_id через сессию, к которой привязано предсказание
        session = (
            db.query(SessionModel)
            .filter(SessionModel.id == pred.session_id)
            .first()
        )
        if session:
            open_ep = (
                db.query(Episode)
                .filter(
                    Episode.user_id == session.user_id,
                    Episode.ended_at.is_(None),
                )
                .order_by(Episode.started_at.desc())
                .first()
            )
            if open_ep:
                open_ep.ended_at = datetime.utcnow()
                db.commit()

    return {"ok": True, "prediction_id": req.prediction_id}
