from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, SessionLocal
from . import models
from .routers import ingest, predict, history, export, feedback

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="NeuroPulse API",
    description="Biometric monitoring for autism/Tourette syndrome",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router, tags=["ingest"])
app.include_router(predict.router, tags=["predict"])
app.include_router(history.router, tags=["history"])
app.include_router(export.router, tags=["export"])
app.include_router(feedback.router, tags=["feedback"])


@app.on_event("startup")
def seed_data():
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.id == 1).first()
        if not user:
            user = models.User(
                id=1,
                name="Demo User",
                baseline_hr=72.0,
                baseline_hrv=45.0,
            )
            db.add(user)

            # Seed a default session
            session = models.Session(
                id=1,
                user_id=1,
                context="home",
            )
            db.add(session)

            # Seed some demo episodes
            from datetime import datetime, timedelta
            now = datetime.utcnow()
            episodes = [
                models.Episode(
                    user_id=1,
                    started_at=now - timedelta(days=2, hours=3),
                    ended_at=now - timedelta(days=2, hours=2, minutes=30),
                    severity=2,
                    trigger_guess="metro",
                    notes="Loud noises at station",
                ),
                models.Episode(
                    user_id=1,
                    started_at=now - timedelta(days=5, hours=1),
                    ended_at=now - timedelta(days=4, hours=23),
                    severity=1,
                    trigger_guess="school",
                    notes="Crowded hallway",
                ),
                models.Episode(
                    user_id=1,
                    started_at=now - timedelta(days=7, hours=5),
                    ended_at=now - timedelta(days=7, hours=4),
                    severity=3,
                    trigger_guess="mall",
                    notes="Sensory overload at shopping centre",
                ),
            ]
            for ep in episodes:
                db.add(ep)

            db.commit()
    finally:
        db.close()


@app.get("/")
def root():
    return {"message": "NeuroPulse API", "version": "0.1.0", "status": "ok"}


@app.get("/health")
def health():
    return {"status": "healthy"}
