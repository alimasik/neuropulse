from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, default="User")
    baseline_hr = Column(Float, nullable=False, default=72.0)
    baseline_hrv = Column(Float, nullable=False, default=45.0)
    created_at = Column(DateTime, server_default=func.now())

    sessions = relationship("Session", back_populates="user")
    episodes = relationship("Episode", back_populates="user")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    started_at = Column(DateTime, server_default=func.now())
    ended_at = Column(DateTime, nullable=True)
    context = Column(String, nullable=True)  # metro/school/home/free

    user = relationship("User", back_populates="sessions")
    samples = relationship("BiometrySample", back_populates="session")
    predictions = relationship("Prediction", back_populates="session")


class BiometrySample(Base):
    __tablename__ = "biometry_samples"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    ts = Column(DateTime, server_default=func.now())
    hr = Column(Integer, nullable=False)
    hrv_sdnn_ms = Column(Float, nullable=False)
    accel_mag = Column(Float, nullable=False)
    gsr_us = Column(Float, nullable=True)

    session = relationship("Session", back_populates="samples")


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    ts = Column(DateTime, server_default=func.now())
    label = Column(Integer, nullable=False)  # 0/1/2
    confidence = Column(Float, nullable=False)
    recommended = Column(String, nullable=True)  # breathing/quiet_route/aac/null

    session = relationship("Session", back_populates="predictions")


class Episode(Base):
    __tablename__ = "episodes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    started_at = Column(DateTime, server_default=func.now())
    ended_at = Column(DateTime, nullable=True)
    severity = Column(Integer, nullable=False)  # 1-3
    trigger_guess = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    user = relationship("User", back_populates="episodes")
