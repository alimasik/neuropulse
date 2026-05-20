import sys
import pathlib

# Корень репозитория: routers/ → app/ → backend/ → <root>
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from ..database import get_db
from ..models import Prediction, Session as SessionModel, User
from ..schemas import PredictRequest, PredictResponse

router = APIRouter()


@router.post("/predict", response_model=PredictResponse)
def predict_status(request: PredictRequest, db: Session = Depends(get_db)):
    # Get user baseline
    user = db.query(User).filter(User.id == request.user_id).first()
    baseline_hr = user.baseline_hr if user else 72.0
    baseline_hrv = user.baseline_hrv if user else 45.0

    # Ensure session exists
    session = db.query(SessionModel).filter(SessionModel.id == request.session_id).first()
    if not session:
        session = SessionModel(
            id=request.session_id,
            user_id=request.user_id,
            context="free"
        )
        db.add(session)
        db.commit()

    # Convert samples to dict list
    samples = [s.model_dump() for s in request.samples]

    from ml_core.feature_extractor import extract_features
    from ml_core.model_predict import predict
    features = extract_features(samples, baseline_hr=baseline_hr, baseline_hrv=baseline_hrv)
    result = predict(features)

    # Save prediction
    pred = Prediction(
        session_id=request.session_id,
        ts=datetime.utcnow(),
        label=result["label"],
        confidence=result["confidence"],
        recommended=result["recommended_action"],
    )
    db.add(pred)
    db.commit()

    return PredictResponse(
        label=result["label"],
        label_name=result["label_name"],
        confidence=result["confidence"],
        recommended_action=result["recommended_action"],
        features=features,
    )
