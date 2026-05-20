from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class BiometrySampleIn(BaseModel):
    ts: str
    hr: int
    hrv_sdnn_ms: float
    accel_mag: float
    gsr_us: Optional[float] = None
    # user_id и session_id — необязательные, основные значения берутся из обёртки запроса.
    # Поля оставлены для обратной совместимости со старыми клиентами.
    user_id: Optional[int] = None
    session_id: Optional[int] = None


class IngestRequest(BaseModel):
    session_id: int
    samples: List[BiometrySampleIn]


class IngestResponse(BaseModel):
    received: int
    session_id: int


class PredictRequest(BaseModel):
    session_id: int
    user_id: int = 1
    samples: List[BiometrySampleIn]


class PredictResponse(BaseModel):
    label: int
    label_name: str
    confidence: float
    recommended_action: Optional[str]
    features: dict


class EpisodeOut(BaseModel):
    id: int
    started_at: datetime
    ended_at: Optional[datetime]
    severity: int
    trigger_guess: Optional[str]
    notes: Optional[str]

    class Config:
        from_attributes = True


class PredictionOut(BaseModel):
    id: int
    ts: datetime
    label: int
    confidence: float
    recommended: Optional[str]

    class Config:
        from_attributes = True


class Stats7d(BaseModel):
    episodes_count: int
    avg_severity: float
    top_trigger: Optional[str]
    critical_events: int


class HistoryResponse(BaseModel):
    episodes: List[EpisodeOut]
    recent_predictions: List[PredictionOut]
    stats_7d: Stats7d


class UserCreate(BaseModel):
    name: str
    baseline_hr: float = 72.0
    baseline_hrv: float = 45.0


class UserOut(BaseModel):
    id: int
    name: str
    baseline_hr: float
    baseline_hrv: float
    created_at: datetime

    class Config:
        from_attributes = True
