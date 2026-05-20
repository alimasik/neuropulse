"""
Feature extraction from biometry sample windows.
"""
from typing import List, Dict, Any, Optional
import statistics


def extract_features(
    samples: List[Dict[str, Any]],
    baseline_hr: float = 72.0,
    baseline_hrv: float = 45.0,
) -> Dict[str, float]:
    """
    Extract statistical features from a window of biometry samples.

    Args:
        samples: List of dicts with keys hr, hrv_sdnn_ms, accel_mag, gsr_us
        baseline_hr: User's resting heart rate
        baseline_hrv: User's baseline HRV (SDNN in ms)

    Returns:
        Dict of feature name → float value
    """
    if not samples:
        return _zero_features()

    hrs = [float(s["hr"]) for s in samples if "hr" in s]
    hrvs = [float(s["hrv_sdnn_ms"]) for s in samples if "hrv_sdnn_ms" in s]
    accels = [float(s["accel_mag"]) for s in samples if "accel_mag" in s]
    gsrs = [float(s["gsr_us"]) for s in samples if s.get("gsr_us") is not None]

    # Heart rate features
    hr_mean = statistics.mean(hrs) if hrs else baseline_hr
    hr_delta = hr_mean - baseline_hr

    # HRV features
    hrv_sdnn = statistics.mean(hrvs) if hrvs else baseline_hrv
    hrv_drop_pct = max(0.0, (baseline_hrv - hrv_sdnn) / baseline_hrv) if baseline_hrv > 0 else 0.0

    # Accelerometer features
    accel_var = statistics.variance(accels) if len(accels) > 1 else 0.0
    accel_spikes = sum(1 for a in accels if a > 0.5)

    # GSR features
    gsr_mean = statistics.mean(gsrs) if gsrs else 0.0
    gsr_slope = _compute_slope(gsrs) if len(gsrs) >= 2 else 0.0

    return {
        "hr_mean": round(hr_mean, 2),
        "hr_delta": round(hr_delta, 2),
        "hrv_sdnn": round(hrv_sdnn, 2),
        "hrv_drop_pct": round(hrv_drop_pct, 4),
        "accel_var": round(accel_var, 4),
        "accel_spikes": float(accel_spikes),
        "gsr_mean": round(gsr_mean, 2),
        "gsr_slope": round(gsr_slope, 4),
    }


def _compute_slope(values: List[float]) -> float:
    """Compute linear regression slope using least squares."""
    n = len(values)
    if n < 2:
        return 0.0
    xs = list(range(n))
    x_mean = sum(xs) / n
    y_mean = sum(values) / n
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, values))
    denominator = sum((x - x_mean) ** 2 for x in xs)
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _zero_features() -> Dict[str, float]:
    return {
        "hr_mean": 72.0,
        "hr_delta": 0.0,
        "hrv_sdnn": 45.0,
        "hrv_drop_pct": 0.0,
        "accel_var": 0.0,
        "accel_spikes": 0.0,
        "gsr_mean": 0.0,
        "gsr_slope": 0.0,
    }
