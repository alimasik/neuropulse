from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from ..database import get_db
from ..models import BiometrySample, Session as SessionModel
from ..schemas import IngestRequest, IngestResponse

router = APIRouter()


@router.post("/ingest", response_model=IngestResponse, status_code=202)
def ingest_biometry(request: IngestRequest, db: Session = Depends(get_db)):
    # Verify session exists
    session = db.query(SessionModel).filter(SessionModel.id == request.session_id).first()
    if not session:
        # Auto-create session for convenience
        session = SessionModel(
            id=request.session_id,
            user_id=1,
            context="free"
        )
        db.add(session)
        db.commit()
        db.refresh(session)

    count = 0
    for sample in request.samples:
        try:
            ts = datetime.fromisoformat(sample.ts.replace("Z", "+00:00"))
        except Exception:
            ts = datetime.utcnow()

        db_sample = BiometrySample(
            session_id=request.session_id,
            ts=ts,
            hr=sample.hr,
            hrv_sdnn_ms=sample.hrv_sdnn_ms,
            accel_mag=sample.accel_mag,
            gsr_us=sample.gsr_us,
        )
        db.add(db_sample)
        count += 1

    db.commit()
    return IngestResponse(received=count, session_id=request.session_id)
